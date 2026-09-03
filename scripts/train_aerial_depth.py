"""Training scaffold for DepthWizard's aerial-domain depth engine.

This intentionally does not ship fabricated weights. Prepare paired aerial RGB
and elevation/DSM tiles, then adapt a Depth Anything V2 encoder + DPT head using
the official metric-depth training recipe. Place the resulting checkpoint at
models/aerial-depth/ to expose the Aerial-Depth engine in the application.
"""
from pathlib import Path
import argparse, json

def main():
    ap=argparse.ArgumentParser(description='Prepare an aerial-depth fine-tuning manifest (no fake weights).')
    ap.add_argument('--rgb-dir',required=True); ap.add_argument('--target-dir',required=True); ap.add_argument('--output',default='aerial_manifest.json')
    args=ap.parse_args(); rgb=sorted(str(x) for x in Path(args.rgb_dir).rglob('*') if x.suffix.lower() in {'.jpg','.jpeg','.png','.tif','.tiff'})
    targets=sorted(str(x) for x in Path(args.target_dir).rglob('*') if x.suffix.lower() in {'.tif','.tiff','.npy','.png'})
    payload={'rgb_files':rgb,'target_files':targets,'count_rgb':len(rgb),'count_targets':len(targets),'notes':['Use geographically separated train/validation regions.','Prefer LiDAR-derived DSM for surface targets; DEM is bare-earth and is not interchangeable with DSM.','Do not use validation regions for calibration or training.','Fine-tune the pretrained Depth Anything V2 encoder with a DPT head following the official metric-depth recipe.']}
    Path(args.output).write_text(json.dumps(payload,indent=2),encoding='utf-8'); print(f'Wrote {args.output}: {len(rgb)} RGB files, {len(targets)} targets')
if __name__=='__main__': main()
