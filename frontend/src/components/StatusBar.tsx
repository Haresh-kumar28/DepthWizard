import type { Project } from '../types';

export function StatusBar({ project }: { project: Project | null }) {
  const progress = project?.progress ?? 0;
  return (
    <div className="status-inner">
      <div className="status-left">
        <span className="status-brand">DEPTHWIZARD</span>
        <span className="status-sep">/</span>
        <span>{project ? project.state.replace(/_/g, ' ') : 'READY'}</span>
        {project?.message && <><span className="status-sep">/</span><span className="status-message">{project.message}</span></>}
      </div>
      <div className="status-right">{progress > 0 && progress < 1 ? `${Math.round(progress * 100)}%` : 'LOCAL • SECURE'}</div>
    </div>
  );
}
