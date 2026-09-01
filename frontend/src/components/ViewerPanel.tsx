import { Canvas, useThree } from '@react-three/fiber';
import { FlyControls, OrbitControls } from '@react-three/drei';
import { useCallback, useEffect, useRef, useState } from 'react';
import type { Project } from '../types';
import { projectApi } from '../services/api';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

interface Props { project: Project | null; }
type ViewMode = 'orbit' | 'fly';
type RenderMode = 'rgb' | 'relief' | 'wire';
type CameraPreset = 'isometric' | 'top' | 'front';

/**
 * DepthWizard backend stores vertices as [image_x, image_y, elevation].
 * Convert them to Three.js's Y-up convention: [x, elevation, -image_y].
 * The old viewer changed vertices without refreshing the geometry bounds,
 * which can make WebGL frustum-cull the entire terrain. This version
 * explicitly recomputes bounds after every vertex transformation.
 */
function prepareTerrain(scene: THREE.Object3D, exaggeration: number) {
  scene.traverse((child) => {
    if (!(child instanceof THREE.Mesh) || !child.geometry?.attributes.position) return;

    const geometry = child.geometry;
    const position = geometry.attributes.position as THREE.BufferAttribute;
    const v = new THREE.Vector3();

    for (let i = 0; i < position.count; i += 1) {
      v.fromBufferAttribute(position, i);
      position.setXYZ(i, v.x, v.z, -v.y);
    }
    position.needsUpdate = true;

    geometry.computeVertexNormals();
    geometry.computeBoundingBox();
    geometry.computeBoundingSphere();

    child.castShadow = true;
    child.receiveShadow = true;
    child.frustumCulled = false;

    const sources = Array.isArray(child.material) ? child.material : [child.material];
    const materials = sources.map((source) => {
      const material = source.clone() as THREE.MeshStandardMaterial;
      material.userData.dwOriginalMap = material.map ?? null;
      material.side = THREE.DoubleSide;
      material.roughness = 0.78;
      material.metalness = 0.02;
      return material;
    });
    child.material = Array.isArray(child.material) ? materials : materials[0];
  });

  // Work in a predictable local coordinate system.
  const box = new THREE.Box3().setFromObject(scene);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const footprint = Math.max(size.x, size.z, 1);
  const horizontalScale = 12 / footprint;

  scene.position.sub(center);
  scene.scale.set(horizontalScale, horizontalScale * 52 * exaggeration, horizontalScale);
  scene.updateMatrixWorld(true);

  // Recalculate world bounds after scaling and keep the lowest point on Z=0 plane.
  const finalBox = new THREE.Box3().setFromObject(scene);
  scene.position.y -= finalBox.min.y;
  scene.updateMatrixWorld(true);

  scene.traverse((child) => {
    if (child instanceof THREE.Mesh) {
      child.frustumCulled = false;
      child.geometry.computeBoundingBox();
      child.geometry.computeBoundingSphere();
    }
  });

  return finalBox;
}

function SurfaceMaterial({ scene, mode }: { scene: THREE.Object3D; mode: RenderMode }) {
  useEffect(() => {
    scene.traverse((child) => {
      if (!(child instanceof THREE.Mesh)) return;
      const list = Array.isArray(child.material) ? child.material : [child.material];
      list.forEach((mat) => {
        const m = mat as THREE.MeshStandardMaterial;
        const original = (m.userData.dwOriginalMap as THREE.Texture | null) ?? null;
        if (mode === 'relief') {
          m.wireframe = false;
          m.map = null;
          m.color.set('#9ec9d8');
          m.roughness = 0.92;
        } else if (mode === 'wire') {
          m.wireframe = true;
          m.map = null;
          m.color.set('#53c7ef');
        } else {
          m.wireframe = false;
          m.map = original;
          m.color.set('#ffffff');
        }
        m.needsUpdate = true;
      });
    });
  }, [scene, mode]);
  return null;
}

function Terrain({ url, exaggeration, renderMode, onLoaded, onError }: {
  url: string;
  exaggeration: number;
  renderMode: RenderMode;
  onLoaded: (object: THREE.Object3D) => void;
  onError: (message: string) => void;
}) {
  const [object, setObject] = useState<THREE.Object3D | null>(null);

  useEffect(() => {
    let alive = true;
    setObject(null);
    onError('');

    const loader = new GLTFLoader();
    loader.load(
      `${url}${url.includes('?') ? '&' : '?'}viewer=dw5`,
      (gltf) => {
        if (!alive) return;
        try {
          const meshes: THREE.Mesh[] = [];
          gltf.scene.traverse((child) => { if (child instanceof THREE.Mesh) meshes.push(child); });
          if (!meshes.length) throw new Error('The generated GLB contains no mesh geometry.');

          prepareTerrain(gltf.scene, exaggeration);
          const bounds = new THREE.Box3().setFromObject(gltf.scene);
          const size = bounds.getSize(new THREE.Vector3());
          if (!Number.isFinite(size.x + size.y + size.z) || size.length() < 0.001) {
            throw new Error('The generated terrain has invalid or zero-sized geometry.');
          }

          setObject(gltf.scene);
          onLoaded(gltf.scene);
        } catch (e) {
          onError(e instanceof Error ? e.message : 'Unable to prepare the generated terrain.');
        }
      },
      undefined,
      (error) => {
        if (!alive) return;
        console.error('DepthWizard terrain load failed:', error);
        onError('Unable to load the generated terrain mesh. Check that the backend is running.');
      },
    );

    return () => { alive = false; };
  }, [url, onLoaded, onError]);

  useEffect(() => {
    if (!object) return;
    object.scale.y = object.scale.x * 52 * exaggeration;
    object.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(object);
    object.position.y -= box.min.y;
    object.updateMatrixWorld(true);
  }, [object, exaggeration]);

  return object ? <>
    <primitive object={object} />
    <SurfaceMaterial scene={object} mode={renderMode} />
  </> : null;
}

