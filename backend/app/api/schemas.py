"""Pydantic request/response schemas for DepthWizard."""
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field

class ProjectState(str, Enum):
    NEW="NEW"; UPLOADED="UPLOADED"; PREPROCESSING="PREPROCESSING"; DEPTH_ESTIMATION="DEPTH_ESTIMATION"; CALIBRATING="CALIBRATING"; DSM_GENERATION="DSM_GENERATION"; MESH_GENERATION="MESH_GENERATION"; READY="READY"; VALIDATED="VALIDATED"; FAILED="FAILED"
class CalibrationType(str, Enum):
    NONE="none"; DEM="dem"; GCP="gcp"
class ReconstructionMode(str, Enum):
    RELATIVE="relative"; METRIC="metric"
class ReconstructionMode(str, Enum):
    RELATIVE="relative"; METRIC="metric"
class CreateProjectRequest(BaseModel):
    name:str=Field(...,min_length=1,max_length=255); description:Optional[str]=None
class CreateProjectResponse(BaseModel):
    project_id:str; name:str; state:ProjectState; created_at:datetime; reconstruction_mode:ReconstructionMode=ReconstructionMode.RELATIVE
class ProjectStatusResponse(BaseModel):
    project_id:str; name:str; state:ProjectState; progress:float=0.0; message:str=""; created_at:datetime; updated_at:datetime; is_georeferenced:bool=False; calibration_type:CalibrationType=CalibrationType.NONE; reconstruction_mode:ReconstructionMode=ReconstructionMode.RELATIVE; error:Optional[str]=None; job_id:Optional[str]=None; job_state:Optional[str]=None; started_at:Optional[float]=None; completed_at:Optional[float]=None
class ImageMetadataResponse(BaseModel):
    filename:str; width:int; height:int; channels:int; dtype:str; file_size_bytes:int; is_georeferenced:bool=False; crs:Optional[str]=None; epsg:Optional[int]=None; bounds:Optional[dict[str,float]]=None; resolution:Optional[tuple[float,float]]=None; transform:Optional[list[float]]=None; nodata:Optional[float]=None; band_count:Optional[int]=None
class GCPInput(BaseModel):
    pixel_x:float; pixel_y:float; reference_elevation:float
class CalibrateRequest(BaseModel):
    method:CalibrationType; gcps:Optional[list[GCPInput]]=None; calibration_fraction:float=Field(0.8,ge=0.1,le=1.0); seed:int=42
class CalibrationResult(BaseModel):
    method:CalibrationType; scale:Optional[float]=None; offset:Optional[float]=None; valid_pixel_count:int=0; rmse:Optional[float]=None; mae:Optional[float]=None; residual_mean:Optional[float]=None; residual_std:Optional[float]=None
class DSMStatisticsResponse(BaseModel):
    min_elevation:float; max_elevation:float; mean_elevation:float; median_elevation:float; std_elevation:float; elevation_range:float; valid_pixel_count:int; total_pixel_count:int; valid_pixel_percentage:float; is_metric:bool=False; unit:str="relative"; slope_min:Optional[float]=None; slope_max:Optional[float]=None; slope_mean:Optional[float]=None
class ValidationRequest(BaseModel):
    reference_type:str="DEM"
    use_holdout:bool=True
    seed:int=42

class ValidationMetrics(BaseModel):
    mae:float; rmse:float; pearson_correlation:float; r2:float=0.0; bias:float; std_error:float; p95_abs_error:float=0.0; max_abs_error:float=0.0; valid_pixel_count:int; valid_pixel_percentage:float
class ProcessingRequest(BaseModel):
    model_name:str="depth-anything-v2-small"
    inference_resolution:int=768
    tile_size:int=768
    tile_overlap:float=0.25
    edge_refinement:bool=True
    terrain_smoothing:bool=True

class ProcessingInfo(BaseModel):
    input_dimensions:tuple[int,int]; model_dimensions:Optional[tuple[int,int]]=None; output_dimensions:tuple[int,int]; processing_time_seconds:float; model_name:str; device:str; hardware:str="unknown"; inference_mode:str="tiled"; inference_resolution:int=768; tile_size:int=768; tile_overlap:float=0.25; edge_refinement:bool=True; terrain_smoothing:bool=True
class ReportResponse(BaseModel):
    project_id:str; project_name:str; input_info:dict[str,Any]; processing_info:dict[str,Any]; inference_settings:dict[str,Any]=Field(default_factory=dict); calibration_info:Optional[dict[str,Any]]=None; dsm_statistics:Optional[dict[str,Any]]=None; validation_metrics:Optional[dict[str,Any]]=None; artifacts:list[str]; limitations:list[str]; generated_at:datetime; current_calibration_id:Optional[str]=None; current_validation_id:Optional[str]=None
    calibration_history:list[dict[str,Any]]=Field(default_factory=list)
    validation_history:list[dict[str,Any]]=Field(default_factory=list)
    inspection_history:list[dict[str,Any]]=Field(default_factory=list)
class ErrorResponse(BaseModel):
    error:str; detail:Optional[str]=None; code:Optional[str]=None
