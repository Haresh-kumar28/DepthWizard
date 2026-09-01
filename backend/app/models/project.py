"""Project data model."""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from app.api.schemas import (
    CalibrationType,
    DSMStatisticsResponse,
    ImageMetadataResponse,
    ProjectState,
    ProjectStatusResponse,
    ValidationMetrics,
)


class Project:
    """Represents a DepthWizard processing project."""

    def __init__(self, name: str, project_dir: Path, description: Optional[str] = None):
        self.project_id: str = uuid.uuid4().hex[:12]
        self.name: str = name
        self.description: Optional[str] = description
        self.state: ProjectState = ProjectState.NEW
        self.progress: float = 0.0
        self.message: str = ""
        self.error: Optional[str] = None
        self.created_at: datetime = datetime.now(timezone.utc)
        self.updated_at: datetime = datetime.now(timezone.utc)

        # Project directory
        self.project_dir: Path = project_dir / self.project_id
        self.project_dir.mkdir(parents=True, exist_ok=True)

        # Input
        self.input_path: Optional[Path] = None
        self.is_georeferenced: bool = False
        self.calibration_type: CalibrationType = CalibrationType.NONE

        # Results
        self.metadata: Optional[ImageMetadataResponse] = None
        self.statistics: Optional[DSMStatisticsResponse] = None
        self.validation: Optional[ValidationMetrics] = None
        self.processing_info: Optional[dict[str, Any]] = None
        self.calibration_result: Optional[dict[str, Any]] = None

        # Artifact paths
        self._artifacts: dict[str, Path] = {}

    def set_state(self, state: ProjectState, progress: float = 0.0, message: str = ""):
        """Update project state."""
        self.state = state
        self.progress = progress
        self.message = message
        self.updated_at = datetime.now(timezone.utc)

    def set_error(self, error: str):
        """Set project to failed state."""
        self.state = ProjectState.FAILED
        self.error = error
        self.updated_at = datetime.now(timezone.utc)

    def set_artifact_path(self, name: str, path: Path):
        """Register an artifact path."""
        self._artifacts[name] = path

    def get_artifact_path(self, name: str) -> Optional[Path]:
        """Get an artifact path."""
        return self._artifacts.get(name)

    def list_artifacts(self) -> list[str]:
        """List available artifact names."""
        return [k for k, v in self._artifacts.items() if v.exists()]

    def to_status_response(self) -> ProjectStatusResponse:
        """Convert to API response."""
        return ProjectStatusResponse(
            project_id=self.project_id,
            name=self.name,
            state=self.state,
            progress=self.progress,
            message=self.message,
            created_at=self.created_at,
            updated_at=self.updated_at,
            is_georeferenced=self.is_georeferenced,
            calibration_type=self.calibration_type,
            error=self.error,
        )
