import React, { useEffect, useRef, useState } from 'react';
import type { Project } from '../types';
import { projectApi } from '../services/api';

interface Props { project: Project | null; onProjectChange: (project: Project | null) => void; }

export function ProjectPanel({ project, onProjectChange }: Props) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<number | null>(null);
  const [projectName, setProjectName] = useState('');
  const [loading, setLoading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const savedId = window.localStorage.getItem('depthwizard.projectId');
    if (!savedId || project) return;
    projectApi.getStatus(savedId)
      .then(onProjectChange)
      .catch(() => window.localStorage.removeItem('depthwizard.projectId'));
  }, [onProjectChange, project]);

  useEffect(() => {
    if (project) window.localStorage.setItem('depthwizard.projectId', project.project_id);
  }, [project]);

  useEffect(() => () => {
    if (pollRef.current !== null) window.clearInterval(pollRef.current);
  }, []);

  const handleCreateProject = async () => {
    if (!projectName.trim() || loading) return;
    setLoading(true); setError(null);
    try {
      const created = await projectApi.create(projectName.trim(), 'Single-view elevation reconstruction workspace');
      onProjectChange(created);
      setProjectName('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create project');
    } finally { setLoading(false); }
  };

  const uploadFile = async (file: File) => {
    if (!project || loading) return;
    const valid = /\.(jpg|jpeg|png|tif|tiff)$/i.test(file.name);
    if (!valid) { setError('Please choose a JPG, PNG, or TIFF image.'); return; }
    setLoading(true); setError(null);
    try {
      await projectApi.upload(project.project_id, file);
      onProjectChange(await projectApi.get(project.project_id));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed');
    } finally { setLoading(false); }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) await uploadFile(file);
    e.target.value = '';
  };

  const handleProcess = async () => {
    if (!project || loading) return;
    setLoading(true); setError(null);
    try {
      await projectApi.process(project.project_id);
      pollRef.current = window.setInterval(async () => {
        try {
          const status = await projectApi.getStatus(project.project_id);
          onProjectChange(status);
          if (['READY', 'FAILED', 'VALIDATED'].includes(status.state)) {
            if (pollRef.current !== null) window.clearInterval(pollRef.current);
            pollRef.current = null;
            setLoading(false);
          }
        } catch {
          if (pollRef.current !== null) window.clearInterval(pollRef.current);
          pollRef.current = null;
          setLoading(false);
          setError('Lost connection while checking reconstruction status.');
        }
      }, 1000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Processing failed');
      setLoading(false);
    }
  };

  const resetWorkspace = () => {
    if (pollRef.current !== null) window.clearInterval(pollRef.current);
    pollRef.current = null;
    window.localStorage.removeItem('depthwizard.projectId');
    onProjectChange(null);
    setProjectName('');
    setError(null);
  };

  const badge = (state: string) => {
    const cls = state === 'FAILED' ? 'failed' : ['READY', 'VALIDATED'].includes(state) ? 'ready' : ['NEW', 'UPLOADED'].includes(state) ? 'neutral' : 'processing';
    return <span className={`state-badge ${cls}`}><i />{state.replace(/_/g, ' ')}</span>;
  };

  return <div className="project-content">
    <div className="panel-intro">
      <span className="panel-kicker">WORKSPACE</span>
      <h2>{project ? 'Project controls' : 'Create a workspace'}</h2>
      <p>{project ? 'Manage input, reconstruction and exports.' : 'Turn a single image into an explorable 3D surface.'}</p>
    </div>

    {!project && <div className="panel-section create-card">
      <label className="field-label">PROJECT NAME</label>
      <input className="input" placeholder="e.g. Campus elevation study" value={projectName} onChange={(e) => setProjectName(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleCreateProject()} autoFocus />
      <button className="btn btn-primary btn-full" onClick={handleCreateProject} disabled={!projectName.trim() || loading}>{loading ? 'Creating…' : 'Create project'} <span>→</span></button>
    </div>}

    {project && <>
      <div className="panel-section project-card">
        <div className="section-head"><span className="panel-kicker">ACTIVE PROJECT</span>{badge(project.state)}</div>
        <div className="project-name">{project.name}</div>
        <div className="project-id">ID · {project.project_id}</div>
      </div>

      {(project.state === 'NEW' || project.state === 'UPLOADED') && <div className="panel-section">
        <div className="section-head"><span className="panel-kicker">INPUT IMAGE</span><span className="mini-label">JPG · PNG · TIFF</span></div>
        <button
          className={`upload-zone ${dragging ? 'dragging' : ''}`}
          onClick={() => fileInputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={async (e) => { e.preventDefault(); setDragging(false); const file = e.dataTransfer.files?.[0]; if (file) await uploadFile(file); }}
          disabled={loading}
        >
          <span className="upload-icon">↑</span>
          <span><b>{project.state === 'UPLOADED' ? 'Replace source image' : 'Choose source image'}</b><small>Click to browse or drag & drop here</small></span>
        </button>
        <input ref={fileInputRef} type="file" accept=".jpg,.jpeg,.png,.tif,.tiff" onChange={handleFileSelect} hidden />
      </div>}

      {project.state === 'UPLOADED' && <div className="panel-section action-card">
        <div className="action-copy"><span className="action-icon">✦</span><div><b>Ready to reconstruct</b><small>Depth estimation → DSM → textured 3D mesh</small></div></div>
        <button className="btn btn-primary btn-full" onClick={handleProcess} disabled={loading}>{loading ? 'Processing…' : 'Run reconstruction'} <span>→</span></button>
      </div>}

      {loading && <div className="panel-section">
        <div className="section-head"><span className="panel-kicker">PIPELINE</span><strong className="progress-value">{Math.round((project.progress || 0) * 100)}%</strong></div>
        <div className="progress-bar"><div className="progress-fill" style={{ width: `${Math.max(3, (project.progress || 0) * 100)}%` }} /></div>
        <div className="progress-copy">{project.message || 'Processing terrain reconstruction…'}</div>
      </div>}

      {(project.state === 'READY' || project.state === 'VALIDATED') && <div className="panel-section">
        <div className="section-head"><span className="panel-kicker">EXPORTS</span><span className="mini-label">4 FILES</span></div>
        <div className="download-list">
          <a className="download-row" href={projectApi.getDownloadUrl(project.project_id, 'dsm')} download><span>DSM surface</span><b>↓</b></a>
          <a className="download-row" href={projectApi.getDownloadUrl(project.project_id, 'depth')} download><span>Depth map</span><b>↓</b></a>
          <a className="download-row" href={projectApi.getDownloadUrl(project.project_id, 'mesh')} download><span>3D mesh · GLB</span><b>↓</b></a>
          <a className="download-row" href={projectApi.getDownloadUrl(project.project_id, 'report')} download><span>Analysis report</span><b>↓</b></a>
        </div>
      </div>}

      <div className="panel-section reset-section"><button className="btn btn-ghost btn-full" onClick={resetWorkspace}>Reset workspace</button></div>
    </>}

    {error && <div className="error-card"><span>!</span><div><b>Something went wrong</b><p>{error}</p></div></div>}
  </div>;
}
