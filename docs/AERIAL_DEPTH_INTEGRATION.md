# Aerial-Depth integration in DepthWizard 1.7.0

DepthWizard now ships the complete, non-fabricated integration surface for an aerial-domain fine-tuned model.

## Current release state

`Aerial-Depth` is **NOT_TRAINED / NOT_BENCHMARKED** in this package. No checkpoint is included and no improvement claim is made.

The reconstruction UI disables Aerial-Depth until a complete local checkpoint and `provenance.json` marked `TRAINED` are present.

## Training assets

See `backend/aerial_depth_training/`:
- `dataset/prepare_dataset.py` — tile-level geographic split and RGB/DSM integrity checks
- `training/train_aerial_depth.py` — fine-tuning entry point
- `evaluation/evaluate_test.py` — frozen held-out test evaluation
- `evaluation/benchmark.py` — baseline vs aerial comparison without fabricated results
- `docs/SCIENTIFIC_PROTOCOL.md` — train/validation/test and acceptance protocol
- `integration/provenance.template.json` — deployment provenance schema

## Deployment gate

Place a real Hugging Face-compatible checkpoint in:
`backend/models/aerial-depth/`

Required files:
- `config.json`
- `model.safetensors`
- `provenance.json`

The provenance file must declare `status: TRAINED` and record dataset/split/checksum/test metrics. Until then the application truthfully reports that Aerial-Depth is unavailable.

## Scientific rule

Do not call the existing USGS bare-earth DEM benchmark a definitive DSM-vs-DSM accuracy result. Preserve the report's DEM/DSM distinction and valid-overlap coverage warnings.

