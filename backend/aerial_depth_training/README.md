# DepthWizard — Aerial-Depth Training & Scientific Validation Kit

This package implements the missing *scientific* pieces for a real aerial-domain model:

1. Paired aerial RGB + DSM dataset preparation
2. Geographic train/validation/test splitting
3. Fine-tuning of a pretrained Depth Anything V2 model
4. Independent held-out urban evaluation
5. Baseline-vs-Aerial-Depth comparison
6. Provenance and reproducibility records
7. Deployment hand-off into `backend/models/aerial-depth`

## Important scientific rule

This kit does **not** contain a fabricated checkpoint or fabricated benchmark numbers.

`Aerial-Depth` becomes a selectable production model only after a real checkpoint has been trained and its checksum/provenance recorded.

## Recommended first dataset

ISPRS Potsdam is a strong starting urban aerial dataset because it provides aligned true orthophotos and DSMs on the same grid at 5 cm GSD. Use the official ISPRS distribution and terms. See `docs/DATASET.md`.

For stronger cross-domain evidence, add a geographically distinct aerial dataset (for example Vaihingen/Toronto or an institutionally licensed dataset) and keep that region entirely held out from training.

## Expected workflow

DATASET
  -> verify RGB/DSM alignment
  -> geographic split
  -> patch extraction
  -> fine-tune
  -> select checkpoint using validation only
  -> freeze checkpoint
  -> evaluate once on held-out urban test
  -> compare against the exact baseline
  -> end-to-end DepthWizard validation
  -> publish provenance + metrics

## What counts as "demonstrated improvement"

Improvement is recorded only when the held-out test shows it.

The benchmark script reports:
- RMSE
- MAE
- R²
- Pearson R
- bias
- P95 absolute error
- valid coverage
- runtime

It will never turn missing metrics into optimistic placeholders.
