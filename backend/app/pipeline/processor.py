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
    lo,hi=np.percentile(v[m],[2,98]) if m.any() else (0,1);x=np.clip((v-lo)/(hi-lo+1e-9)*255,0,255).astype(np.uint8);Image.fromarray(x).save(path)

def _slope(z,rx=1,ry=1):
    dy,dx=np.gradient(z,ry,rx);return np.degrees(np.arctan(np.sqrt(dx*dx+dy*dy)))

class PipelineProcessor:
    def __init__(self,settings):self.settings=settings;self.estimator=DepthAnythingV2Estimator(settings.depth_model_name,settings.device,str(settings.models_dir))
    async def run(self,project_id,project_manager,job):
        project=project_manager.get_project(project_id)
        if not project or not project.input_path:raise ValueError("No input image uploaded")
        start=time.perf_counter()
        try:
            project.set_state(ProjectState.PREPROCESSING,.1,"Reading image and metadata...");job.progress=.1;job.message=project.message
            md=inspect_image(project.input_path);project.metadata=ImageMetadataResponse(filename=project.input_path.name,file_size_bytes=project.input_path.stat().st_size,**md);project.is_georeferenced=bool(md.get("crs"))
            rgb=read_rgb(project.input_path);project.set_state(ProjectState.DEPTH_ESTIMATION,.3,"Running Depth Anything V2...");job.progress=.3;job.message=project.message
            result=self.estimator.predict(rgb);project.set_state(ProjectState.CALIBRATING,.55,"Building relative surface height...");job.progress=.55;job.message=project.message
            rel=compute_relative_height(result.normalized_depth)
            out=project.project_dir;np.save(out/"relative_depth.npy",result.depth);np.save(out/"relative_height.npy",rel);_preview(result.normalized_depth,out/"depth_preview.png");_preview(rel,out/"relative_height_preview.png");_preview(rel,out/"dsm_preview.png")
            # Scientific raster: for non-georeferenced input use a clearly labelled local raster; georeferenced input preserves CRS.
            project.set_state(ProjectState.DSM_GENERATION,.7,"Writing DSM and statistics...");job.progress=.7;job.message=project.message
            dsm_path=out/"dsm.tif";create_dsm_geotiff(rel,dsm_path,reference_path=str(project.input_path) if project.is_georeferenced else None)
            stats=compute_dsm_statistics(rel);slope=_slope(rel,*(md.get("resolution") or (1,1)));stats.update({"is_metric":False,"unit":"relative","slope_min":float(np.nanmin(slope)),"slope_max":float(np.nanmax(slope)),"slope_mean":float(np.nanmean(slope))});project.statistics=DSMStatisticsResponse(**stats)
            project.set_state(ProjectState.MESH_GENERATION,.9,"Generating 3D terrain mesh...");job.progress=.9;job.message=project.message
            mesh=generate_terrain_mesh(rel,self.settings.render_max_resolution);export_glb(mesh,out/"terrain.glb",rgb)
            project.set_artifact_path("depth_preview",out/"depth_preview.png");project.set_artifact_path("dsm_preview",out/"dsm_preview.png");project.set_artifact_path("depth",out/"depth_preview.png");project.set_artifact_path("relative_depth_npy",out/"relative_depth.npy");project.set_artifact_path("relative_height",out/"relative_height.npy");project.set_artifact_path("dsm",dsm_path);project.set_artifact_path("mesh",out/"terrain.glb");project.set_artifact_path("rgb",project.input_path)
            project.set_artifact_path("report",out/"report.json")
            elapsed=time.perf_counter()-start;project.processing_info=ProcessingInfo(input_dimensions=(md["height"],md["width"]),model_dimensions=(rgb.shape[0],rgb.shape[1]),output_dimensions=rel.shape,processing_time_seconds=elapsed,model_name=result.model_name,device=result.device,hardware="CUDA" if result.device=="cuda" else "CPU").model_dump()
            (out/"statistics.json").write_text(json.dumps(project.statistics.model_dump(),indent=2));(out/"report.json").write_text(json.dumps({"project_id":project.project_id,"project_name":project.name,"input_info":project.metadata.model_dump(),"processing_info":project.processing_info,"calibration_info":None,"dsm_statistics":project.statistics.model_dump(),"validation_metrics":None,"artifacts":project.list_artifacts(),"limitations":["Monocular depth is scale-ambiguous without DEM/GCP calibration.","Accuracy depends on image domain, resolution, viewing geometry and reference quality."],"generated_at":project.updated_at.isoformat()},indent=2,default=str));project.set_artifact_path("report",out/"report.json");project.set_state(ProjectState.READY,1.0,f"Complete in {elapsed:.1f}s");job.progress=1;job.message=project.message
            return {"elapsed_seconds":elapsed}
        except Exception as e:project.set_error(str(e));raise
