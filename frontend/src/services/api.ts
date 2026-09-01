/**
 * API client for DepthWizard backend.
 */

import axios from 'axios';
import type {
  Project,
  ImageMetadata,
  DSMStatistics,
  CalibrationResult,
  CalibrationType,
  GCPInput,
  ValidationMetrics,
} from '../types';

const api = axios.create({
  baseURL: '/api',
  timeout: 300000, // 5 min timeout for processing
});

export const projectApi = {
  create: async (name: string, description?: string): Promise<Project> => {
    const { data } = await api.post('/projects', { name, description });
    return data;
  },

  get: async (projectId: string): Promise<Project> => {
    const { data } = await api.get(`/projects/${projectId}`);
    return data;
  },

  getStatus: async (projectId: string): Promise<Project> => {
    const { data } = await api.get(`/projects/${projectId}/status`);
    return data;
  },

  upload: async (projectId: string, file: File): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post(`/projects/${projectId}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  process: async (projectId: string): Promise<any> => {
    const { data } = await api.post(`/projects/${projectId}/process`);
    return data;
  },

  getMetadata: async (projectId: string): Promise<ImageMetadata> => {
    const { data } = await api.get(`/projects/${projectId}/metadata`);
    return data;
  },

  getDepthUrl: (projectId: string): string => `/api/projects/${projectId}/depth`,

  getDsmUrl: (projectId: string): string => `/api/projects/${projectId}/dsm`,

  getMeshUrl: (projectId: string): string => `/api/projects/${projectId}/mesh`,

  getStatistics: async (projectId: string): Promise<DSMStatistics> => {
    const { data } = await api.get(`/projects/${projectId}/statistics`);
    return data;
  },

  calibrate: async (
    projectId: string,
    method: CalibrationType,
    gcps?: GCPInput[]
  ): Promise<CalibrationResult> => {
    const { data } = await api.post(`/projects/${projectId}/calibrate`, { method, gcps });
    return data;
  },

  validate: async (projectId: string, referenceFile: File): Promise<ValidationMetrics> => {
    const formData = new FormData();
    formData.append('reference_file', referenceFile);
    const { data } = await api.post(`/projects/${projectId}/validate`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  getReport: async (projectId: string): Promise<any> => {
    const { data } = await api.get(`/projects/${projectId}/report`);
    return data;
  },

  getDownloadUrl: (projectId: string, artifact: string): string =>
    `/api/projects/${projectId}/download/${artifact}`,
};

export default api;
