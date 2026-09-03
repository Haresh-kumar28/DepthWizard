# Dataset protocol

## Primary urban dataset: ISPRS Potsdam

The official ISPRS Potsdam dataset contains 38 patches, each with a true orthophoto and DSM. RGB, DSM and georeferencing are supplied on the same grid. The published GSD is 5 cm.

Official source:
https://www.isprs.org/resources/datasets/benchmarks/UrbanSemLab/2d-sem-label-potsdam.aspx

Use the RGB TIFF and DSM TIFF pairs. Do not mix neighboring pixels from the same geographic tile across train and test.

## Recommended split

Do not randomly split pixels.

Example:
- TRAIN: geographically separated Potsdam tiles
- VALIDATION: different Potsdam tiles
- TEST: different Potsdam tiles never used for model selection

For a stronger claim, keep a second city/region completely outside all training and tuning.

## Target semantics

For the primary model, target is absolute DSM elevation in meters.

Do not silently treat a bare-earth DEM as DSM ground truth. If using a DEM:
- label it as DEM
- record the semantic mismatch
- report it in the validation report

## Data integrity checks

Every pair must pass:
- same width/height
- same CRS or explicit reprojection
- same affine transform/grid after alignment
- finite DSM values
- explicit nodata mask
- plausible elevation range
- no accidental RGB/DSM filename pairing errors

The preparation script records these checks.
