from abc import ABC, abstractmethod
from pydantic import BaseModel

from ocelescope.visualization import Visualization


class Resource(BaseModel, ABC):
    @abstractmethod
    def vizualize(self) -> Visualization:
        pass
