"""Pydantic request/response schemas for the API."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ProjectState(str, Enum):
    """Project processing states."""
    NEW = "NEW"
    UPLOADED = "UPLOADED"
    PREPROCESSING = "PREPROCESSING"
    DEPTH_ESTIMATION = "DEPTH_ESTIMATION"
    CALIBRATING = "CALIBRATING"
    DSM_GENERATION = "DSM_GENERATION"
    MESH_GENERATION = "MESH_GENERATION"
    READY = "READY"
    VALIDATED = "VALIDATED"
    FAILED = "FAILED"


class CalibrationType(str, Enum):
    """Calibration method types."""
    NONE = "none"
    DEM = "dem"
    GCP = "gcp"


class CreateProjectRequest(BaseModel):
    """Request to create a new project."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class CreateProjectResponse(BaseModel):
    """Response after creating a project."""
    project_id: str
    name: str
    state: ProjectState
    created_at: datetime


class ProjectStatusResponse(BaseModel):
    """Project status response."""
    project_id: str
    name: str
    state: ProjectState
    progress: float = 0.0
    message: str = ""
    created_at: datetime
    updated_at: datetime
    is_georeferenced: bool = False
    calibration_type: CalibrationType = CalibrationType.NONE
    error: Optional[str] = None


class ImageMetadataResponse(BaseModel):
    """Image metadata response."""
    filename: str
    width: int
    height: int
    channels: int
    dtype: str
    file_size_bytes: int
    is_georeferenced: bool = False
    crs: Optional[str] = None
    epsg: Optional[int] = None
    bounds: Optional[dict[str, float]] = None
    resolution: Optional[tuple[float, float]] = None
    transform: Optional[list[float]] = None
    nodata: Optional[float] = None
    band_count: Optional[int] = None


class GCPInput(BaseModel):
    """Ground Control Point input."""
    pixel_x: float
    pixel_y: float
    reference_elevation: float


class CalibrateRequest(BaseModel):
    """Calibration request."""
    method: CalibrationType
    gcps: Optional[list[GCPInput]] = None


class CalibrationResult(BaseModel):
    """Calibration result."""
    method: CalibrationType
    scale: Optional[float] = None
    offset: Optional[float] = None
    valid_pixel_count: int = 0
    rmse: Optional[float] = None
    mae: Optional[float] = None
    residual_mean: Optional[float] = None
    residual_std: Optional[float] = None


class DSMStatisticsResponse(BaseModel):
    """DSM statistics response."""
    min_elevation: float
    max_elevation: float
    mean_elevation: float
    median_elevation: float
    std_elevation: float
    elevation_range: float
    valid_pixel_count: int
    total_pixel_count: int
    valid_pixel_percentage: float
    is_metric: bool = False
    unit: str = "relative"
    slope_min: Optional[float] = None
    slope_max: Optional[float] = None
    slope_mean: Optional[float] = None


class ValidationMetrics(BaseModel):
    """Validation metrics when comparing against reference."""
    mae: float
    rmse: float
    pearson_correlation: float
    bias: float
    std_error: float
    valid_pixel_count: int
    valid_pixel_percentage: float


class ProcessingInfo(BaseModel):
    """Processing information."""
    input_dimensions: tuple[int, int]
    model_dimensions: Optional[tuple[int, int]] = None
    output_dimensions: tuple[int, int]
    processing_time_seconds: float
    model_name: str
    device: str
    hardware: str = "unknown"


class ReportResponse(BaseModel):
    """Project report response."""
    project_id: str
    project_name: str
    input_info: dict[str, Any]
    processing_info: dict[str, Any]
    calibration_info: Optional[dict[str, Any]] = None
    dsm_statistics: Optional[dict[str, Any]] = None
    validation_metrics: Optional[dict[str, Any]] = None
    artifacts: list[str]
    limitations: list[str]
    generated_at: datetime


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
