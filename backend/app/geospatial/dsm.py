from pathlib import Path
import numpy as np, rasterio
from rasterio.transform import Affine

def create_dsm_geotiff(elevation,output_path,crs=None,transform=None,nodata=-9999.0,reference_path=None,profile_extra=None):
    a=np.asarray(elevation,dtype=np.float32); p=Path(output_path); p.parent.mkdir(parents=True,exist_ok=True)
    if a.ndim!=2: raise ValueError('Elevation must be a 2D array')
    if reference_path:
        with rasterio.open(reference_path) as s:
            profile=s.profile.copy(); profile.update(width=a.shape[1],height=a.shape[0])
    else:
        tr=Affine(*transform) if isinstance(transform,(list,tuple)) else (transform or Affine.identity())
        profile={'driver':'GTiff','height':a.shape[0],'width':a.shape[1],'count':1,'dtype':'float32','crs':crs,'transform':tr}
    profile.update(driver='GTiff',height=a.shape[0],width=a.shape[1],count=1,dtype='float32',nodata=nodata,compress='deflate',predictor=3,tiled=False)
    if profile_extra: profile.update(profile_extra)
    with rasterio.open(p,'w',**profile) as dst: dst.write(np.where(np.isfinite(a),a,nodata).astype(np.float32),1)
    return p

def compute_dsm_statistics(elevation,nodata=-9999.0):
    a=np.asarray(elevation,float); v=a[np.isfinite(a)&(a!=nodata)]
    if not v.size: raise ValueError('DSM contains no valid pixels')
    return {'min_elevation':float(v.min()),'max_elevation':float(v.max()),'mean_elevation':float(v.mean()),'median_elevation':float(np.median(v)),'std_elevation':float(v.std()),'elevation_range':float(v.max()-v.min()),'valid_pixel_count':int(v.size),'total_pixel_count':int(a.size),'valid_pixel_percentage':float(100*v.size/a.size)}
