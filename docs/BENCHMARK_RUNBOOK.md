# DepthWizard multi-landscape benchmark

Use this only with real predicted DSMs and real reference DSM/DEM/LiDAR-derived surfaces. Never insert invented accuracy values into a report.

## 1. Prepare a manifest

Copy `docs/benchmark_template.csv` and fill in one row per dataset. Suggested coverage:

- Urban
- Sparse / rural
- Hilly
- Forested
- Difficult / mixed scene

`predicted` should point to the calibrated DepthWizard DSM GeoTIFF. `reference` should point to the corresponding ground-truth DSM/DEM.

## 2. Run

From the repository root with the backend virtual environment active:

```bat
python scripts\benchmark_metrics.py docs\benchmark.csv
```

The script aligns reference rasters to the prediction grid using CRS/transform when available and reports RMSE, MAE, R², Pearson correlation, bias, standard error and valid-pixel coverage.

## 3. Report

For each landscape record:

| Dataset | Landscape | RMSE (m) | MAE (m) | R² | Pearson r | Valid % |
|---|---|---:|---:|---:|---:|---:|
| Dataset A | Urban | from run | from run | from run | from run | from run |
| Dataset B | Sparse | from run | from run | from run | from run | from run |
| Dataset C | Hilly | from run | from run | from run | from run | from run |
| Dataset D | Forested | from run | from run | from run | from run | from run |
| Dataset E | Mixed | from run | from run | from run | from run | from run |

The benchmark is meaningful only when the predicted DSM has been calibrated to metric elevation and the reference surface is spatially corresponding.