function CameraRig({ target, resetToken, preset }: {
  target: THREE.Object3D | null;
  resetToken: number;
  preset: CameraPreset;
}) {
  const { camera } = useThree();
  const controls = useRef<any>(null);

  useEffect(() => {
    if (!target) return;
    target.updateMatrixWorld(true);

    const box = new THREE.Box3().setFromObject(target);
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    const maxDimension = Math.max(size.x, size.y, size.z, 1);
    const distance = Math.max(maxDimension * 1.65, 8);
    const perspective = camera as THREE.PerspectiveCamera;

    perspective.near = 0.01;
    perspective.far = Math.max(distance * 20, 500);

    if (preset === 'top') {
      camera.position.set(center.x, center.y + distance * 1.35, center.z + 0.01);
    } else if (preset === 'front') {
      camera.position.set(center.x, center.y + distance * 0.35, center.z + distance * 1.45);
    } else {
      camera.position.set(center.x + distance * 0.95, center.y + distance * 0.78, center.z + distance * 0.95);
    }

    camera.lookAt(center);
    perspective.updateProjectionMatrix();

    if (controls.current) {
      controls.current.target.copy(center);
      controls.current.minDistance = Math.max(maxDimension * 0.12, 1);
      controls.current.maxDistance = Math.max(maxDimension * 8, 100);
      controls.current.update();
    }
  }, [target, resetToken, preset, camera]);

  return <OrbitControls
    ref={controls}
    makeDefault
    enableDamping
    dampingFactor={0.08}
    rotateSpeed={0.65}
    zoomSpeed={0.9}
    panSpeed={0.8}
    screenSpacePanning
    minPolarAngle={0.05}
    maxPolarAngle={Math.PI * 0.49}
  />;
}

function TerrainStage({ project, exaggeration, renderMode, mode, resetToken, preset, onLoaded, onError }: {
  project: Project;
  exaggeration: number;
  renderMode: RenderMode;
  mode: ViewMode;
  resetToken: number;
  preset: CameraPreset;
  onLoaded: (object: THREE.Object3D) => void;
  onError: (message: string) => void;
}) {
  const [terrain, setTerrain] = useState<THREE.Object3D | null>(null);
  const stableLoaded = useCallback((object: THREE.Object3D) => { setTerrain(object); onLoaded(object); }, [onLoaded]);
  const stableError = useCallback((message: string) => onError(message), [onError]);

  return <>
    <color attach="background" args={['#071019']} />
    <ambientLight intensity={0.75} />
    <hemisphereLight intensity={1.15} groundColor="#172735" color="#eef9ff" />
    <directionalLight castShadow position={[7, 14, 8]} intensity={3.2} shadow-mapSize={[2048, 2048]} shadow-bias={-0.0001} shadow-normalBias={0.03} />
    <directionalLight position={[-8, 6, -10]} intensity={1.0} />
    <Terrain url={projectApi.getMeshUrl(project.project_id)} exaggeration={exaggeration} renderMode={renderMode} onLoaded={stableLoaded} onError={stableError} />
    {terrain && <CameraRig target={terrain} resetToken={resetToken} preset={preset} />}
    {mode === 'fly' && <FlyControls movementSpeed={4} rollSpeed={0.2} dragToLook={false} />}
    <gridHelper args={[22, 22, '#294557', '#172a39']} position={[0, -0.04, 0]} />
  </>;
}

