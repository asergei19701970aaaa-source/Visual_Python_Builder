"""Импорт Qt Designer .ui в формат Visual Python Builder.

Модуль намеренно не зависит от Qt и не импортирует NodeFlow. Он разбирает
XML-файл Designer в обычный проект Builder, поэтому импорт работает и в
безоконных тестах, и до запуска QApplication.
"""
from __future__ import annotations

import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from components import COMPONENTS, default_properties, effective_ports


MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_DEPTH = 40
MAX_NODES = 2000

SKIP_WIDGETS = {
    "QMenuBar",
    "QStatusBar",
    "QMenu",
    "QAction",
    "QToolBar",
}

# Qt Designer classes that have a direct Builder equivalent.
WIDGET_MAP = {
    "QPushButton": "Button",
    "QToolButton": "ToolButton",
    "QCommandLinkButton": "CommandLinkButton",
    "QLabel": "Label",
    "QLineEdit": "LineEdit",
    "QTextEdit": "TextEdit",
    "QPlainTextEdit": "PlainTextEdit",
    "QTextBrowser": "TextBrowser",
    "QCheckBox": "CheckBox",
    "QRadioButton": "RadioButton",
    "QComboBox": "ComboBox",
    "QFontComboBox": "FontComboBox",
    "QListWidget": "ListWidget",
    "QTreeWidget": "TreeWidget",
    "QTableWidget": "TableWidget",
    "QTableView": "TableView",
    "QDialogButtonBox": "DialogButtonBox",
    "QGroupBox": "GroupBox",
    "QFrame": "Frame",
    "QScrollArea": "Frame",
    "QDockWidget": "GroupBox",
    "QSplitter": "Frame",
    "QTabWidget": "GroupBox",
    "QToolBox": "GroupBox",
    "QStackedWidget": "GroupBox",
    "QSpinBox": "SpinBox",
    "QDoubleSpinBox": "DoubleSpinBox",
    "QTimeEdit": "TimeEdit",
    "QDateEdit": "DateEdit",
    "QDateTimeEdit": "DateTimeEdit",
    "QSlider": "Slider",
    "QDial": "Dial",
    "QScrollBar": "ScrollBar",
    "QLCDNumber": "LCDNumber",
    "QProgressBar": "ProgressBar",
    "QCalendarWidget": "Calendar",
    "QKeySequenceEdit": "KeySequenceEdit",
    "QGraphicsView": "Frame",
    "QOpenGLWidget": "Frame",
    "QQuickWidget": "Frame",
    "QWebEngineView": "Frame",
    "QMdiArea": "Frame",
    "QMdiSubWindow": "Frame",
    "Line": "HorizontalLine",
}

CONTAINER_CLASSES = {
    "QGroupBox",
    "QFrame",
    "QWidget",
    "QScrollArea",
    "QDockWidget",
    "QSplitter",
    "QTabWidget",
    "QToolBox",
    "QStackedWidget",
    "QMdiArea",
    "QMdiSubWindow",
}

SIGNAL_MAP = {
    "clicked": "onClick",
    "pressed": "onPressed",
    "released": "onReleased",
    "toggled": "onToggle",
    "stateChanged": "onChange",
    "textChanged": "onChange",
    "textEdited": "onChange",
    "returnPressed": "onReturn",
    "editingFinished": "onEditingFinished",
    "currentIndexChanged": "onChange",
    "currentTextChanged": "onTextChange",
    "activated": "onActivated",
    "valueChanged": "onChange",
    "dateChanged": "onChange",
    "timeChanged": "onChange",
    "itemSelectionChanged": "onSelect",
    "itemClicked": "onClick",
    "itemDoubleClicked": "onDoubleClick",
    "cellClicked": "onClick",
    "cellDoubleClicked": "onDoubleClick",
    "cellChanged": "onCellChange",
    "triggered": "onClick",
}

SLOT_MAP = {
    "click": "doClick",
    "setText": "doSetText",
    "clear": "doClear",
    "setValue": "doValue",
    "setChecked": "doCheck",
    "setCheckState": "doCheck",
    "show": "doShow",
    "hide": "doHide",
    "setEnabled": "doEnable",
    "setDisabled": "doDisable",
    "setWindowTitle": "doSetTitle",
    "setTitle": "doSetTitle",
}


def _text(node: ET.Element | None, default: str = "") -> str:
    return (node.text or default) if node is not None else default


