import numpy as np

def _fit(x,y):
    A=np.column_stack([x,np.ones_like(x)]); a,b=np.linalg.lstsq(A,y,rcond=None)[0]; e=a*x+b-y
    return float(a),float(b),float(np.sqrt(np.mean(e*e))),float(np.mean(np.abs(e))),float(np.mean(e)),float(np.std(e))

def calibrate_with_arrays(relative_height,reference_elevation):
    x=np.asarray(relative_height,float); y=np.asarray(reference_elevation,float)
    if x.shape!=y.shape: raise ValueError('Relative and reference rasters must be aligned to the same shape')
    m=np.isfinite(x)&np.isfinite(y)&(x!=-9999)&(y!=-9999); x=x[m]; y=y[m]
    if x.size<10: raise ValueError('At least 10 valid overlapping pixels are required')
    a,b,*_= _fit(x,y); e=a*x+b-y; med=np.median(e); mad=np.median(np.abs(e-med))
    if mad>1e-9:
        keep=np.abs(e-med)<=4*1.4826*mad
        if keep.sum()>=10: x=x[keep]; y=y[keep]
    a,b,rmse,mae,mean,std=_fit(x,y)
    return {'scale':a,'offset':b,'valid_pixel_count':int(x.size),'rmse':rmse,'mae':mae,'residual_mean':mean,'residual_std':std}

def apply_calibration(relative_height,scale,offset):
    a=np.asarray(relative_height,dtype=np.float32); out=scale*a+offset; return np.where(np.isfinite(a),out,np.nan).astype(np.float32)

def calibrate_with_gcps(relative_height,gcps):
    vals=[]
    for g in gcps:
        x=int(round(g['pixel_x'])); y=int(round(g['pixel_y']))
        if 0<=y<relative_height.shape[0] and 0<=x<relative_height.shape[1] and np.isfinite(relative_height[y,x]): vals.append((relative_height[y,x],g['reference_elevation']))
    if len(vals)<3: raise ValueError('At least 3 valid GCPs are required')
    x=np.array([v[0] for v in vals],float); y=np.array([v[1] for v in vals],float)
    a,b,rmse,mae,mean,std=_fit(x,y)
    return {'scale':a,'offset':b,'valid_pixel_count':len(vals),'rmse':rmse,'mae':mae,'residual_mean':mean,'residual_std':std}
