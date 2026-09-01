# DepthWizard Frontend Stable v4

## Fix included
- TypeScript build error in `ViewerPanel.tsx` fixed by safely handling `Material.wireframe`.
- No backend/model changes.

## Windows run
```cmd
cd /d D:\DEPTHWIZARD\frontend
npm install
npm run build
npm run dev
```

If Vite says port 5173 is already in use, either use the displayed port (for example 5174), or stop the previous Vite process before restarting.

To find/stop the old Vite process:
```cmd
netstat -ano | findstr :5173
taskkill /PID <PID> /F
```
