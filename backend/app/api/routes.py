"""API route definitions."""

import logging
import json
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from app.api.schemas import (
    ProcessingRequest, ValidationRequest,
    CalibrateRequest,
    CalibrationResult,
    CreateProjectRequest,
    CreateProjectResponse,
    DSMStatisticsResponse,
    ErrorResponse,
    ImageMetadataResponse,
    ProjectStatusResponse,
    ReportResponse,
    ValidationMetrics,
)
from app.services.project_manager import ProjectManager
from app.services.job_manager import JobManager, JobState

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/models")
async def list_models(request: Request):
    """Return model availability and provenance without claiming unmeasured accuracy."""
    settings = request.app.state.settings
    models_dir = settings.models_dir
    variants = [
        ("depth-anything-v2-small", "Depth Anything V2 · Small", True),
        ("depth-anything-v2-base", "Depth Anything V2 · Base", True),
        ("depth-anything-v2-large", "Depth Anything V2 · Large", True),
    ]
    result = [{"id": mid, "label": label, "available": True, "status": "BASELINE"} for mid, label, _ in variants]
    local = models_dir / "aerial-depth"
    provenance_path = local / "provenance.json"
    available = (local / "config.json").exists() and (local / "model.safetensors").exists() and provenance_path.exists()
    item = {"id": "aerial-depth", "label": "Aerial-Depth · fine-tuned checkpoint", "available": False, "status": "NOT_TRAINED"}
    if available:
        try:
            prov = json.loads(provenance_path.read_text(encoding="utf-8"))
            trained = prov.get("status") == "TRAINED"
            item["available"] = bool(trained)
            item["status"] = "TRAINED" if trained else "NOT_TRAINED"
            item["provenance"] = {k: prov.get(k) for k in (
                "base_model", "dataset", "training_regions", "validation_regions",
                "held_out_test_regions", "checkpoint_sha256", "validation_metrics",
                "held_out_test_metrics", "baseline_metrics", "improvement"
            )}
        except Exception:
            item["status"] = "INVALID_PROVENANCE"
    result.append(item)
    return result


def get_project_manager(request: Request) -> ProjectManager:
    """Dependency injection for project manager."""
    return request.app.state.project_manager


def get_job_manager(request: Request) -> JobManager:
    """Dependency injection for job manager."""
    return request.app.state.job_manager



@router.get("/projects")
async def list_projects(pm: ProjectManager = Depends(get_project_manager)):
    return [p.to_status_response().model_dump() for p in pm.list_projects()]

@router.patch("/projects/{project_id}")
async def rename_project(project_id: str, body: CreateProjectRequest, pm: ProjectManager = Depends(get_project_manager)):
    try: return pm.rename_project(project_id, body.name).to_status_response()
    except ValueError as e: raise HTTPException(status_code=400, detail=str(e))

@router.post("/projects/{project_id}/reset")
async def reset_project(project_id: str, pm: ProjectManager = Depends(get_project_manager)):
    try: return pm.reset_project(project_id).to_status_response()
    except ValueError as e: raise HTTPException(status_code=400, detail=str(e))

@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, pm: ProjectManager = Depends(get_project_manager)):
    if not pm.delete_project(project_id): raise HTTPException(status_code=404, detail="Project not found")
    pm.store.delete_project(project_id)
    return {"deleted": True, "project_id": project_id}

@router.post("/projects", response_model=CreateProjectResponse)
async def create_project(
    body: CreateProjectRequest,
    pm: ProjectManager = Depends(get_project_manager),
):
    """Create a new project."""
    project = pm.create_project(body.name, body.description)
    return CreateProjectResponse(
        project_id=project.project_id,
        name=project.name,
        state=project.state,
        created_at=project.created_at,
        reconstruction_mode=project.reconstruction_mode,
    )


@router.get("/projects/{project_id}", response_model=ProjectStatusResponse)
async def get_project(
    project_id: str,
    pm: ProjectManager = Depends(get_project_manager),
):
    """Get project details."""
    project = pm.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.to_status_response()


@router.post("/projects/{project_id}/upload")
async def upload_image(
    project_id: str,
    file: UploadFile = File(...),
    pm: ProjectManager = Depends(get_project_manager),
):
    """Upload an image to a project."""
    project = pm.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        result = await pm.upload_image(project_id, file)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="Upload failed")


