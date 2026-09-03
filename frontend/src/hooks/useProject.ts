/**
 * Custom hook for project state management.
 * Will be expanded in later milestones.
 */

import { useState, useCallback } from 'react';
import type { Project } from '../types';
import { projectApi } from '../services/api';

export function useProject() {
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshProject = useCallback(async () => {
    if (!project) return;
    try {
      const updated = await projectApi.getStatus(project.project_id);
      setProject(updated);
    } catch (err) {
      console.error('Failed to refresh project:', err);
    }
  }, [project]);

  const resetProject = useCallback(() => {
    setProject(null);
    setError(null);
  }, []);

  return {
    project,
    setProject,
    loading,
    setLoading,
    error,
    setError,
    refreshProject,
    resetProject,
  };
}
