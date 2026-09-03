"""Application configuration using Pydantic Settings."""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """DepthWizard application settings."""

    # Application
    app_name: str = "DepthWizard"
    app_version: str = "1.7.0"
    debug: bool = False

    # Paths
    data_dir: Path = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) / "data"
    models_dir: Path = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) / "models"
    input_dir: Optional[Path] = None
    output_dir: Optional[Path] = None
    reference_dir: Optional[Path] = None

    # Processing
    device: str = "auto"  # "auto", "cpu", "cuda"
    max_image_size: int = 4096  # Maximum image dimension
    max_upload_size_mb: int = 500
    render_max_resolution: int = 1024  # Max mesh render resolution
    depth_model_name: str = "depth-anything-v2-small"
    depth_inference_mode: str = "tiled"  # tiled is recommended for aerial imagery
    depth_tile_size: int = 768
    depth_tile_overlap: float = 0.25

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174", "http://localhost:5175", "http://127.0.0.1:5175"]

    model_config = {
        "env_prefix": "DEPTHWIZARD_",
        "env_file": ".env",
        "extra": "ignore",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set derived paths
        if self.input_dir is None:
            self.input_dir = self.data_dir / "input"
        if self.output_dir is None:
            self.output_dir = self.data_dir / "outputs"
        if self.reference_dir is None:
            self.reference_dir = self.data_dir / "reference"

        # Create directories
        for d in [self.data_dir, self.input_dir, self.output_dir, self.reference_dir, self.models_dir]:
            d.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    """Get application settings (cached)."""
    return Settings()
