import numpy as np
def _fit(x,y):
    A=np.column_stack([x,np.ones_like(x)]); a,b=np.linalg.lstsq(A,y,rcond=None)[0]; r=a*x+b-y
    return float(a),float(b),float(np.sqrt(np.mean(r*r))),float(np.mean(np.abs(r))),float(np.mean(r)),float(np.std(r))
def calibrate_with_arrays(relative_height,reference_elevation):
    m=np.isfinite(relative_height)&np.isfinite(reference_elevation); x=relative_height[m].astype(float); y=reference_elevation[m].astype(float)
    if x.size<10:raise ValueError("At least 10 valid overlapping pixels are required")
    a,b,*_= _fit(x,y); r=a*x+b-y; med=np.median(r); mad=np.median(np.abs(r-med))+1e-9; keep=np.abs(r-med)<=4*1.4826*mad
    if keep.sum()>=10:x=x[keep];y=y[keep]
    a,b,rmse,mae,mean,std=_fit(x,y); return {"scale":a,"offset":b,"valid_pixel_count":int(x.size),"rmse":rmse,"mae":mae,"residual_mean":mean,"residual_std":std}
def apply_calibration(relative_height,scale,offset):return (scale*relative_height+offset).astype(np.float32)
def calibrate_with_gcps(relative_height,gcps):
    vals=[]
    for g in gcps:
        x=int(round(g["pixel_x"]));y=int(round(g["pixel_y"]))
        if 0<=y<relative_height.shape[0] and 0<=x<relative_height.shape[1] and np.isfinite(relative_height[y,x]):vals.append((relative_height[y,x],g["reference_elevation"]))
    if len(vals)<3:raise ValueError("At least 3 valid GCPs are required")
    x=np.array([v[0] for v in vals],float);y=np.array([v[1] for v in vals],float);a,b,rmse,mae,mean,std=_fit(x,y)
    return {"scale":a,"offset":b,"valid_pixel_count":len(vals),"rmse":rmse,"mae":mae,"residual_mean":mean,"residual_std":std}
