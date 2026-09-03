import json,logging,time
from pathlib import Path
import numpy as np
from PIL import Image
from app.api.schemas import ProjectState,DSMStatisticsResponse,ImageMetadataResponse,ProcessingInfo
from app.geospatial.metadata import inspect_image,read_rgb
from app.calibration.relative import compute_relative_height
from app.geospatial.dsm import create_dsm_geotiff,compute_dsm_statistics
from app.visualization.mesh import generate_terrain_mesh,export_glb
from app.depth.estimator import DepthAnythingV2Estimator
logger=logging.getLogger(__name__)

def _preview(a,path):
 v=np.asarray(a,float);m=np.isfinite(v)
 if not m.any(): Image.new('L',(64,64)).save(path);return
 lo,hi=np.percentile(v[m],[2,98]);x=np.clip((v-lo)/(hi-lo+1e-9)*255,0,255).astype(np.uint8);Image.fromarray(x).save(path)
def _slope(z,rx=1,ry=1):
 dy,dx=np.gradient(z,ry,rx);return np.degrees(np.arctan(np.sqrt(dx*dx+dy*dy))).astype(np.float32)
class PipelineProcessor:
 def __init__(self,settings):
  self.settings=settings; self.estimator=None
 def run(self,project_id,project_manager,job):
  project=project_manager.get_project(project_id)
  if not project or not project.input_path: raise ValueError('No input image uploaded')
  start=time.perf_counter()
  try:
   project.set_state(ProjectState.PREPROCESSING,.06,'Reading image, CRS, resolution and NoData metadata...');project.progress_stage='Read imagery';job.progress=.06;job.message=project.message;project_manager._save_project(project)
   md=inspect_image(project.input_path);project.metadata=ImageMetadataResponse(filename=project.input_path.name,file_size_bytes=project.input_path.stat().st_size,is_georeferenced=bool(md.get('crs')),**md);project.is_georeferenced=bool(md.get('crs'));rgb=read_rgb(project.input_path)
   project.set_state(ProjectState.DEPTH_ESTIMATION,.18,'Loading configured depth engine...');project.progress_stage='Load model';job.progress=.18;job.message=project.message;project_manager._save_project(project)
   cfg={**{'model_name':self.settings.depth_model_name,'inference_resolution':768,'tile_size':self.settings.depth_tile_size,'tile_overlap':self.settings.depth_tile_overlap,'edge_refinement':True,'terrain_smoothing':True},**(project.inference_settings or {})}
   self.estimator=DepthAnythingV2Estimator(cfg['model_name'],self.settings.device,str(self.settings.models_dir),cfg['tile_size'],cfg['tile_overlap'],'tiled',cfg['inference_resolution'])
   last_persist=[0.0]
   def _depth_progress(local):
    value=.18 + float(np.clip(local,0,1))*.32
    job.progress=value; job.message=f'Running depth inference · {round(value*100)}%'
    project.progress=value; project.progress_stage='Infer overlapping tiles'; project.message=job.message; project.updated_at=__import__('datetime').datetime.now(__import__('datetime').timezone.utc)
    now=time.perf_counter()
    if value>=.50 or now-last_persist[0]>=1.0:
     project_manager._save_project(project); last_persist[0]=now
   result=self.estimator.predict(rgb, progress_callback=_depth_progress)
   job.progress=.50; job.message='Depth inference complete · refining surface'
   project.progress=.50; project.progress_stage='Blend and refine'; project.message=job.message; project_manager._save_project(project)
   project.inference_settings=cfg
   project.set_state(ProjectState.CALIBRATING,.53,'Normalizing relative surface height...');project.progress_stage='Normalize relative height';job.progress=.53;job.message=project.message
   rel=compute_relative_height(result.normalized_depth).astype(np.float32)
   if cfg.get('edge_refinement') or cfg.get('terrain_smoothing'):
    try:
     import cv2
     if cfg.get('terrain_smoothing'): rel=cv2.bilateralFilter(rel.astype(np.float32),7,0.08,3.0)
     if cfg.get('edge_refinement'):
      blur=cv2.GaussianBlur(rel,(0,0),1.0); rel=np.clip(rel + 0.18*(rel-blur),0,1).astype(np.float32)
    except Exception: pass
   out=project.project_dir
   np.save(out/'relative_depth.npy',result.depth);np.save(out/'relative_height.npy',rel);_preview(result.normalized_depth,out/'depth_preview.png');_preview(rel,out/'relative_height_preview.png');_preview(rel,out/'dsm_preview.png')
   rx,ry=(md.get('resolution') or (1.0,1.0)); project.set_state(ProjectState.DSM_GENERATION,.70,'Writing DSM raster and terrain derivatives...');project.progress_stage='Generate DSM and derivatives';job.progress=.70;job.message=project.message
   dsm_path=out/'dsm.tif';create_dsm_geotiff(rel,dsm_path,reference_path=str(project.input_path) if project.is_georeferenced else None)
   slope=_slope(rel,abs(rx) or 1,abs(ry) or 1);np.save(out/'slope.npy',slope);_preview(slope,out/'slope_preview.png')
   stats=compute_dsm_statistics(rel);stats.update({'is_metric':False,'unit':'relative','slope_min':float(np.nanmin(slope)),'slope_max':float(np.nanmax(slope)),'slope_mean':float(np.nanmean(slope))});project.statistics=DSMStatisticsResponse(**stats)
   project.set_state(ProjectState.MESH_GENERATION,.90,'Generating textured terrain mesh with geospatial scale...');project.progress_stage='Generate terrain mesh';job.progress=.90;job.message=project.message
   gsd_x=abs(rx) if project.is_georeferenced and rx else 1.0;gsd_y=abs(ry) if project.is_georeferenced and ry else 1.0
   mesh=generate_terrain_mesh(rel,self.settings.render_max_resolution,x_scale=gsd_x,y_scale=gsd_y,vertical_scale=1.0);export_glb(mesh,out/'terrain.glb',rgb)
   for k,v in {'depth_preview':out/'depth_preview.png','dsm_preview':out/'dsm_preview.png','depth':out/'depth_preview.png','relative_depth_npy':out/'relative_depth.npy','relative_height':out/'relative_height.npy','dsm':dsm_path,'mesh':out/'terrain.glb','rgb':project.input_path,'slope':out/'slope_preview.png'}.items(): project.set_artifact_path(k,v)
   elapsed=time.perf_counter()-start;project.processing_info=ProcessingInfo(input_dimensions=(md['height'],md['width']),model_dimensions=(rgb.shape[0],rgb.shape[1]),output_dimensions=rel.shape,processing_time_seconds=elapsed,model_name=result.model_name,device=result.device,hardware='CUDA' if result.device=='cuda' else 'CPU', inference_mode='tiled', inference_resolution=int(cfg['inference_resolution']), tile_size=int(cfg['tile_size']), tile_overlap=float(cfg['tile_overlap']), edge_refinement=bool(cfg['edge_refinement']), terrain_smoothing=bool(cfg['terrain_smoothing'])).model_dump()
   rec_id=f"rec-{len(project.reconstruction_history)+1:03d}"; rec={'run_id':rec_id,'created_at':project.updated_at.isoformat(),'model':result.model_name,'settings':cfg,'processing_seconds':elapsed,'status':'completed'}; project.reconstruction_history.insert(0,rec); project_manager.store.add_reconstruction(project.project_id,rec_id,rec['created_at'],result.model_name,cfg,elapsed); project_manager.store.add_artifacts(project.project_id,project.updated_at.isoformat(),{k:v for k,v in project._artifacts.items() if v.exists()})
   project_manager.generate_report(project.project_id);project.set_state(ProjectState.READY,1.0,f'Complete in {elapsed:.1f}s');project.progress_stage='Complete';project_manager._save_project(project);job.progress=1;job.message=project.message;return {'elapsed_seconds':elapsed}
  except Exception as e: project.set_error(str(e));raise
