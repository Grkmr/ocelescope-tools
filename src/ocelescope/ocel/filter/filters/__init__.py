from typing import TypedDict


from .attribute import EventAttributeFilter, ObjectAttributeFilter
from .entity_type import (
    EventTypeFilter,
    ObjectTypeFilter,
)
from .relation_count import E2OCountFilter, O2OCountFilter
from .time_range import TimeFrameFilter


class OCELFilter(TypedDict, total=False):
    object_types: ObjectTypeFilter
    event_type: EventTypeFilter
    time_range: TimeFrameFilter
    o2o_count: list[O2OCountFilter]
    e2o_count: list[E2OCountFilter]
    event_attributes: list[EventAttributeFilter]
    object_attributes: list[ObjectAttributeFilter]


__all__ = [
    "OCELFilter",
    "ObjectTypeFilter",
    "EventTypeFilter",
    "ObjectAttributeFilter",
    "EventAttributeFilter",
    "O2OCountFilter",
    "E2OCountFilter",
    "TimeFrameFilter",
]
