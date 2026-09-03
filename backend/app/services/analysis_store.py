"""Small embedded SQLite index for reproducible DepthWizard analysis history."""
import json, sqlite3
from pathlib import Path
from typing import Any

class AnalysisStore:
    def __init__(self, data_dir: Path):
        self.path = Path(data_dir) / "depthwizard.db"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self):
        con=sqlite3.connect(self.path)
        con.row_factory=sqlite3.Row
        return con

    def _init(self):
        with self._connect() as c:
            c.executescript('''
            CREATE TABLE IF NOT EXISTS projects(
              project_id TEXT PRIMARY KEY, name TEXT NOT NULL, created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL, state TEXT, current_calibration_id TEXT,
              current_validation_id TEXT
            );
            CREATE TABLE IF NOT EXISTS reconstruction_runs(
              run_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, created_at TEXT NOT NULL,
              model TEXT, settings_json TEXT, processing_seconds REAL, status TEXT,
              FOREIGN KEY(project_id) REFERENCES projects(project_id)
            );
            CREATE TABLE IF NOT EXISTS calibration_runs(
              run_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, created_at TEXT NOT NULL,
              method TEXT, metrics_json TEXT, reference_file TEXT, status TEXT,
              FOREIGN KEY(project_id) REFERENCES projects(project_id)
            );
            CREATE TABLE IF NOT EXISTS validation_runs(
              run_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, created_at TEXT NOT NULL,
              metrics_json TEXT, reference_file TEXT, calibration_run_id TEXT,
              split_json TEXT, status TEXT,
              FOREIGN KEY(project_id) REFERENCES projects(project_id)
            );
            CREATE TABLE IF NOT EXISTS inspection_points(
              id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT NOT NULL, created_at TEXT NOT NULL,
              point_json TEXT NOT NULL, FOREIGN KEY(project_id) REFERENCES projects(project_id)
            );
            CREATE TABLE IF NOT EXISTS snapshots(
              snapshot_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, created_at TEXT NOT NULL,
              name TEXT NOT NULL, state_json TEXT NOT NULL, FOREIGN KEY(project_id) REFERENCES projects(project_id)
            );
            CREATE TABLE IF NOT EXISTS artifacts(
              id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT NOT NULL, created_at TEXT NOT NULL,
              name TEXT NOT NULL, path TEXT NOT NULL, kind TEXT,
              FOREIGN KEY(project_id) REFERENCES projects(project_id)
            );
            ''')

    def upsert_project(self,p):
        with self._connect() as c:
            c.execute('''INSERT INTO projects(project_id,name,created_at,updated_at,state,current_calibration_id,current_validation_id)
                         VALUES(?,?,?,?,?,?,?) ON CONFLICT(project_id) DO UPDATE SET name=excluded.name,updated_at=excluded.updated_at,state=excluded.state,current_calibration_id=excluded.current_calibration_id,current_validation_id=excluded.current_validation_id''',
                      (p.project_id,p.name,p.created_at.isoformat(),p.updated_at.isoformat(),p.state.value,getattr(p,'current_calibration_id',None),getattr(p,'current_validation_id',None)))

    def add_reconstruction(self, project_id, run_id, created_at, model, settings, seconds, status='completed'):
        with self._connect() as c: c.execute('INSERT OR REPLACE INTO reconstruction_runs VALUES(?,?,?,?,?,?,?)',(run_id,project_id,created_at,model,json.dumps(settings,default=str),seconds,status))

    def add_calibration(self, project_id, record):
        with self._connect() as c: c.execute('INSERT OR REPLACE INTO calibration_runs VALUES(?,?,?,?,?,?,?)',(record['run_id'],project_id,record['created_at'],record.get('method'),json.dumps(record,default=str),record.get('reference_file'),'completed'))

    def add_validation(self, project_id, record):
        with self._connect() as c: c.execute('INSERT OR REPLACE INTO validation_runs VALUES(?,?,?,?,?,?,?,?)',(record['run_id'],project_id,record['created_at'],json.dumps(record,default=str),record.get('reference_file'),record.get('calibration_run_id'),json.dumps(record.get('split') or {},default=str),'completed'))

    def add_inspection(self, project_id, point):
        with self._connect() as c: c.execute('INSERT INTO inspection_points(project_id,created_at,point_json) VALUES(?,?,?)',(project_id,point.get('created_at',''),json.dumps(point,default=str)))

    def add_artifacts(self, project_id, created_at, artifacts):
        with self._connect() as c:
            for name,path in artifacts.items(): c.execute('INSERT INTO artifacts(project_id,created_at,name,path,kind) VALUES(?,?,?,?,?)',(project_id,created_at,name,str(path),'artifact'))

    def delete_run(self, project_id, run_id, kind):
        table={'reconstruction':'reconstruction_runs','calibration':'calibration_runs','validation':'validation_runs'}.get(kind)
        if not table: return False
        with self._connect() as c:
            cur=c.execute(f'DELETE FROM {table} WHERE project_id=? AND run_id=?',(project_id,run_id))
            return cur.rowcount>0

    def add_snapshot(self, project_id, snapshot_id, created_at, name, state):
        with self._connect() as c: c.execute('INSERT INTO snapshots VALUES(?,?,?,?,?)',(snapshot_id,project_id,created_at,name,json.dumps(state,default=str)))

    def list_snapshots(self, project_id):
        with self._connect() as c:
            return [dict(r) for r in c.execute('SELECT snapshot_id,created_at,name FROM snapshots WHERE project_id=? ORDER BY created_at DESC',(project_id,))]

    def delete_project(self, project_id):
        with self._connect() as c:
            for table in ('reconstruction_runs','calibration_runs','validation_runs','inspection_points','snapshots','artifacts'):
                c.execute(f'DELETE FROM {table} WHERE project_id=?',(project_id,))
            c.execute('DELETE FROM projects WHERE project_id=?',(project_id,))

    def summary(self, project_id):
        with self._connect() as c:
            cal=[json.loads(r['metrics_json']) for r in c.execute('SELECT metrics_json FROM calibration_runs WHERE project_id=? ORDER BY created_at DESC',(project_id,))]
            val=[json.loads(r['metrics_json']) for r in c.execute('SELECT metrics_json FROM validation_runs WHERE project_id=? ORDER BY created_at DESC',(project_id,))]
            rec=[dict(r) for r in c.execute('SELECT run_id,created_at,model,settings_json,processing_seconds,status FROM reconstruction_runs WHERE project_id=? ORDER BY created_at DESC',(project_id,))]
            for r in rec:
                r['settings']=json.loads(r.pop('settings_json') or '{}')
            ins=[json.loads(r['point_json']) for r in c.execute('SELECT point_json FROM inspection_points WHERE project_id=? ORDER BY id DESC LIMIT 100',(project_id,))]
            return {'calibration_history':cal,'validation_history':val,'reconstruction_history':rec,'inspection_history':ins}