export function ViewerPanel({ project }: Props) {
  const [mode, setMode] = useState<ViewMode>('orbit');
  const [renderMode, setRenderMode] = useState<RenderMode>('rgb');
  const [exaggeration, setExaggeration] = useState(1.8);
  const [preset, setPreset] = useState<CameraPreset>('isometric');
  const [resetToken, setResetToken] = useState(0);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState('');
  const [showControls, setShowControls] = useState(true);
  const [fullscreen, setFullscreen] = useState(false);
  const viewerRef = useRef<HTMLDivElement>(null);
  const ready = !!project && ['READY', 'VALIDATED'].includes(project.state);

  const handleLoaded = useCallback(() => { setLoaded(true); setError(''); }, []);
  const handleError = useCallback((message: string) => { setLoaded(false); setError(message); }, []);

  useEffect(() => {
    setLoaded(false);
    setError('');
    setResetToken((v) => v + 1);
  }, [project?.project_id]);

  useEffect(() => {
    const handler = () => setFullscreen(document.fullscreenElement === viewerRef.current);
    document.addEventListener('fullscreenchange', handler);
    return () => document.removeEventListener('fullscreenchange', handler);
  }, []);

  if (!ready || !project) {
    return <div className="viewer-placeholder">
      <div className="empty-orb">◇</div>
      <div className="empty-title">3D terrain workspace</div>
      <div className="empty-copy">Upload an image and run reconstruction. Your generated DSM and textured mesh will appear here.</div>
    </div>;
  }

  const toggleFullscreen = async () => {
    if (!viewerRef.current) return;
    if (document.fullscreenElement) await document.exitFullscreen().catch(() => {});
    else await viewerRef.current.requestFullscreen().catch(() => {});
  };

  const changeMode = (next: ViewMode) => { setMode(next); setResetToken((v) => v + 1); };
  const changePreset = (next: CameraPreset) => { setPreset(next); setResetToken((v) => v + 1); };

  return <div className={`viewer-wrap ${fullscreen ? 'viewer-fullscreen' : ''}`} ref={viewerRef}>
    <div className="viewer-topbar">
      <div className="viewer-heading">
        <div className="eyebrow">RECONSTRUCTION VIEW</div>
        <div className="viewer-title">3D Terrain</div>
        <div className="viewer-subtitle">Interactive surface reconstruction · {project.name}</div>
      </div>
      <div className="viewer-top-actions">
        <span className={`viewer-chip ${loaded ? 'ok' : error ? 'bad' : ''}`}><span className="live-dot" /> {loaded ? 'MODEL READY' : error ? 'MODEL ERROR' : 'LOADING MODEL'}</span>
        <button className="icon-btn" title="Toggle controls" aria-label="Toggle controls" onClick={() => setShowControls((v) => !v)}>☷</button>
        <button className="icon-btn" title="Fullscreen" aria-label="Fullscreen" onClick={toggleFullscreen}>⛶</button>
      </div>
    </div>

    <Canvas
      shadows
      dpr={[1, 1.5]}
      camera={{ position: [14, 10, 14], fov: 42, near: 0.01, far: 1000 }}
      gl={{ antialias: true, powerPreference: 'high-performance' }}
      onCreated={({ gl }) => { gl.setClearColor('#071019', 1); }}
    >
      <TerrainStage project={project} exaggeration={exaggeration} renderMode={renderMode} mode={mode} resetToken={resetToken} preset={preset} onLoaded={handleLoaded} onError={handleError} />
    </Canvas>

    {!loaded && !error && <div className="viewer-loading"><div className="spinner" /><span>Loading generated terrain…</span></div>}
    {error && <div className="viewer-error"><strong>3D mesh unavailable</strong><span>{error}</span><button onClick={() => setResetToken((v) => v + 1)}>Retry</button></div>}

    <div className="viewer-help"><span>Left drag</span> orbit <span>·</span> <span>Wheel</span> zoom <span>·</span> <span>Right drag</span> pan</div>

    {showControls && <div className="viewer-controls">
      <div className="control-block"><div className="control-label">CAMERA</div><div className="segmented"><button className={mode === 'orbit' ? 'active' : ''} onClick={() => changeMode('orbit')}>Orbit</button><button className={mode === 'fly' ? 'active' : ''} onClick={() => changeMode('fly')}>Fly</button></div></div>
      <div className="control-block"><div className="control-label">VIEW</div><div className="segmented"><button className={preset === 'isometric' ? 'active' : ''} onClick={() => changePreset('isometric')}>Iso</button><button className={preset === 'top' ? 'active' : ''} onClick={() => changePreset('top')}>Top</button><button className={preset === 'front' ? 'active' : ''} onClick={() => changePreset('front')}>Front</button></div></div>
      <div className="control-block"><div className="control-label">SURFACE</div><div className="segmented"><button className={renderMode === 'rgb' ? 'active' : ''} onClick={() => setRenderMode('rgb')}>RGB</button><button className={renderMode === 'relief' ? 'active' : ''} onClick={() => setRenderMode('relief')}>Relief</button><button className={renderMode === 'wire' ? 'active' : ''} onClick={() => setRenderMode('wire')}>Wire</button></div></div>
      <div className="control-block relief-block"><div className="control-label"><span>RELIEF</span><strong>{exaggeration.toFixed(1)}×</strong></div><input aria-label="Vertical relief" type="range" min="0.5" max="4" step="0.1" value={exaggeration} onChange={(e) => setExaggeration(Number(e.target.value))} /></div>
      <button className="reset-view" onClick={() => setResetToken((v) => v + 1)}>Reset</button>
    </div>}
  </div>;
}
