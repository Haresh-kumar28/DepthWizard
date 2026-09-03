import numpy as np

def calculate_metrics(predicted, reference):
    p=np.asarray(predicted,dtype=float); r=np.asarray(reference,dtype=float)
    if p.shape!=r.shape: raise ValueError('Predicted and reference arrays must have identical shape')
    m=np.isfinite(p)&np.isfinite(r)&(p!=-9999)&(r!=-9999)
    p=p[m]; r=r[m]
    if p.size<2: raise ValueError('At least 2 valid comparison pixels are required')
    e=p-r; mae=float(np.mean(np.abs(e))); rmse=float(np.sqrt(np.mean(e*e))); bias=float(np.mean(e)); std=float(np.std(e))
    corr=float(np.corrcoef(p,r)[0,1]) if np.std(p)>0 and np.std(r)>0 else 0.0
    ss_res=float(np.sum((r-p)**2)); ss_tot=float(np.sum((r-np.mean(r))**2)); r2=float(1-ss_res/ss_tot) if ss_tot>1e-12 else 0.0
    return {'mae':mae,'rmse':rmse,'pearson_correlation':corr,'r2':r2,'bias':bias,'std_error':std,'p95_abs_error':float(np.percentile(np.abs(e),95)),'max_abs_error':float(np.max(np.abs(e))),'valid_pixel_count':int(p.size),'valid_pixel_percentage':float(100*p.size/m.size if m.size else 0)}
