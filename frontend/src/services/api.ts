import axios from 'axios';
import type {Project,ImageMetadata,DSMStatistics,CalibrationResult,CalibrationType,GCPInput,ValidationMetrics,HistoryResponse,ProcessSettings} from '../types';
const api=axios.create({baseURL:'/api',timeout:300000});
export const projectApi={
 create:async(name:string,description?:string):Promise<Project>=>{const{data}=await api.post('/projects',{name,description});return data},
 list:async():Promise<Project[]>=>{const{data}=await api.get('/projects');return data},
 get:async(id:string):Promise<Project>=>{const{data}=await api.get(`/projects/${id}`);return data},
 getStatus:async(id:string):Promise<Project>=>{const{data}=await api.get(`/projects/${id}/status`);return data},
 upload:async(id:string,file:File)=>{const fd=new FormData();fd.append('file',file);const{data}=await api.post(`/projects/${id}/upload`,fd);return data},
 process:async(id:string,settings?:ProcessSettings)=>{const{data}=await api.post(`/projects/${id}/process`,settings||undefined);return data},
 getMetadata:async(id:string):Promise<ImageMetadata>=>{const{data}=await api.get(`/projects/${id}/metadata`);return data},
 getStatistics:async(id:string):Promise<DSMStatistics>=>{const{data}=await api.get(`/projects/${id}/statistics`);return data},
 listModels:async():Promise<any[]>=>{const{data}=await api.get('/models');return data},
 getHistory:async(id:string):Promise<HistoryResponse>=>{const{data}=await api.get(`/projects/${id}/history`);return data},
 rename:async(id:string,name:string)=>{const{data}=await api.patch(`/projects/${id}`,{name});return data},
 reset:async(id:string)=>{const{data}=await api.post(`/projects/${id}/reset`);return data},
 remove:async(id:string)=>{const{data}=await api.delete(`/projects/${id}`);return data},
 deleteHistory:async(id:string,kind:string,runId:string)=>{const{data}=await api.delete(`/projects/${id}/history/${kind}/${runId}`);return data},
 createSnapshot:async(id:string,name?:string)=>{const{data}=await api.post(`/projects/${id}/snapshots`,null,{params:{name:name||''}});return data},
 listSnapshots:async(id:string)=>{const{data}=await api.get(`/projects/${id}/snapshots`);return data},
 getReport:async(id:string)=>{const{data}=await api.get(`/projects/${id}/report`);return data},
 calibrate:async(id:string,method:CalibrationType,gcps?:GCPInput[],calibration_fraction=0.8,seed=42):Promise<CalibrationResult>=>{const{data}=await api.post(`/projects/${id}/calibrate`,{method,gcps,calibration_fraction,seed});return data},
 calibrateDem:async(id:string,file:File,fraction=0.8,seed=42):Promise<CalibrationResult>=>{const fd=new FormData();fd.append('dem_file',file);const{data}=await api.post(`/projects/${id}/calibrate-dem?calibration_fraction=${fraction}&seed=${seed}`,fd);return data},
 validate:async(id:string,file:File,useHoldout=true,referenceType='DEM'):Promise<ValidationMetrics>=>{const fd=new FormData();fd.append('reference_file',file);const{data}=await api.post(`/projects/${id}/validate?use_holdout=${useHoldout}&reference_type=${encodeURIComponent(referenceType)}`,fd);return data},
 inspectPixel:async(id:string,x:number,y:number)=>{const{data}=await api.get(`/projects/${id}/inspect`,{params:{pixel_x:x,pixel_y:y}});return data},
 getMeshUrl:(id:string)=>`/api/projects/${id}/mesh`,getDepthUrl:(id:string)=>`/api/projects/${id}/depth`,getDsmUrl:(id:string)=>`/api/projects/${id}/dsm`,getErrorMapUrl:(id:string)=>`/api/projects/${id}/error-map`,
 getDownloadUrl:(id:string,a:string)=>`/api/projects/${id}/download/${a}`,
};
export default api;
