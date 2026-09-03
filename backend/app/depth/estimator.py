import logging,time
from pathlib import Path
from typing import Optional
import numpy as np, torch
from PIL import Image
from app.depth.base import DepthEstimator, DepthResult
logger=logging.getLogger(__name__)
class DepthAnythingV2Estimator(DepthEstimator):
    MODEL_VARIANTS={"depth-anything-v2-small":"depth-anything/Depth-Anything-V2-Small-hf","depth-anything-v2-base":"depth-anything/Depth-Anything-V2-Base-hf","depth-anything-v2-large":"depth-anything/Depth-Anything-V2-Large-hf"}
    def __init__(self,model_name="depth-anything-v2-small",device_preference="auto",models_dir:Optional[str]=None,tile_size=768,overlap=0.25,mode="tiled",inference_resolution=768):
        self._model_name=model_name; self._device_str=self._choose_device(device_preference); self._models_dir=Path(models_dir) if models_dir else None; self._model=None; self._processor=None; self._loaded=False
        self.tile_size=max(256,int(tile_size)); self.overlap=float(np.clip(overlap,0.0,0.5)); self.mode=mode; self.inference_resolution=max(256,int(inference_resolution))
    @staticmethod
    def _choose_device(pref):
        if pref=="cuda" and not torch.cuda.is_available(): raise RuntimeError("CUDA requested but unavailable")
        return pref if pref in ("cpu","cuda") else ("cuda" if torch.cuda.is_available() else "cpu")
    def load_model(self):
        if self._loaded:return
        from transformers import AutoImageProcessor,AutoModelForDepthEstimation
        mid=self.MODEL_VARIANTS.get(self._model_name,self._model_name); kw={"cache_dir":str(self._models_dir)} if self._models_dir else {}
        if self._model_name=="aerial-depth":
            local=(self._models_dir or Path("models"))/"aerial-depth"
            provenance=local/"provenance.json"
            config=local/"config.json"
            weights=local/"model.safetensors"
            if not local.exists() or not config.exists() or not weights.exists():
                raise RuntimeError("Aerial-Depth is not trained/deployed. Install a complete fine-tuned checkpoint under models/aerial-depth.")
            if provenance.exists():
                try:
                    prov=__import__("json").loads(provenance.read_text(encoding="utf-8"))
                    if prov.get("status") != "TRAINED":
                        raise RuntimeError("Aerial-Depth provenance is not marked TRAINED; deployment is blocked.")
                except RuntimeError:
                    raise
                except Exception as exc:
                    raise RuntimeError(f"Aerial-Depth provenance is invalid: {exc}") from exc
            else:
                raise RuntimeError("Aerial-Depth provenance.json is required for deployment.")
            mid=str(local); kw={}
        self._processor=AutoImageProcessor.from_pretrained(mid,**kw); self._model=AutoModelForDepthEstimation.from_pretrained(mid,**kw); self._model.to(self._device_str).eval(); self._loaded=True
    def _predict_once(self,image):
        h,w=image.shape[:2]
        inputs=self._processor(images=Image.fromarray(image.astype(np.uint8)),return_tensors="pt",size={"height":self.inference_resolution,"width":self.inference_resolution}); inputs={k:v.to(self._device_str) for k,v in inputs.items()}
        with torch.inference_mode():
            out=self._model(**inputs); pred=torch.nn.functional.interpolate(out.predicted_depth.unsqueeze(1),size=(h,w),mode="bicubic",align_corners=False).squeeze()
        return np.nan_to_num(pred.float().cpu().numpy().astype(np.float32),nan=0,posinf=0,neginf=0)
    def _predict_tiled(self,image,progress_callback=None):
        h,w=image.shape[:2]
        if max(h,w)<=self.tile_size:
            d=self._predict_once(image)
            if progress_callback: progress_callback(1.0)
            return d
        stride=max(1,int(self.tile_size*(1.0-self.overlap)))
        ys=list(range(0,max(h-self.tile_size,0)+1,stride)); xs=list(range(0,max(w-self.tile_size,0)+1,stride))
        if not ys or ys[-1]+self.tile_size<h: ys.append(max(0,h-self.tile_size))
        if not xs or xs[-1]+self.tile_size<w: xs.append(max(0,w-self.tile_size))
        acc=np.zeros((h,w),np.float32); weights=np.zeros((h,w),np.float32)
        # Smooth center-weighted blending avoids seams between overlapping tiles.
        yy=np.linspace(-1,1,self.tile_size,dtype=np.float32); xx=np.linspace(-1,1,self.tile_size,dtype=np.float32)
        win=np.outer(1-np.abs(yy),1-np.abs(xx)); win=np.maximum(win,0.05).astype(np.float32)
        tiles_total=max(1,len(ys)*len(xs)); tiles_done=0
        for y in ys:
            for x in xs:
                tile=image[y:min(y+self.tile_size,h),x:min(x+self.tile_size,w)]
                ph,pw=tile.shape[:2]
                d=self._predict_once(tile)
                ww=win[:ph,:pw]
                acc[y:y+ph,x:x+pw]+=d*ww; weights[y:y+ph,x:x+pw]+=ww
                tiles_done+=1
                if progress_callback: progress_callback(tiles_done/tiles_total)
        return acc/np.maximum(weights,1e-6)
    def predict(self,image:np.ndarray,progress_callback=None)->DepthResult:
        if image.ndim!=3 or image.shape[2]!=3: raise ValueError("Expected RGB image HxWx3")
        self.load_model(); start=time.perf_counter(); h,w=image.shape[:2]
        depth=self._predict_tiled(image,progress_callback) if self.mode=="tiled" else self._predict_once(image)
        if progress_callback: progress_callback(1.0)
        norm=self._normalize(depth)
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
