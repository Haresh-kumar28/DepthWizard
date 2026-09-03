from pathlib import Path
import numpy as np, rasterio
from PIL import Image
SUPPORTED_RASTER_EXTENSIONS={'.jpg','.jpeg','.png','.tif','.tiff'}

def inspect_image(path):
    p=Path(path)
    if not p.exists(): raise FileNotFoundError(path)
    if p.suffix.lower() not in SUPPORTED_RASTER_EXTENSIONS: raise ValueError(f'Unsupported file type: {p.suffix}')
    try:
        with rasterio.open(p) as s:
            return {'type':'geospatial' if s.crs or p.suffix.lower() in {'.tif','.tiff'} else 'image','width':s.width,'height':s.height,'channels':min(s.count,3),'dtype':str(s.dtypes[0]),'crs':s.crs.to_string() if s.crs else None,'epsg':s.crs.to_epsg() if s.crs else None,'transform':list(s.transform),'bounds':{'left':s.bounds.left,'bottom':s.bounds.bottom,'right':s.bounds.right,'top':s.bounds.top},'resolution':list(s.res),'nodata':s.nodata,'band_count':s.count}
    except Exception:
        with Image.open(p) as im: return {'type':'image','width':im.width,'height':im.height,'channels':len(im.getbands()),'dtype':'uint8','crs':None,'epsg':None,'transform':None,'bounds':None,'resolution':None,'nodata':None,'band_count':len(im.getbands())}

def read_rgb(path):
    try:
        with rasterio.open(path) as s:
            a=np.moveaxis(s.read(min(3,s.count),masked=True).filled(np.nan),0,-1)
            if a.shape[2]==1: a=np.repeat(a,3,axis=2)
            if not np.isfinite(a).all() or a.dtype!=np.uint8:
                vals=a[np.isfinite(a)]; lo,hi=np.percentile(vals,[2,98]) if vals.size else (0,1); a=np.nan_to_num(np.clip((a-lo)/(hi-lo+1e-9)*255,0,255)).astype(np.uint8)
            return a
    except Exception:
        with Image.open(path).convert('RGB') as im: return np.asarray(im)
