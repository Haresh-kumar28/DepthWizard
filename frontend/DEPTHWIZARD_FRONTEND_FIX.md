# DepthWizard Frontend — Stability + Usability Fix

This version fixes the 3D viewer and improves the working interface while preserving the existing backend/API contract.

## Critical 3D fix
The backend terrain mesh is exported as vertices `[image_x, image_y, elevation]`. The previous viewer rotated the whole GLB and then exaggerated the wrong local axis, which could make the terrain appear edge-on, extremely elongated, or disappear from the usable camera range.

The new viewer transforms the vertex coordinates explicitly to Three.js Y-up terrain coordinates:

`[x, y_image, elevation] -> [x, elevation, -y_image]`

It then applies controlled vertical relief, centers the model, keeps the lowest point on the grid, and dynamically fits the camera.

## Viewer improvements
- Reliable GLB loading using `GLTFLoader.loadAsync`.
- Explicit mesh orientation conversion instead of a blanket scene rotation.
- Dynamic camera framing and clipping planes.
- Isometric, top and front camera presets.
- Orbit and Fly modes.
- RGB, Relief and Wireframe surface modes.
- Working vertical-relief control.
- Fullscreen and control visibility.
- Loading and mesh-error states with retry.
- Improved lighting, shadows, fog and grid.
- Correct restoration of the RGB texture after switching visual modes.

## Interface improvements
- Larger, more readable typography and controls.
- More balanced three-column workspace.
- Clearer project/input/reconstruction/export hierarchy.
- Drag-and-drop source image upload.
- Project ID persistence across browser refreshes using localStorage.
- Safer polling cleanup for reconstruction jobs.
- Better error feedback.
- Responsive layout for smaller screens.

## Run

From `D:\DEPTHWIZARD\frontend`:

```cmd
npm install
npm run build
npm run dev
```

Keep the existing backend running on `http://127.0.0.1:8000`.

Do not reinstall the Python environment or model just for this frontend update.
