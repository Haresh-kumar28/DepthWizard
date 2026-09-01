import numpy as np
def calculate_metrics(predicted,reference):
    p=np.asarray(predicted,float);r=np.asarray(reference,float)
    if p.shape!=r.shape: raise ValueError("Predicted and reference arrays must have identical shape")
    m=np.isfinite(p)&np.isfinite(r);p=p[m];r=r[m]
    if not p.size:raise ValueError("No valid comparison pixels")
    e=p-r; corr=float(np.corrcoef(p,r)[0,1]) if p.size>1 and np.std(p)>0 and np.std(r)>0 else 0.0
    return {"mae":float(np.mean(np.abs(e))),"rmse":float(np.sqrt(np.mean(e**2))),"pearson_correlation":corr,"bias":float(np.mean(e)),"std_error":float(np.std(e)),"valid_pixel_count":int(p.size),"valid_pixel_percentage":float(100*p.size/(np.asarray(predicted).size))}
