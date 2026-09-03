# DepthWizard v1.7.0

**Single-View Height Estimation and 3D Flythrough — final polished SIH-ready architecture**

DepthWizard is a local-first geospatial AI workstation that converts a single RGB JPG/PNG/GeoTIFF into relative surface height, optional metric elevation, a standard GeoTIFF surface, terrain derivatives and an interactive Three.js 3D flythrough.

## What is included

### Accuracy & scientific integrity
- Depth Anything V2 Small / Base / Large model selection.
- Optional **Aerial-Depth** engine hook for a real fine-tuned checkpoint at `models/aerial-depth/` (no fabricated weights are included).
- 518 / 768 / 1024 inference-resolution controls.
- Overlapping tiled inference with configurable tile size and overlap.
- Optional edge refinement and terrain smoothing.
- Native raster grid/CRS preservation for georeferenced inputs.
- DEM calibration with deterministic calibration/validation split (default 80/20).
- GCP calibration for known control points.
- Independent holdout validation or explicit diagnostic full-reference validation.
- Raster CRS/grid alignment before evaluation.
- RMSE, MAE, R², Pearson correlation, bias, standard error, P95 and maximum absolute error.
- Spatial error-map generation.
- Explicit DEM vs DSM/LiDAR-derived reference labeling and scientific limitations.
- Reproducible reconstruction settings stored with every run.

### Persistence & reproducibility
- Project state survives browser refresh and backend restart.
- `project_state.json` is the portable project state record.
- Embedded SQLite index: `data/depthwizard.db`.
- Tables: projects, reconstruction_runs, calibration_runs, validation_runs, inspection_points, artifacts.
- Calibration, validation and reconstruction runs are never overwritten by the next run.
- Current calibration and validation run IDs are persisted.
- Reference files, error maps, NPY arrays, GeoTIFF, GLB, HTML and JSON reports are retained as project artifacts.
- Inspection points are automatically persisted.

### Frontend / UX
The new task-based interface follows:

**Prepare → Reconstruct → Calibrate → Validate → Explore → Inspect → Compare → Export**

Workspaces:
- Overview
- Project / Imagery
- Reconstruction
- Calibration
- Validation
- 3D Terrain
- Inspection
- Error Analysis
- History
- Exports
- Settings

The shell includes persistent navigation, project/status context, activity center, Ctrl/Cmd+K command palette, contextual controls, progress states, professional empty states, responsive layout and a dedicated 3D hero workspace.

## v1.7.0 final polish

This release hardens the workstation behavior around the final SIH workflow: live job status is exposed by the backend, progress is persisted at meaningful stages, completion notices auto-dismiss, reconstruction settings persist with the project, and the 3D grid/camera framing are computed from the actual terrain bounds. Contours are generated from the loaded terrain mesh when enabled.

## Quick start — Windows

### Backend

```powershell
py -3.12 -m venv backend\.venv
backend\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
cd backend
$env:PYTHONPATH='.'
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Frontend

Open a second PowerShell window:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal, normally `http://localhost:5173`.

## Model download

The source package does not bundle large model weights. From the project root:

```powershell
python scripts\download_model.py
```

For the experimental Aerial-Depth option, place a genuine fine-tuned Hugging Face-compatible checkpoint under:

```text
models\aerial-depth\
```

A preparation helper is provided at `scripts/train_aerial_depth.py`. It creates a paired RGB/target manifest and deliberately does **not** invent or ship weights.

## Evidence / benchmark policy

The application records measured metrics but does not manufacture an "after optimization" score. The previously observed benchmark values should be treated as measured baseline evidence with the documented caveats. For a headline SIH result, use a geographically independent reference or a deterministic holdout that was not used for calibration.

A USGS 1 m DEM is generally a bare-earth elevation product. It is not automatically equivalent to a vegetation/building DSM. The report therefore surfaces this limitation explicitly.

## Release documentation

- `docs/V1.6.0-FINAL-ARCHITECTURE.md`
- `docs/V1.4.0-ACCURACY-UPGRADE.md`
- `docs/V1.3.0-PERSISTENT-ANALYSIS-HISTORY.md`
- `docs/BENCHMARK_RUNBOOK.md`
- `docs/DEMO_SCRIPT.md`
- `docs/FEATURE_MATRIX.md`
