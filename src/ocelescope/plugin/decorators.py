from typing import (
    Annotated,
    Callable,
    Literal,
    Optional,
    TypeAlias,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from pydantic import BaseModel, Field

from ocelescope.ocel.ocel import OCEL
from ocelescope.plugin.input import PluginInput
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


class OCELResult(BaseModel):
    type: Literal["ocel"] = "ocel"
    is_list: bool
    annotation: Optional[OCELAnnotation]


class ResourceResult(BaseModel):
    type: Literal["resource"] = "resource"
    resource_type: str
    is_list: bool
    annotation: Optional[ResourceAnnotation]


PluginResult: TypeAlias = Annotated[Union[OCELResult, ResourceResult], Field(discriminator="type")]


class PluginMethod(BaseModel):
    name: str
    label: Optional[str] = None
    description: Optional[str] = None
    input_schema: Optional[type[PluginInput]] = None
    input_ocels: dict[str, OCELAnnotation]
    input_resources: dict[str, tuple[str, ResourceAnnotation]]
    resource_types: set[type[Resource]]
    results: list[PluginResult]
    _method: Callable


def extract_info(typ) -> tuple[type, Optional[Annotation]]:
    if get_origin(typ) is Annotated:
        base_type, *annotations = get_args(typ)
        annotation = next((a for a in annotations if isinstance(a, Annotation)), None)
    else:
        base_type = typ
        annotation = None
    return base_type, annotation


def plugin_method(
    label: Optional[str] = None,
    description: Optional[str] = None,
):
    def decorator(func):
        method_hints = get_type_hints(func, include_extras=True)

        resource_types: set[type[Resource]] = set()
        input_schema: Optional[type[PluginInput]] = None
        input_ocels: dict[str, OCELAnnotation] = {}
        input_resources: dict[str, tuple[str, ResourceAnnotation]] = {}

        for arg_name, hint in method_hints.items():
            base_type, annotation = extract_info(hint)

            if not isinstance(base_type, type) or arg_name == "return":
                continue

            if issubclass(base_type, PluginInput):
                input_schema = base_type
            elif issubclass(base_type, OCEL):
                input_ocels[arg_name] = (
                    OCELAnnotation(**annotation.model_dump())
                    if annotation is not None
                    else OCELAnnotation(label=arg_name)
                )
            elif issubclass(base_type, Resource):
                resource_types.add(base_type)
                field_info = base_type.model_fields.get("type")

                if field_info is None or field_info.default is None:
                    raise ValueError(
                        f"{base_type.__name__} must define `type: Literal[...] = ...` with a default value."
                    )

                type_value: str = field_info.default

                input_resources[arg_name] = (
                    type_value,
                    ResourceAnnotation(**annotation.model_dump())
                    if annotation is not None
                    else ResourceAnnotation(label=arg_name),
                )
            else:
                raise TypeError(
                    f"Argument {arg_name} must be either an OCEL, Resource or Input Schema"
                )

        results: list[PluginResult] = []

        return_type = method_hints.get("return", None)

        if return_type is not None:
            origin = get_origin(return_type)

            types_to_parse = []

            if origin is tuple:
                types_to_parse = get_args(return_type)
            else:
                types_to_parse = [return_type]

            for typ in types_to_parse:
                base_type, annotation = extract_info(typ)

                if get_origin(base_type) is list:
                    inner_type = get_args(base_type)[0]
                    base_type, annotation = extract_info(inner_type)
                    is_list = True
                else:
                    is_list = False

                # Now determine what kind of result it is
                if issubclass(base_type, OCEL):
                    results.append(
                        OCELResult(
                            type="ocel",
                            is_list=is_list,
                            annotation=OCELAnnotation(**annotation.model_dump())
                            if annotation is not None
                            else None,
                        )
                    )
                elif issubclass(base_type, Resource):
                    resource_types.add(base_type)
                    resource_type = base_type.model_fields.get("type")
                    if resource_type is None or resource_type.default is None:
                        raise ValueError(
                            f"Resource {base_type.__name__} must define a default `type` field."
                        )
                    results.append(
                        ResourceResult(
                            type="resource",
                            is_list=is_list,
                            annotation=ResourceAnnotation(**annotation.model_dump())
                            if annotation is not None
                            else None,
                            resource_type=resource_type.default,
                        )
                    )
                else:
                    raise TypeError(f"Unsupported return type: {base_type}")

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
                resource_types=resource_types,
                results=results,
                _method=func,
            ),
        )

        return func

    return decorator


# endregion
