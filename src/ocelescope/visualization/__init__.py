from typing import Annotated, TypeAlias

from pydantic import Field

from ocelescope.visualization.default.graph import Graph
from ocelescope.visualization.util.color import generate_color_map

Visualization: TypeAlias = Annotated[Graph, Field(discriminator="type")]

__all__ = ["Visualization", "Graph", "generate_color_map"]
