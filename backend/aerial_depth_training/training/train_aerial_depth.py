#!/usr/bin/env python
"""Fine-tune Depth Anything V2 for aerial metric elevation.

Uses Hugging Face Transformers Depth Anything V2 as the backbone.
Target is absolute DSM elevation in meters.

This is intentionally explicit: no synthetic metrics and no fake checkpoint.
"""

from __future__ import annotations
import argparse, json, math, time
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from transformers import AutoImageProcessor, AutoModelForDepthEstimation

class PatchDataset(Dataset):
    def __init__(self, root, split):
        self.rgb = sorted((Path(root)/split/"rgb").glob("*.npy"))
        if not self.rgb:
            raise RuntimeError(f"No patches found for {split}")
        self.dsm = [Path(root)/split/"dsm"/p.name for p in self.rgb]
    def __len__(self): return len(self.rgb)
    def __getitem__(self, i):
        x = np.load(self.rgb[i]).astype(np.uint8)
        y = np.load(self.dsm[i]).astype(np.float32)
        return x, y

def grad_loss(pred, target, mask):
    px = pred[..., :, 1:] - pred[..., :, :-1]
    py = pred[..., 1:, :] - pred[..., :-1, :]
    tx = target[..., :, 1:] - target[..., :, :-1]
    ty = target[..., 1:, :] - target[..., :-1, :]
    mx = mask[..., :, 1:] & mask[..., :, :-1]
    my = mask[..., 1:, :] & mask[..., :-1, :]
    vals = []
    if mx.any(): vals.append((px[mx]-tx[mx]).abs().mean())
    if my.any(): vals.append((py[my]-ty[my]).abs().mean())
    return sum(vals)/len(vals) if vals else pred.new_tensor(0.)

def metrics(pred, target, mask):
    p, t = pred[mask], target[mask]
    err = p-t
    mae = err.abs().mean().item()
    rmse = torch.sqrt((err**2).mean()).item()
    bias = err.mean().item()
    p95 = torch.quantile(err.abs(), 0.95).item()
    if p.numel() > 1:
        r = torch.corrcoef(torch.stack([p,t]))[0,1].item()
        ss_res = ((t-p)**2).sum()
        ss_tot = ((t-t.mean())**2).sum().clamp_min(1e-12)
        r2 = (1-ss_res/ss_tot).item()
    else:
        r, r2 = float("nan"), float("nan")
    return {"mae":mae,"rmse":rmse,"bias":bias,"p95_abs_error":p95,
            "pearson_r":r,"r2":r2,"valid_pixels":int(p.numel())}

@torch.no_grad()
def evaluate(model, processor, loader, device):
    model.eval()
    agg = []
    for rgb, dsm in loader:
        inputs = processor(images=[im for im in rgb], return_tensors="pt").to(device)
        out = model(**inputs).predicted_depth
        out = F.interpolate(out[:,None], size=dsm.shape[-2:], mode="bilinear", align_corners=False)[:,0]
        target = dsm.to(device)
        mask = torch.isfinite(target)
        # Align global affine ambiguity only for evaluation if requested elsewhere.
        agg.append(metrics(out, target, mask))
    keys = ["mae","rmse","bias","p95_abs_error","pearson_r","r2"]
    return {k: float(np.nanmean([a[k] for a in agg])) for k in keys}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--model", default="depth-anything/Depth-Anything-V2-Small-hf")
    ap.add_argument("--output", required=True)
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--batch-size", type=int, default=2)
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--grad-weight", type=float, default=0.25)
    args = ap.parse_args()

    device = torch.device(args.device if torch.cuda.is_available() or args.device=="cpu" else "cpu")
    if device.type == "cpu":
        print("WARNING: CPU training is suitable only for smoke tests, not final SIH training.")

    processor = AutoImageProcessor.from_pretrained(args.model)
    model = AutoModelForDepthEstimation.from_pretrained(args.model).to(device)
    train = PatchDataset(args.data, "train")
    val = PatchDataset(args.data, "val")
    tr = DataLoader(train, batch_size=args.batch_size, shuffle=True, num_workers=0)
    va = DataLoader(val, batch_size=1, shuffle=False, num_workers=0)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)

    history=[]
    best=float("inf")
    outdir=Path(args.output); outdir.mkdir(parents=True, exist_ok=True)

    for epoch in range(1,args.epochs+1):
        model.train(); losses=[]
        for rgb, dsm in tr:
            inputs = processor(images=[im for im in rgb], return_tensors="pt").to(device)
            target = dsm.to(device)
            mask = torch.isfinite(target)
            pred = model(**inputs).predicted_depth
            pred = F.interpolate(pred[:,None], size=target.shape[-2:], mode="bilinear", align_corners=False)[:,0]
            # Per-image robust normalization stabilizes optimization while preserving surface structure.
            vals = []
            for b in range(pred.shape[0]):
                m=mask[b]
                if m.any():
                    mu, sd = target[b][m].mean(), target[b][m].std().clamp_min(1e-3)
                    vals.append((pred[b][m]-target[b][m]/sd).abs().mean() + (pred[b][m]-target[b][m]).abs().mean()*0.0)
            if not vals: continue
            loss = torch.stack(vals).mean()
            loss = loss + args.grad_weight*grad_loss(pred, target, mask)
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            losses.append(loss.item())

        val_metrics = evaluate(model, processor, va, device)
        rec={"epoch":epoch,"train_loss":float(np.mean(losses)),"val":val_metrics}
        history.append(rec)
        print(json.dumps(rec))
        if val_metrics["rmse"] < best:
            best=val_metrics["rmse"]
            model.save_pretrained(outdir/"best")
            processor.save_pretrained(outdir/"best")
            (outdir/"best_metrics.json").write_text(json.dumps(rec, indent=2))

    (outdir/"history.json").write_text(json.dumps(history, indent=2))
    print(f"Best validation RMSE: {best:.6f} m")

if __name__=="__main__":
    main()
