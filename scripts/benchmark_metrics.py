"""Evaluate predicted DSMs against reference DSM/DEM rasters.

Manifest CSV columns:
name,predicted,reference,landscape
Paths are relative to the manifest directory unless absolute.
"""
import argparse, csv, json
from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import reproject
from rasterio.enums import Resampling
from app.evaluation.metrics import calculate_metrics

def resolve(base, value):
    p=Path(value); return p if p.is_absolute() else base/p

def evaluate(pred_path, ref_path):
    with rasterio.open(pred_path) as p, rasterio.open(ref_path) as r:
        pred=p.read(1).astype(np.float32)
        ref=np.full(pred.shape,np.nan,np.float32)
        if p.crs and r.crs:
            reproject(rasterio.band(r,1),ref,src_transform=r.transform,src_crs=r.crs,dst_transform=p.transform,dst_crs=p.crs,resampling=Resampling.bilinear,dst_nodata=np.nan)
        elif pred.shape==r.shape:
            ref=r.read(1).astype(np.float32)
        else:
            raise ValueError('Reference has no CRS and dimensions do not match prediction')
    return calculate_metrics(pred,ref)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('manifest',type=Path);ap.add_argument('--output',type=Path,default=None);args=ap.parse_args()
    rows=[]
    with args.manifest.open(newline='',encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            name=row.get('name') or Path(row['predicted']).stem
            m=evaluate(resolve(args.manifest.parent,row['predicted']),resolve(args.manifest.parent,row['reference']))
            m.update({'name':name,'landscape':row.get('landscape','unspecified')});rows.append(m)
    out=args.output or args.manifest.with_name(args.manifest.stem+'_results.json');out.write_text(json.dumps(rows,indent=2),encoding='utf-8')
    print(f'Evaluated {len(rows)} dataset(s)')
    for r in rows: print(f"{r['name']}: RMSE={r['rmse']:.3f} MAE={r['mae']:.3f} R2={r['r2']:.3f} R={r['pearson_correlation']:.3f} ({r['landscape']})")
    print(f'Results: {out}')
if __name__=='__main__': main()
