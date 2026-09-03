"""Download the Depth Anything V2 Small Transformers checkpoint into models/."""
from pathlib import Path
from transformers import AutoImageProcessor, AutoModelForDepthEstimation
root=Path(__file__).resolve().parents[1]
cache=root/'models'/'depth-anything-v2-small'
cache.mkdir(parents=True,exist_ok=True)
model_id='depth-anything/Depth-Anything-V2-Small-hf'
AutoImageProcessor.from_pretrained(model_id,cache_dir=str(cache))
AutoModelForDepthEstimation.from_pretrained(model_id,cache_dir=str(cache))
print(f'Model cached under {cache}')
