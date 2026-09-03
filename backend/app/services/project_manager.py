import os,re,shutil,json,tempfile,datetime,uuid
from pathlib import Path
from fastapi import UploadFile
from app.api.schemas import *
from app.models.project import Project
from app.geospatial.metadata import inspect_image
from app.calibration.metric import calibrate_with_gcps,calibrate_with_arrays,apply_calibration
from app.geospatial.dsm import create_dsm_geotiff,compute_dsm_statistics
from app.evaluation.metrics import calculate_metrics
from app.services.analysis_store import AnalysisStore
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject,calculate_default_transform
ALLOWED_EXTENSIONS={'.jpg','.jpeg','.png','.tif','.tiff'};MAX_UPLOAD_BYTES=500*1024*1024

def sanitize_filename(filename):
    filename=os.path.basename(filename or '').replace('\x00',''); filename=re.sub(r'[<>:"/\\|?*]','_',filename)
    return filename if len(filename)<=200 else Path(filename).stem[:196]+Path(filename).suffix

def _write_preview(a,path):
    from PIL import Image
    v=np.asarray(a,float); m=np.isfinite(v)
    if not m.any(): Image.new('L',(64,64)).save(path); return
    lo,hi=np.percentile(v[m],[2,98]); x=np.clip((v-lo)/(hi-lo+1e-9)*255,0,255).astype(np.uint8); Image.fromarray(x).save(path)

def _slope(z,rx=1,ry=1):
    dy,dx=np.gradient(z,ry,rx); return np.degrees(np.arctan(np.sqrt(dx*dx+dy*dy))).astype(np.float32)

def _write_error_preview(error,path):
    from PIL import Image
    e=np.asarray(error,float); m=np.isfinite(e)
    if not m.any(): Image.new('RGB',(64,64),(120,120,120)).save(path); return
    lim=float(np.percentile(np.abs(e[m]),98)); lim=max(lim,1e-9)
    t=np.clip(e/lim,-1,1)
    # blue = negative, white = zero, red = positive
    r=np.where(t>0,255,255*(1+t)); g=255*(1-np.abs(t)); b=np.where(t<0,255,255*(1-t))
    rgb=np.stack([r,g,b],axis=-1).clip(0,255).astype(np.uint8)
    rgb[~m]=np.array([120,120,120],dtype=np.uint8)
    Image.fromarray(rgb,'RGB').save(path)

