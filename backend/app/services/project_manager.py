import os,re,shutil,json
from pathlib import Path
from fastapi import UploadFile
from app.api.schemas import *
from app.models.project import Project
from app.geospatial.metadata import inspect_image
from app.calibration.metric import calibrate_with_gcps,apply_calibration
from app.geospatial.dsm import create_dsm_geotiff,compute_dsm_statistics
from app.evaluation.metrics import calculate_metrics
import numpy as np
ALLOWED_EXTENSIONS={".jpg",".jpeg",".png",".tif",".tiff"};MAX_UPLOAD_BYTES=500*1024*1024
def sanitize_filename(filename):
    filename=os.path.basename(filename).replace("\x00","");filename=re.sub(r'[<>:"/\\|?*]','_',filename)
    if len(filename)>200:
        stem,ext=os.path.splitext(filename);filename=stem[:200-len(ext)]+ext
    return filename
class ProjectManager:
    def __init__(self,settings):self.settings=settings;self.projects={};self.workspace_dir=settings.output_dir;self.workspace_dir.mkdir(parents=True,exist_ok=True)
    def create_project(self,name,description=None):
        p=Project(name,self.workspace_dir,description);self.projects[p.project_id]=p;return p
    def get_project(self,pid):return self.projects.get(pid)
    async def upload_image(self,pid,file):
        p=self.get_project(pid)
        if not p:raise ValueError("Project not found")
        name=sanitize_filename(file.filename or "");ext=Path(name).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:raise ValueError("Unsupported image format")
        dest=p.project_dir/name;total=0
        with open(dest,"wb") as f:
            while chunk:=await file.read(1024*1024):
                total+=len(chunk)
                if total>MAX_UPLOAD_BYTES:dest.unlink(missing_ok=True);raise ValueError("File exceeds 500 MB limit")
                f.write(chunk)
        md=inspect_image(dest);p.input_path=dest;p.metadata=ImageMetadataResponse(filename=name,file_size_bytes=total,**md);p.is_georeferenced=bool(md.get("crs"));p.set_state(ProjectState.UPLOADED,0,"Image uploaded");return {"filename":name,"size_bytes":total,"project_id":pid,"state":p.state,"metadata":p.metadata.model_dump()}
    async def calibrate_project(self,pid,request):
        p=self.get_project(pid)
        if not p:raise ValueError("Project not found")
        if request.method!=CalibrationType.GCP:raise ValueError("Use GCP calibration in this release; DEM-assisted calibration requires a DEM upload")
        arr=np.load(p.project_dir/"relative_height.npy");res=calibrate_with_gcps(arr,[g.model_dump() for g in (request.gcps or [])]);metric=apply_calibration(arr,res["scale"],res["offset"]);path=p.project_dir/"dsm_metric.tif";create_dsm_geotiff(metric,path,reference_path=str(p.input_path) if p.is_georeferenced else None);p.calibration_type=CalibrationType.GCP;p.calibration_result=res;stats=compute_dsm_statistics(metric);stats.update({"is_metric":True,"unit":"meters"});p.statistics=DSMStatisticsResponse(**stats);p.set_artifact_path("dsm",path);return CalibrationResult(method=request.method,**res)
    async def validate_project(self,pid,reference_file):
        p=self.get_project(pid)
        if not p:raise ValueError("Project not found")
        from tempfile import NamedTemporaryFile
        suffix=Path(reference_file.filename or ".tif").suffix
        with NamedTemporaryFile(delete=False,suffix=suffix) as f:
            while chunk:=await reference_file.read(1024*1024):f.write(chunk)
            tmp=f.name
        try:
            import rasterio
            with rasterio.open(p.get_artifact_path("dsm")) as a, rasterio.open(tmp) as r:
                ref=r.read(1,out_shape=(a.height,a.width),resampling=rasterio.enums.Resampling.bilinear)
                pred=a.read(1);m=calculate_metrics(pred,ref)
            p.validation=ValidationMetrics(**m);p.state=ProjectState.VALIDATED;return p.validation
        finally:os.unlink(tmp)
    def generate_report(self,pid):
        p=self.get_project(pid)
        if not p:raise ValueError("Project not found")
        limitations=["Monocular depth is scale-ambiguous without DEM/GCP calibration.","Accuracy depends on image domain, resolution, viewing geometry and reference quality."]
        data={"project_id":p.project_id,"project_name":p.name,"input_info":p.metadata.model_dump() if p.metadata else {},"processing_info":p.processing_info or {},"calibration_info":p.calibration_result,"dsm_statistics":p.statistics.model_dump() if p.statistics else None,"validation_metrics":p.validation.model_dump() if p.validation else None,"artifacts":p.list_artifacts(),"limitations":limitations,"generated_at":p.updated_at.isoformat()}
        path=p.project_dir/"report.json";path.write_text(json.dumps(data,indent=2,default=str));p.set_artifact_path("report",path);return ReportResponse(**data)
    def delete_project(self,pid):
        p=self.projects.pop(pid,None)
        if not p:return False
        shutil.rmtree(p.project_dir,ignore_errors=True);return True
