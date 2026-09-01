import logging,time
from pathlib import Path
from typing import Optional
import numpy as np, torch
from PIL import Image
from app.depth.base import DepthEstimator, DepthResult
logger=logging.getLogger(__name__)
class DepthAnythingV2Estimator(DepthEstimator):
    MODEL_VARIANTS={"depth-anything-v2-small":"depth-anything/Depth-Anything-V2-Small-hf","depth-anything-v2-base":"depth-anything/Depth-Anything-V2-Base-hf","depth-anything-v2-large":"depth-anything/Depth-Anything-V2-Large-hf"}
    def __init__(self,model_name="depth-anything-v2-small",device_preference="auto",models_dir:Optional[str]=None):
        self._model_name=model_name; self._device_str=self._choose_device(device_preference); self._models_dir=Path(models_dir) if models_dir else None; self._model=None; self._processor=None; self._loaded=False
    @staticmethod
    def _choose_device(pref):
        if pref=="cuda" and not torch.cuda.is_available(): raise RuntimeError("CUDA requested but unavailable")
        return pref if pref in ("cpu","cuda") else ("cuda" if torch.cuda.is_available() else "cpu")
    def load_model(self):
        if self._loaded:return
        from transformers import AutoImageProcessor,AutoModelForDepthEstimation
        mid=self.MODEL_VARIANTS.get(self._model_name,self._model_name); kw={"cache_dir":str(self._models_dir)} if self._models_dir else {}
        self._processor=AutoImageProcessor.from_pretrained(mid,**kw); self._model=AutoModelForDepthEstimation.from_pretrained(mid,**kw); self._model.to(self._device_str).eval(); self._loaded=True
    def predict(self,image:np.ndarray)->DepthResult:
        if image.ndim!=3 or image.shape[2]!=3: raise ValueError("Expected RGB image HxWx3")
        self.load_model(); start=time.perf_counter(); h,w=image.shape[:2]
        inputs=self._processor(images=Image.fromarray(image.astype(np.uint8)),return_tensors="pt"); inputs={k:v.to(self._device_str) for k,v in inputs.items()}
        with torch.inference_mode():
            out=self._model(**inputs); pred=torch.nn.functional.interpolate(out.predicted_depth.unsqueeze(1),size=(h,w),mode="bicubic",align_corners=False).squeeze()
        depth=np.nan_to_num(pred.float().cpu().numpy().astype(np.float32),nan=0,posinf=0,neginf=0); norm=self._normalize(depth)
        return DepthResult(depth,norm,time.perf_counter()-start,self._model_name,self._device_str)
    @staticmethod
    def _normalize(d):
        v=np.isfinite(d)
        if not v.any():raise ValueError("Depth output contains no valid pixels")
        lo,hi=np.percentile(d[v],[2,98]); return np.zeros_like(d,dtype=np.float32) if hi<=lo else np.clip((d-lo)/(hi-lo),0,1).astype(np.float32)
    def get_model_name(self):return self._model_name
    def is_loaded(self):return self._loaded
    @property
    def device(self):return self._device_str
