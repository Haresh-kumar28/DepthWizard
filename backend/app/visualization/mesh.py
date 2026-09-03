from dataclasses import dataclass
from pathlib import Path
import numpy as np
@dataclass
class TerrainMesh:
    vertices:np.ndarray; faces:np.ndarray; uvs:np.ndarray; vertex_count:int; face_count:int

def generate_terrain_mesh(elevation,max_resolution=768,invalid_mask=None,x_scale=1.0,y_scale=1.0,vertical_scale=1.0):
    z=np.asarray(elevation,dtype=np.float32)
    if z.ndim!=2: raise ValueError('Elevation must be 2D')
    step=max(1,int(np.ceil(max(z.shape)/max_resolution))); z=z[::step,::step]; h,w=z.shape; yy,xx=np.mgrid[0:h,0:w]
    finite=np.isfinite(z) if invalid_mask is None else np.isfinite(z)&(~invalid_mask[::step,::step]); zz=np.where(finite,z,0)
    # Three.js is Y-up: [east/x, elevation/y, north/z].
    v=np.column_stack([(xx*step).ravel()*x_scale,zz.ravel()*vertical_scale,-(yy*step).ravel()*y_scale]).astype(np.float32)
    uv=np.column_stack([xx.ravel()/max(w-1,1),1-yy.ravel()/max(h-1,1)]).astype(np.float32)
    faces=[]
    for y in range(h-1):
      for x in range(w-1):
        i=y*w+x
        if finite[y,x] and finite[y,x+1] and finite[y+1,x] and finite[y+1,x+1]: faces.extend(((i,i+1,i+w),(i+1,i+w+1,i+w)))
    f=np.asarray(faces,dtype=np.int32).reshape(-1,3)
    return TerrainMesh(v,f,uv,len(v),len(f))

def export_glb(mesh,output_path,texture_image=None):
    import trimesh
    tm=trimesh.Trimesh(vertices=mesh.vertices,faces=mesh.faces,process=False)
    if texture_image is not None:
        from PIL import Image
        img=Image.fromarray(texture_image.astype(np.uint8)).convert('RGB'); mat=trimesh.visual.material.PBRMaterial(baseColorTexture=img,roughnessFactor=.8,metallicFactor=0.0)
        tm.visual=trimesh.visual.TextureVisuals(uv=mesh.uvs,material=mat)
    p=Path(output_path); p.parent.mkdir(parents=True,exist_ok=True); tm.export(p,file_type='glb'); return p
