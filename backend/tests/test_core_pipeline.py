import numpy as np
from app.calibration.relative import compute_relative_height
from app.calibration.metric import calibrate_with_arrays,apply_calibration
from app.evaluation.metrics import calculate_metrics
from app.geospatial.dsm import compute_dsm_statistics
from app.visualization.mesh import generate_terrain_mesh

def test_relative_height():
    x=np.array([[0.,.5,1.]],dtype=np.float32)
    np.testing.assert_allclose(compute_relative_height(x),[[1,.5,0]])

def test_calibration():
    h=np.tile(np.linspace(0,1,10),(10,1)); ref=20*h+500
    r=calibrate_with_arrays(h,ref)
    assert abs(r['scale']-20)<1e-5 and abs(r['offset']-500)<1e-5
    np.testing.assert_allclose(apply_calibration(h,r['scale'],r['offset']),ref,atol=1e-4)

def test_metrics():
    a=np.array([[1,2],[3,4]],float);b=a+1
    r=calculate_metrics(a,b);assert r['mae']==1 and r['rmse']==1

def test_stats_mesh():
    z=np.arange(16,dtype=np.float32).reshape(4,4);s=compute_dsm_statistics(z);assert s['max_elevation']==15
    m=generate_terrain_mesh(z,max_resolution=4);assert m.vertex_count==16 and m.face_count==18


def test_mesh_has_terrain_relief():
    z=np.zeros((4,4),dtype=np.float32); z[:,2:]=10
    m=generate_terrain_mesh(z,max_resolution=4)
    assert float(m.vertices[:,1].max()-m.vertices[:,1].min()) == 10.0

def test_metric_calibration_produces_absolute_surface():
    rel=np.tile(np.linspace(0,1,10,dtype=np.float32),(10,1))
    ref=100+25*rel
    r=calibrate_with_arrays(rel,ref)
    assert abs(r['scale']-25)<1e-5
    assert abs(r['offset']-100)<1e-5