def _value_of(prop: ET.Element) -> Any:
    """Convert one Qt Designer property to a JSON-compatible value."""
    for child in list(prop):
        tag = child.tag
        if tag in {"string", "cstring", "enum", "set", "keysequence", "url"}:
            if tag == "url":
                return _text(child.find("string"))
            return child.text or ""
        if tag == "bool":
            return _text(child).strip().lower() == "true"
        if tag in {"number", "double", "longLong", "uInt"}:
            raw = _text(child, "0").strip()
            try:
                return float(raw) if tag == "double" else int(float(raw))
            except ValueError:
                return 0
        if tag in {"rect", "size"}:
            if tag == "rect":
                result = {}
                for key in ("x", "y", "width", "height"):
                    try:
                        result[key] = int(float(_text(child.find(key), "0") or 0))
                    except ValueError:
                        result[key] = 0
                return result
            return [
                int(float(_text(child.find("width"), "0") or 0)),
                int(float(_text(child.find("height"), "0") or 0)),
            ]
        if tag == "font":
            result: dict[str, Any] = {}
            for key in ("family", "pointsize", "bold", "italic", "underline", "strikeout"):
                value = child.find(key)
                if value is None or value.text is None:
                    continue
                if key in {"bold", "italic", "underline", "strikeout"}:
                    result[key] = value.text.strip().lower() == "true"
                elif key == "pointsize":
                    try:
                        result[key] = int(float(value.text))
                    except ValueError:
                        pass
                else:
                    result[key] = value.text
            return result
        if tag in {"iconset", "pixmap"}:
            return _text(child).strip()
        if tag == "color":
            values = {key: _text(child.find(key), "") for key in ("red", "green", "blue", "alpha")}
            if all(values.get(key, "").isdigit() for key in ("red", "green", "blue")):
                return "#{:02x}{:02x}{:02x}".format(
                    int(values["red"]), int(values["green"]), int(values["blue"])
                )
            return values
    return None


def _properties(element: ET.Element | None) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if element is None:
        return result
    for prop in element.findall("property"):
        name = prop.get("name")
        if not name:
            continue
        value = _value_of(prop)
        if value is not None and value != "":
            result[name] = value
    return result


def _menu_bar_structure(root: ET.Element) -> tuple[bool, list[dict[str, Any]]]:
    """Convert Designer menus/actions to a compact JSON-compatible tree."""
    menu_bar = next(
        (
            widget for widget in root.iter("widget")
            if widget.get("class") == "QMenuBar"
        ),
        None,
    )
    if menu_bar is None:
        return False, []

    menus = {
        str(widget.get("name")): widget
        for widget in root.iter("widget")
        if widget.get("class") == "QMenu" and widget.get("name")
    }
    actions = {
        str(action.get("name")): action
        for action in root.iter("action")
        if action.get("name")
    }

    def action_data(name: str) -> dict[str, Any] | None:
        element = actions.get(name)
        if element is None:
            return None
        props = _properties(element)
        if bool(props.get("separator", False)):
            return {"type": "separator"}
        result = {
            "type": "action",
            "name": name,
            "text": str(props.get("text") or name),
            "shortcut": str(props.get("shortcut") or ""),
            "checkable": bool(props.get("checkable", False)),
            "checked": bool(props.get("checked", False)),
            "enabled": bool(props.get("enabled", True)),
            "visible": bool(props.get("visible", True)),
            "tooltip": str(props.get("toolTip") or ""),
            "status_tip": str(props.get("statusTip") or ""),
            "icon": str(props.get("icon") or ""),
        }
        return result

    def menu_data(name: str, stack: set[str]) -> dict[str, Any] | None:
        element = menus.get(name)
        if element is None or name in stack:
            return None
        props = _properties(element)
        items: list[dict[str, Any]] = []
        next_stack = {*stack, name}
        for reference in element.findall("addaction"):
            ref = str(reference.get("name") or "")
            if not ref:
                continue
            if ref == "separator":
                items.append({"type": "separator"})
            elif ref in menus:
                child = menu_data(ref, next_stack)
                if child is not None:
                    items.append(child)
            else:
                action = action_data(ref)
                if action is not None:
                    items.append(action)
        # Be tolerant of hand-written .ui files that omit addaction entries.
        if not items:
            for child in element.findall("widget"):
                if child.get("class") == "QMenu" and child.get("name"):
                    nested = menu_data(str(child.get("name")), next_stack)
                    if nested is not None:
                        items.append(nested)
        return {
            "type": "menu",
            "name": name,
            "title": str(props.get("title") or name),
            "enabled": bool(props.get("enabled", True)),
            "visible": bool(props.get("visible", True)),
            "icon": str(props.get("icon") or ""),
            "items": items,
        }

    result: list[dict[str, Any]] = []
    for reference in menu_bar.findall("addaction"):
        ref = str(reference.get("name") or "")
        item = menu_data(ref, set())
        if item is not None:
            result.append(item)
    if not result:
        for child in menu_bar.findall("widget"):
            if child.get("class") == "QMenu" and child.get("name"):
                item = menu_data(str(child.get("name")), set())
                if item is not None:
                    result.append(item)
    return True, result


