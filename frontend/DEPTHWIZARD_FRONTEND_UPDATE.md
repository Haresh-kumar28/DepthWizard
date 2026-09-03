# DepthWizard Frontend — Polished 3D Viewer Update

This frontend update focuses on the presentation layer while keeping the existing backend/API contract unchanged.

## Improvements
- Corrects the generated image-plane/DSM orientation for the Three.js viewer.
- Centers and auto-frames the generated GLB terrain.
- Adds controlled vertical relief exaggeration.
- Adds Orbit and Flythrough modes.
- Adds RGB / Relief / Wireframe surface modes.
- Adds reset-view and fullscreen controls.
- Adds stronger terrain lighting, shadows, fog and ground grid.
- Adds loading state for the GLB.
- Reworks the entire shell into a minimal dark enterprise-style interface.
- Improves project creation, upload, pipeline progress, export controls and status presentation.
- Improves right-side DSM preview and elevation/quality metrics.
- Responsive layout is included for narrower screens.

## Install / run on the existing Windows project

From `D:\DEPTHWIZARD\frontend`:

```cmd
npm install
npm run build
npm run dev
```

The backend remains at `http://127.0.0.1:8000` and Vite continues to proxy `/api` to it.

## Important
Do not copy the `node_modules` or old `dist` folder from the previous frontend archive. This update intentionally ships source/configuration files only so Windows installs the correct native npm dependencies.

The backend, model, generated GLB, database and data folders are not included in this frontend-only package.
