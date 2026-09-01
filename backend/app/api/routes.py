"""API route definitions."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from app.api.schemas import (
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
from app.services.job_manager import JobManager

logger = logging.getLogger(__name__)

router = APIRouter()


def get_project_manager(request: Request) -> ProjectManager:
    """Dependency injection for project manager."""
    return request.app.state.project_manager


def get_job_manager(request: Request) -> JobManager:
    """Dependency injection for job manager."""
    return request.app.state.job_manager


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
    pm: ProjectManager = Depends(get_project_manager),
    jm: JobManager = Depends(get_job_manager),
):
    """Start processing pipeline."""
    project = pm.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        job_id = await jm.submit_processing_job(project_id, pm)
        return {"job_id": job_id, "message": "Processing started"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects/{project_id}/status", response_model=ProjectStatusResponse)
async def get_project_status(
    project_id: str,
    pm: ProjectManager = Depends(get_project_manager),
):
    """Get project processing status."""
    project = pm.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.to_status_response()


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
    pm: ProjectManager = Depends(get_project_manager),
):
    """Validate DSM against reference."""
    project = pm.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        result = await pm.validate_project(project_id, reference_file)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
    ALLOWED_ARTIFACTS = {"dsm", "depth", "relative_height", "mesh", "report", "rgb"}
    if artifact not in ALLOWED_ARTIFACTS:
        raise HTTPException(status_code=400, detail=f"Invalid artifact: {artifact}")

    project = pm.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    artifact_path = project.get_artifact_path(artifact)
    if not artifact_path or not artifact_path.exists():
        raise HTTPException(status_code=404, detail=f"Artifact '{artifact}' not available")

    return FileResponse(str(artifact_path), filename=artifact_path.name)
