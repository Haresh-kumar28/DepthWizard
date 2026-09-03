from pathlib import Path
import ast
root=Path(__file__).resolve().parents[1]
required=['backend/app/main.py','backend/app/pipeline/processor.py','backend/app/calibration/metric.py','backend/app/geospatial/dsm.py','backend/app/evaluation/metrics.py','backend/app/visualization/mesh.py','frontend/src/App.tsx','frontend/src/components/ViewerPanel.tsx','docs/FEATURE_MATRIX.md','docs/BENCHMARK.md','docker-compose.yml']
missing=[x for x in required if not (root/x).exists()]
pyfiles=list((root/'backend').rglob('*.py'))
errors=[]
for p in pyfiles:
 try: ast.parse(p.read_text(encoding='utf-8'))
 except Exception as e: errors.append(f'{p}: {e}')
print('Required files:', 'OK' if not missing else missing)
print('Python syntax:', 'OK' if not errors else errors)
raise SystemExit(1 if missing or errors else 0)