def _children(element: ET.Element | None) -> list[ET.Element]:
    """Return direct widgets/layouts, including Designer's <item> wrappers."""
    result: list[ET.Element] = []
    for child in list(element) if element is not None else []:
        if child.tag in {"widget", "layout"}:
            result.append(child)
        elif child.tag == "item":
            result.extend(
                item for item in list(child) if item.tag in {"widget", "layout"}
            )
    return result


def _widget_children(element: ET.Element | None) -> list[ET.Element]:
    """Return widgets directly owned by a widget, through layout wrappers."""
    result: list[ET.Element] = []
    for child in _children(element):
        if child.tag == "widget":
            result.append(child)
        elif child.tag == "layout":
            for nested in _children(child):
                if nested.tag == "widget":
                    result.append(nested)
                elif nested.tag == "layout":
                    result.extend(_widget_children(nested))
    return result


def _all_widgets(root: ET.Element) -> list[ET.Element]:
    return list(root.iter("widget"))


def _item_texts(element: ET.Element) -> list[str]:
    values = []
    for item in element.findall("item"):
        value = item.find("property[@name='text']/string")
        if value is not None and value.text:
            values.append(value.text)
    return values


def _headers(element: ET.Element) -> list[str]:
    values = []
    for tag in ("column", "row"):
        for item in element.findall(tag):
            value = item.find("property[@name='text']/string")
            values.append(value.text if value is not None and value.text else "")
    return values


def _table_rows(element: ET.Element) -> list[list[str]]:
    cells: dict[tuple[int, int], str] = {}
    for item in element.findall("item"):
        try:
            row = int(item.get("row", "0"))
            column = int(item.get("column", "0"))
        except ValueError:
            continue
        value = item.find("property[@name='text']/string")
        cells[(row, column)] = value.text if value is not None and value.text else ""
    if not cells:
        return []
    rows = max(row for row, _ in cells) + 1
    columns = max(column for _, column in cells) + 1
    return [[cells.get((row, column), "") for column in range(columns)] for row in range(rows)]


def _plain_text(element: ET.Element, props: dict[str, Any]) -> str:
    for key in ("plainText", "html", "markdown", "text"):
        value = props.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def _strip_signature(value: str) -> str:
    return value.split("(", 1)[0].strip()


def _orientation_value(value: Any) -> str:
    """Normalize Qt enum spellings to the Builder's two choices."""
    text = str(value or "").strip()
    return "Vertical" if text.split("::")[-1].strip() == "Vertical" else "Horizontal"


_DIALOG_BUTTON_NAMES = {
    "Ok", "Save", "SaveAll", "Open", "Yes", "YesToAll", "No", "NoToAll",
    "Abort", "Retry", "Ignore", "Close", "Cancel", "Discard", "Help",
    "Apply", "Reset", "RestoreDefaults",
}


def _dialog_buttons_value(value: Any) -> str:
    """Normalize Designer's scoped StandardButton flags for the generator."""
    result: list[str] = []
    for part in str(value or "").split("|"):
        name = part.strip().split("::")[-1]
        if name in _DIALOG_BUTTON_NAMES and name not in result:
            result.append(name)
    return "|".join(result) or "Ok|Cancel"


def _safe_name(value: str, used: set[str], fallback: str) -> str:
    value = re.sub(r"\W+", "_", value or "").strip("_") or fallback
    if value[0].isdigit():
        value = "_" + value
    candidate = value
    index = 2
    while candidate in used:
        candidate = f"{value}_{index}"
        index += 1
    used.add(candidate)
    return candidate


