import numpy as np
def compute_relative_height(normalized_depth:np.ndarray)->np.ndarray:
    if normalized_depth.ndim!=2:raise ValueError("Depth must be 2D")
    return np.clip(1.0-normalized_depth,0,1).astype(np.float32)
