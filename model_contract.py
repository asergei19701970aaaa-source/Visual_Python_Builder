"""Единый контракт модели нод, точек и свойств.

Модуль не зависит от Qt. Его можно использовать в редакторе, импортёре,
генераторе и тестах, чтобы все слои одинаково понимали паспорт компонента.
"""
from __future__ import annotations

from copy import deepcopy
import uuid
from typing import Any

from components import COMPONENTS, default_properties, effective_ports

VALID_PORT_KINDS = frozenset({"work_in", "event_out", "data_in", "data_out"})
VALID_PROPERTY_KINDS = frozenset({
    "str", "int", "real", "bool", "choice", "enum", "multiline",
    "code", "color", "font", "table",
})


def port_identifier(name: str, kind: str) -> str:
    """Return a stable, direction-aware identifier for an in-memory port."""
    return f"{kind}:{name}"


def split_port_identifier(value: str) -> tuple[str, str | None]:
    """Read a direction-aware id while keeping legacy names supported."""
    text = str(value)
    if ":" not in text:
        return text, None
    kind, name = text.split(":", 1)
    if kind in VALID_PORT_KINDS and name:
        return name, kind
    return text, None

GEOMETRY_PROPERTIES = frozenset({
    "x", "y", "left", "top", "width", "height", "min_width",
    "min_height", "max_width", "max_height", "minimum_width",
    "minimum_height", "maximum_width", "maximum_height",
})
APPEARANCE_PROPERTIES = frozenset({
    "color", "background_color", "text_color", "border_color",
    "border_width", "border_radius", "font", "font_family",
    "font_size", "font_bold", "font_italic", "font_underline",
    "font_strikeout", "style", "icon", "icon_path", "opacity",
})
VALUE_PROPERTIES = frozenset({
    "minimum", "maximum", "step", "page_step", "value", "default",
    "current_index", "decimals", "precision", "warning", "critical",
})


def property_group_name(property_spec) -> str:
    """Return the stable UI group for a PropertySpec."""
    name = str(property_spec.name).lower()
    if name in GEOMETRY_PROPERTIES:
        return "Положение и размер"
    if name in APPEARANCE_PROPERTIES or any(
        token in name for token in ("color", "font", "style", "icon")
    ):
        return "Внешний вид"
    if name in VALUE_PROPERTIES:
        return "Значения"
    if name in {"name", "title", "tooltip", "tool_tip", "accessible_name",
                "accessible_description", "enabled", "visible"}:
        return "Основные"
    return "Настройки"


def validate_component_catalog() -> list[str]:
    """Return human-readable catalog errors without importing Qt."""
    errors: list[str] = []
    for key, spec in COMPONENTS.items():
        if key != spec.type_name:
            errors.append(f"{key}: ключ не совпадает с type_name={spec.type_name}")
        if not spec.caption.strip():
            errors.append(f"{key}: пустая подпись компонента")
        port_keys: set[tuple[str, str]] = set()
        for port in spec.ports:
            port_key = (port.name, port.kind)
            if port_key in port_keys:
                errors.append(
                    f"{key}: повторная точка {port.name} ({port.kind})"
                )
            port_keys.add(port_key)
            if port.kind not in VALID_PORT_KINDS:
                errors.append(f"{key}.{port.name}: неизвестный kind {port.kind}")
            if not port.caption.strip():
                errors.append(f"{key}.{port.name}: пустая подпись")
        property_defs: dict[str, tuple[Any, ...]] = {}
        for prop in spec.properties:
            signature = (
                prop.kind, repr(prop.default), prop.minimum, prop.maximum,
                tuple(prop.options),
            )
            previous = property_defs.get(prop.name)
            if previous is not None and previous != signature:
                errors.append(f"{key}: конфликтующее свойство {prop.name}")
            property_defs[prop.name] = signature
            if prop.kind not in VALID_PROPERTY_KINDS:
                errors.append(f"{key}.{prop.name}: неизвестный kind {prop.kind}")
            if prop.kind in {"choice", "enum"} and not prop.options:
                errors.append(f"{key}.{prop.name}: у выбора нет options")
            if prop.minimum is not None and prop.maximum is not None:
                if prop.minimum > prop.maximum:
                    errors.append(f"{key}.{prop.name}: minimum больше maximum")
    return errors