def _default_enabled_ports(type_name: str, props: dict[str, Any]) -> list[str]:
    """Keep imported nodes compact, exposing one useful port per direction."""
    ports = tuple(effective_ports(type_name, props))
    enabled = [port.name for port in ports if port.required]
    priorities = {
        "work_in": (
            "doClick", "doSetText", "doValue", "doSetTitle",
            "doWork", "doData", "doSet", "doShow", "doOn", "doRun",
        ),
        "event_out": (
            "onClick", "onChange", "onCreate", "onStart", "onResult",
            "onSuccess", "onEvent",
        ),
        "data_in": ("Data", "Value", "Text", "Caption", "String"),
        "data_out": ("Result", "Value", "Text", "Data", "String"),
    }
    for kind, preferred in priorities.items():
        candidates = [port for port in ports if port.kind == kind]
        if not candidates:
            continue
        chosen = next(
            (port for name in preferred for port in candidates if port.name == name),
            candidates[0],
        )
        if chosen.name not in enabled:
            enabled.append(chosen.name)
    return enabled


def _layout_imported_graph(nodes: list[dict[str, Any]]) -> None:
    """Assign readable graph positions without changing form geometry."""
    by_id = {str(node.get("id")): node for node in nodes}

    def depth_of(node: dict[str, Any]) -> int:
        if node.get("type") == "Form":
            return 0
        depth = 1
        seen = {str(node.get("id"))}
        parent_id = str(node.get("parent_id", ""))
        while parent_id and parent_id in by_id and parent_id not in seen:
            seen.add(parent_id)
            parent = by_id[parent_id]
            if parent.get("type") == "Form":
                break
            depth += 1
            parent_id = str(parent.get("parent_id", ""))
        return depth

    columns: dict[int, list[dict[str, Any]]] = {}
    for node in nodes:
        if node.get("type") == "Form":
            node["x"], node["y"] = 40.0, 40.0
            continue
        columns.setdefault(depth_of(node), []).append(node)
    rows_per_subcolumn = 12
    for depth, column_nodes in columns.items():
        column_nodes.sort(
            key=lambda node: (
                float(node.get("properties", {}).get("y", 0) or 0),
                float(node.get("properties", {}).get("x", 0) or 0),
                str(node.get("id", "")),
            )
        )
        for index, node in enumerate(column_nodes):
            subcolumn = index // rows_per_subcolumn
            row = index % rows_per_subcolumn
            node["x"] = float(220 + (depth - 1) * 360 + subcolumn * 130)
            node["y"] = float(50 + row * 94)


def _load_root(path: str | os.PathLike[str]) -> ET.Element:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"Файл .ui не найден: {source}")
    if source.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("Файл .ui слишком большой (более 20 МБ).")
    try:
        root = ET.parse(source).getroot()
    except ET.ParseError as exc:
        raise ValueError(f"Файл .ui повреждён или не является XML: {exc}") from exc
    if root.tag != "ui":
        raise ValueError("Ожидался корневой элемент <ui>.")
    return root


def _runtime_widget_geometry(path: str | os.PathLike[str]) -> dict[str, dict[str, Any]]:
    """Read post-layout geometries when PySide6/QUiLoader is available.

    XML stores layout membership but not the final pixel positions. Loading the
    same file once through Qt gives the importer the exact positions that
    Designer preview uses. Headless tests and files with custom widgets simply
    fall back to the XML geometry.
    """
    try:
        from PySide6 import QtCore, QtWidgets, QtUiTools
    except Exception:
        return {}
    app = QtWidgets.QApplication.instance()
    if app is None or QtUiTools is None:
        return {}
    handle = QtCore.QFile(str(path))
    if not handle.open(QtCore.QIODevice.OpenModeFlag.ReadOnly):
        return {}
    window = None
    try:
        window = QtUiTools.QUiLoader().load(handle)
        if window is None:
            return {}
        window.setAttribute(QtCore.Qt.WidgetAttribute.WA_DontShowOnScreen, True)
        window.show()
        app.processEvents()
        result: dict[str, dict[str, Any]] = {}
        widgets = [window, *window.findChildren(QtWidgets.QWidget)]
        for widget in widgets:
            name = str(widget.objectName() or "")
            if not name:
                continue
            rect = widget.geometry()
            result[name] = {
                "x": int(rect.x()),
                "y": int(rect.y()),
                "width": int(rect.width()),
                "height": int(rect.height()),
            }
        return result
    except Exception:
        return {}
    finally:
        handle.close()
        if window is not None:
            window.close()
            window.deleteLater()
            app.processEvents()


def inspect_ui(path: str | os.PathLike[str]) -> list[dict[str, str]]:
    """Return a small inventory for a preview or diagnostics dialog."""
    root = _load_root(path)
    result = [
        {"class": item.get("class", ""), "name": item.get("name", "")}
        for item in root.iter("widget")
    ]
    result.extend(
        {"class": item.get("class", ""), "name": item.get("name", "")}
        for item in root.iter("layout")
    )
    return result


