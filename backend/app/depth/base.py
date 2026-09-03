from abc import ABC,abstractmethod
from dataclasses import dataclass
import numpy as np
@dataclass
class DepthResult:
    depth:np.ndarray; normalized_depth:np.ndarray; inference_time:float; model_name:str; device:str
class DepthEstimator(ABC):
    @abstractmethod
    def predict(self,image:np.ndarray)->DepthResult:...
