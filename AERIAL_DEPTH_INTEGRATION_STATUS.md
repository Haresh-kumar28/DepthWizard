# DepthWizard v1.7.0 — Aerial-Depth Integration Status

Release status: **READY FOR REAL TRAINING / NOT TRAINED**

This release is based on the supplied DepthWizard v1.7.0 workstation package and adds the aerial-domain model training/evaluation integration without fabricating a checkpoint or benchmark.

### What is integrated
- Aerial-Depth training kit bundled under `backend/aerial_depth_training/`.
- Geographic tile-level dataset split and RGB/DSM integrity checks.
- Fine-tuning entry point based on Depth Anything V2.
- Frozen held-out test evaluation.
- Baseline-vs-Aerial benchmark comparison.
- Provenance template and deployment instructions.
- Backend `/api/models` availability registry.
- UI gating so Aerial-Depth cannot be selected until a complete verified local checkpoint is present.
- Deployment requires `config.json`, `model.safetensors`, and `provenance.json` with `status: TRAINED`.

### What is deliberately NOT included
- No trained Aerial-Depth weights.
- No claimed improvement.
- No fabricated accuracy.
- No claim that generic model size implies better aerial performance.

### Scientific acceptance
Only after real training and held-out testing should the checkpoint be marked `TRAINED` and production-enabled.
