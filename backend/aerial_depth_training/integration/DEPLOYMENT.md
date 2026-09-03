# Deploy the real checkpoint into DepthWizard

After and ONLY after a real training run succeeds:

1. Copy the trained model directory to:

`D:\DEPTHWIZARD\backend\models\aerial-depth`

2. Keep the complete processor/config files with the checkpoint.

3. Calculate SHA-256 for the checkpoint/config package and store it in provenance.

4. Update DepthWizard's model registry so `aerial-depth` is enabled only when the directory is complete.

5. The UI should display:
   - Aerial-Depth
   - training dataset
   - training/validation/test regions
   - checkpoint version/hash
   - validation metrics
   - held-out test metrics
   - baseline comparison

6. If the checkpoint is missing or provenance is incomplete, the UI must show:
   `Aerial-Depth — Not trained / not benchmarked`
   rather than implying accuracy.

## Existing backend compatibility

The current DepthWizard estimator already has an `aerial-depth` concept that expects a local checkpoint under `models/aerial-depth`. This kit supplies the real training/validation side needed to populate that directory.
