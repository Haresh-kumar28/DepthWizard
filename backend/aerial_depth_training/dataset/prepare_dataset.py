#!/usr/bin/env python
"""Prepare paired aerial RGB/DSM GeoTIFFs into train/val/test patches.

Expected source layout:
source/
  tile_01_rgb.tif
  tile_01_dsm.tif
  tile_02_rgb.tif
  tile_02_dsm.tif

Pairing is based on the shared tile stem after removing _rgb/_dsm.
The split is tile-level to prevent spatial leakage.
"""

from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import Window

def pair_files(src: Path):
    rgbs = sorted(src.glob("*_rgb.tif")) + sorted(src.glob("*_rgb.tiff"))
    out = []
    for rgb in rgbs:
        stem = rgb.stem
        key = stem[:-4] if stem.endswith("_rgb") else stem
        candidates = [src / f"{key}_dsm.tif", src / f"{key}_dsm.tiff"]
        dsm = next((p for p in candidates if p.exists()), None)
        if dsm:
            out.append((key, rgb, dsm))
    if not out:
        raise SystemExit("No *_rgb.tif + *_dsm.tif pairs found.")
    return out

def check_pair(rgb_path, dsm_path):
    with rasterio.open(rgb_path) as r, rasterio.open(dsm_path) as d:
        if r.width != d.width or r.height != d.height:
            raise ValueError(f"shape mismatch: {rgb_path.name} vs {dsm_path.name}")
        if r.transform != d.transform:
            raise ValueError(f"transform mismatch: {rgb_path.name} vs {dsm_path.name}")
        if r.crs != d.crs:
            raise ValueError(f"CRS mismatch: {rgb_path.name} vs {dsm_path.name}")
        if d.count != 1:
            raise ValueError(f"DSM must have one band: {dsm_path}")
        if r.count < 3:
            raise ValueError(f"RGB must have >=3 bands: {rgb_path}")
        arr = d.read(1, masked=True)
        valid = np.asarray(arr.filled(np.nan), dtype=np.float32)
        valid = valid[np.isfinite(valid)]
        if valid.size < 100:
            raise ValueError(f"DSM has too few valid pixels: {dsm_path}")
        return {
            "width": r.width, "height": r.height,
            "crs": str(r.crs), "transform": list(r.transform),
            "bounds": list(r.bounds),
            "resolution": list(r.res),
            "dsm_min": float(valid.min()),
            "dsm_max": float(valid.max()),
            "valid_fraction": float(valid.size / (r.width*r.height)),
        }

def write_patch(rgb, dsm, out_dir, split, tile, x, y, size):
    rgb_arr = rgb.read([1,2,3], window=Window(x,y,size,size))
    dsm_arr = dsm.read(1, window=Window(x,y,size,size), masked=True)
    rgb_path = out_dir / split / "rgb" / f"{tile}_{x}_{y}.npy"
    dsm_path = out_dir / split / "dsm" / f"{tile}_{x}_{y}.npy"
    rgb_path.parent.mkdir(parents=True, exist_ok=True)
    dsm_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(rgb_path, np.transpose(rgb_arr, (1,2,0)).astype(np.uint8))
    np.save(dsm_path, dsm_arr.filled(np.nan).astype(np.float32))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--patch-size", type=int, default=518)
    ap.add_argument("--stride", type=int, default=450)
    ap.add_argument("--val-tiles", default="")
    ap.add_argument("--test-tiles", default="")
    args = ap.parse_args()

    src, out = Path(args.source), Path(args.output)
    pairs = pair_files(src)
    val_tiles = {x.strip() for x in args.val_tiles.split(",") if x.strip()}
    test_tiles = {x.strip() for x in args.test_tiles.split(",") if x.strip()}

    if val_tiles & test_tiles:
        raise SystemExit("A tile cannot be both validation and test.")

    manifest = []
    for tile, rgb_path, dsm_path in pairs:
        info = check_pair(rgb_path, dsm_path)
        if tile in test_tiles: split = "test"
        elif tile in val_tiles: split = "val"
        else: split = "train"

        with rasterio.open(rgb_path) as rgb, rasterio.open(dsm_path) as dsm:
            for y in range(0, max(1, rgb.height - args.patch_size + 1), args.stride):
                for x in range(0, max(1, rgb.width - args.patch_size + 1), args.stride):
                    if x + args.patch_size > rgb.width or y + args.patch_size > rgb.height:
                        continue
                    write_patch(rgb, dsm, out, split, tile, x, y, args.patch_size)

        manifest.append({"tile": tile, "split": split, **info})

    (out / "manifest.json").write_text(json.dumps({
        "schema_version": 1,
        "patch_size": args.patch_size,
        "stride": args.stride,
        "tiles": manifest
    }, indent=2))

    print(f"Prepared {len(manifest)} tiles under {out}")

if __name__ == "__main__":
    main()
