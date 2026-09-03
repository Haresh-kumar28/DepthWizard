#!/usr/bin/env python
"""Benchmark baseline vs aerial checkpoint on the untouched test split.

This script deliberately does not invent a result. If a checkpoint is absent,
Aerial-Depth is marked NOT_BENCHMARKED.
"""

from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--baseline-json", required=True)
    ap.add_argument("--aerial-json", required=False)
    ap.add_argument("--output", required=True)
    args=ap.parse_args()

    base=json.loads(Path(args.baseline_json).read_text())
    aerial=json.loads(Path(args.aerial_json).read_text()) if args.aerial_json and Path(args.aerial_json).exists() else None

    result={
      "protocol":"held_out_urban_test",
      "baseline":base,
      "aerial_depth":aerial if aerial else {"status":"NOT_BENCHMARKED"},
      "improvement":{}
    }
    if aerial:
        for k in ("rmse","mae","p95_abs_error"):
            if k in base and k in aerial:
                result["improvement"][k] = {
                    "absolute": float(base[k]-aerial[k]),
                    "percent": float(100*(base[k]-aerial[k])/base[k]) if base[k] else None
                }
        if "rmse" in base and "rmse" in aerial:
            result["improvement"]["status"] = "IMPROVED" if aerial["rmse"] < base["rmse"] else "NOT_IMPROVED"
    else:
        result["improvement"]["status"]="NOT_BENCHMARKED"

    Path(args.output).write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))

if __name__=="__main__":
    main()
