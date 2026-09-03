#!/usr/bin/env python
"""Evaluate a saved checkpoint on the untouched test set.

The test split must not be used for training or hyperparameter selection.
"""

from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np, torch
import torch.nn.functional as F
from transformers import AutoImageProcessor, AutoModelForDepthEstimation
from training.train_aerial_depth import PatchDataset, metrics

@torch.no_grad()
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--device", default="cuda")
    args=ap.parse_args()
    device=torch.device(args.device if torch.cuda.is_available() or args.device=="cpu" else "cpu")
    processor=AutoImageProcessor.from_pretrained(args.model)
    model=AutoModelForDepthEstimation.from_pretrained(args.model).to(device).eval()
    ds=PatchDataset(args.data,"test")
    vals=[]
    for i in range(len(ds)):
        rgb,dsm=ds[i]
        inp=processor(images=rgb,return_tensors="pt").to(device)
        pred=model(**inp).predicted_depth
        pred=F.interpolate(pred[:,None],size=dsm.shape,mode="bilinear",align_corners=False)[0,0]
        target=torch.from_numpy(dsm).to(device)
        mask=torch.isfinite(target)
        vals.append(metrics(pred,target,mask))
    keys=["mae","rmse","bias","p95_abs_error","pearson_r","r2"]
    result={k:float(np.nanmean([x[k] for x in vals])) for k in keys}
    result["valid_coverage_percent"]=float(np.mean([x["valid_pixels"]/(ds[i][1].size)*100 for i,x in enumerate(vals)]))
    Path(args.output).write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    main()
