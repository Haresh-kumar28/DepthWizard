# DepthWizard Pipeline

1. Validate and inspect JPG/PNG/TIFF/GeoTIFF input.
2. Extract RGB and preserve GeoTIFF CRS/transform when available.
3. Run Depth Anything V2 Small locally through Transformers.
4. Convert normalized relative depth into a clearly-labelled relative surface-height raster.
5. Export a relative DSM. No metric elevation is claimed without external calibration.
6. Optional GCP calibration fits `Z = scale * H_relative + offset` and writes a metric DSM for georeferenced input.
7. Compute DSM statistics and terrain slope.
8. Downsample only the rendering copy and create a GLB terrain mesh with RGB texture.
9. View the terrain interactively in Three.js with orbit or flythrough controls.
10. Validate against a reference DSM using MAE, RMSE, correlation, bias and standard error.

## Scientific limitation
Depth Anything V2 is a monocular relative-depth foundation model. It does not, by itself, establish absolute geodetic elevation. DEM/GCP calibration and independent reference validation are required for metric claims.
