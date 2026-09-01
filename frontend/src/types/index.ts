/**
 * DepthWizard TypeScript type definitions.
 */

export type ProjectState =
  | 'NEW'
  | 'UPLOADED'
  | 'PREPROCESSING'
  | 'DEPTH_ESTIMATION'
  | 'CALIBRATING'
  | 'DSM_GENERATION'
  | 'MESH_GENERATION'
  | 'READY'
  | 'VALIDATED'
  | 'FAILED';

export type CalibrationType = 'none' | 'dem' | 'gcp';

export interface Project {
  project_id: string;
  name: string;
  state: ProjectState;
  progress: number;
  message: string;
  created_at: string;
  updated_at: string;
  is_georeferenced: boolean;
  calibration_type: CalibrationType;
  error?: string;
}

export interface ImageMetadata {
  filename: string;
  width: number;
  height: number;
  channels: number;
  dtype: string;
  file_size_bytes: number;
  is_georeferenced: boolean;
  crs?: string;
  epsg?: number;
  bounds?: { left: number; bottom: number; right: number; top: number };
  resolution?: [number, number];
  transform?: number[];
  nodata?: number;
  band_count?: number;
}

export interface DSMStatistics {
  min_elevation: number;
  max_elevation: number;
  mean_elevation: number;
  median_elevation: number;
  std_elevation: number;
  elevation_range: number;
  valid_pixel_count: number;
  total_pixel_count: number;
  valid_pixel_percentage: number;
  is_metric: boolean;
  unit: string;
  slope_min?: number;
  slope_max?: number;
  slope_mean?: number;
}

export interface GCPInput {
  pixel_x: number;
  pixel_y: number;
  reference_elevation: number;
}

export interface CalibrationResult {
  method: CalibrationType;
  scale?: number;
  offset?: number;
  valid_pixel_count: number;
  rmse?: number;
  mae?: number;
  residual_mean?: number;
  residual_std?: number;
}

export interface ValidationMetrics {
  mae: number;
  rmse: number;
  pearson_correlation: number;
  bias: number;
  std_error: number;
  valid_pixel_count: number;
  valid_pixel_percentage: number;
}

export interface TerrainInspection {
  x: number;
  y: number;
  elevation: number;
  relative_height?: number;
  slope?: number;
}