@router.post("/projects/{project_id}/process")
async def process_project(
    project_id: str,
    request: Request,
    body: ProcessingRequest | None = None,
    pm: ProjectManager = Depends(get_project_manager),
    jm: JobManager = Depends(get_job_manager),
):
    """Start processing pipeline."""
    project = pm.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        if body:
            project.inference_settings = body.model_dump()
            pm._save_project(project)
        job_id = await jm.submit_processing_job(project_id, pm)
        return {"job_id": job_id, "message": "Processing started"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects/{project_id}/status", response_model=ProjectStatusResponse)
async def get_project_status(
    project_id: str,
    pm: ProjectManager = Depends(get_project_manager),
    jm: JobManager = Depends(get_job_manager),
):
    """Get project processing status."""
    project = pm.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    response = project.to_status_response()
    job = jm.get_project_job(project_id)
    if job:
        response.job_id = job.job_id
        response.job_state = job.state.value
        response.started_at = job.started_at
        response.completed_at = job.completed_at
        if job.state in (JobState.QUEUED, JobState.PROCESSING):
            response.progress = max(response.progress, job.progress)
            response.message = job.message or response.message
    return response


@router.get("/projects/{project_id}/metadata", response_model=ImageMetadataResponse)
async def get_metadata(
    project_id: str,
    pm: ProjectManager = Depends(get_project_manager),
):
    """Get image metadata."""
    project = pm.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.metadata:
        raise HTTPException(status_code=400, detail="No image uploaded yet")
    return project.metadata


@router.get("/projects/{project_id}/depth")
async def get_depth(
    project_id: str,
    pm: ProjectManager = Depends(get_project_manager),
):
    """Get depth map preview."""
    project = pm.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    depth_path = project.get_artifact_path("depth_preview")
    if not depth_path or not depth_path.exists():
        raise HTTPException(status_code=404, detail="Depth map not generated yet")
    return FileResponse(str(depth_path), media_type="image/png")


@router.get("/projects/{project_id}/dsm")
async def get_dsm(
    project_id: str,
    pm: ProjectManager = Depends(get_project_manager),
):
    """Get DSM preview."""
    project = pm.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    dsm_path = project.get_artifact_path("dsm_preview")
    if not dsm_path or not dsm_path.exists():
        raise HTTPException(status_code=404, detail="DSM not generated yet")
    return FileResponse(str(dsm_path), media_type="image/png")


@router.get("/projects/{project_id}/mesh")
async def get_mesh(
    project_id: str,
    pm: ProjectManager = Depends(get_project_manager),
):
    """Get 3D mesh."""
    project = pm.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    mesh_path = project.get_artifact_path("mesh")
    if not mesh_path or not mesh_path.exists():
        raise HTTPException(status_code=404, detail="Mesh not generated yet")
    return FileResponse(str(mesh_path), media_type="model/gltf-binary", filename="terrain.glb")


@router.get("/projects/{project_id}/statistics", response_model=DSMStatisticsResponse)
async def get_statistics(
    project_id: str,
    pm: ProjectManager = Depends(get_project_manager),
):
    """Get DSM statistics."""
    project = pm.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.statistics:
        raise HTTPException(status_code=400, detail="Statistics not available yet")
    return project.statistics


@router.post("/projects/{project_id}/calibrate", response_model=CalibrationResult)
async def calibrate(
    project_id: str,
    body: CalibrateRequest,
    pm: ProjectManager = Depends(get_project_manager),
):
    """Calibrate depth to metric elevation."""
    project = pm.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        result = await pm.calibrate_project(project_id, body)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/projects/{project_id}/validate", response_model=ValidationMetrics)
async def validate_project(
    project_id: str,
    reference_file: UploadFile = File(...),
    use_holdout: bool = True,
    reference_type: str = "DEM",
    pm: ProjectManager = Depends(get_project_manager),
):
    """Validate DSM against reference with optional independent holdout."""
    project = pm.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        result = await pm.validate_project(project_id, reference_file, ValidationRequest(use_holdout=use_holdout, reference_type=reference_type))
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/projects/{project_id}/calibrate-dem", response_model=CalibrationResult)
async def calibrate_dem(project_id: str, dem_file: UploadFile = File(...), calibration_fraction: float = 0.8, seed: int = 42, pm: ProjectManager = Depends(get_project_manager)):
    project = pm.get_project(project_id)
    if not project: raise HTTPException(status_code=404, detail="Project not found")
    try: return await pm.calibrate_dem(project_id, dem_file, calibration_fraction, seed)
    except ValueError as e: raise HTTPException(status_code=400, detail=str(e))

@router.get("/projects/{project_id}/error-map")
async def get_error_map(project_id: str, pm: ProjectManager = Depends(get_project_manager)):
    project=pm.get_project(project_id)
    if not project: raise HTTPException(status_code=404, detail="Project not found")
    path=project.get_artifact_path("error_map")
    if not path or not path.exists(): raise HTTPException(status_code=404, detail="Run validation first")
    return FileResponse(str(path), media_type="image/png")

@router.get("/projects/{project_id}/inspect")
async def inspect_point(project_id: str, x: float | None = None, y: float | None = None, pixel_x: float | None = None, pixel_y: float | None = None, pm: ProjectManager = Depends(get_project_manager)):
    project=pm.get_project(project_id)
    if not project: raise HTTPException(status_code=404, detail="Project not found")
    try:
        if pixel_x is not None and pixel_y is not None:
            return pm.inspect_pixel(project_id,pixel_x,pixel_y)
        if x is None or y is None:
            raise ValueError("Provide pixel_x/pixel_y or x/y coordinates")
        return pm.inspect_point(project_id,x,y)
    except ValueError as e: raise HTTPException(status_code=400, detail=str(e))

@router.get("/projects/{project_id}/history")
async def get_history(project_id: str, pm: ProjectManager = Depends(get_project_manager)):
    project = pm.get_project(project_id)
    if not project: raise HTTPException(status_code=404, detail="Project not found")
    return {"project_id": project_id, "calibration_history": project.calibration_history, "validation_history": project.validation_history, "reconstruction_history": project.reconstruction_history, "inspection_history": project.inspection_history, "current_calibration_id": project.current_calibration_id, "current_validation_id": project.current_validation_id}



@router.post("/projects/{project_id}/snapshots")
async def create_snapshot(project_id: str, name: str = "", pm: ProjectManager = Depends(get_project_manager)):
    try: return pm.create_snapshot(project_id,name.strip() or None)
    except ValueError as e: raise HTTPException(status_code=400, detail=str(e))

@router.get("/projects/{project_id}/snapshots")
async def list_snapshots(project_id: str, pm: ProjectManager = Depends(get_project_manager)):
    try: return pm.list_snapshots(project_id)
    except ValueError as e: raise HTTPException(status_code=404, detail=str(e))

@router.delete("/projects/{project_id}/history/{kind}/{run_id}")
async def delete_history_run(project_id: str, kind: str, run_id: str, pm: ProjectManager = Depends(get_project_manager)):
    try:
        pm.delete_run(project_id, kind, run_id)
        return {"deleted": True, "run_id": run_id, "kind": kind}
    except ValueError as e: raise HTTPException(status_code=400, detail=str(e))

@router.get("/projects/{project_id}/report", response_model=ReportResponse)
async def get_report(
    project_id: str,
    pm: ProjectManager = Depends(get_project_manager),
):
    """Get project report."""
    project = pm.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return pm.generate_report(project_id)


@router.get("/projects/{project_id}/download/{artifact}")
async def download_artifact(
    project_id: str,
    artifact: str,
    pm: ProjectManager = Depends(get_project_manager),
):
    """Download a project artifact."""
    ALLOWED_ARTIFACTS = {"dsm", "metric_dsm", "depth", "relative_depth_npy", "relative_height", "mesh", "report", "report_html", "rgb", "dsm_preview", "slope", "error_map", "error_map_npy"}
    if artifact not in ALLOWED_ARTIFACTS:
        raise HTTPException(status_code=400, detail=f"Invalid artifact: {artifact}")

    project = pm.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    artifact_path = project.get_artifact_path(artifact)
    if not artifact_path or not artifact_path.exists():
        raise HTTPException(status_code=404, detail=f"Artifact '{artifact}' not available")

    return FileResponse(str(artifact_path), filename=artifact_path.name)
