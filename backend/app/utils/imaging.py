"""Image processing utilities.

Handles:
- RGB extraction from various formats
- Image preprocessing (resize, normalize)
- Color space conversion
- Channel handling
"""

import logging
from typing import Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


def load_rgb_image(filepath: str) -> np.ndarray:
    """Load an image file and return as RGB numpy array.
    
    Will be fully implemented in M1.
    """
    raise NotImplementedError("Image loading will be implemented in M1")


def preprocess_for_depth(
    image: np.ndarray,
    max_size: int = 4096,
) -> Tuple[np.ndarray, dict]:
    """Preprocess image for depth estimation model.
    
    Will be fully implemented in M1.
    """
    raise NotImplementedError("Image preprocessing will be implemented in M1")
