# DepthWizard v1.5.0 Feature Matrix

| Requirement | Final implementation | Evidence / location |
|---|---|---|
| JPG / PNG / TIFF input | Yes | Project upload API + UI |
| GeoTIFF CRS metadata | Yes | Metadata workspace |
| Relative DSM/raster | Yes | Reconstruction pipeline |
| Metric DSM | Yes | DEM/GCP calibration |
| Depth Anything V2 | Small/Base/Large | Reconstruction settings |
| Higher-resolution inference | 518/768/1024 | Reconstruction settings |
| Tiled inference | Overlap + configurable tile size | Depth estimator |
| Edge refinement | Optional | Processing settings |
| Terrain smoothing | Optional | Processing settings |
| Aerial-domain model | Explicit checkpoint hook | `models/aerial-depth/` |
| DEM calibration | Yes | Calibration workspace |
| GCP calibration | Yes | Calibration workspace |
| Calibration holdout | Default 80/20 deterministic split | Calibration history |
| Independent validation | Yes | Validation workspace |
| CRS/grid alignment | Yes | Calibration/validation backend |
| RMSE / MAE | Yes | Validation metrics |
| R² / Pearson | Yes | Validation metrics |
| Bias / Std error | Yes | Validation metrics |
| P95 / max error | Yes | Error analysis |
| Error map | Yes | Validation artifact |
| DEM vs DSM caveat | Yes | Reports + UI |
| 3D textured terrain | Yes | Three.js + GLB |
| Orbit navigation | Yes | 3D Terrain |
| Flythrough | Yes | 3D Terrain |
| Surface layers | RGB/elevation/relief/slope/wire | 3D Terrain |
| Point inspection | Yes | UV-to-pixel mapping |
| Inspection history | Yes | SQLite + project state |
| Calibration history | Yes | SQLite + project state |
| Validation history | Yes | SQLite + project state |
| Reconstruction history | Yes | SQLite + project state |
| Current result IDs | Yes | Project state |
| Refresh persistence | Yes | localStorage + backend state |
| Backend restart persistence | Yes | JSON + SQLite |
| Artifact store | Yes | Project folders |
| Export center | GeoTIFF/NPY/GLB/reports/previews | Exports workspace |
| Run comparison | Yes | History workspace |
| Activity center | Yes | Top bar |
| Command palette | Ctrl/Cmd+K | Top bar |
| Responsive UX | Yes | CSS breakpoints |
| Empty/loading/error states | Yes | Frontend |
| Local-first / standalone | Yes | No cloud dependency required |
| No fabricated accuracy | Yes | Documentation + validation policy |
