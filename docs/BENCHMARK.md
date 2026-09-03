# DepthWizard benchmark protocol

Use 3–5 strong aerial/remote-sensing scenes, ideally including:

- Urban: dense buildings/roads
- Sparse: open terrain
- Hilly: strong relief
- Forested: vegetation complexity
- Mixed: generalization check

For each scene record: input type, CRS/EPSG, GSD, image dimensions, calibration method, calibration RMSE/MAE, validation RMSE/MAE/R²/correlation, valid percentage, runtime, and qualitative 3D notes.

Recommended table:

| Scene | Landscape | CRS | GSD | Calibration | RMSE (m) | MAE (m) | R² | Pearson r | Runtime |
|---|---|---|---:|---|---:|---:|---:|---:|---:|
| 01 | Urban | | | DEM/GCP | | | | | |
| 02 | Sparse | | | DEM/GCP | | | | | |
| 03 | Hilly | | | DEM/GCP | | | | | |
| 04 | Forested | | | DEM/GCP | | | | | |
| 05 | Mixed | | | DEM/GCP | | | | | |
