# DepthWizard v1.1.0 — release checklist

## Implemented capability matrix

1. **Stable 3D viewer** — GLB validation, loading/error states, retry, camera presets, Orbit/Fly, fullscreen.
2. **Convincing 3D geometry** — geospatial pixel scale, vertical relief control, RGB/relief/wireframe modes, terrain lighting.
3. **Point-click inspection** — click terrain to inspect elevation, relative height, slope and pixel coordinates.
4. **GeoTIFF + CRS** — GeoTIFF metadata, CRS/EPSG, transform, bounds, resolution and NoData preservation.
5. **DEM/GCP calibration** — robust DEM raster calibration endpoint and 3-point GCP affine scale/offset calibration.
6. **Metric DSM GeoTIFF** — float32 metre-valued DSM after calibration, with geospatial profile preserved for GeoTIFF inputs.
7. **RMSE/MAE/R²/correlation** — spatially aligned reference validation with bias and standard error.
8. **Error map** — predicted minus reference PNG + NumPy error raster.
9. **UI/UX** — integrated project, terrain, calibration, validation, inspection and export workflow.
10. **3–5 datasets** — benchmark template is provided in `docs/BENCHMARK.md`.
11. **Multi-landscape evaluation** — urban, sparse, hilly and forested evaluation matrix is provided.
12. **Input/output/export** — JPG/PNG/GeoTIFF upload, DSM, GLB, depth, slope, error map and reports.
13. **Performance/stability** — cached model, bounded mesh resolution, progress polling, input limits and error handling.
14. **Automated report** — JSON reproducibility report plus HTML report artifact.
15. **Standalone deployment** — Dockerfiles and compose configuration retained; see `docs/INSTALLATION.md`.

## Scientific note

Depth Anything V2 supplies relative monocular depth. A metric elevation claim should only be made after DEM/GCP calibration and reference validation. For non-georeferenced imagery, the exported DSM remains explicitly labelled **relative**.

## v1.2.0 SIH readiness pass

v1.2 makes the two reconstruction modes explicit in the product:

- **Relative Mode:** JPG/PNG or non-CRS imagery; normalized elevation for visual exploration.
- **Georeferenced Mode:** GeoTIFF with CRS; calibration workflow is enabled.
- **Metric Mode:** after DEM/GCP calibration; DSM and validation are reported in metres.

The UI now gates metric exports until calibration and error-map exports until reference validation. Reference validation aligns the reference raster to the prediction grid and reports RMSE, MAE, R², Pearson r, bias and valid-pixel coverage. The benchmark runner is provided for real multi-landscape evaluation only; it does not manufacture accuracy values.


## 1.7.0 Aerial-Depth integration addendum
- Bundled the real training/evaluation protocol and deployment provenance template.
- Added a backend model registry endpoint and UI availability gate.
- No checkpoint, benchmark result, or improvement claim is fabricated.
