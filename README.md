# DepthWizard

**Single-View Height Estimation and 3D Flythrough**

DepthWizard is a local-first geospatial computer-vision application that turns a single RGB image into a relative surface-height map and an interactive 3D terrain representation. For georeferenced imagery, external GCP calibration can convert relative surface height into metric elevation.

## Current implementation

- JPG/PNG/TIFF/GeoTIFF upload and metadata inspection
- Local Depth Anything V2 Small inference through Hugging Face Transformers
- Relative depth and relative-height artifacts
- DSM GeoTIFF generation with geospatial metadata preservation
- GCP-based metric calibration
- DSM statistics and terrain slope
- Reference DSM validation metrics
- Rendering-resolution terrain mesh and GLB export
- RGB texture mapping
- Three.js orbit/flythrough viewer
- Background processing state and progress
- JSON project report and downloadable artifacts
- Backend unit tests

## Important scientific note

Monocular depth is scale ambiguous. A relative DSM is not an absolute geodetic DSM. Metric elevation requires DEM/GCP calibration and should be independently validated against reference data. Do not report fabricated accuracy.

## Quick start

### Backend

```powershell
py -3.12 -m venv backend\.venv
backend\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
cd backend
$env:PYTHONPATH='.'
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Then open `http://localhost:5173`.

### Tests

```powershell
cd backend
$env:PYTHONPATH='.'
pytest -q
```

## Model cache

The model checkpoint is intentionally not bundled in the source ZIP. Run `python scripts/download_model.py` once or allow the first inference to download/cache it. This keeps the repository portable and avoids redistributing a large binary checkpoint.

## Project flow

`Upload → Metadata → Depth Anything V2 → Relative Height → DSM → Mesh/GLB → Three.js Flythrough → Optional GCP Calibration → Validation`

See `docs/PIPELINE.md` and `docs/INSTALLATION.md` for details.
