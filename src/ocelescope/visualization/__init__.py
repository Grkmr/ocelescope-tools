from typing import Annotated, Union

from pydantic import Field

from .default.Graph import Graph

Visualization = Annotated[Union[Graph], Field(discriminator="type")]

__all__ = ["Visualization", "Graph"]