class ProjectManager:
    def __init__(self,settings):
        self.settings=settings; self.projects={}; self.workspace_dir=settings.output_dir; self.workspace_dir.mkdir(parents=True,exist_ok=True); self.store=AnalysisStore(settings.data_dir)
        self._load_projects()

    def _project_state_path(self,p): return p.project_dir/'project_state.json'

    def _save_project(self,p):
        data={
            'project_id':p.project_id,'name':p.name,'description':p.description,'state':p.state.value,
            'progress':p.progress,'message':p.message,'error':p.error,
            'created_at':p.created_at.isoformat(),'updated_at':p.updated_at.isoformat(),
            'input_path':str(p.input_path) if p.input_path else None,
            'is_georeferenced':p.is_georeferenced,'calibration_type':p.calibration_type.value,
            'reconstruction_mode':p.reconstruction_mode.value,
            'metadata':p.metadata.model_dump() if p.metadata else None,
            'statistics':p.statistics.model_dump() if p.statistics else None,
            'validation':p.validation.model_dump() if p.validation else None,
            'processing_info':p.processing_info,'calibration_result':p.calibration_result,
            'inference_settings':p.inference_settings,'calibration_fraction':p.calibration_fraction,'calibration_seed':p.calibration_seed,'progress_stage':p.progress_stage,
            'calibration_history':p.calibration_history,'validation_history':p.validation_history,
            'inspection_history':p.inspection_history,'reconstruction_history':p.reconstruction_history,'current_calibration_id':p.current_calibration_id,'current_validation_id':p.current_validation_id,'artifacts':{k:str(v) for k,v in p._artifacts.items() if v.exists()},
        }
        path=self._project_state_path(p); tmp=path.with_suffix('.tmp')
        tmp.write_text(json.dumps(data,indent=2,default=str),encoding='utf-8'); tmp.replace(path); self.store.upsert_project(p)

    def _load_projects(self):
        for state_path in self.workspace_dir.glob('*/project_state.json'):
            try:
                d=json.loads(state_path.read_text(encoding='utf-8')); p=Project(d['name'],self.workspace_dir,d.get('description'));
                # Project() creates a new id/directory; replace with persisted identity.
                shutil.rmtree(p.project_dir,ignore_errors=True); p.project_id=d['project_id']; p.project_dir=state_path.parent; p.project_dir.mkdir(parents=True,exist_ok=True)
                p.state=ProjectState(d.get('state','NEW')); p.progress=float(d.get('progress',0)); p.message=d.get('message',''); p.progress_stage=d.get('progress_stage','Idle'); p.error=d.get('error')
                from datetime import datetime
                p.created_at=datetime.fromisoformat(d['created_at']) if d.get('created_at') else p.created_at; p.updated_at=datetime.fromisoformat(d['updated_at']) if d.get('updated_at') else p.updated_at
                ip=d.get('input_path'); p.input_path=Path(ip) if ip and Path(ip).exists() else None
                p.is_georeferenced=bool(d.get('is_georeferenced')); p.calibration_type=CalibrationType(d.get('calibration_type','none')); p.reconstruction_mode=ReconstructionMode(d.get('reconstruction_mode','relative'))
                if d.get('metadata'): p.metadata=ImageMetadataResponse(**d['metadata'])
                if d.get('statistics'): p.statistics=DSMStatisticsResponse(**d['statistics'])
                if d.get('validation'): p.validation=ValidationMetrics(**d['validation'])
                p.processing_info=d.get('processing_info'); p.calibration_result=d.get('calibration_result'); p.inference_settings=d.get('inference_settings') or {}; p.calibration_fraction=float(d.get('calibration_fraction',0.8)); p.calibration_seed=int(d.get('calibration_seed',42))
                p.calibration_history=d.get('calibration_history') or []; p.validation_history=d.get('validation_history') or []; p.inspection_history=d.get('inspection_history') or []; p.reconstruction_history=d.get('reconstruction_history') or []; p.current_calibration_id=d.get('current_calibration_id'); p.current_validation_id=d.get('current_validation_id')
                for k,v in (d.get('artifacts') or {}).items():
                    path=Path(v)
                    if path.exists(): p.set_artifact_path(k,path)
                self.projects[p.project_id]=p; self.store.upsert_project(p)
                for rec in p.calibration_history: self.store.add_calibration(p.project_id,rec)
                for rec in p.validation_history: self.store.add_validation(p.project_id,rec)
                for rec in p.inspection_history: self.store.add_inspection(p.project_id,rec)
            except Exception:
                continue

    def create_project(self,name,description=None):
        name=(name or '').strip() or 'Untitled project'
        p=Project(name,self.workspace_dir,description); self.projects[p.project_id]=p; self._save_project(p); self.store.upsert_project(p); return p
    def get_project(self,pid): return self.projects.get(pid)
    def list_projects(self):
        return sorted(self.projects.values(), key=lambda x: x.updated_at, reverse=True)
    def rename_project(self,pid,name):
        p=self.get_project(pid)
        if not p: raise ValueError('Project not found')
        name=(name or '').strip()
        if not name: raise ValueError('Project name cannot be empty')
        p.name=name; p.updated_at=__import__('datetime').datetime.now(__import__('datetime').timezone.utc); self._save_project(p); return p
    def reset_project(self,pid):
        p=self.get_project(pid)
        if not p: raise ValueError('Project not found')
        source=p.input_path
        for child in list(p.project_dir.iterdir()):
            if source and child.resolve()==source.resolve(): continue
            if child.name=='project_state.json': continue
            if child.is_dir(): shutil.rmtree(child,ignore_errors=True)
            else: child.unlink(missing_ok=True)
        p.state=ProjectState.UPLOADED if source and source.exists() else ProjectState.NEW
        p.progress=0.0; p.message='Project reset; source imagery preserved' if source and source.exists() else 'Project reset'; p.error=None
        p.statistics=None; p.validation=None; p.processing_info=None; p.calibration_result=None; p.reference_path=None; p.error_map_path=None; p.slope_path=None; p.confidence_path=None
        p.calibration_type=CalibrationType.NONE; p.reconstruction_mode=ReconstructionMode.RELATIVE
        p.calibration_history=[]; p.validation_history=[]; p.inspection_history=[]; p.reconstruction_history=[]; p.inference_settings={}; p.current_calibration_id=None; p.current_validation_id=None
        p._artifacts={}
        if source and source.exists():
            p.metadata=ImageMetadataResponse(**({**inspect_image(source),'filename':source.name,'file_size_bytes':source.stat().st_size}))
            p.is_georeferenced=bool(p.metadata.crs)
        else:
            p.input_path=None; p.metadata=None; p.is_georeferenced=False
        self.store.delete_project(pid); self._save_project(p); return p
    def create_snapshot(self,pid,name=None):
        p=self.get_project(pid)
        if not p: raise ValueError('Project not found')
        sid=f"snap-{uuid.uuid4().hex[:8]}"
        state={
            'project_id':p.project_id,'name':p.name,'state':p.state.value,'progress':p.progress,'message':p.message,
            'is_georeferenced':p.is_georeferenced,'calibration_type':p.calibration_type.value,'reconstruction_mode':p.reconstruction_mode.value,
            'metadata':p.metadata.model_dump() if p.metadata else None,'statistics':p.statistics.model_dump() if p.statistics else None,
            'processing_info':p.processing_info,'inference_settings':p.inference_settings,'calibration_result':p.calibration_result,
            'calibration_history':p.calibration_history,'validation_history':p.validation_history,'reconstruction_history':p.reconstruction_history,
            'inspection_history':p.inspection_history,'current_calibration_id':p.current_calibration_id,'current_validation_id':p.current_validation_id
        }
        path=p.project_dir/f'{sid}.json'; path.write_text(json.dumps(state,indent=2,default=str),encoding='utf-8')
        now=datetime.datetime.now(datetime.timezone.utc).isoformat(); self.store.add_snapshot(pid,sid,now,name or f'Snapshot {len(self.store.list_snapshots(pid))+1:03d}',state); self._save_project(p); return {'snapshot_id':sid,'name':name or f'Snapshot {len(self.store.list_snapshots(pid)) :03d}','created_at':now}
    def list_snapshots(self,pid):
        if not self.get_project(pid): raise ValueError('Project not found')
        return self.store.list_snapshots(pid)

    def delete_run(self,pid,kind,run_id):
        p=self.get_project(pid)
        if not p: raise ValueError('Project not found')
        hist={'reconstruction':p.reconstruction_history,'calibration':p.calibration_history,'validation':p.validation_history}.get(kind)
        if hist is None: raise ValueError('Invalid history type')
        before=len(hist); hist[:]=[x for x in hist if x.get('run_id')!=run_id]
        if len(hist)==before: raise ValueError('Run not found')
        if kind=='calibration' and p.current_calibration_id==run_id:
            p.current_calibration_id=hist[0].get('run_id') if hist else None
            p.calibration_result=hist[0] if hist else None
        if kind=='validation' and p.current_validation_id==run_id:
            p.current_validation_id=hist[0].get('run_id') if hist else None
            p.validation=ValidationMetrics(**hist[0]) if hist and all(k in hist[0] for k in ('mae','rmse','pearson_correlation','r2','bias','std_error','p95_abs_error','max_abs_error','valid_pixel_count','valid_pixel_percentage')) else None
        self.store.delete_run(pid,run_id,kind); self._save_project(p); self.generate_report(pid); return True
    async def upload_image(self,pid,file):
        p=self.get_project(pid)
        if not p: raise ValueError('Project not found')
        name=sanitize_filename(file.filename); ext=Path(name).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS: raise ValueError('Unsupported image format. Use JPG, PNG or GeoTIFF.')
        dest=p.project_dir/name; total=0
        with open(dest,'wb') as f:
            while chunk:=await file.read(1024*1024):
                total+=len(chunk)
                if total>MAX_UPLOAD_BYTES: dest.unlink(missing_ok=True); raise ValueError('File exceeds 500 MB limit')
                f.write(chunk)
        md=inspect_image(dest); p.input_path=dest; p.metadata=ImageMetadataResponse(filename=name,file_size_bytes=total,is_georeferenced=bool(md.get('crs')),**md); p.is_georeferenced=bool(md.get('crs')); p.reconstruction_mode=ReconstructionMode.RELATIVE; p.calibration_type=CalibrationType.NONE; p.validation=None; p.calibration_history=[]; p.validation_history=[]; p.inspection_history=[]; p.reconstruction_history=[]; p.current_calibration_id=None; p.current_validation_id=None; p.inference_settings={}; p.set_state(ProjectState.UPLOADED,0,'Image uploaded and metadata inspected'); self._save_project(p); self.store.upsert_project(p); return {'filename':name,'size_bytes':total,'project_id':pid,'state':p.state,'metadata':p.metadata.model_dump()}
    async def calibrate_project(self,pid,request):
        p=self.get_project(pid)
        if not p or not p.input_path: raise ValueError('Project not ready')
        rel_path=p.project_dir/'relative_height.npy'
        if not rel_path.exists(): raise ValueError('Run reconstruction before calibration')
        rel=np.load(rel_path)
        if request.method==CalibrationType.GCP:
            res=calibrate_with_gcps(rel,[g.model_dump() for g in (request.gcps or [])])
        elif request.method==CalibrationType.DEM:
            raise ValueError('DEM calibration requires POST /projects/{id}/calibrate-dem with a DEM GeoTIFF')
        else: raise ValueError('Calibration method must be DEM or GCP')
        result=self._apply_calibration(p,res,request.method)
        run_id=f"cal-{len(p.calibration_history)+1:03d}"
        record={'run_id':run_id,'method':'gcp','created_at':p.updated_at.isoformat(),'gcps':[g.model_dump() for g in (request.gcps or [])],'split':{'type':'gcp_calibration','validation':'independent_reference'},**res}
        p.calibration_history.insert(0,record); p.current_calibration_id=run_id; self.store.add_calibration(pid,record); self._save_project(p); self.generate_report(pid); self._save_project(p); self.store.upsert_project(p); return result
    async def calibrate_dem(self,pid,dem_file,calibration_fraction=0.8,seed=42):
        p=self.get_project(pid)
        if not p or not p.input_path: raise ValueError('Project not ready')
        if not p.is_georeferenced: raise ValueError('DEM calibration requires a georeferenced input GeoTIFF')
        with tempfile.NamedTemporaryFile(delete=False,suffix=Path(dem_file.filename or '.tif').suffix) as f:
            while chunk:=await dem_file.read(1024*1024): f.write(chunk)
            tmp=f.name
        try:
            rel=np.load(p.project_dir/'relative_height.npy')
            with rasterio.open(p.input_path) as src, rasterio.open(tmp) as dem:
                if not dem.crs: raise ValueError('Reference DEM has no CRS')
                if src.crs!=dem.crs:
                    ref=np.full((src.height,src.width),np.nan,np.float32)
                    reproject(rasterio.band(dem,1),ref,src_transform=dem.transform,src_crs=dem.crs,dst_transform=src.transform,dst_crs=src.crs,resampling=Resampling.bilinear,dst_nodata=np.nan)
                else:
                    ref=np.full((src.height,src.width),np.nan,np.float32)
                    reproject(rasterio.band(dem,1),ref,src_transform=dem.transform,src_crs=dem.crs,dst_transform=src.transform,dst_crs=src.crs,resampling=Resampling.bilinear,dst_nodata=np.nan)
            if ref.shape!=rel.shape:
                raise ValueError('Reference DEM could not be aligned to input image grid')
            valid=np.isfinite(rel)&np.isfinite(ref)&(rel!=-9999)&(ref!=-9999)
            fraction=float(calibration_fraction); seed=int(seed)
            rng=np.random.default_rng(seed); mask=np.zeros(valid.shape,dtype=bool); idx=np.flatnonzero(valid)
            if fraction>=0.999: mask[valid]=True
            else:
                take=rng.choice(idx,size=max(2,int(idx.size*fraction)),replace=False); mask.flat[take]=True
            res=calibrate_with_arrays(np.where(mask,rel,np.nan),np.where(mask,ref,np.nan))
            history_dir=p.project_dir/'calibration_history'; history_dir.mkdir(exist_ok=True)
            run_id=f"cal-{len(p.calibration_history)+1:03d}"
            saved_ref=history_dir/f"{run_id}_reference.tif"; shutil.copy2(tmp,saved_ref)
            p.reference_path=Path(tmp); result=self._apply_calibration(p,res,CalibrationType.DEM); p.reference_path=None
            np.save(history_dir/f'{run_id}_calibration_mask.npy',mask.astype(np.uint8)); p.calibration_fraction=fraction; p.calibration_seed=seed
            record={'run_id':run_id,'method':'dem','created_at':p.updated_at.isoformat(),'reference_file':saved_ref.name,'split':{'type':'random_holdout','calibration_fraction':fraction,'validation_fraction':1-fraction,'seed':seed,'mask_file':f'{run_id}_calibration_mask.npy'},**res}
            p.calibration_history.insert(0,record); p.current_calibration_id=run_id; self.store.add_calibration(pid,record); self._save_project(p); self.generate_report(pid); self._save_project(p); self.store.upsert_project(p); return result
        finally: os.unlink(tmp)
    def _apply_calibration(self,p,res,method):
        rel=np.load(p.project_dir/'relative_height.npy'); metric=apply_calibration(rel,res['scale'],res['offset']); path=p.project_dir/'dsm_metric.tif'
        create_dsm_geotiff(metric,path,reference_path=str(p.input_path) if p.is_georeferenced else None)
        p.calibration_type=method; p.reconstruction_mode=ReconstructionMode.METRIC; p.calibration_result=res
        # Regenerate the terrain from the calibrated metric surface so the 3D
        # viewer and the exported DSM are always the same elevation product.
        from app.visualization.mesh import generate_terrain_mesh, export_glb
        rgb = None
        try:
            from app.geospatial.metadata import read_rgb
            rgb = read_rgb(p.input_path)
        except Exception:
            rgb = None
        md=p.metadata.model_dump() if p.metadata else {}; rx,ry=(md.get('resolution') or (1,1))
        slope=_slope(metric,abs(rx) or 1,abs(ry) or 1)
        stats=compute_dsm_statistics(metric); stats.update({'is_metric':True,'unit':'meters','slope_min':float(np.nanmin(slope)),'slope_max':float(np.nanmax(slope)),'slope_mean':float(np.nanmean(slope))})
        p.statistics=DSMStatisticsResponse(**stats)
        p.set_artifact_path('dsm',path); p.set_artifact_path('metric_dsm',path)
        np.save(p.project_dir/'metric_elevation.npy',metric); np.save(p.project_dir/'slope.npy',slope)
        _write_preview(metric,p.project_dir/'dsm_preview.png'); _write_preview(slope,p.project_dir/'slope_preview.png')
        p.set_artifact_path('dsm_preview',p.project_dir/'dsm_preview.png'); p.set_artifact_path('slope',p.project_dir/'slope_preview.png')
        mesh=generate_terrain_mesh(metric,self.settings.render_max_resolution,x_scale=abs(rx) or 1.0,y_scale=abs(ry) or 1.0)
        export_glb(mesh,p.project_dir/'terrain.glb',rgb); p.set_artifact_path('mesh',p.project_dir/'terrain.glb')
        self.generate_report(p.project_id); p.set_state(ProjectState.READY,1,'Metric calibration applied; metric DSM and terrain regenerated'); return CalibrationResult(method=method,**res)
    async def validate_project(self,pid,reference_file,request=None):
        p=self.get_project(pid)
        if not p: raise ValueError('Project not found')
        suffix=Path(reference_file.filename or '.tif').suffix
        with tempfile.NamedTemporaryFile(delete=False,suffix=suffix) as f:
            while chunk:=await reference_file.read(1024*1024): f.write(chunk)
            tmp=f.name
        try:
            pred_path=p.get_artifact_path('dsm');
            if not pred_path: raise ValueError('DSM is not available')
            if p.is_georeferenced and p.reconstruction_mode != ReconstructionMode.METRIC:
                raise ValueError('Metric validation requires DEM or GCP calibration first')
            with rasterio.open(pred_path) as a, rasterio.open(tmp) as r:
                pred=a.read(1); ref=np.full((a.height,a.width),np.nan,np.float32)
                if a.crs and r.crs:
                    reproject(rasterio.band(r,1),ref,src_transform=r.transform,src_crs=r.crs,dst_transform=a.transform,dst_crs=a.crs,resampling=Resampling.bilinear,dst_nodata=np.nan)
                elif a.shape==(r.height,r.width): ref=r.read(1)
                else: raise ValueError('Reference must have CRS information or identical dimensions')
            use_holdout=True if request is None else bool(request.use_holdout); mask_path=None
            if use_holdout and p.calibration_history:
                latest=p.calibration_history[0]; split=latest.get('split') or {}; mf=split.get('mask_file')
                if mf:
                    candidate=p.project_dir/'calibration_history'/mf
                    if candidate.exists(): mask_path=candidate
            if mask_path:
                calmask=np.load(mask_path).astype(bool); ref=np.where(~calmask,ref,np.nan)
            m=calculate_metrics(pred,ref); p.validation=ValidationMetrics(**m); np.save(p.project_dir/'error_map.npy',np.where(np.isfinite(pred)&np.isfinite(ref),pred-ref,np.nan).astype(np.float32)); _write_error_preview(pred-ref,p.project_dir/'error_map.png'); p.set_artifact_path('error_map',p.project_dir/'error_map.png'); p.set_artifact_path('error_map_npy',p.project_dir/'error_map.npy')
            history_dir=p.project_dir/'validation_history'; history_dir.mkdir(exist_ok=True)
            run_id=f"val-{len(p.validation_history)+1:03d}"
            saved_ref=history_dir/f"{run_id}_reference.tif"; shutil.copy2(tmp,saved_ref)
            p.state=ProjectState.VALIDATED
            record={'run_id':run_id,'created_at':p.updated_at.isoformat(),'reference_file':saved_ref.name,'calibration_run_id':p.current_calibration_id,'split':{'type':'independent_holdout','use_holdout':bool(mask_path),'reference_type':getattr(request,'reference_type','DEM') if request else 'DEM'},**m}
            p.validation_history.insert(0,record); p.current_validation_id=run_id; self.store.add_validation(pid,record); self.generate_report(pid); self._save_project(p); self.store.upsert_project(p); return p.validation
        finally: os.unlink(tmp)
    def inspect_pixel(self,pid,pixel_x,pixel_y):
        p=self.get_project(pid); path=p.get_artifact_path('dsm') if p else None
        if not path or not path.exists(): raise ValueError('DSM not available')
        with rasterio.open(path) as src:
            col=int(round(float(pixel_x))); row=int(round(float(pixel_y)))
            if not (0<=row<src.height and 0<=col<src.width):
                raise ValueError(f'Point is outside raster: pixel ({col}, {row}) for {src.width} × {src.height}')
            arr=src.read(1)
            z=float(arr[row,col])
            if not np.isfinite(z) or z==-9999: raise ValueError('Selected point is NoData')
            rel_path=p.project_dir/'relative_height.npy'
            rz=float(np.load(rel_path)[row,col]) if rel_path.exists() else None
            slope=_slope(arr,abs(src.res[0]) or 1,abs(src.res[1]) or 1)
            if p.is_georeferenced:
                wx,wy=src.xy(row,col)
                result={'x':float(wx),'y':float(wy),'pixel_x':col,'pixel_y':row,'elevation':z,'relative_height':rz,'slope':float(slope[row,col]),'unit':'m'}
                point={'created_at':p.updated_at.isoformat(),**result}; p.inspection_history.insert(0,point); p.inspection_history=p.inspection_history[:100]; self.store.add_inspection(pid,point); self._save_project(p); return result
            result={'x':float(col),'y':float(row),'pixel_x':col,'pixel_y':row,'elevation':z,'relative_height':rz,'slope':float(slope[row,col]),'unit':'relative'}
            point={'created_at':p.updated_at.isoformat(),**result}; p.inspection_history.insert(0,point); p.inspection_history=p.inspection_history[:100]; self.store.add_inspection(pid,point); self._save_project(p); return result

    def inspect_point(self,pid,x,y):
        p=self.get_project(pid); path=p.get_artifact_path('dsm') if p else None
        if not path or not path.exists(): raise ValueError('DSM not available')
        with rasterio.open(path) as src:
            md=p.metadata.model_dump() if p.metadata else {}
            rx,ry=(md.get('resolution') or (1.0,1.0))
            if p.is_georeferenced:
                col=int(round(float(x)/(abs(rx) or 1.0)))
                row=int(round(float(-y)/(abs(ry) or 1.0)))
            else:
                col=int(round(float(x))); row=int(round(float(y)))
        return self.inspect_pixel(pid,col,row)

    def generate_report(self,pid):
        p=self.get_project(pid)
        if not p: raise ValueError('Project not found')
        data={'project_id':p.project_id,'project_name':p.name,'input_info':p.metadata.model_dump() if p.metadata else {},'processing_info':p.processing_info or {},'inference_settings':p.inference_settings,'calibration_info':p.calibration_result,'dsm_statistics':p.statistics.model_dump() if p.statistics else None,'validation_metrics':p.validation.model_dump() if p.validation else None,'reconstruction_mode':p.reconstruction_mode.value,'artifacts':p.list_artifacts(),'limitations':['Monocular depth is scale-ambiguous until DEM/GCP calibration.','Metric validation requires a spatially aligned reference DSM/DEM and valid calibration.','Accuracy depends on imagery domain, GSD, viewing geometry and reference quality.'],'generated_at':p.updated_at.isoformat(),'calibration_history':p.calibration_history,'validation_history':p.validation_history,'inspection_history':p.inspection_history,'reconstruction_history':p.reconstruction_history,'current_calibration_id':p.current_calibration_id,'current_validation_id':p.current_validation_id}
        path=p.project_dir/'report.json'; p.set_artifact_path('report',path); path.write_text(json.dumps(data,indent=2,default=str),encoding='utf-8')
        html=p.project_dir/'report.html'; p.set_artifact_path('report_html',html)
        v=data.get('validation_metrics') or {}; c=data.get('calibration_info') or {}; st=data.get('dsm_statistics') or {}
        cards=''.join(f'<div class="card"><small>{k}</small><strong>{val}</strong></div>' for k,val in st.items() if k in ['min_elevation','max_elevation','mean_elevation','elevation_range','unit','is_metric'])
        html.write_text('<!doctype html><html><head><meta charset="utf-8"><title>DepthWizard Report</title><style>body{font-family:Arial;background:#071019;color:#dbe8ef;max-width:1100px;margin:40px auto;padding:0 24px}section{border:1px solid #20323e;border-radius:12px;padding:18px;margin:14px 0}h1{color:#72d6ff}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.card{background:#0c1922;padding:12px;border-radius:8px}small{color:#8197a7}strong{display:block;margin-top:5px}</style></head><body><h1>DepthWizard Analysis Report</h1><p>'+data['project_name']+' · '+data['project_id']+' · mode='+data['reconstruction_mode']+'</p><section><h2>Input & CRS</h2><pre>'+json.dumps(data['input_info'],indent=2,default=str)+'</pre></section><section><h2>DSM</h2><div class="grid">'+cards+'</div></section><section><h2>Calibration</h2><pre>'+json.dumps(c,indent=2,default=str)+'</pre></section><section><h2>Validation</h2><pre>'+json.dumps(v,indent=2,default=str)+'</pre></section><section><h2>Artifacts</h2><p>'+', '.join(data['artifacts'])+'</p></section></body></html>',encoding='utf-8')
        self._save_project(p); return ReportResponse(**data)
    def delete_project(self,pid):
        p=self.projects.pop(pid,None)
        if not p:return False
        shutil.rmtree(p.project_dir,ignore_errors=True);return True
