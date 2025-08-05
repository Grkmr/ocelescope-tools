from typing import Literal, Optional

from pydantic import BaseModel

from ocelescope import Graph


from ..resource import Resource


class Place(BaseModel):
    id: str
    object_type: str
    place_type: Optional[Literal["sink", "source", None]]


class Transition(BaseModel):
    id: str
    label: Optional[str]


class Arc(BaseModel):
    source: str
    target: str
    variable: bool = False


class PetriNet(Resource):
    places: list[Place]
    transitions: list[Transition]
    arcs: list[Arc]
    type: str = "ocpn"

    def vizualize(self):
        return Graph(edges=[], nodes=[], type="graph")