class _BuilderImporter:
    def __init__(
        self,
        root: ET.Element,
        runtime_geometry: dict[str, dict[str, Any]] | None = None,
    ):
        self.root = root
        self.runtime_geometry = runtime_geometry or {}
        self.nodes: list[dict[str, Any]] = []
        self.connections: list[dict[str, Any]] = []
        self.report: list[dict[str, str]] = []
        self.used_ids: set[str] = set()
        self.used_names: set[str] = set()
        self.seen: set[int] = set()
        self.node_by_designer_name: dict[str, dict[str, Any]] = {}

    def note(self, kind: str, text: str) -> None:
        self.report.append({"class": kind, "name": str(text)})

    def add_node(
        self,
        type_name: str,
        element: ET.Element,
        parent_id: str | None,
        props: dict[str, Any],
    ) -> dict[str, Any] | None:
        if len(self.nodes) >= MAX_NODES:
            self.note("limit", f"достигнут лимит {MAX_NODES} компонентов")
            return None
        if type_name not in COMPONENTS:
            self.note("missing_component", type_name)
            return None
        designer_name = element.get("name") or type_name
        node_id = _safe_name("ui_" + designer_name, self.used_ids, "ui_component")
        # Do not keep the component's default name ("button", "frame", ...)
        # from default_properties: Designer objectName is the real identity.
        props["name"] = _safe_name(
            designer_name, self.used_names, type_name.lower()
        )
        model = {
            "id": node_id,
            "type": type_name,
            "x": float(props.get("x", 0) or 0),
            "y": float(props.get("y", 0) or 0),
            "properties": props,
            # Imported projects should expose every port used by a Designer
            # connection. The normal palette intentionally hides optional
            # ports, but hiding them here would make a valid .ui connection
            # look broken after import.
            "enabled_ports": _default_enabled_ports(type_name, props),
        }
        if parent_id:
            model["parent_id"] = parent_id
        self.nodes.append(model)
        self.node_by_designer_name[designer_name] = model
        self.note("created_node", f"{designer_name} → {type_name}")
        return model

    def widget_props(self, element: ET.Element, type_name: str, index: int) -> dict[str, Any]:
        return self._widget_props(
            element, type_name, index, use_runtime=True
        )

    def _widget_props(
        self,
        element: ET.Element,
        type_name: str,
        index: int,
        use_runtime: bool = True,
    ) -> dict[str, Any]:
        raw = _properties(element)
        geometry = raw.get("geometry") if isinstance(raw.get("geometry"), dict) else {}
        runtime = self.runtime_geometry.get(element.get("name", ""), {})
        if use_runtime and runtime:
            geometry = runtime
        props = default_properties(type_name)
        props["x"] = int(geometry.get("x", index * 24) or 0)
        props["y"] = int(geometry.get("y", index * 24) or 0)
        if "width" in geometry:
            props["width"] = int(geometry["width"])
        if "height" in geometry:
            props["height"] = int(geometry["height"])

        common = {
            "enabled": raw.get("enabled", props.get("enabled", True)),
            "visible": raw.get("visible", props.get("visible", True)),
            "tooltip": raw.get("toolTip", props.get("tooltip", "")),
            "style": raw.get("styleSheet", props.get("style", "")),
            "accessible_name": raw.get("accessibleName", props.get("accessible_name", "")),
        }
        for key, value in common.items():
            if key in props and value not in ("", None):
                props[key] = value

        text = raw.get("text", "")
        if type_name == "Form":
            props["title"] = raw.get("windowTitle", text or props.get("title"))
            return props
        if type_name == "Frame" and element.get("class") in {
            "QMdiArea", "QMdiSubWindow"
        }:
            props["mdi_role"] = (
                "area" if element.get("class") == "QMdiArea" else "subwindow"
            )
            if element.get("class") == "QMdiSubWindow":
                props["mdi_title"] = raw.get(
                    "windowTitle", element.get("name", "Дочернее окно")
                )
        if "text" in props and text:
            props["text"] = text
        if "value" in props:
            props["value"] = raw.get("value", props["value"])
        if "title" in props:
            props["title"] = raw.get("title", text or props["title"])
        if "placeholder" in props:
            props["placeholder"] = raw.get("placeholderText", props["placeholder"])
        if "read_only" in props:
            props["read_only"] = raw.get("readOnly", props["read_only"])
        if "checked" in props:
            props["checked"] = raw.get("checked", props["checked"])
        if "word_wrap" in props:
            props["word_wrap"] = raw.get("wordWrap", props["word_wrap"])
        if "wrap" in props:
            props["wrap"] = raw.get("wordWrap", props["wrap"])
        if "style" in props and isinstance(raw.get("styleSheet"), str):
            props["style"] = raw["styleSheet"]
        if "minimum" in props:
            props["minimum"] = raw.get("minimum", props["minimum"])
        if "maximum" in props:
            props["maximum"] = raw.get("maximum", props["maximum"])
        if "step" in props:
            props["step"] = raw.get("singleStep", props["step"])
        if "orientation" in props:
            props["orientation"] = _orientation_value(
                raw.get("orientation", props["orientation"])
            )
        if type_name == "DialogButtonBox":
            props["buttons"] = _dialog_buttons_value(
                raw.get("standardButtons", props.get("buttons"))
            )
            props["center_buttons"] = bool(
                raw.get("centerButtons", props.get("center_buttons", False))
            )
        if type_name == "HorizontalLine":
            props["vertical"] = (
                _orientation_value(raw.get("orientation")) == "Vertical"
            )
        if type_name in {"TextEdit", "PlainTextEdit", "TextBrowser"}:
            value = _plain_text(element, raw)
            if "text" in props:
                props["text"] = value
            if "value" in props:
                props["value"] = value
        if type_name in {"ComboBox", "ListWidget"}:
            props["items"] = "|".join(_item_texts(element))
        if type_name == "TableWidget":
            headers = _headers(element)
            if headers:
                props["columns"] = "|".join(headers)
            rows = _table_rows(element)
            props["rows"] = max(int(props.get("rows", 0) or 0), len(rows))
            if rows:
                self.note("data_warning", f"{element.get('name', type_name)}: ячейки таблицы сохранены как количество строк")
        if type_name == "TreeWidget":
            headers = _headers(element)
            if headers:
                props["header"] = "|".join(headers)
        if type_name == "DateEdit" and raw.get("date"):
            props["date"] = raw["date"]
        if "font" in raw and isinstance(raw["font"], dict):
            font = raw["font"]
            for raw_key, target_key in (
                ("family", "font_family"),
                ("pointsize", "font_size"),
                ("bold", "font_bold"),
                ("italic", "font_italic"),
                ("underline", "font_underline"),
            ):
                if target_key in props and raw_key in font:
                    props[target_key] = font[raw_key]
        return props

    def _has_mdi_ancestor(self, parent_id: str | None) -> bool:
        """Return whether a widget belongs to the MDI coordinate system."""
        seen: set[str] = set()
        current = parent_id
        while current and current not in seen:
            seen.add(current)
            parent = next(
                (model for model in self.nodes if model.get("id") == current),
                None,
            )
            if parent is None:
                return False
            props = parent.get("properties", {})
            if props.get("mdi_role") in {"area", "subwindow"}:
                return True
            current = parent.get("parent_id")
        return False

    def parse_widget(
        self,
        element: ET.Element,
        parent_id: str | None,
        depth: int = 0,
        index: int = 0,
    ) -> list[str]:
        if depth > MAX_DEPTH:
            self.note("limit", f"превышена глубина вложенности у {element.get('name', '')}")
            return []
        marker = id(element)
        if marker in self.seen:
            return []
        self.seen.add(marker)

        cls = element.get("class") or "QWidget"
        name = element.get("name") or cls
        raw_properties = _properties(element)
        parent_model = next(
            (
                model for model in self.nodes
                if model.get("id") == parent_id
            ),
            None,
        )
        parent_is_mdi = bool(
            parent_model
            and parent_model.get("properties", {}).get("mdi_role") == "area"
        )
        parent_is_scroll_area = bool(
            parent_model
            and parent_model.get("properties", {}).get("_qt_class")
            == "QScrollArea"
        )
        parent_is_mdi_subwindow = bool(
            parent_model
            and parent_model.get("properties", {}).get("mdi_role")
            == "subwindow"
        )
        if cls in SKIP_WIDGETS:
            self.note("skipped_structure", f"{cls} {name}")
            return []
        if cls == "QWidget" and parent_is_scroll_area:
            # QScrollArea owns a generated scrollAreaWidgetContents QWidget.
            # It is a Qt implementation detail, not a visual component the
            # user should have to arrange in the Builder schema.
            self.note("skipped_wrapper", f"{name}: содержимое QScrollArea")
            for child_index, child in enumerate(_widget_children(element)):
                self.parse_widget(child, parent_id, depth + 1, child_index)
            return []
        if cls == "QWidget" and (
            (parent_id is None and name.lower() == "centralwidget")
            or parent_is_mdi_subwindow
        ):
            # QMainWindow.centralWidget and the content QWidget owned by an
            # MDI subwindow are coordinate-system wrappers, not user controls.
            self.note("skipped_wrapper", f"{name}: служебный QWidget")
            for child_index, child in enumerate(_widget_children(element)):
                self.parse_widget(child, parent_id, depth + 1, child_index)
            return []
        if (
            cls == "QWidget"
            and not raw_properties.get("geometry")
            and not parent_is_mdi
        ):
            # Designer commonly uses an invisible central QWidget as a layout
            # wrapper. Keep its children but do not create a meaningless node.
            child_parent = parent_id
            for child_index, child in enumerate(_widget_children(element)):
                self.parse_widget(child, child_parent, depth + 1, child_index)
            return []

        type_name = WIDGET_MAP.get(cls)
        if type_name is None:
            if parent_is_mdi and cls == "QWidget":
                # Some Designer files serialize an MDI child as a plain
                # QWidget. It is promoted below to a real subwindow.
                type_name = "Frame"
                self.note("promoted_widget", f"{cls} {name} → MDI-дочернее окно")
            else:
                type_name = "Frame" if cls not in {"QMainWindow", "QDialog"} else "Form"
                self.note("unsupported_widget", f"{cls} {name} → {type_name}")
        try:
            in_mdi_tree = (
                cls in {"QMdiArea", "QMdiSubWindow"}
                or self._has_mdi_ancestor(parent_id)
            )
            has_explicit_geometry = isinstance(
                raw_properties.get("geometry"), dict
            )
            props = self._widget_props(
                element,
                type_name,
                index,
                use_runtime=not in_mdi_tree,
            )
            # Qt Designer often serializes an MDI child as an ordinary QWidget
            # (not as QMdiSubWindow). Promote that direct child so the editor
            # and generated application both get a real title-bar offset.
            if (
                parent_is_mdi
                and type_name == "Frame"
                and (
                    cls in {"QWidget", "QFrame", "QMdiSubWindow"}
                    or "windowTitle" in raw_properties
                )
            ):
                props["mdi_role"] = "subwindow"
                props["_qt_class"] = "QMdiSubWindow"
                props["mdi_title"] = raw_properties.get(
                    "windowTitle", name
                )
            # Preserve the original Designer class for renderer-specific
            # fallbacks (for example QGraphicsView -> a visible gray canvas).
            props.setdefault("_qt_class", cls)
            node = self.add_node(type_name, element, parent_id, props)
        except Exception as exc:  # keep one broken widget from aborting import
            self.note("node_error", f"{cls} {name}: {exc}")
            return []
        if node is None:
            return []

        children = [
            child for child in _widget_children(element)
            if child.get("class") not in SKIP_WIDGETS
        ]
        for child_index, child in enumerate(children):
            self.parse_widget(child, node["id"], depth + 1, child_index)
        if (
            node.get("properties", {}).get("mdi_role") == "subwindow"
            and not has_explicit_geometry
        ):
            child_models = [
                model for model in self.nodes
                if model.get("parent_id") == node.get("id")
            ]
            right = max(
                (
                    int(model.get("properties", {}).get("x", 0))
                    + int(model.get("properties", {}).get("width", 120))
                    for model in child_models
                ),
                default=260,
            )
            bottom = max(
                (
                    int(model.get("properties", {}).get("y", 0))
                    + int(model.get("properties", {}).get("height", 32))
                    for model in child_models
                ),
                default=160,
            )
            parent_props = (
                parent_model.get("properties", {})
                if parent_model else {}
            )
            area_width = int(parent_props.get("width", 751) or 751)
            area_height = int(parent_props.get("height", 371) or 371)
            node_props = node.setdefault("properties", {})
            node_props["width"] = max(360, right + 40)
            node_props["height"] = max(240, bottom + 60)
            node_props["x"] = max(
                10, (area_width - node_props["width"]) // 2
            )
            node_props["y"] = max(
                10, (area_height - node_props["height"]) // 2
            )
        return [node["id"]]

    def parse_connections(self) -> None:
        for connection in self.root.findall("connections/connection"):
            sender = _text(connection.find("sender")).strip()
            signal = _strip_signature(_text(connection.find("signal")).strip())
            receiver = _text(connection.find("receiver")).strip()
            slot = _strip_signature(_text(connection.find("slot")).strip())
            source = self.node_by_designer_name.get(sender)
            target = self.node_by_designer_name.get(receiver)
            from_port = SIGNAL_MAP.get(signal)
            to_port = SLOT_MAP.get(slot)
            if not source or not target or not from_port or not to_port:
                self.note("connection_warning", f"{sender}.{signal} → {receiver}.{slot}: точка не сопоставлена")
                continue
            self.connections.append({
                "from_node": source["id"],
                "from_port": from_port,
                "to_node": target["id"],
                "to_port": to_port,
                "line_style": "orthogonal",
                "bends": [],
            })
            for node, port in ((source, from_port), (target, to_port)):
                enabled = node.setdefault("enabled_ports", [])
                if port not in enabled:
                    enabled.append(port)
            self.note("created_connection", f"{sender}.{signal} → {receiver}.{slot}")


