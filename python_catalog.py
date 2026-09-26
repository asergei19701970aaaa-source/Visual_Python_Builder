from __future__ import annotations

"""Adapter for the native Python NodeFlow library.

Only real, callable data/property nodes are registered here. Event and GUI
families remain represented by the editor's native components until their
specialised Qt/event generators are selected. Ports always follow the current
four-side model: method left, event right, data top, property bottom.
"""
from typing import Any


def _property_kind(port) -> str:
    if port.choices:
        return "enum"
    return {
        "number": "real", "bool": "bool", "color": "color",
        "font": "font", "code": "code", "list": "multiline",
        "dict": "multiline", "text": "multiline" if port.multiline else "str",
        "file": "str",
    }.get(port.type, "str")


def _bounds(port):
    lo = int(port.minimum) if port.minimum is not None else None
    hi = int(port.maximum) if port.maximum is not None else None
    return lo, hi


def load_python_components(PortSpec, PropertySpec, ComponentSpec):
    from python_library.loader import discover
    specs, errors = discover()
    result = {}
    excluded_prefixes = (
        "Gui.", "GuiQt.", "Layout.", "Window.", "Export.",
        "Container.", "Runtime.", "EventCore.", "Game.",
    )
    structural_types = {"widget", "layout", "window", "menu", "action", "binding", "actions", "events"}
    for key, spec in specs.items():
        if key.startswith(excluded_prefixes) or spec.fn is None:
            continue
        visible_inputs = [p for p in spec.inputs if not p.internal and not p.inspector_only]
        visible_outputs = [p for p in spec.outputs if not p.internal]
        if any(p.kind == "method" for p in visible_inputs):
            continue
        if any(p.kind == "event" for p in visible_outputs):
            continue
        if any(p.type in structural_types for p in (*visible_inputs, *visible_outputs)):
            continue
        ports = []
        properties = []
        for p in visible_inputs:
            if p.kind != "data":
                continue
            ports.append(PortSpec(
                p.name, p.label or p.name, "data_in",
                description=p.tooltip, data_type=p.type or "any",
            ))
            lo, hi = _bounds(p)
            default = p.default
            properties.append(PropertySpec(
                p.name, p.label or p.name, _property_kind(p), default,
                lo, hi, tuple(str(v) for v in (p.choices or ())), p.tooltip,
            ))
        for p in visible_outputs:
            if p.kind == "property":
                ports.append(PortSpec(
                    p.name, p.label or p.name, "data_out",
                    description=p.tooltip, data_type=p.type or "any",
                ))
        category = str(spec.category)
        category = category.split('. ', 1)[-1]
        type_name = f"Python::{key}"
        result[type_name] = ComponentSpec(
            type_name, spec.title, f"Python · {category}", spec.color or "#E5F2FC",
            ports=tuple(ports), properties=tuple(properties),
            description=(spec.description or spec.doc or "Нативная Python-нода."),
            source="python", implemented=True, visual=False,
            subgroup="", support_status="работает",
        )
    return result, errors
