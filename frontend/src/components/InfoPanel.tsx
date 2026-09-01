import { useEffect, useState } from 'react';
import type { Project, DSMStatistics } from '../types';
import { projectApi } from '../services/api';

export function InfoPanel({ project }: { project: Project | null }) {
  const [stats, setStats] = useState<DSMStatistics | null>(null);
  const [preview, setPreview] = useState('');

  useEffect(() => {
    setStats(null);
    setPreview('');
    if (project && ['READY', 'VALIDATED'].includes(project.state)) {
      projectApi.getStatistics(project.project_id).then(setStats).catch(() => {});
      setPreview(`${projectApi.getDsmUrl(project.project_id)}?t=${Date.now()}`);
    }
  }, [project?.project_id, project?.state]);

  if (!project) return <div className="info-empty"><span className="panel-kicker">ANALYSIS</span><div className="info-empty-title">Nothing loaded</div><p>Start a project on the left to inspect reconstruction results.</p></div>;

  return (
    <div className="info-content">
      <div className="panel-section info-hero">
        <div className="panel-kicker">PROJECT INPUT</div>
        <div className="input-state"><span className="status-dot" />{project.is_georeferenced ? 'Georeferenced' : 'Non-georeferenced'}</div>
        <div className="project-id">{project.project_id}</div>
      </div>

      {preview && <div className="panel-section preview-section">
        <div className="section-head"><span className="panel-kicker">DSM PREVIEW</span><span className="mini-label">RELATIVE</span></div>
        <div className="preview-frame"><img src={preview} alt="Digital surface model preview" /></div>
      </div>}

      {stats && <>
        <div className="panel-section">
          <div className="section-head"><span className="panel-kicker">ELEVATION</span><span className="mini-label">{stats.unit}</span></div>
          <div className="metric-grid">
            <div><span>MIN</span><strong>{stats.min_elevation.toFixed(3)}</strong></div>
            <div><span>MAX</span><strong>{stats.max_elevation.toFixed(3)}</strong></div>
            <div><span>MEAN</span><strong>{stats.mean_elevation.toFixed(3)}</strong></div>
            <div><span>RANGE</span><strong>{stats.elevation_range.toFixed(3)}</strong></div>
          </div>
        </div>
        <div className="panel-section compact-stats">
          <div className="section-head"><span className="panel-kicker">QUALITY</span></div>
          <div className="quality-row"><span>Valid surface</span><b>{stats.valid_pixel_percentage.toFixed(1)}%</b></div>
          {stats.slope_mean !== undefined && <div className="quality-row"><span>Mean slope</span><b>{stats.slope_mean.toFixed(3)}°</b></div>}
          <div className="quality-bar"><span style={{ width: `${Math.min(100, stats.valid_pixel_percentage)}%` }} /></div>
        </div>
      </>}

      <div className="panel-section limitations">
        <div className="section-head"><span className="panel-kicker">MODEL NOTE</span></div>
        <p>Monocular depth is relative until calibrated with DEM or GCP reference data.</p>
      </div>
    </div>
  );
}
