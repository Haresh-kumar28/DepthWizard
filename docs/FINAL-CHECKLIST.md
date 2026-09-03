# v1.5.0 Final Completion Checklist

## Accuracy
- [x] Depth Anything V2 Small/Base/Large selector
- [x] Aerial-Depth checkpoint hook with explicit missing-checkpoint error
- [x] 518/768/1024 inference resolution control
- [x] Overlapping tiled inference
- [x] Configurable tile size
- [x] Configurable overlap
- [x] Edge refinement toggle
- [x] Terrain smoothing toggle
- [x] Reconstruction settings persisted per run
- [x] DEM calibration
- [x] GCP calibration
- [x] Deterministic calibration/holdout split
- [x] Independent holdout validation option
- [x] Diagnostic full-reference validation option
- [x] CRS/grid alignment before comparison
- [x] DEM/DSM/LiDAR-derived reference labeling
- [x] RMSE, MAE, R², Pearson, bias, standard error, P95 and max error
- [x] Error map
- [x] Scientific disclosure of DEM vs DSM semantics
- [x] No fabricated benchmark or improvement numbers

## Persistence
- [x] project_state.json
- [x] SQLite embedded index
- [x] projects table
- [x] reconstruction_runs table
- [x] calibration_runs table
- [x] validation_runs table
- [x] inspection_points table
- [x] artifacts table
- [x] Current calibration ID
- [x] Current validation ID
- [x] Automatic run creation
- [x] Historical runs preserved
- [x] Reference files preserved
- [x] Error maps preserved
- [x] Inspection history preserved
- [x] Browser refresh persistence
- [x] Backend restart persistence

## Frontend / UX
- [x] Persistent left navigation
- [x] Top application bar
- [x] Project context/status
- [x] Overview dashboard
- [x] Project/Imagery workspace
- [x] Reconstruction workspace
- [x] Calibration workspace
- [x] Validation workspace
- [x] 3D Terrain hero workspace
- [x] Inspection workspace
- [x] Error Analysis workspace
- [x] History workspace
- [x] Run comparison
- [x] Export center
- [x] Settings workspace
- [x] Activity center
- [x] Ctrl/Cmd+K command palette
- [x] Progress state
- [x] Empty states
- [x] Error states
- [x] Responsive layout
- [x] Professional dark technical visual system
- [x] Task workflow: Prepare → Reconstruct → Calibrate → Validate → Explore → Inspect → Compare → Export

## Existing core functionality preserved
- [x] JPG/PNG/GeoTIFF upload
- [x] 3D orbit controls
- [x] 3D flythrough
- [x] RGB/elevation/relief/slope/wire surface views
- [x] Terrain click inspection via UV-to-pixel mapping
- [x] GLB generation
- [x] Metric DSM GeoTIFF export
- [x] Relative-height export
- [x] JSON/HTML reports