def import_ui_to_project(path: str | os.PathLike[str]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Import a Designer file and return ``(project, report)``.

    The report is intentionally machine-readable so the GUI can later display
    filters, counts and links to the affected node or connection.
    """
    root = _load_root(path)
    top = root.find("widget")
    if top is None:
        top = next(iter(root.iter("widget")), None)
    if top is None:
        raise ValueError("В файле .ui не найдено ни одного виджета.")

    runtime_geometry = _runtime_widget_geometry(path)
    importer = _BuilderImporter(root, runtime_geometry)
    top_props = _properties(top)
    geometry = top_props.get("geometry") if isinstance(top_props.get("geometry"), dict) else {}
    geometry = runtime_geometry.get(top.get("name", ""), geometry)
    form_props = default_properties("Form")
    form_props["title"] = top_props.get("windowTitle") or Path(path).stem
    form_props["width"] = int(geometry.get("width", form_props.get("width", 640)) or 640)
    form_props["height"] = int(geometry.get("height", form_props.get("height", 420)) or 420)
    # A Designer QMainWindow is a normal central widget, not an automatically
    # scrolling document.  Keep the imported outer size and do not add the
    # Builder's optional document scroll bars unless the user enables them.
    if "viewport_width" in form_props:
        form_props["viewport_width"] = form_props["width"]
    if "viewport_height" in form_props:
        form_props["viewport_height"] = form_props["height"]
    if "scrollable" in form_props:
        form_props["scrollable"] = False
    form_props["_qt_class"] = top.get("class", "QMainWindow")
    menu_bar, menus = _menu_bar_structure(root)
    if "menu_bar" in form_props:
        form_props["menu_bar"] = menu_bar
    if "menus" in form_props:
        form_props["menus"] = json.dumps(menus, ensure_ascii=False, indent=2)
    form_props["name"] = "form"
    status = next((w for w in _all_widgets(root) if w.get("class") == "QStatusBar"), None)
    if "statusbar_enabled" in form_props:
        form_props["statusbar_enabled"] = status is not None
    if status is not None and "statusbar" in form_props:
        form_props["statusbar"] = _properties(status).get("windowTitle", "")
    form = importer.add_node("Form", top, None, form_props)
    if form is None:
        raise ValueError("Не удалось создать главную форму.")

    # Parse the top-level widget's children. The top widget itself is the form.
    # The Form node describes the generated QMainWindow, but it is not a
    # QWidget attribute in generated code. Top-level Designer widgets must
    # therefore use the Builder's central widget, represented by parent_id=None.
    for index, child in enumerate(_widget_children(top)):
        importer.parse_widget(child, None, 0, index)
    importer.parse_connections()
    _layout_imported_graph(importer.nodes)

    if menu_bar:
        action_count = sum(
            1 for menu in menus for item in menu.get("items", [])
            if item.get("type") == "action"
        )
        importer.note(
            "imported_menu",
            f"строка меню: разделов {len(menus)}, действий верхнего уровня {action_count}",
        )
    for layout in root.iter("layout"):
        importer.note("layout_info", f"{layout.get('class', 'layout')}: структура преобразована в геометрию виджетов")

    project = {
        "format": 1,
        "name": str(form_props["title"]),
        "nodes": importer.nodes,
        "connections": importer.connections,
    }
    return project, importer.report


def report_counts(report: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in report:
        key = str(item.get("class", "info"))
        counts[key] = counts.get(key, 0) + 1
    return counts