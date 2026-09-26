"""Прозрачная библиотека готовых контейнеров из обычных нод."""
from __future__ import annotations

import copy
import json
import os
import re
import uuid
from pathlib import Path
from typing import Any

from components import effective_ports
from connection_advisor import advise_connection, normalize_data_type

APP_ROOT = Path(__file__).resolve().parent
BUILTIN_CONTAINERS_DIR = APP_ROOT / "container_templates"
USER_CONTAINERS_DIR = (
    Path(os.path.expanduser("~")) / ".visual_python_builder" / "containers"
)
USER_LIBRARY_FILE = USER_CONTAINERS_DIR / "library.json"


def _clean_label(value: Any, fallback: str) -> str:
    text = re.sub(r"[\x00-\x1f]+", " ", str(value or "")).strip()
    return text[:100] or fallback


def _empty_library() -> dict[str, Any]:
    return {"format": 1, "categories": [], "templates": []}


def load_user_library(path: Path | None = None) -> dict[str, Any]:
    filename = path or USER_LIBRARY_FILE
    if not filename.exists():
        return _empty_library()
    try:
        data = json.loads(filename.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return _empty_library()
    if not isinstance(data, dict):
        return _empty_library()
    categories = data.get("categories")
    templates = data.get("templates")
    return {
        "format": 1,
        "categories": categories if isinstance(categories, list) else [],
        "templates": templates if isinstance(templates, list) else [],
    }


def save_user_library(data: dict[str, Any], path: Path | None = None) -> None:
    filename = path or USER_LIBRARY_FILE
    filename.parent.mkdir(parents=True, exist_ok=True)
    temporary = filename.with_suffix(filename.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(filename)


def ensure_user_category(
    category: str,
    subgroup: str = "",
    path: Path | None = None,
) -> None:
    category = _clean_label(category, "Мои контейнеры")
    subgroup = _clean_label(subgroup, "") if subgroup else ""
    library = load_user_library(path)
    for item in library["categories"]:
        if not isinstance(item, dict) or item.get("name") != category:
            continue
        subgroups = item.setdefault("subgroups", [])
        if subgroup and subgroup not in subgroups:
            subgroups.append(subgroup)
        save_user_library(library, path)
        return
    library["categories"].append(
        {"name": category, "subgroups": [subgroup] if subgroup else []}
    )
    save_user_library(library, path)


def _portable_container_model(model: dict[str, Any]) -> dict[str, Any]:
    if str(model.get("type")) != "UserContainer":
        raise ValueError("В библиотеку можно сохранить только контейнер пользователя.")
    result = copy.deepcopy(model)
    result["id"] = "template_container"
    result["x"] = 0
    result["y"] = 0
    result.setdefault("properties", {}).setdefault("name", "Контейнер")
    return result


def save_container_template(
    model: dict[str, Any],
    title: str,
    category: str,
    subgroup: str = "",
    description: str = "",
    path: Path | None = None,
) -> str:
    title = _clean_label(title, "Новый контейнер")
    category = _clean_label(category, "Мои контейнеры")
    subgroup = _clean_label(subgroup, "") if subgroup else ""
    ensure_user_category(category, subgroup, path)
    library = load_user_library(path)
    template_id = "user-" + uuid.uuid4().hex
    library["templates"].append(
        {
            "id": template_id,
            "title": title,
            "category": category,
            "subgroup": subgroup,
            "description": _clean_label(description, "") if description else "",
            "source": "user",
            "model": _portable_container_model(model),
        }
    )
    save_user_library(library, path)
    return template_id


def delete_user_template(template_id: str, path: Path | None = None) -> bool:
    library = load_user_library(path)
    before = len(library["templates"])
    library["templates"] = [
        item for item in library["templates"]
        if not isinstance(item, dict) or str(item.get("id")) != str(template_id)
    ]
    changed = len(library["templates"]) != before
    if changed:
        save_user_library(library, path)
    return changed


def _load_builtin_templates(folder: Path | None = None) -> list[dict[str, Any]]:
    root = folder or BUILTIN_CONTAINERS_DIR
    result = []
    if not root.exists():
        return result
    for filename in sorted(root.rglob("*.json")):
        try:
            data = json.loads(filename.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            continue
        if not isinstance(data, dict) or not isinstance(data.get("model"), dict):
            continue
        item = copy.deepcopy(data)
        item["id"] = str(item.get("id") or f"builtin-{filename.stem}")
        item["title"] = _clean_label(item.get("title"), filename.stem)
        item["category"] = _clean_label(item.get("category"), "Готовые")
        item["subgroup"] = _clean_label(item.get("subgroup"), "") if item.get("subgroup") else ""
        item["description"] = str(item.get("description") or "")
        item["source"] = "builtin"
        result.append(item)
    return result


def discover_container_library(
    builtin_folder: Path | None = None,
    user_path: Path | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    user = load_user_library(user_path)
    templates = _load_builtin_templates(builtin_folder)
    for raw in user["templates"]:
        if not isinstance(raw, dict) or not isinstance(raw.get("model"), dict):
            continue
        item = copy.deepcopy(raw)
        item["source"] = "user"
        templates.append(item)
    categories = [
        copy.deepcopy(item)
        for item in user["categories"]
        if isinstance(item, dict) and str(item.get("name", "")).strip()
    ]
    return templates, categories


def _remap_subgraph(subgraph: dict[str, Any], prefix: str) -> dict[str, Any]:
    result = copy.deepcopy(subgraph)
    nodes = result.get("nodes", [])
    mapping = {
        str(node.get("id")): f"{prefix}_{index}_{uuid.uuid4().hex[:5]}"
        for index, node in enumerate(nodes)
        if isinstance(node, dict)
    }
    for node in nodes:
        if not isinstance(node, dict):
            continue
        old_id = str(node.get("id"))
        node["id"] = mapping.get(old_id, old_id)
        props = node.get("properties", {})
        if node.get("type") == "UserContainer" and isinstance(props, dict):
            inner = props.get("subgraph")
            if isinstance(inner, dict):
                props["subgraph"] = _remap_subgraph(
                    inner, prefix + "_nested"
                )
                interface = props.get("interface", [])
                nested_proxy_map = {
                    str(child.get("properties", {}).get("name", "")):
                    str(child.get("id"))
                    for child in props["subgraph"].get("nodes", [])
                    if isinstance(child, dict)
                    and str(child.get("type", "")).startswith("Container")
                }
                for port in interface if isinstance(interface, list) else []:
                    if isinstance(port, dict):
                        caption = str(
                            port.get("caption") or port.get("port") or ""
                        )
                        if caption in nested_proxy_map:
                            port["proxy_id"] = nested_proxy_map[caption]
    for connection in result.get("connections", []):
        if not isinstance(connection, dict):
            continue
        connection["from_node"] = mapping.get(
            str(connection.get("from_node")), connection.get("from_node")
        )
        connection["to_node"] = mapping.get(
            str(connection.get("to_node")), connection.get("to_node")
        )
    return result


def instantiate_container_template(
    template: dict[str, Any],
    x: float,
    y: float,
) -> dict[str, Any]:
    model = _portable_container_model(template["model"])
    prefix = uuid.uuid4().hex[:8]
    model["id"] = prefix
    model["x"] = round(float(x), 1)
    model["y"] = round(float(y), 1)
    props = model.setdefault("properties", {})
    inner = props.get("subgraph")
    if isinstance(inner, dict):
        props["subgraph"] = _remap_subgraph(inner, prefix)
        props["interface"] = copy.deepcopy(props.get("interface", []))
        proxy_map = {
            str(node.get("properties", {}).get("name", "")): str(node.get("id"))
            for node in props["subgraph"].get("nodes", [])
            if isinstance(node, dict)
            and str(node.get("type", "")).startswith("Container")
        }
        for port in props["interface"] if isinstance(props["interface"], list) else []:
            if isinstance(port, dict):
                name = str(port.get("caption") or port.get("port") or "")
                if name in proxy_map:
                    port["proxy_id"] = proxy_map[name]
    return model


INTERFACE_KINDS = {
    "work_in": {
        "label": "Вход действия",
        "type": "ContainerEventInput",
        "inner_port": "onEvent",
    },
    "data_in": {
        "label": "Вход данных",
        "type": "ContainerDataInput",
        "inner_port": "Data",
    },
    "event_out": {
        "label": "Выход события",
        "type": "ContainerEventOutput",
        "inner_port": "doEvent",
    },
    "data_out": {
        "label": "Выход данных",
        "type": "ContainerDataOutput",
        "inner_port": "Data",
    },
}

INTERFACE_DATA_TYPES = {
    "any": "Любые данные",
    "text": "Текст",
    "number": "Число",
    "bool": "Да / нет",
    "list": "Список",
    "dict": "Словарь",
    "color": "Цвет",
    "file": "Файл или путь",
}


def validate_container_model(model: dict[str, Any]) -> list[str]:
    """Проверить паспорт, интерфейс и соответствие служебным proxy-нодам."""
    if str(model.get("type")) != "UserContainer":
        return ["Проверять как контейнер можно только UserContainer."]
    props = model.get("properties", {})
    subgraph = props.get("subgraph", {}) if isinstance(props, dict) else {}
    interface = props.get("interface", []) if isinstance(props, dict) else []
    if not isinstance(subgraph, dict):
        return ["Внутренняя схема контейнера повреждена."]
    if not isinstance(interface, list):
        return ["Интерфейс контейнера должен быть списком."]
    nodes = {
        str(node.get("id")): node
        for node in subgraph.get("nodes", [])
        if isinstance(node, dict)
    }
    errors, names = [], set()
    for index, item in enumerate(interface, 1):
        if not isinstance(item, dict):
            errors.append(f"Точка {index}: неверная запись.")
            continue
        port = str(item.get("port", "")).strip()
        caption = str(item.get("caption", "")).strip()
        kind = str(item.get("kind", ""))
        data_type = str(item.get("data_type") or "any")
        proxy_id = str(item.get("proxy_id", ""))
        if not port:
            errors.append(f"Точка {index}: не задано техническое имя.")
        elif port in names:
            errors.append(f"Повторяется имя внешней точки «{port}».")
        names.add(port)
        if not caption:
            errors.append(f"Точка «{port or index}»: не задано понятное название.")
        definition = INTERFACE_KINDS.get(kind)
        if definition is None:
            errors.append(f"Точка «{caption or port}»: неизвестный тип {kind}.")
            continue
        if kind in {"data_in", "data_out"}:
            if data_type not in INTERFACE_DATA_TYPES:
                errors.append(
                    f"Точка «{caption or port}»: неизвестный тип данных "
                    f"{data_type}."
                )
        elif data_type != "any":
            errors.append(
                f"Точка «{caption or port}»: событию или действию нельзя "
                "назначить тип данных."
            )
        proxy = nodes.get(proxy_id)
        if proxy is None:
            errors.append(f"Точка «{caption or port}»: внутренняя proxy-нода потеряна.")
        elif proxy.get("type") != definition["type"]:
            errors.append(
                f"Точка «{caption or port}»: proxy-нода имеет неверное направление."
            )
        else:
            proxy_props = proxy.get("properties", {})
            proxy_type = normalize_data_type(
                proxy_props.get("data_type")
                if isinstance(proxy_props, dict) else "any"
            )
            interface_type = normalize_data_type(data_type)
            if (
                kind in {"data_in", "data_out"}
                and proxy_type != "any"
                and proxy_type != interface_type
            ):
                errors.append(
                    f"Точка «{caption or port}»: в паспорте указан тип "
                    f"«{interface_type}», а внутренняя proxy-нода хранит "
                    f"«{proxy_type}». Откройте паспорт и выберите один тип."
                )

        if (
            definition is not None
            and proxy is not None
            and kind in {"data_in", "data_out"}
        ):
            interface_type = normalize_data_type(data_type)
            related = [
                connection
                for connection in subgraph.get("connections", [])
                if isinstance(connection, dict)
                and (
                    str(connection.get("from_node")) == proxy_id
                    or str(connection.get("to_node")) == proxy_id
                )
            ]
            for connection in related:
                if str(connection.get("from_node")) == proxy_id:
                    other = nodes.get(str(connection.get("to_node")))
                    port_name = str(connection.get("to_port", ""))
                    wanted_kind = "data_in"
                    source_first = True
                else:
                    other = nodes.get(str(connection.get("from_node")))
                    port_name = str(connection.get("from_port", ""))
                    wanted_kind = "data_out"
                    source_first = False
                if other is None or other.get("type") is None:
                    continue
                try:
                    other_port = next(
                        port for port in effective_ports(
                            str(other["type"]),
                            other.get("properties", {}),
                        )
                        if port.name == port_name
                        and port.kind == wanted_kind
                    )
                except (KeyError, StopIteration):
                    continue
                advice = (
                    advise_connection(
                        "data_out", other_port.kind,
                        interface_type, other_port.data_type,
                    )
                    if source_first else
                    advise_connection(
                        other_port.kind, "data_in",
                        other_port.data_type, interface_type,
                    )
                )
                if not advice.allowed:
                    fix = (
                        f" Добавьте «{advice.adapter_caption}» внутри контейнера."
                        if advice.needs_adapter else ""
                    )
                    errors.append(
                        f"Точка «{caption or port}» имеет тип "
                        f"«{interface_type}», несовместимый с внутренней "
                        f"точкой «{other_port.caption}».{fix}"
                    )
    return errors


def apply_container_interface(
    model: dict[str, Any],
    rows: list[dict[str, str]],
) -> dict[str, str]:
    """Применить строки редактора интерфейса и вернуть old_port → new_port."""
    if str(model.get("type")) != "UserContainer":
        raise ValueError("Интерфейс доступен только пользовательскому контейнеру.")
    props = model.setdefault("properties", {})
    subgraph = props.setdefault(
        "subgraph",
        {"format": 1, "name": "Внутренняя схема", "nodes": [], "connections": []},
    )
    nodes = subgraph.setdefault("nodes", [])
    connections = subgraph.setdefault("connections", [])
    old_interface = props.get("interface", [])
    old_by_proxy = {
        str(item.get("proxy_id")): item
        for item in old_interface
        if isinstance(item, dict)
    }
    used_ports, normalized, rename_map = set(), [], {}
    keep_proxies = set()
    for index, raw in enumerate(rows):
        caption = _clean_label(raw.get("caption"), f"Точка {index + 1}")
        port = re.sub(r"\W+", "_", str(raw.get("port") or caption)).strip("_")
        port = port or f"Port{index + 1}"
        base, number = port, 2
        while port in used_ports:
            port = f"{base}_{number}"
            number += 1
        used_ports.add(port)
        kind = str(raw.get("kind"))
        definition = INTERFACE_KINDS.get(kind)
        if definition is None:
            raise ValueError(f"Неизвестный тип точки: {kind}")
        data_type = (
            str(raw.get("data_type") or "any")
            if kind in {"data_in", "data_out"} else "any"
        )
        if data_type not in INTERFACE_DATA_TYPES:
            raise ValueError(
                f"Неизвестный тип данных точки «{caption}»: {data_type}"
            )
        proxy_id = str(raw.get("proxy_id") or "")
        old = old_by_proxy.get(proxy_id)
        old_type = (
            str(old.get("data_type") or "any")
            if isinstance(old, dict) else "any"
        )
        data_type_source = str(
            raw.get("data_type_source") or ""
        ).strip()
        if data_type != old_type:
            data_type_source = "Выбран вручную в паспорте"
        elif not data_type_source and kind in {"data_in", "data_out"}:
            data_type_source = str(
                old.get("data_type_source") or "Старый контейнер: тип не указан"
            ) if isinstance(old, dict) else "Выбран вручную в паспорте"
        proxy = next(
            (
                node for node in nodes
                if isinstance(node, dict) and str(node.get("id")) == proxy_id
            ),
            None,
        )
        if proxy is None:
            proxy_id = "port_" + uuid.uuid4().hex[:10]
            is_input = kind in {"work_in", "data_in"}
            proxy = {
                "id": proxy_id,
                "type": definition["type"],
                "x": 0 if is_input else 560,
                "y": 70 + index * 72,
                "properties": {
                    "name": caption,
                    "data_type": data_type,
                    "data_type_source": data_type_source,
                },
                "enabled_ports": [definition["inner_port"]],
            }
            nodes.append(proxy)
        elif proxy.get("type") != definition["type"]:
            raise ValueError(
                f"Нельзя изменить направление существующей точки «{caption}». "
                "Удалите её и создайте новую."
            )
        proxy.setdefault("properties", {}).update({
            "name": caption,
            "data_type": data_type,
            "data_type_source": data_type_source,
        })
        keep_proxies.add(proxy_id)
        old = old_by_proxy.get(proxy_id)
        if old and str(old.get("port")) != port:
            rename_map[str(old.get("port"))] = port
        normalized.append(
            {
                "port": port,
                "caption": caption,
                "kind": kind,
                "data_type": data_type,
                "data_type_source": data_type_source,
                "proxy_id": proxy_id,
                "description": str(raw.get("description") or "").strip(),
            }
        )
    removed = set(old_by_proxy) - keep_proxies
    if removed:
        subgraph["nodes"] = [
            node for node in nodes
            if str(node.get("id")) not in removed
        ]
        subgraph["connections"] = [
            connection for connection in connections
            if str(connection.get("from_node")) not in removed
            and str(connection.get("to_node")) not in removed
        ]
    props["interface"] = normalized
    model["enabled_ports"] = [item["port"] for item in normalized]
    return rename_map