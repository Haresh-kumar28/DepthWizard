"""Tests for application configuration."""

import os
import sys
from pathlib import Path

# Ensure backend is in path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_default_settings():
    """Test default settings creation."""
    from app.config import Settings
    settings = Settings(
        data_dir=Path(__file__).parent / "test_data",
        models_dir=Path(__file__).parent / "test_models",
    )
    assert settings.app_name == "DepthWizard"
    assert settings.app_version == "1.3.0"
    assert settings.device in ("auto", "cpu", "cuda")
    assert settings.max_image_size == 4096
    assert settings.max_upload_size_mb == 500


def test_data_dirs_created(tmp_path):
    """Test that data directories are created."""
    from app.config import Settings
    data_dir = tmp_path / "data"
    models_dir = tmp_path / "models"
    settings = Settings(data_dir=data_dir, models_dir=models_dir)
    assert settings.input_dir.exists()
    assert settings.output_dir.exists()
    assert settings.reference_dir.exists()
    assert models_dir.exists()


def test_settings_env_prefix():
    """Test that settings can be configured via environment variables."""
    os.environ["DEPTHWIZARD_DEBUG"] = "true"
    from app.config import Settings
    settings = Settings(
        data_dir=Path(__file__).parent / "test_data",
        models_dir=Path(__file__).parent / "test_models",
    )
    assert settings.debug is True
    del os.environ["DEPTHWIZARD_DEBUG"]


def test_project_states():
    """Test project state enum."""
    from app.api.schemas import ProjectState
    assert ProjectState.NEW == "NEW"
    assert ProjectState.UPLOADED == "UPLOADED"
    assert ProjectState.READY == "READY"
    assert ProjectState.FAILED == "FAILED"


def test_project_model():
    """Test project model creation."""
    from app.models.project import Project
    from app.api.schemas import ProjectState
    project = Project(name="Test Project", project_dir=Path(__file__).parent / "test_data")
    assert project.name == "Test Project"
    assert project.state == ProjectState.NEW
    assert project.project_id
    assert len(project.project_id) == 12
    assert project.progress == 0.0


def test_project_state_transitions():
    """Test project state transitions."""
    from app.models.project import Project
    from app.api.schemas import ProjectState
    project = Project(name="Test", project_dir=Path(__file__).parent / "test_data")
    
    project.set_state(ProjectState.UPLOADED, 0.1, "Image uploaded")
    assert project.state == ProjectState.UPLOADED
    assert project.progress == 0.1
    
    project.set_error("Something failed")
    assert project.state == ProjectState.FAILED
    assert project.error == "Something failed"


def test_sanitize_filename():
    """Test filename sanitization."""
    from app.services.project_manager import sanitize_filename
    assert sanitize_filename("test.jpg") == "test.jpg"
    assert sanitize_filename("../../../etc/passwd") == "passwd"
    assert sanitize_filename("test<>:.jpg") == "test___.jpg"
    assert sanitize_filename("a" * 300 + ".jpg") == "a" * 196 + ".jpg"
