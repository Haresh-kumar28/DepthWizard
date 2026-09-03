"""Pytest configuration and shared fixtures."""

import os
import sys
import pytest
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


@pytest.fixture
def settings():
    """Create test settings."""
    from app.config import Settings
    return Settings(
        data_dir=Path(__file__).parent / "test_data",
        models_dir=Path(__file__).parent / "test_models",
        debug=True,
    )


@pytest.fixture
def project_manager(settings):
    """Create a test project manager."""
    from app.services.project_manager import ProjectManager
    return ProjectManager(settings)
