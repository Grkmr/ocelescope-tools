from abc import ABC
from typing import (
    Annotated,
    Callable,
    Optional,
    get_args,
    get_origin,
    get_type_hints,
)

from pydantic import BaseModel

from ocelescope.ocel.ocel import OCEL
from ocelescope.resource.resource import Resource


# region Plugin Metadata
class PluginMeta(BaseModel):
    name: str
    version: str
    label: str
    description: Optional[str]


def plugin_meta(
    name: Optional[str] = None,
    version: str = "1.0",
    label: Optional[str] = None,
    description: Optional[str] = None,
):
    def decorator(cls):
        cls.__meta__ = PluginMeta(
            name=name or cls.__name__,
            version=version,
            label=label or cls.__name__,
            description=description,
        )
        return cls

    return decorator


# endregion


# region Plugin Method
class Annotation(BaseModel):
    label: str
    description: Optional[str] = None


class OCELAnnotation(Annotation):
    extension_label: Optional[str] = None


class ResourceAnnotation(Annotation):
    pass


class PluginMethodInput(ABC, BaseModel):
    pass


class PluginMethod(BaseModel):
    name: str
    label: Optional[str] = None
    description: Optional[str] = None
    input_schema: Optional[type[PluginMethodInput]] = None
    input_ocels: dict[str, OCELAnnotation]
    input_resources: dict[str, tuple[str, ResourceAnnotation]]
    _method: Callable


def plugin_method(
    label: Optional[str] = None,
    description: Optional[str] = None,
):
    def decorator(func):
        method_hints = get_type_hints(func, include_extras=True)

        input_schema: Optional[type[PluginMethodInput]] = None
        input_ocels: dict[str, OCELAnnotation] = {}
        input_resources: dict[str, tuple[str, ResourceAnnotation]] = {}

        for arg_name, hint in method_hints.items():
            origin = get_origin(hint)
            arg_annotation: Annotation = Annotation(label=arg_name)

            if origin is Annotated:
                base_type, *annotations = get_args(hint)
                arg_annotation = next(
                    (
                        annotation
                        for annotation in annotations
                        if isinstance(annotation, Annotation)
                    ),
                    arg_annotation,
                )

            else:
                base_type = hint

            if not isinstance(base_type, type) or arg_name == "return":
                continue

            print(base_type, issubclass(base_type, Resource))
            if issubclass(base_type, PluginMethodInput):
                input_schema = base_type
            elif issubclass(base_type, OCEL):
                input_ocels[arg_name] = OCELAnnotation(**arg_annotation.model_dump())
            elif issubclass(base_type, Resource):
                field_info = base_type.model_fields.get("type")

                if field_info is None or field_info.default is None:
                    raise ValueError(
                        f"{base_type.__name__} must define `type: Literal[...] = ...` with a default value."
                    )

                type_value: str = field_info.default

                input_resources[arg_name] = (
                    type_value,
                    ResourceAnnotation(**arg_annotation.model_dump()),
                )
            else:
                raise TypeError(
                    f"Argument {arg_name} must be either an OCEL, Resource or Input Schema"
                )

        setattr(
            func,
            "__meta__",
            PluginMethod(
                name=func.__name__,
                label=label or func.__name__,
                description=description,
                input_schema=input_schema,
                input_ocels=input_ocels,
                input_resources=input_resources,
                _method=func,
            ),
        )

        return func

    return decorator


# endregion