def component_passport(
    type_name: str, properties: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Return one serializable description used by help, diagnostics and tools."""
    spec = COMPONENTS[type_name]
    ports = effective_ports(type_name, properties or {})
    return {
        "type": spec.type_name,
        "caption": spec.caption,
        "category": spec.category,
        "subgroup": spec.subgroup,
        "description": spec.description,
        "source": spec.source,
        "implemented": bool(spec.implemented),
        "visual": bool(spec.visual),
        "support_status": spec.support_status,
        "hiasm": {
            "class": spec.hiasm_class,
            "inherit": spec.hiasm_inherit,
            "interfaces": spec.hiasm_interfaces,
            "sub": spec.hiasm_sub,
            "edit_class": spec.hiasm_edit_class,
        },
        "properties": [
            {
                "name": item.name,
                "caption": item.caption,
                "kind": item.kind,
                "default": deepcopy(item.default),
                "minimum": item.minimum,
                "maximum": item.maximum,
                "options": list(item.options),
                "description": item.description,
            }
            for item in spec.properties
        ],
        "ports": [
            {
                "name": port.name,
                "id": port_identifier(port.name, port.kind),
                "caption": port.caption,
                "kind": port.kind,
                "data_type": port.data_type,
                "required": bool(port.required),
                "description": port.description,
            }
            for port in ports
        ],
    }


def normalize_node_model(model: dict[str, Any]) -> dict[str, Any]:
    """Fill model defaults once before any editor or generator consumes it."""
    type_name = str(model.get("type", ""))
    if type_name not in COMPONENTS:
        raise KeyError(f"Неизвестный тип ноды: {type_name}")
    properties = default_properties(type_name)
    properties.update(model.get("properties") or {})
    model["properties"] = properties
    model.setdefault("x", 0.0)
    model.setdefault("y", 0.0)
    if not isinstance(model.get("enabled_ports"), list):
        model["enabled_ports"] = []
    valid = {port.name for port in effective_ports(type_name, properties)}
    required = {
        port.name for port in effective_ports(type_name, properties) if port.required
    }
    model["enabled_ports"] = [
        name for name in model["enabled_ports"] if name in valid
    ]
    for name in required:
        if name not in model["enabled_ports"]:
            model["enabled_ports"].append(name)
    return model


def diagnose_node_model(model: dict[str, Any]) -> list[str]:
    """Return precise, user-facing errors for one node model.

    This is deliberately independent from Qt so the same diagnostics can be
    used by the editor, import checks and future headless tooling.
    """
    node_id = str(model.get("id", "")).strip() or "без идентификатора"
    type_name = str(model.get("type", ""))
    spec = COMPONENTS.get(type_name)
    if spec is None:
        return [f"[{node_id}] Неизвестный тип компонента: {type_name}"]
    if type_name == "UserContainer":
        from container_library import validate_container_model
        container_errors = validate_container_model(model)
        if container_errors:
            return [f"[{node_id}] {error}" for error in container_errors]
    properties = model.get("properties")
    if properties is None:
        properties = {}
    if not isinstance(properties, dict):
        return [f"[{node_id}] Свойства компонента должны быть объектом."]
    errors: list[str] = []
    property_specs = {item.name: item for item in spec.properties}
    imported_qt = bool(properties.get("_qt_class"))
    for name, value in properties.items():
        prop = property_specs.get(name)
        if prop is None or value is None:
            continue
        if prop.kind == "bool" and not isinstance(value, bool):
            errors.append(f"[{node_id}] Свойство «{prop.caption}» должно быть логическим.")
            continue
        if prop.kind == "int" and (
            isinstance(value, bool) or not isinstance(value, int)
        ):
            errors.append(f"[{node_id}] Свойство «{prop.caption}» должно быть целым числом.")
            continue
        if prop.kind == "real" and (
            isinstance(value, bool) or not isinstance(value, (int, float))
        ):
            errors.append(f"[{node_id}] Свойство «{prop.caption}» должно быть числом.")
            continue
        if prop.kind in {"str", "multiline", "code", "color", "font"} and not isinstance(value, str):
            errors.append(f"[{node_id}] Свойство «{prop.caption}» должно быть текстом.")
            continue
        if prop.kind in {"choice", "enum"} and str(value) not in prop.options:
            errors.append(
                f"[{node_id}] Свойство «{prop.caption}»: значение «{value}» "
                f"не входит в список допустимых."
            )
            continue
        # Qt Designer permits compact labels, separators and controls whose
        # dimensions are below the native Builder palette minimum. Their
        # geometry is intentional and must survive import unchanged.
        skip_imported_geometry_range = (
            imported_qt and name in GEOMETRY_PROPERTIES
        )
        if (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and not skip_imported_geometry_range
        ):
            if prop.minimum is not None and value < prop.minimum:
                errors.append(
                    f"[{node_id}] Свойство «{prop.caption}» меньше минимума "
                    f"{prop.minimum}."
                )
            if prop.maximum is not None and value > prop.maximum:
                errors.append(
                    f"[{node_id}] Свойство «{prop.caption}» больше максимума "
                    f"{prop.maximum}."
                )
    enabled = model.get("enabled_ports")
    if enabled is not None:
        if not isinstance(enabled, list):
            errors.append(f"[{node_id}] enabled_ports должен быть списком.")
        else:
            try:
                ports = effective_ports(type_name, properties)
            except Exception as exc:
                errors.append(f"[{node_id}] Не удалось построить точки: {exc}")
            else:
                known = {port.name for port in ports}
                for name in enabled:
                    if name not in known:
                        errors.append(f"[{node_id}] Неизвестная включённая точка «{name}».")
    return errors


def diagnose_event_flow(project: dict[str, Any]) -> list[str]:
    """Explain action nodes that cannot be reached from a real event source."""
    nodes = [
        node for node in project.get("nodes", [])
        if isinstance(node, dict)
        and str(node.get("type", "")) in COMPONENTS
    ]
    links = [
        link for link in project.get("connections", [])
        if isinstance(link, dict)
    ]
    by_id = {str(node.get("id")): node for node in nodes}
    port_maps = {
        node_id: {
            (port.name, port.kind): port
            for port in effective_ports(
                node["type"], node.get("properties", {})
            )
        }
        for node_id, node in by_id.items()
    }
    graph: dict[str, set[str]] = {}
    incoming: set[tuple[str, str]] = set()
    outgoing: set[tuple[str, str]] = set()
    for link in links:
        source_id = str(link.get("from_node", ""))
        target_id = str(link.get("to_node", ""))
        source_port = port_maps.get(source_id, {}).get(
            (str(link.get("from_port", "")), "event_out")
        )
        target_port = port_maps.get(target_id, {}).get(
            (str(link.get("to_port", "")), "work_in")
        )
        if source_port is None or target_port is None:
            continue
        graph.setdefault(source_id, set()).add(target_id)
        outgoing.add((source_id, source_port.name))
        incoming.add((target_id, target_port.name))

    roots: set[str] = set()
    for node_id, node in by_id.items():
        spec = COMPONENTS[node["type"]]
        ports = tuple(port_maps[node_id].values())
        event_ports = [port for port in ports if port.kind == "event_out"]
        work_ports = [port for port in ports if port.kind == "work_in"]
        if event_ports and (
            node["type"] in {"Start", "Form"}
            or spec.visual
            or not work_ports
        ):
            roots.add(node_id)

    reachable = set(roots)
    pending = list(roots)
    while pending:
        source_id = pending.pop()
        for target_id in graph.get(source_id, ()):
            if target_id not in reachable:
                reachable.add(target_id)
                pending.append(target_id)

    def node_title(node):
        spec = COMPONENTS[node["type"]]
        name = str(node.get("properties", {}).get("name", "")).strip()
        return (
            f"«{spec.caption}» ({name})"
            if name and name != spec.caption else f"«{spec.caption}»"
        )

    warnings: list[str] = []
    for node_id, node in by_id.items():
        spec = COMPONENTS[node["type"]]
        ports = tuple(port_maps[node_id].values())
        work_ports = [port for port in ports if port.kind == "work_in"]
        if node["type"] == "Start":
            event_ports = [
                port for port in ports if port.kind == "event_out"
            ]
            if event_ports and not any(
                (node_id, port.name) in outgoing for port in event_ports
            ):
                warnings.append(
                    f"[{node_id}] {node_title(node)} никуда не передаёт запуск. "
                    "Что сделать: протяните оранжевую нить от «Запуск» к "
                    "первому действию программы."
                )
            continue
        if not work_ports or spec.visual or node["type"] == "Form":
            continue
        connected = [
            port for port in work_ports
            if (node_id, port.name) in incoming
        ]
        if not connected:
            names = ", ".join(f"«{port.caption}»" for port in work_ports[:3])
            warnings.append(
                f"[{node_id}] {node_title(node)} не получает команду и не "
                f"выполнится. Что сделать: соедините событие с входом {names}."
            )
        elif node_id not in reachable:
            warnings.append(
                f"[{node_id}] {node_title(node)} соединена, но эта цепочка "
                "не начинается от старта или действия пользователя. "
                "Что сделать: проследите оранжевую нить назад и подключите "
                "её к «Старт», кнопке, клавиатуре или другому источнику события."
            )
    return warnings


def repair_mdi_parentage(project: dict[str, Any]) -> dict[str, Any]:
    """Repair orphaned MDI children in projects saved by older importers."""
    nodes = project.setdefault("nodes", [])
    if not isinstance(nodes, list):
        return project
    subwindows = [
        node for node in nodes
        if node.get("properties", {}).get("_qt_class") == "QMdiSubWindow"
    ]
    if not subwindows:
        return project
    areas = [
        node for node in nodes
        if node.get("properties", {}).get("_qt_class") == "QMdiArea"
    ]
    if not areas:
        form = next((node for node in nodes if node.get("type") == "Form"), {})
        form_props = form.get("properties", {})
        used_ids = {str(node.get("id")) for node in nodes}
        area_id = "_recovered_mdi_area"
        while area_id in used_ids:
            area_id = "_recovered_mdi_area_" + uuid.uuid4().hex[:6]
        area_props = default_properties("Frame")
        area_props.update({
            "name": "mdiAreaRecovered",
            "_qt_class": "QMdiArea",
            "mdi_role": "area",
            "x": 10,
            "y": 10,
            "width": max(320, int(form_props.get("width", 640)) - 20),
            "height": max(240, int(form_props.get("height", 420)) - 20),
        })
        recovered = {
            "id": area_id,
            "type": "Frame",
            "x": 10,
            "y": 10,
            "properties": area_props,
            "enabled_ports": [],
        }
        nodes.append(recovered)
        areas = [recovered]
    by_id = {str(node.get("id")): node for node in nodes}
    for subwindow in subwindows:
        parent = by_id.get(str(subwindow.get("parent_id", "")))
        if parent and parent.get("properties", {}).get("_qt_class") == "QMdiArea":
            continue
        # Most Designer forms contain one MDI area. For the rare multi-area
        # case, prefer the nearest area in the editor coordinate system.
        props = subwindow.get("properties", {})
        sx = float(props.get("x", subwindow.get("x", 0)) or 0)
        sy = float(props.get("y", subwindow.get("y", 0)) or 0)
        chosen = min(
            areas,
            key=lambda area: (
                float(area.get("properties", {}).get("x", area.get("x", 0)) or 0) - sx
            ) ** 2 + (
                float(area.get("properties", {}).get("y", area.get("y", 0)) or 0) - sy
            ) ** 2,
        )
        subwindow["parent_id"] = chosen["id"]
    return project
