# Scientific validation protocol

## Phase A — baseline

Run the exact current generic model with:
- fixed preprocessing
- fixed input resolution
- fixed calibration method
- fixed held-out test
- no test-set tuning

Record the complete configuration.

## Phase B — aerial fine-tuning

Train only on training regions.

Use validation regions for:
- checkpoint selection
- learning-rate decisions
- epoch selection
- preprocessing decisions

Do not inspect test metrics during tuning.

## Phase C — frozen test

After selecting the checkpoint, freeze it.

Evaluate once on the held-out urban test regions.

Report:
RMSE, MAE, R², Pearson R, bias, P95 absolute error, valid coverage, runtime.

## Phase D — end-to-end validation

Run the actual DepthWizard pipeline with the selected checkpoint:

RGB
 -> Aerial-Depth
 -> metric elevation/DSM
 -> independent calibration (if the deployment protocol requires it)
 -> independent validation
 -> error map
 -> 3D terrain
 -> export
 -> reproducibility report

## Acceptance rule

Do not claim "improved accuracy" unless held-out RMSE/MAE (and preferably multiple metrics) actually improve over the frozen baseline.

Do not claim centimeter-level or survey-grade accuracy merely because the training data has 5 cm GSD.

Do not compare predicted DSM against a bare-earth DEM as though they were identical targets.

## Current benchmark context

DepthWizard's previous urban benchmark is a baseline only; its reported urban result was RMSE 35.306 m, MAE 27.494 m, R² 0.014 and Pearson R 0.120. Those numbers demonstrate why the aerial-domain experiment is necessary, but they are not an Aerial-Depth result.
