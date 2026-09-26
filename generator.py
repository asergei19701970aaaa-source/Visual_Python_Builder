from __future__ import annotations

import json

from instruments_runtime import INSTRUMENT_RUNTIME_SOURCE
from python_library.codegen.game_helpers import TETRIS_WIDGET
import keyword
import re
from collections import defaultdict
from typing import Any

from components import COMPONENTS, effective_ports
from hiasm_support import parse_hiasm_font
from model_contract import repair_mdi_parentage

DELPHI_COLOR_MAP = {
    "clblack": "#000000", "clmaroon": "#800000", "clgreen": "#008000",
    "clolive": "#808000", "clnavy": "#000080", "clpurple": "#800080",
    "clteal": "#008080", "clgray": "#808080", "clsilver": "#C0C0C0",
    "clred": "#FF0000", "cllime": "#00FF00", "clyellow": "#FFFF00",
    "clblue": "#0000FF", "clfuchsia": "#FF00FF", "claqua": "#00FFFF",
    "clwhite": "#FFFFFF", "clwindow": "#FFFFFF", "clbtnface": "#F0F0F0",
    "clbtntext": "#000000", "clhighlight": "#0078D7",
    "clgraytext": "#6D6D6D", "clmedgray": "#A0A0A0",
    "clskyblue": "#87CEEB", "clbtnshadow": "#A0A0A0",
    "clbtnhighlight": "#FFFFFF",
}


def normalized_delphi_color(value: Any, fallback: str) -> str:
    text = str(value or "").strip()
    if text.startswith("#"):
        return text
    return DELPHI_COLOR_MAP.get(text.lower(), fallback)


def normalized_delphi_font(value: Any) -> tuple[str, int, bool, bool, bool, bool]:
    font = parse_hiasm_font(value)
    return (
        font.name, font.size, font.bold, font.italic,
        font.underline, font.strikeout,
    )


DELPHI_RUNTIME_SOURCE = r'''
DELPHI_COLOR_MAP = {
    "clblack": "#000000", "clmaroon": "#800000", "clgreen": "#008000",
    "clred": "#FF0000", "clblue": "#0000FF", "clwhite": "#FFFFFF",
    "clgray": "#808080", "clsilver": "#C0C0C0", "clyellow": "#FFFF00",
    "clwindow": "#FFFFFF", "clbtnface": "#F0F0F0",
    "clhighlight": "#0078D7", "clmedgray": "#A0A0A0",
    "clskyblue": "#87CEEB",
}


def delphi_color(value, fallback):
    text = str(value or "").strip()
    return text if text.startswith("#") else DELPHI_COLOR_MAP.get(
        text.lower(), fallback
    )

def delphi_font_parts(value):
    """Read HiAsm TFontRec: Name,Size,Style,Color,CharSet."""
    text = str(value or "").strip()
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]
    parts = [part.strip() for part in text.split(",")] if text else []
    name = parts[0] if parts and parts[0] else "Arial"
    try:
        size = max(1, int(float(parts[1]))) if len(parts) > 1 else 8
    except (TypeError, ValueError):
        size = 8
    try:
        style = max(0, min(15, int(float(parts[2])))) if len(parts) > 2 else 0
    except (TypeError, ValueError):
        style = 0
    color = parts[3] if len(parts) > 3 and parts[3] else "0"
    charset = parts[4] if len(parts) > 4 and parts[4] else "1"
    return name, size, style, color, charset


def delphi_qfont(value):
    name, size, style, _color, _charset = delphi_font_parts(value)
    font = QFont(name, size)
    font.setBold(bool(style & 1))
    font.setItalic(bool(style & 2))
    font.setUnderline(bool(style & 4))
    font.setStrikeOut(bool(style & 8))
    return font


def apply_delphi_font(widget, value):
    _name, _size, _style, color, _charset = delphi_font_parts(value)
    font = delphi_qfont(value)
    widget.setFont(font)
    palette = widget.palette()
    qt_color = QColor(delphi_color(color, "#000000"))
    for role in (
        QPalette.ColorRole.WindowText,
        QPalette.ColorRole.Text,
        QPalette.ColorRole.ButtonText,
    ):
        palette.setColor(role, qt_color)
    widget.setPalette(palette)


class DelphiCompatibilityRuntime:
    """Executable fallback for imported HiAsm/Delphi components."""

    def __init__(self, type_name, properties, outputs, events):
        self.type_name = type_name
        self.properties = dict(properties)
        self.initial = dict(properties)
        self.outputs = {name: None for name in outputs}
        self.events = list(events)
        self.counter = int(self.properties.get("Start", 0) or 0)

    def get(self, name):
        if name in self.outputs and self.outputs[name] is not None:
            return self.outputs[name]
        return self.properties.get(name)

    def _value(self, inputs, *names, default=None):
        for name in names:
            if name in inputs and inputs[name] is not None:
                return inputs[name]
            if name in self.properties:
                return self.properties[name]
        return default

    def _finish(self, preferred=()):
        for name in preferred:
            if name in self.events:
                return [name]
        for name in ("onResult", "onSuccess", "onDone", "onEvent",
                     "onData", "onChange", "onEnd", "onMessage"):
            if name in self.events:
                return [name]
        return self.events[:1]

    def invoke(self, action, inputs):
        self.properties.update(
            {key: value for key, value in inputs.items() if value is not None}
        )
        component = self.type_name.lower()
        stem = action[2:] if action.startswith("do") else action
        try:
            # Shared THIWin/WinControl behavior. These methods are inherited by
            # Button, Label, Edit, GroupBox, Panel and the other visual controls.
            # A setter must not emit an arbitrary first event: Qt signals (or an
            # explicitly named HiAsm event) are responsible for continuation.
            if action in {
                "doSetFocus", "doSendToBack", "doBringToFront",
                "doCenterPos", "doSelectAll", "doClick",
            }:
                return []

            if action in {"doCaption", "doText", "doText2", "doString"}:
                value = self._value(
                    inputs, stem, "Caption", "Text", "String", "Data",
                    default="",
                )
                key = "Caption" if action == "doCaption" else "Text"
                self.properties[key] = value
                for name in (key, "Caption", "Text", "String"):
                    if name in self.outputs:
                        self.outputs[name] = value
                return []

            if action in {
                "doEnabled", "doEnable", "doDisable", "doVisible",
                "doReadOnly", "doPassword", "doMaxLenField",
                "doPosition", "doSelectLength", "doSelectText",
            }:
                value = self._value(inputs, stem, "Data", "Value", default=None)
                self.properties[stem] = value
                return []

            if action in {"doShow", "doHide"}:
                return self._finish(("onShow",)) if action == "doShow" else self._finish(("onHide",))

            if action in {"doClear", "doReset"}:
                self.properties = dict(self.initial)
                self.outputs = {key: None for key in self.outputs}
                self.counter = int(self.properties.get("Start", 0) or 0)
                return self._finish(("onClear", "onReset"))

            if component == "math":
                left = self._value(inputs, "Op1", default=0)
                right = self._value(inputs, "Op2", default=0)
                operator = str(self.properties.get("OpType", "+"))
                operations = {
                    "+": lambda: left + right, "-": lambda: left - right,
                    "*": lambda: left * right, "/": lambda: left / right,
                    "div": lambda: int(left) // int(right),
                    "mod": lambda: int(left) % int(right),
                    "and": lambda: int(left) & int(right),
                    "or": lambda: int(left) | int(right),
                    "xor": lambda: int(left) ^ int(right),
                    "shl": lambda: int(left) << int(right),
                    "shr": lambda: int(left) >> int(right),
                    "x^y": lambda: left ** right,
                    "min": lambda: min(left, right),
                    "max": lambda: max(left, right),
                }
                result = operations.get(operator, lambda: left)()
                self.outputs["Result"] = result
                return self._finish(("onResult",))

            if component == "hub":
                return list(self.events)

            if component == "font" and action == "doFont":
                current = delphi_font_parts(
                    self.properties.get("Font", "Arial,8,0,0,1")
                )
                name = self._value(inputs, "Name", default=current[0])
                size = self._value(inputs, "Size", default=current[1])
                style = self._value(inputs, "Style", default=current[2])
                color = self._value(inputs, "Color", default=current[3])
                charset = self._value(inputs, "CharSet", default=current[4])
                try:
                    size = max(1, int(float(size)))
                except (TypeError, ValueError):
                    size = current[1]
                try:
                    style = max(0, min(15, int(float(style))))
                except (TypeError, ValueError):
                    style = current[2]
                value = f"{name},{size},{style},{color},{charset}"
                self.properties["Font"] = value
                self.outputs.update({
                    "FontName": str(name),
                    "FontColor": color,
                    "FontSize": size,
                    "FontStyle": style,
                    "FontStrStyle": "".join(
                        letter for bit, letter in (
                            (1, "b"), (2, "i"), (4, "u"), (8, "s")
                        ) if style & bit
                    ),
                    "FontCharSet": charset,
                })
                return self._finish(("onFont",))

            if component in {"if_else", "ifelse", "compare", "between"}:
                left = self._value(inputs, "Op1", "Value", "Data", default=0)
                right = self._value(inputs, "Op2", "Value2", default=0)
                operator = str(
                    self.properties.get(
                        "Type", self.properties.get("OpType", "==")
                    )
                ).lower()
                if operator in {"=", "=="}:
                    matched = left == right
                elif operator in {"<>", "!="}:
                    matched = left != right
                elif operator == ">":
                    matched = left > right
                elif operator == "<":
                    matched = left < right
                elif operator == ">=":
                    matched = left >= right
                elif operator == "<=":
                    matched = left <= right
                else:
                    matched = bool(left)
                preferred = (
                    ("onTrue", "onYes", "onEqual")
                    if matched
                    else ("onFalse", "onNo", "onNotEqual")
                )
                return self._finish(preferred)

            if component in {"memory", "dodata"}:
                value = self._value(inputs, "Data", "Value", default=None)
                self.outputs["Value"] = value
                self.outputs["Data"] = value
                self.properties["Value"] = value
                return self._finish(("onData", "onResult"))

            if component in {"counter", "index_to_chanel"}:
                step = int(self.properties.get("Step", 1) or 1)
                self.counter += step
                self.outputs["Count"] = self.counter
                self.outputs["Value"] = self.counter
                return self._finish(("onNext", "onResult", "onValue"))

            if component == "random":
                low = int(self._value(inputs, "Min", "Minimum", default=0))
                high = int(self._value(inputs, "Max", "Maximum", default=100))
                value = random.randint(low, high)
                self.outputs["Random"] = value
                self.outputs["Result"] = value
                return self._finish(("onRandom", "onResult"))

            if component in {"strcat", "stringbuilder"}:
                left = str(self._value(inputs, "Str1", "Data1", default=""))
                right = str(self._value(inputs, "Str2", "Data2", default=""))
                value = left + right
                self.outputs["Result"] = value
                self.outputs["Text"] = value
                return self._finish(("onStrCat", "onResult"))

            if component in {"length", "strlen"}:
                value = str(self._value(inputs, "String", "Text", "Data", default=""))
                self.outputs["Result"] = len(value)
                self.outputs["Length"] = len(value)
                return self._finish(("onLength", "onResult"))

            if component in {"replace", "strreplace"}:
                text = str(self._value(inputs, "Text", "String", default=""))
                old = str(self._value(inputs, "SubStr", "Search", default=""))
                new = str(self._value(inputs, "Dest", "Replace", default=""))
                value = text.replace(old, new)
                self.outputs["Result"] = value
                self.outputs["Text"] = value
                return self._finish(("onReplace", "onResult"))

            if component in {"tostring", "inttostr", "realtostr"}:
                value = str(self._value(inputs, "Data", "Value", default=""))
                self.outputs["Result"] = value
                self.outputs["String"] = value
                return self._finish(("onResult",))

            if component in {"tointeger", "strtoint"}:
                value = int(float(self._value(inputs, "Data", "String", default=0)))
                self.outputs["Result"] = value
                self.outputs["Number"] = value
                return self._finish(("onResult",))

            if component in {"arraycount", "arraysize"}:
                value = self._value(inputs, "Array", "Data", default=[])
                self.outputs["Count"] = len(value)
                self.outputs["Size"] = len(value)
                self.outputs["Result"] = len(value)
                return self._finish(("onResult", "onCount"))

            if component == "arraysum":
                value = self._value(inputs, "Array", "Data", default=[])
                result = sum(value)
                self.outputs["Sum"] = result
                self.outputs["Result"] = result
                return self._finish(("onResult", "onSum"))

            if component == "arraysort":
                value = self._value(inputs, "Array", "Data", default=[])
                result = sorted(value)
                self.outputs["Array"] = result
                self.outputs["Result"] = result
                return self._finish(("onResult", "onSort"))

            if component in {"filepart", "filetools"}:
                value = Path(str(self._value(inputs, "FileName", "Path", default="")))
                self.outputs.update({
                    "Name": value.name, "Path": str(value.parent),
                    "Ext": value.suffix, "FileName": str(value),
                })
                return self._finish(("onResult",))

            if component in {"fileread", "datafromfile"}:
                path = Path(str(self._value(inputs, "FileName", "Path", default="")))
                value = path.read_text(encoding=str(self.properties.get("Charset", "utf-8")))
                self.outputs["Text"] = value
                self.outputs["Data"] = value
                return self._finish(("onRead", "onSuccess"))

            if component in {"filewrite", "datatofile"}:
                path = Path(str(self._value(inputs, "FileName", "Path", default="")))
                value = str(self._value(inputs, "Text", "Data", default=""))
                path.write_text(value, encoding=str(self.properties.get("Charset", "utf-8")))
                return self._finish(("onWrite", "onSuccess"))

            # Generic HiAsm convention: doX consumes X/Data/Value and exposes
            # the value through outputs with the same or common result names.
            value = self._value(
                inputs, stem, "Data", "Value", "Text", "String", default=None
            )
            if value is not None:
                self.properties[stem] = value
                for name in (stem, "Result", "Value"):
                    if name in self.outputs:
                        self.outputs[name] = value
            return self._finish((f"on{stem}",))
        except Exception as exc:
            self.outputs["Error"] = str(exc)
            if "onError" in self.events:
                return ["onError"]
            return []


def apply_delphi_widget_action(widget, action, runtime, inputs):
    """Synchronize the compatibility state with a real Qt widget."""
    lower = action.lower()
    stem = action[2:] if action.startswith("do") else action
    value = next(
        (inputs[name] for name in (stem, "Caption", "Text", "String", "Data", "Value")
         if name in inputs and inputs[name] is not None),
        runtime.get(stem),
    )
    if lower == "dofont" and value is not None:
        apply_delphi_font(widget, value)
        return
    if lower == "dosetfocus":
        widget.setFocus()
        return
    if lower == "dobringtofront":
        widget.raise_()
        return
    if lower == "dosendtoback":
        widget.lower()
        return
    if lower == "docenterpos" and widget.parentWidget() is not None:
        parent = widget.parentWidget().rect()
        widget.move(
            max(0, (parent.width() - widget.width()) // 2),
            max(0, (parent.height() - widget.height()) // 2),
        )
        return
    if lower == "doclick" and hasattr(widget, "click"):
        widget.click()
        return
    if lower == "doselectall" and hasattr(widget, "selectAll"):
        widget.selectAll()
        return
    if lower == "doreadonly" and hasattr(widget, "setReadOnly"):
        widget.setReadOnly(bool(value))
        return
    if lower == "domaxlenfield" and hasattr(widget, "setMaxLength"):
        widget.setMaxLength(max(0, int(value or 0)))
        return
    if lower == "dopassword" and hasattr(widget, "setEchoMode"):
        widget.setEchoMode(
            QLineEdit.EchoMode.Password if bool(value)
            else QLineEdit.EchoMode.Normal
        )
        return
    if lower == "doposition" and hasattr(widget, "setCursorPosition"):
        widget.setCursorPosition(max(0, int(value or 0)))
        return
    if lower == "doselectlength" and hasattr(widget, "setSelection"):
        widget.setSelection(widget.cursorPosition(), max(0, int(value or 0)))
        return
    if "show" in lower:
        widget.show()
    elif "hide" in lower:
        widget.hide()
    elif "enable" in lower:
        widget.setEnabled(True if value is None else bool(value))
    elif "disable" in lower:
        widget.setEnabled(False)
    elif "visible" in lower:
        widget.setVisible(True if value is None else bool(value))
    elif "clear" in lower and hasattr(widget, "clear"):
        widget.clear()

    if any(token in lower for token in ("text", "caption", "string")):
        if value is not None:
            if hasattr(widget, "setText"):
                widget.setText(str(value))
            elif hasattr(widget, "setPlainText"):
                widget.setPlainText(str(value))
            elif hasattr(widget, "setTitle"):
                widget.setTitle(str(value))

    if any(token in lower for token in ("value", "position", "check")):
        if value is not None:
            if hasattr(widget, "setValue"):
                widget.setValue(int(float(value)))
            elif hasattr(widget, "display"):
                widget.display(float(value))
            elif hasattr(widget, "setChecked"):
                widget.setChecked(bool(value))

    if "led" in runtime.type_name.lower():
        if "off" in lower:
            state = False
        elif "on" in lower:
            state = True
        elif "toggle" in lower:
            state = not bool(widget.property("ledState"))
        else:
            state = bool(value)
        widget.setProperty("ledState", state)
        radius = max(4, min(widget.width(), widget.height()) // 2)
        color = delphi_color(
            runtime.properties.get("ColorOn" if state else "ColorOff"),
            "#33D05A" if state else "#59615B",
        )
        widget.setStyleSheet(
            f"background:{color}; border:1px solid #303532;"
            f"border-radius:{radius}px;"
        )
'''


def py_string(value: Any) -> str:
    return repr(str(value))


def safe_name(value: str, fallback: str) -> str:
    result = re.sub(r"\W+", "_", value.strip(), flags=re.UNICODE)
    if not result or result[0].isdigit() or keyword.iskeyword(result):
        result = re.sub(r"\W+", "_", fallback.strip(), flags=re.UNICODE)
    if not result or result[0].isdigit() or keyword.iskeyword(result):
        result = "component"
    return result


def python_literal(value: Any) -> str:
    if not isinstance(value, str):
        return repr(value)
    stripped = value.strip()
    lowered = stripped.lower()
    if lowered in {"true", "false"}:
        return "True" if lowered == "true" else "False"
    if lowered in {"none", "null"}:
        return "None"
    try:
        int(stripped)
        return stripped
    except ValueError:
        try:
            float(stripped)
            return stripped
        except ValueError:
            return repr(value)


def expand_user_containers(project: dict[str, Any]) -> dict[str, Any]:
    project=json.loads(json.dumps(project,ensure_ascii=False))
    for _ in range(17):
        nodes=list(project.get("nodes",[])); links=list(project.get("connections",[]))
        container=next((n for n in nodes if n.get("type")=="UserContainer"),None)
        if container is None:return project
        cid=str(container.get("id")); props=container.get("properties",{}); inner=props.get("subgraph",{})
        if isinstance(inner,str):
            try:inner=json.loads(inner)
            except Exception:inner={}
        inner_nodes=list(inner.get("nodes",[])) if isinstance(inner,dict) else []
        inner_links=list(inner.get("connections",[])) if isinstance(inner,dict) else []
        inner_helpers=list(inner.get("helpers",[])) if isinstance(inner,dict) else []
        proxy_types={"ContainerEventInput","ContainerDataInput","ContainerEventOutput","ContainerDataOutput"}
        proxies={str(n.get("id")):n for n in inner_nodes if n.get("type") in proxy_types}; normal=[n for n in inner_nodes if str(n.get("id")) not in proxies]
        ids={str(n.get("id")):cid+"__"+str(n.get("id")) for n in normal}; interface=props.get("interface",[]) if isinstance(props.get("interface",[]),list) else []; by_port={str(i.get("port")):i for i in interface if isinstance(i,dict)}
        kept=[e for e in links if e.get("to_node")!=cid and e.get("from_node")!=cid]; incoming=[e for e in links if e.get("to_node")==cid]; outgoing=[e for e in links if e.get("from_node")==cid]
        normal_links=[]; p_to_n={}; n_to_p={}
        for e in inner_links:
            a,b=str(e.get("from_node")),str(e.get("to_node"))
            if a in ids and b in ids:
                x=dict(e);x["from_node"]=ids[a];x["to_node"]=ids[b];normal_links.append(x)
            elif a in proxies and b in ids:p_to_n.setdefault(a,[]).append((ids[b],str(e.get("to_port"))))
            elif a in ids and b in proxies:n_to_p.setdefault(b,[]).append((ids[a],str(e.get("from_port"))))
        bridge=[]
        for e in incoming:
            pid=str(by_port.get(str(e.get("to_port")),{}).get("proxy_id",""))
            for target,port in p_to_n.get(pid,[]):x=dict(e);x["to_node"]=target;x["to_port"]=port;bridge.append(x)
        for e in outgoing:
            pid=str(by_port.get(str(e.get("from_port")),{}).get("proxy_id",""))
            for source,port in n_to_p.get(pid,[]):x=dict(e);x["from_node"]=source;x["from_port"]=port;bridge.append(x)
        expanded=[]
        for n in normal:
            x=dict(n);x["id"]=ids[str(n.get("id"))];x["x"]=float(container.get("x",0))+float(n.get("x",0));x["y"]=float(container.get("y",0))+float(n.get("y",0));expanded.append(x)
        expanded_helpers=[]
        for helper in inner_helpers:
            if not isinstance(helper, dict):
                continue
            h=dict(helper)
            h["x"]=float(container.get("x", 0))+float(helper.get("x", 0))
            h["y"]=float(container.get("y", 0))+float(helper.get("y", 0))
            expanded_helpers.append(h)
        project["nodes"]=[n for n in nodes if n.get("id")!=cid]+expanded
        project["connections"]=kept+normal_links+bridge
        project["helpers"]=list(project.get("helpers", []))+expanded_helpers
    raise ValueError("Превышена глубина вложенности контейнеров (16).")


def generate_python(project: dict[str, Any]) -> str:
    project = expand_user_containers(project)
    repair_mdi_parentage(project)
    nodes = project.get("nodes", [])
    connections = project.get("connections", [])
    by_id = {node["id"]: node for node in nodes}
    form = next((node for node in nodes if node["type"] == "Form"), None)
    form_props = (form or {}).get("properties", {})

    def property_lookup(
        properties: dict[str, Any], *names: str, default: Any = None
    ) -> Any:
        lowered = {
            str(key).lower(): value for key, value in properties.items()
        }
        for name in names:
            if name in properties:
                return properties[name]
            if name.lower() in lowered:
                return lowered[name.lower()]
        return default

    names: dict[str, str] = {}
    used_names: set[str] = set()
    for node in nodes:
        props = node.get("properties", {})
        configured_name = props.get("name", props.get("Name"))
        base = safe_name(
            str(configured_name or node["type"].lower()),
            node["type"].lower(),
        )
        candidate = base
        number = 2
        while candidate in used_names:
            candidate = f"{base}_{number}"
            number += 1
        used_names.add(candidate)
        names[node["id"]] = candidate

    event_connections: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    data_connections: dict[tuple[str, str], dict[str, Any]] = {}
    for connection in connections:
        source = by_id.get(connection["from_node"])
        if source is None:
            continue
        from_port = connection["from_port"]
        source_spec = COMPONENTS.get(source["type"])
        source_ports = (
            effective_ports(source["type"], source.get("properties", {}))
            if source_spec else ()
        )
        port_kind = next(
            (
                port.kind
                for port in source_ports
                if port.name == from_port
            ),
            "",
        ) if source_spec else ""
        if port_kind == "event_out":
            event_connections[(connection["from_node"], from_port)].append(connection)
        else:
            data_connections[(connection["to_node"], connection["to_port"])] = connection

    def attribute(node_id: str, prefix: str = "") -> str:
        name = names[node_id]
        return f"self._{prefix}{name}" if prefix else f"self.{name}"

    def source_expression(node: dict[str, Any], port: str) -> str:
        node_type, node_id = node["type"], node["id"]
        ref = attribute(node_id)
        if node_type.startswith("Delphi::"):
            return f"{attribute(node_id, 'delphi_')}.get({port!r})"
        if node_type.startswith("Python::"):
            return f"self.{method_token(node_id, 'value', 'py')}().get({port!r})"
        if node_type == "GridCanvas":
            return {
                "Column": f"{ref}.currentColumn()",
                "Row": f"{ref}.currentRow()",
                "CellValue": f"{ref}.currentValue()",
                "CurrentGrid": f"{ref}.grid()",
                "ColumnCount": f"{ref}.columnCount()",
                "RowCount": f"{ref}.rowCount()",
            }.get(port, "None")
        if node_type == "GridBatchWriter":
            return {
                "CurrentGrid": attribute(node_id, "grid_batch_"),
                "ChangedCells": attribute(node_id, "grid_batch_changed_"),
                "Error": attribute(node_id, "grid_batch_error_"),
            }.get(port, "None")
        if node_type in {"ForRange", "ForEach", "WhileLoop"}:
            if port == "Index": return attribute(node_id, "loop_index_")
            if port == "Item": return attribute(node_id, "loop_item_")
            if port == "LimitReached": return attribute(node_id, "loop_limit_")
        if node_type == "EventGate" and port == "IsOpen": return attribute(node_id, "gate_")
        if node_type == "Once" and port == "HasFired": return attribute(node_id, "once_")
        if node_type == "DictStore":
            d=attribute(node_id,"dict_"); key=input_expression(node,"Key","")
            return {"Dictionary":d,"Item":f"{d}.get({key})","Keys":f"list({d}.keys())","Values":f"list({d}.values())","Count":f"len({d})","ContainsKey":f"({key} in {d})"}.get(port,"None")
        if node_type == "ConvertValue": return attribute(node_id,"convert_" if port=="Result" else "convert_error_")
        if node_type == "Geometry2D": return attribute(node_id,{"Result":"geometry_result_","Distance":"geometry_distance_","X":"geometry_x_","Y":"geometry_y_"}.get(port,"geometry_result_"))
        if node_type == "MouseInput": return attribute(node_id,{"X":"mouse_x_","Y":"mouse_y_","Button":"mouse_button_"}.get(port,"mouse_x_"))
        if node_type == "RepeatLoop" and port == "Index":
            return attribute(node_id, "loop_index_")
        if node_type == "ListStore":
            if port == "Items": return attribute(node_id, "list_")
            if port == "Count": return f"len({attribute(node_id, 'list_')})"
            if port == "Item": return attribute(node_id, "list_item_")
        if node_type == "GridState":
            col = input_expression(node, "Column", 0, True)
            row = input_expression(node, "Row", 0, True)
            if port == "Grid": return attribute(node_id, "grid_")
            if port == "RowsJson": return f"json.dumps({attribute(node_id, 'grid_')}, ensure_ascii=False)"
            if port == "ClearedLines": return attribute(node_id, "cleared_lines_")
            if port == "Cell": return f"self._grid_cell({attribute(node_id, 'grid_')}, int({col}), int({row}))"
        if node_type == "KeyboardInput":
            if port == "Key": return attribute(node_id, "key_")
            if port == "IsAutoRepeat": return attribute(node_id, "key_repeat_")
        if node_type == "TetrisGame":
            values = {"Score": "score", "Lines": "lines", "Level": "level", "IsPaused": "paused", "IsGameOver": "over"}
            if port in values: return f"{ref}.board.{values[port]}"
        if node_type == "TwoWayBinding" and port == "CurrentValue":
            return attribute(node_id, "binding_value_")
        if node_type == "DataHub" and port.startswith("DataOut"):
            suffix = port[len("DataOut"):] or "1"
            wanted = f"DataIn{suffix}"
            available = {p.name for p in effective_ports(node_type, node.get("properties", {}))}
            return input_expression(node, wanted if wanted in available else "DataIn1", "")
        mappings = {
            ("LineEdit", "Text"): f"{ref}.text()",
            ("TextEdit", "Text"): f"{ref}.toPlainText()",
            ("ComboBox", "Text"): f"{ref}.currentText()",
            ("ComboBox", "CurrentIndex"): f"{ref}.currentIndex()",
            ("ListWidget", "Text"): f"({ref}.currentItem().text() if {ref}.currentItem() else '')",
            ("ListWidget", "CurrentIndex"): f"{ref}.currentRow()",
            ("Slider", "Value"): f"{ref}.value()",
            ("SpinBox", "Value"): f"{ref}.value()",
            ("CheckBox", "Checked"): f"{ref}.isChecked()",
            ("Button", "Caption"): f"{ref}.text()",
            ("Label", "Caption"): f"{ref}.text()",
            ("Memory", "Value"): attribute(node_id, "memory_"),
            ("Math", "Result"): attribute(node_id, "result_"),
            ("FormatStr", "Result"): attribute(node_id, "result_"),
            ("FileRead", "Text"): attribute(node_id, "text_"),
            ("FileRead", "Error"): attribute(node_id, "error_"),
            ("FileWrite", "Error"): attribute(node_id, "error_"),
            ("Counter", "Value"): attribute(node_id, "counter_"),
            ("Random", "Result"): attribute(node_id, "result_"),
            ("OpenFileDialog", "FileName"): attribute(node_id, "filename_"),
            ("SaveFileDialog", "FileName"): attribute(node_id, "filename_"),
            ("HTTPGet", "Text"): attribute(node_id, "text_"),
            ("HTTPGet", "Status"): attribute(node_id, "status_"),
            ("HTTPGet", "Error"): attribute(node_id, "error_"),
            ("RunProcess", "Output"): attribute(node_id, "output_"),
            ("RunProcess", "ExitCode"): attribute(node_id, "exitcode_"),
            ("RunProcess", "Error"): attribute(node_id, "error_"),
            ("TableWidget", "CellText"): f"({ref}.currentItem().text() if {ref}.currentItem() else '')",
            ("TableWidget", "CurrentRow"): f"{ref}.currentRow()",
            ("TableWidget", "CurrentColumn"): f"{ref}.currentColumn()",
            ("TreeWidget", "Text"): f"({ref}.currentItem().text(0) if {ref}.currentItem() else '')",
            ("DateEdit", "Text"): f"{ref}.date().toString('yyyy-MM-dd')",
            ("Calendar", "Text"): f"{ref}.selectedDate().toString('yyyy-MM-dd')",
            ("JSONParse", "Value"): attribute(node_id, "value_"),
            ("JSONParse", "Error"): attribute(node_id, "error_"),
            ("JSONStringify", "Text"): attribute(node_id, "text_"),
            ("SQLiteQuery", "Rows"): attribute(node_id, "rows_"),
            ("SQLiteQuery", "Error"): attribute(node_id, "error_"),
            ("Clipboard", "Value"): attribute(node_id, "clipboard_"),
            ("MessageBox", "Result"): attribute(node_id, "message_result_"),
            ("RadioButton", "Checked"): f"{ref}.isChecked()", ("GroupBox", "Checked"): f"{ref}.isChecked()",
            ("Dial", "Value"): f"{ref}.value()", ("ToolButton", "Caption"): f"{ref}.text()",
            ("PlainTextEdit", "Text"): f"{ref}.toPlainText()",
            ("DoubleSpinBox", "Value"): f"{ref}.value()",
            ("ScrollBar", "Value"): f"{ref}.value()",
            ("TimeEdit", "Text"): f"{ref}.time().toString('HH:mm:ss')",
            ("DateTimeEdit", "Text"): f"{ref}.dateTime().toString(Qt.DateFormat.ISODate)",
            ("TextBrowser", "Text"): f"{ref}.toPlainText()",
            ("FontComboBox", "CurrentFamily"): f"{ref}.currentFont().family()",
            ("KeySequenceEdit", "CurrentSequence"): f"{ref}.keySequence().toString()",
            ("CommandLinkButton", "Caption"): f"{ref}.text()",
            ("Form", "CurrentTitle"): "self.windowTitle()", ("Form", "CurrentWidth"): "self.width()", ("Form", "CurrentHeight"): "self.height()",
        }
        if node_type in {"Gauge","Speedometer","Tachometer","Thermometer","LevelMeter","LEDIndicator","Compass","BatteryIndicator","SignalIndicator","Sparkline","AnalogClock","Knob","LineChart","BarChart","PieChart","RadarChart","Oscilloscope","VUMeter","SevenSegmentDisplay","LEDMatrix","XYPlot","HeatMap","Timeline","WaterfallChart","GeoMap","Waveform","SpectrumAnalyzer","MultiSegmentDisplay","CustomInstrument"}:
            if port == "Value": return f"{ref}.value()"
            if port == "IsAlarm": return f"{ref}.isAlarm()"
        if node_type == "XYPlot":
            if port == "LastX": return f"{ref}.xValue()"
            if port == "LastY": return f"{ref}.yValue()"
        if node_type == "GeoMap":
            if port == "CurrentLatitude": return f"{ref}.latitude"
            if port == "CurrentLongitude": return f"{ref}.longitude"
        if node_type in {"XYPlot","HeatMap","Timeline","WaterfallChart","GeoMap","Waveform","SpectrumAnalyzer","MultiSegmentDisplay","CustomInstrument"} and port == "SeriesCount": return f"{ref}.seriesCount()"
        if node_type == "DashboardCanvas":
            if port == "SceneJson": return f"{ref}.sceneJson()"
            if port == "ItemCount": return f"{ref}.itemCount()"
        if node_type in visual_types:
            common = {"CurrentX": f"{ref}.x()", "CurrentY": f"{ref}.y()", "CurrentWidth": f"{ref}.width()", "CurrentHeight": f"{ref}.height()", "IsVisible": f"{ref}.isVisible()", "IsEnabled": f"{ref}.isEnabled()"}
            if port in common: return common[port]
        return mappings.get((node_type, port), "None")

    def input_expression(
        node: dict[str, Any],
        port: str,
        fallback: Any = "",
        raw_fallback: bool = False,
    ) -> str:
        connection = data_connections.get((node["id"], port))
        if connection:
            source = by_id.get(connection["from_node"])
            if source:
                expression = source_expression(source, connection["from_port"])
                probe = connection.get("probe")
                breakpoint = bool(connection.get("breakpoint"))
                if breakpoint or isinstance(probe, dict):
                    label = (
                        str(probe.get("name", "")).strip()
                        if isinstance(probe, dict) else ""
                    ) or (
                        f"breakpoint:{connection['from_node']}:{connection['from_port']}"
                        f"→{connection['to_node']}:{connection['to_port']}"
                    )
                    return (
                        f"_vpb_trace({label!r}, {expression}, "
                        f"{connection['from_node']!r}, "
                        f"{connection['from_port']!r}, {breakpoint!r})"
                    )
                label = (
                    f"flow:{connection['from_node']}:{connection['from_port']}"
                    f"→{connection['to_node']}:{connection['to_port']}"
                )
                return (
                    f"_vpb_flow({label!r}, {expression}, "
                    f"{connection['from_node']!r}, {connection['from_port']!r})"
                )
        return str(fallback) if raw_fallback else python_literal(fallback)

    def method_token(node_id: str, port: str, prefix: str) -> str:
        return f"_{prefix}_{names[node_id]}_{re.sub(r'\\W+', '_', port)}"

    def action_method(node_id: str, port: str) -> str:
        return method_token(node_id, port, "act")

    def event_method(node_id: str, port: str) -> str:
        return method_token(node_id, port, "evt")

    def dispatch_lines(
        node_id: str, event_port: str, indent: str = "        ",
        argument: str | None = None,
    ) -> list[str]:
        suffix = argument if argument is not None else ""
        result = []
        for connection in event_connections.get((node_id, event_port), []):
            probe = connection.get("probe")
            breakpoint = bool(connection.get("breakpoint"))
            if breakpoint or isinstance(probe, dict):
                label = (
                    str(probe.get("name", "")).strip()
                    if isinstance(probe, dict) else ""
                ) or (
                    f"breakpoint:{node_id}:{event_port}"
                    f"→{connection['to_node']}:{connection['to_port']}"
                )
                value = suffix or "None"
                result.append(
                    f"{indent}_vpb_trace({label!r}, {value}, "
                    f"{node_id!r}, {event_port!r}, "
                    f"{breakpoint!r})"
                )
            else:
                label = (
                    f"flow:{node_id}:{event_port}"
                    f"→{connection['to_node']}:{connection['to_port']}"
                )
                result.append(
                    f"{indent}_vpb_flow({label!r}, {suffix or 'None'}, "
                    f"{node_id!r}, {event_port!r})"
                )
            result.append(
                f"{indent}self.{action_method(connection['to_node'], connection['to_port'])}({suffix})"
            )
        return result

    visual_types = {
        "Button", "Label", "LineEdit", "TextEdit", "CheckBox", "ComboBox",
        "ListWidget", "ProgressBar", "Slider", "SpinBox",
        "TableWidget", "TableView", "TreeWidget", "DateEdit", "Calendar", "LCDNumber",
        "RadioButton", "GroupBox", "Dial", "ToolButton", "PlainTextEdit",
        "DoubleSpinBox", "ScrollBar", "TimeEdit", "DateTimeEdit", "TextBrowser",
        "FontComboBox", "KeySequenceEdit", "CommandLinkButton", "DialogButtonBox", "Frame", "HorizontalLine",
        "Gauge", "Speedometer", "Tachometer", "Thermometer", "LevelMeter", "LEDIndicator",
        "Compass", "BatteryIndicator", "SignalIndicator", "Sparkline", "AnalogClock", "Knob",
        "LineChart", "BarChart", "PieChart", "RadarChart", "Oscilloscope", "VUMeter", "SevenSegmentDisplay", "LEDMatrix",
        "XYPlot", "HeatMap", "Timeline", "WaterfallChart", "GeoMap", "Waveform", "SpectrumAnalyzer", "MultiSegmentDisplay", "CustomInstrument", "DashboardCanvas", "GridCanvas", "TetrisGame",
    }
    # Схема и окно используют одну геометрию. Старые проекты хранили
    # координаты нод в корне записи, а импортёр — в properties.
    visual_nodes = [
        node for node in nodes if node.get("type") in visual_types
    ]

    def _visual_coordinate(node, key, default=0):
        props = node.get("properties", {})
        value = props.get(key)
        if value is None:
            value = node.get(key, default)
        try:
            return float(value)
        except (TypeError, ValueError):
            return float(default)

    visual_geometry = []
    for visual_node in visual_nodes:
        visual_props = visual_node.get("properties", {})
        visual_geometry.append(
            (
                visual_node,
                _visual_coordinate(visual_node, "x"),
                _visual_coordinate(visual_node, "y"),
                max(1, int(_visual_coordinate(visual_node, "width", 120))),
                max(1, int(_visual_coordinate(visual_node, "height", 32))),
                "x" in visual_props and "y" in visual_props,
            )
        )
    all_visual_coordinates_explicit = bool(visual_geometry) and all(
        entry[5] for entry in visual_geometry
    )
    min_visual_x = min((entry[1] for entry in visual_geometry), default=0.0)
    min_visual_y = min((entry[2] for entry in visual_geometry), default=0.0)
    visual_origin_x = (
        0.0 if all_visual_coordinates_explicit
        else max(0.0, 30.0 - min_visual_x)
    )
    visual_origin_y = (
        0.0 if all_visual_coordinates_explicit
        else max(0.0, 30.0 - min_visual_y)
    )
    visual_coordinates = {
        str(node["id"]): (
            int(round(x + visual_origin_x)),
            int(round(y + visual_origin_y)),
            width,
            height,
        )
        for node, x, y, width, height, _explicit in visual_geometry
    }
    content_width = max(
        int(form_props.get("width", 640)),
        max(
            (x + width + 30 for x, _y, width, _height in visual_coordinates.values()),
            default=640,
        ),
    )
    content_height = max(
        int(form_props.get("height", 420)),
        max(
            (y + height + 30 for _x, y, _width, height in visual_coordinates.values()),
            default=420,
        ),
    )
    viewport_width = int(form_props.get("viewport_width", min(content_width,1050)))
    viewport_height = int(form_props.get("viewport_height", min(content_height,650)))
    scrollable = bool(form_props.get("scrollable", True))
    lines = [
        '"""Создано в Visual Python Builder."""',
        "",
        "import json",
        "import math",
        "import os",
        "import random",
        "import sqlite3",
        "import shlex",
        "import subprocess",
        "import threading",
        "import time",
        "import sys",
        "import tempfile",
        "import traceback",
        "import urllib.request",
        "from pathlib import Path",
        "try:",
        "    from python_library.loader import discover as _discover_python_nodes",
        "    _PYTHON_NODE_SPECS, _PYTHON_NODE_ERRORS = _discover_python_nodes()",
        "except Exception:",
        "    _PYTHON_NODE_SPECS, _PYTHON_NODE_ERRORS = {}, []",
        "if hasattr(sys.stdout, 'reconfigure'):",
        "    sys.stdout.reconfigure(encoding='utf-8', line_buffering=True, write_through=True)",
        "if hasattr(sys.stderr, 'reconfigure'):",
        "    sys.stderr.reconfigure(encoding='utf-8', line_buffering=True, write_through=True)",
        "",
        "from PySide6.QtCore import QDate, QDateTime, QEvent, QPointF, QRectF, QSignalBlocker, QSize, QTime, Qt, QTimer, Signal",
        "from PySide6.QtGui import QAction, QBrush, QColor, QFont, QIcon, QKeySequence, QPainter, QPalette, QPen, QPolygonF",
        "from PySide6 import QtCore, QtGui, QtWidgets",
        "from PySide6.QtWidgets import (",
        "    QApplication, QCheckBox, QComboBox, QDial, QFileDialog, QFontDialog, QGroupBox, QLabel,",
        "    QLineEdit, QListWidget, QMainWindow, QMessageBox, QRadioButton,",
        "    QCalendarWidget, QDateEdit, QLCDNumber, QProgressBar, QPushButton,",
        "    QSlider, QSpinBox, QTableView, QTableWidget, QTableWidgetItem, QTextEdit,",
        "    QCommandLinkButton, QDateTimeEdit, QDoubleSpinBox, QFontComboBox, QFrame,",
        "    QKeySequenceEdit, QPlainTextEdit, QScrollArea, QScrollBar, QSizePolicy, QTextBrowser,",
        "    QTimeEdit, QToolButton, QTreeWidget, QTreeWidgetItem, QWidget, QGraphicsView,",
        "    QDialogButtonBox, QMdiArea, QMdiSubWindow,",
        ")",
        "",
        "_VPB_DEBUG_PREFIX = '__VPB_DEBUG__ '",
        "_VPB_DEBUG_ENABLED = os.environ.get('VPB_DEBUG_MODE', '0') == '1'",
        "_VPB_SYNC_FLOW = _VPB_DEBUG_ENABLED",
        "_VPB_WAIT_START = os.environ.get('VPB_DEBUG_WAIT_START', '0') == '1'",
        "_vpb_debug_condition = threading.Condition()",
        "_vpb_debug_release = False",
        "_vpb_start_released = not _VPB_WAIT_START",
        "",
        "def _vpb_safe_value(value):",
        "    try:",
        "        json.dumps(value, ensure_ascii=False, default=str)",
        "        return value",
        "    except Exception:",
        "        return repr(value)",
        "",
        "def _vpb_emit(kind, point, value=None, node_id='', port='', paused=False):",
        "    payload = {",
        "        'kind': kind, 'point': str(point),",
        "        'value': _vpb_safe_value(value),",
        "        'type': type(value).__name__,",
        "        'node_id': str(node_id), 'port': str(port),",
        "        'time': time.strftime('%H:%M:%S'), 'paused': bool(paused),",
        "    }",
        "    print(_VPB_DEBUG_PREFIX + json.dumps(payload, ensure_ascii=False, default=str), flush=True)",
        "",
        "def _vpb_command_reader():",
        "    global _vpb_debug_release, _vpb_start_released",
        "    try:",
        "        for raw in sys.stdin:",
        "            try:",
        "                command = json.loads(raw).get('cmd')",
        "            except Exception:",
        "                continue",
        "            if command == 'debug_start':",
        "                with _vpb_debug_condition:",
        "                    _vpb_start_released = True",
        "                    _vpb_debug_condition.notify_all()",
        "            elif command in {'continue', 'resume', 'stop', 'flow_ack'}:",
        "                with _vpb_debug_condition:",
        "                    _vpb_debug_release = True",
        "                    _vpb_debug_condition.notify_all()",
        "    finally:",
        "        with _vpb_debug_condition:",
        "            _vpb_debug_release = True",
        "            _vpb_debug_condition.notify_all()",
        "",
        "def _vpb_wait_start():",
        "    if not _VPB_WAIT_START:",
        "        return",
        "    with _vpb_debug_condition:",
        "        while not _vpb_start_released:",
        "            _vpb_debug_condition.wait(timeout=0.25)",
        "",
        "def _vpb_trace(point, value=None, node_id='', port='', breakpoint=False):",
        "    global _vpb_debug_release",
        "    if not _VPB_DEBUG_ENABLED:",
        "        return value",
        "    _vpb_emit('breakpoint' if breakpoint else 'probe', point, value, node_id, port, breakpoint)",
        "    if breakpoint:",
        "        with _vpb_debug_condition:",
        "            _vpb_debug_release = False",
        "            while not _vpb_debug_release:",
        "                _vpb_debug_condition.wait(timeout=0.25)",
        "            _vpb_debug_release = False",
        "    return value",
        "",
        "def _vpb_flow(point, value=None, node_id='', port=''):",
        "    if not _VPB_DEBUG_ENABLED:",
        "        return value",
        "    _vpb_emit('flow', point, value, node_id, port, False)",
        "    if _VPB_SYNC_FLOW:",
        "        global _vpb_debug_release",
        "        with _vpb_debug_condition:",
        "            _vpb_debug_release = False",
        "            while not _vpb_debug_release:",
        "                _vpb_debug_condition.wait(timeout=0.25)",
        "            _vpb_debug_release = False",
        "    return value",
        "",
        *(
            DELPHI_RUNTIME_SOURCE.strip().splitlines()
            if any(node.get("type", "").startswith("Delphi::") for node in nodes)
            else []
        ),
        "",
        *INSTRUMENT_RUNTIME_SOURCE.strip().splitlines(),
        "",
        *(TETRIS_WIDGET.strip().splitlines() if any(node.get("type") == "TetrisGame" for node in nodes) else []),
        "",
        "class ClickableLabel(QLabel):",
        "    clicked = Signal(object)",
        "",
        "    def mousePressEvent(self, event):",
        "        self.clicked.emit(None)",
        "        super().mousePressEvent(event)",
        "",
        "",
        "class MainWindow(QMainWindow):",
        "    def __init__(self):",
        "        super().__init__()",
        f"        self.setWindowTitle({py_string(form_props.get('title', 'Моя программа'))})",
        "        _screen = QApplication.primaryScreen().availableGeometry()",
        f"        self.resize(min({viewport_width}, max(480, int(_screen.width()*0.92))), min({viewport_height}, max(320, int(_screen.height()*0.86))))",
        f"        self.setEnabled({bool(form_props.get('enabled', True))!r})",
        f"        self.setWindowOpacity({float(form_props.get('opacity',1.0) or 1.0)!r})",
        f"        self.setMinimumSize(min({int(form_props.get('minimum_width',0) or 0)}, int(_screen.width()*0.8)), min({int(form_props.get('minimum_height',0) or 0)}, int(_screen.height()*0.75)))",
        f"        self.setMaximumSize({int(form_props.get('maximum_width',16777215) or 16777215)}, {int(form_props.get('maximum_height',16777215) or 16777215)})",
        f"        self.setToolTip({py_string(form_props.get('tool_tip',''))})",
        f"        self.setAccessibleName({py_string(form_props.get('accessible_name','Главное окно'))})",
        "        self.central = QWidget()",
    ]
    if scrollable:
        lines += [
            f"        self.central.setMinimumSize({content_width}, {content_height})",
            f"        self.central.resize({content_width}, {content_height})",
            "        self.content_scroll = QScrollArea(self)",
            "        self.content_scroll.setWidgetResizable(False)",
            "        self.content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)",
            "        self.content_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)",
            "        self.content_scroll.setWidget(self.central)",
            "        self.content_scroll.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)",
            "        self.setCentralWidget(self.content_scroll)",
        ]
    else:
        lines += [
            f"        self.central.resize({content_width}, {content_height})",
            "        self.setCentralWidget(self.central)",
        ]
    if not form_props.get("resizable", True):
        lines.append(
            "        self.setFixedSize(self.size())"
        )
    if form_props.get("always_on_top", False):
        lines.append(
            "        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)"
        )
    bg=str(form_props.get("background_color","#F4F8FF")); fg=str(form_props.get("text_color","#17243A")); bc=str(form_props.get("border_color","#477DC2")); bw=int(form_props.get("border_width",0) or 0); br=int(form_props.get("border_radius",0) or 0)
    qss=f"QMainWindow {{ background:{bg}; color:{fg}; border:{bw}px solid {bc}; border-radius:{br}px; }}"+str(form_props.get("style","") or "")
    lines.append(f"        self.setStyleSheet({py_string(qss)})")
    menu_data = form_props.get("menus", [])
    if isinstance(menu_data, str):
        try:
            menu_data = json.loads(menu_data or "[]")
        except (TypeError, ValueError, json.JSONDecodeError):
            menu_data = []
    if not isinstance(menu_data, list):
        menu_data = []
    if form_props.get("menu_bar") or menu_data:
        lines.append("        self.menuBar()")
    used_menu_attributes: set[str] = set()
    action_attributes: dict[str, str] = {}

    def unique_menu_attribute(prefix: str, raw_name: Any) -> str:
        base = safe_name(f"{prefix}_{raw_name}", prefix)
        result = base
        index = 2
        while result in used_menu_attributes:
            result = f"{base}_{index}"
            index += 1
        used_menu_attributes.add(result)
        return result

    def emit_menu(menu: dict[str, Any], parent_expression: str) -> None:
        if not isinstance(menu, dict):
            return
        menu_name = str(menu.get("name") or menu.get("title") or "menu")
        menu_attr = unique_menu_attribute("menu", menu_name)
        lines.extend([
            f"        self.{menu_attr} = {parent_expression}.addMenu({py_string(menu.get('title', menu_name))})",
            f"        self.{menu_attr}.setObjectName({py_string(menu_name)})",
            f"        self.{menu_attr}.setEnabled({bool(menu.get('enabled', True))!r})",
            f"        self.{menu_attr}.menuAction().setVisible({bool(menu.get('visible', True))!r})",
        ])
        if menu.get("icon"):
            lines.append(
                f"        self.{menu_attr}.setIcon(QIcon({py_string(menu.get('icon'))}))"
            )
        for item in menu.get("items", []):
            if not isinstance(item, dict):
                continue
            item_type = str(item.get("type", "action"))
            if item_type == "separator":
                lines.append(f"        self.{menu_attr}.addSeparator()")
                continue
            if item_type == "menu":
                emit_menu(item, f"self.{menu_attr}")
                continue
            action_name = str(item.get("name") or item.get("text") or "action")
            action_attr = action_attributes.get(action_name)
            if action_attr is None:
                action_attr = unique_menu_attribute("action", action_name)
                action_attributes[action_name] = action_attr
                lines.extend([
                    f"        self.{action_attr} = QAction({py_string(item.get('text', action_name))}, self)",
                    f"        self.{action_attr}.setObjectName({py_string(action_name)})",
                    f"        self.{action_attr}.setCheckable({bool(item.get('checkable', False))!r})",
                    f"        self.{action_attr}.setChecked({bool(item.get('checked', False))!r})",
                    f"        self.{action_attr}.setEnabled({bool(item.get('enabled', True))!r})",
                    f"        self.{action_attr}.setVisible({bool(item.get('visible', True))!r})",
                ])
                if item.get("shortcut"):
                    lines.append(
                        f"        self.{action_attr}.setShortcut(QKeySequence({py_string(item.get('shortcut'))}))"
                    )
                if item.get("tooltip"):
                    lines.append(
                        f"        self.{action_attr}.setToolTip({py_string(item.get('tooltip'))})"
                    )
                if item.get("status_tip"):
                    lines.append(
                        f"        self.{action_attr}.setStatusTip({py_string(item.get('status_tip'))})"
                    )
                if item.get("icon"):
                    lines.append(
                        f"        self.{action_attr}.setIcon(QIcon({py_string(item.get('icon'))}))"
                    )
            lines.append(f"        self.{menu_attr}.addAction(self.{action_attr})")

    for menu in menu_data:
        if isinstance(menu, dict):
            emit_menu(menu, "self.menuBar()")
    if form_props.get("statusbar_enabled", bool(form_props.get("statusbar"))):
        lines.append("        self.statusBar()")
        if form_props.get("statusbar"):
            lines.append(f"        self.statusBar().showMessage({py_string(form_props.get('statusbar'))})")
    if form_props.get("icon"): lines.append(f"        self.setWindowIcon(QIcon({py_string(form_props.get('icon'))}))")
    lines.append("        print('[OK] Программа запущена. Консоль работает без задержки.', flush=True)")
    lines.append("")

    def _parent_depth(node: dict[str, Any]) -> int:
        depth = 0
        seen = {node["id"]}
        parent_id = node.get("parent_id")
        while parent_id in by_id and parent_id not in seen:
            seen.add(parent_id)
            depth += 1
            parent_id = by_id[parent_id].get("parent_id")
        return depth

    initialization_nodes = sorted(nodes, key=_parent_depth)
    for node in initialization_nodes:
        node_type, node_id = node["type"], node["id"]
        props, name = node.get("properties", {}), names[node_id]
        parent_id = node.get("parent_id")
        parent_model = by_id.get(parent_id, {})
        parent_ref = (
            f"self.{names[parent_id]}_content"
            if (
                parent_id in names
                and parent_model.get("properties", {}).get("_qt_class")
                == "QMdiSubWindow"
            )
            else (
                f"self.{names[parent_id]}_inner"
                if (
                    parent_id in names
                    and parent_model.get("properties", {}).get("_qt_class")
                    == "QScrollArea"
                )
                else (
                    f"self.{names[parent_id]}"
                    if parent_id in names else "self.central"
                )
            )
        )
        # Construct a child directly in its real Qt parent.  Reparenting
        # after construction works for simple controls, but it is unreliable
        # for QMdiSubWindow and QScrollArea children (their layout/visibility
        # can be reset by Qt during the reparent operation).
        creation_parent = parent_ref if parent_id in names else "self.central"
        if node_type in visual_types:
            node_lines_start = len(lines)
            lines.append(f"        # VPB_NODE id={node_id} type={node_type}")
            x, y, width, height = visual_coordinates.get(
                str(node_id),
                (
                    int(props.get("x", 0)),
                    int(props.get("y", 0)),
                    int(props.get("width", 120)),
                    int(props.get("height", 32)),
                ),
            )
            if node_type == "Button":
                lines.append(f"        self.{name} = QPushButton({py_string(props.get('text', 'Кнопка'))}, self.central)")
            elif node_type == "Label":
                lines.append(f"        self.{name} = QLabel({py_string(props.get('text', 'Надпись'))}, self.central)")
            elif node_type == "LineEdit":
                lines += [
                    f"        self.{name} = QLineEdit(self.central)",
                    f"        self.{name}.setText({py_string(props.get('text', ''))})",
                    f"        self.{name}.setPlaceholderText({py_string(props.get('placeholder', ''))})",
                    f"        self.{name}.setReadOnly({bool(props.get('read_only', False))!r})",
                    f"        self.{name}.setClearButtonEnabled({bool(props.get('clear_button', False))!r})",
                    f"        self.{name}.setMaxLength({int(props.get('max_length', 32767))})",
                ]
                if props.get("password", False):
                    lines.append(f"        self.{name}.setEchoMode(QLineEdit.EchoMode.Password)")
            elif node_type == "TextEdit":
                lines += [
                    f"        self.{name} = QTextEdit(self.central)",
                    f"        self.{name}.setPlainText({py_string(props.get('text', ''))})",
                    f"        self.{name}.setPlaceholderText({py_string(props.get('placeholder', ''))})",
                    f"        self.{name}.setReadOnly({bool(props.get('read_only', False))!r})",
                    f"        self.{name}.setAcceptRichText({bool(props.get('accept_rich_text', False))!r})",
                ]
            elif node_type == "CheckBox":
                lines += [
                    f"        self.{name} = QCheckBox({py_string(props.get('text', 'Флажок'))}, self.central)",
                    f"        self.{name}.setChecked({bool(props.get('checked', False))!r})",
                    f"        self.{name}.setTristate({bool(props.get('tristate', False))!r})",
                ]
            elif node_type == "ComboBox":
                items = [item for item in str(props.get("items", "")).split("|") if item]
                lines += [
                    f"        self.{name} = QComboBox(self.central)",
                    f"        self.{name}.addItems({items!r})",
                    f"        self.{name}.setCurrentIndex({int(props.get('current_index', 0))})",
                    f"        self.{name}.setEditable({bool(props.get('editable', False))!r})",
                ]
            elif node_type == "ListWidget":
                items = [item for item in str(props.get("items", "")).split("|") if item]
                lines += [
                    f"        self.{name} = QListWidget(self.central)",
                    f"        self.{name}.addItems({items!r})",
                    f"        self.{name}.setCurrentRow({int(props.get('current_index', 0))})",
                    f"        self.{name}.setSortingEnabled({bool(props.get('sorting', False))!r})",
                ]
            elif node_type == "ProgressBar":
                lines += [
                    f"        self.{name} = QProgressBar(self.central)",
                    f"        self.{name}.setRange({int(props.get('minimum', 0))}, {int(props.get('maximum', 100))})",
                    f"        self.{name}.setValue({int(props.get('value', 0))})",
                    f"        self.{name}.setTextVisible({bool(props.get('show_text', True))!r})",
                    f"        self.{name}.setOrientation(Qt.Orientation.{('Vertical' if str(props.get('orientation', 'Horizontal')) == 'Vertical' else 'Horizontal')})",
                ]
            elif node_type == "Slider":
                slider_orientation = (
                    "Vertical"
                    if str(props.get("orientation", "Horizontal")) == "Vertical"
                    else "Horizontal"
                )
                lines += [
                    f"        self.{name} = QSlider(Qt.Orientation.{slider_orientation}, self.central)",
                    f"        self.{name}.setRange({int(props.get('minimum', 0))}, {int(props.get('maximum', 100))})",
                    f"        self.{name}.setSingleStep({int(props.get('step', 1))})",
                    f"        self.{name}.setValue({int(props.get('value', 0))})",
                ]
            elif node_type == "SpinBox":
                lines += [
                    f"        self.{name} = QSpinBox(self.central)",
                    f"        self.{name}.setRange({int(props.get('minimum', 0))}, {int(props.get('maximum', 100))})",
                    f"        self.{name}.setSingleStep({int(props.get('step', 1))})",
                    f"        self.{name}.setValue({int(props.get('value', 0))})",
                ]
            elif node_type == "TableWidget":
                headers = [item for item in str(props.get("columns", "")).split("|") if item]
                lines += [
                    f"        self.{name} = QTableWidget({int(props.get('rows', 5))}, {len(headers)}, self.central)",
                    f"        self.{name}.setHorizontalHeaderLabels({headers!r})",
                    f"        self.{name}.setEditTriggers(QTableWidget.EditTrigger.AllEditTriggers if {bool(props.get('editable', True))!r} else QTableWidget.EditTrigger.NoEditTriggers)",
                ]
            elif node_type == "TableView":
                lines += [
                    f"        self.{name} = QTableView(self.central)",
                    f"        self.{name}.setEditTriggers(QTableView.EditTrigger.AllEditTriggers if {bool(props.get('editable', True))!r} else QTableView.EditTrigger.NoEditTriggers)",
                ]
            elif node_type == "TreeWidget":
                items = [item for item in str(props.get("items", "")).split("|") if item]
                lines += [
                    f"        self.{name} = QTreeWidget(self.central)",
                    f"        self.{name}.setHeaderLabel({py_string(props.get('header', 'Элементы'))})",
                    f"        self.{name}.addTopLevelItems([QTreeWidgetItem([text]) for text in {items!r}])",
                ]
            elif node_type == "DateEdit":
                lines += [
                    f"        self.{name} = QDateEdit(self.central)",
                    f"        self.{name}.setDate(QDate.fromString({py_string(props.get('date', '2026-01-01'))}, 'yyyy-MM-dd'))",
                    f"        self.{name}.setDisplayFormat({py_string(props.get('format', 'dd.MM.yyyy'))})",
                    f"        self.{name}.setCalendarPopup({bool(props.get('calendar_popup', True))!r})",
                ]
            elif node_type == "Calendar":
                lines += [
                    f"        self.{name} = QCalendarWidget(self.central)",
                    f"        self.{name}.setSelectedDate(QDate.fromString({py_string(props.get('date', '2026-01-01'))}, 'yyyy-MM-dd'))",
                    f"        self.{name}.setGridVisible({bool(props.get('grid', True))!r})",
                ]
            elif node_type == "RadioButton":
                lines += [f"        self.{name} = QRadioButton({py_string(props.get('text', 'Переключатель'))}, self.central)", f"        self.{name}.setChecked({bool(props.get('checked', False))!r})"]
            elif node_type == "GroupBox":
                lines += [f"        self.{name} = QGroupBox({py_string(props.get('title', 'Группа'))}, self.central)", f"        self.{name}.setCheckable({bool(props.get('checkable', False))!r})", f"        self.{name}.setChecked({bool(props.get('checked', True))!r})"]
            elif node_type == "Dial":
                lines += [f"        self.{name} = QDial(self.central)", f"        self.{name}.setRange({int(props.get('minimum',0))}, {int(props.get('maximum',100))})", f"        self.{name}.setSingleStep({int(props.get('step',1))})", f"        self.{name}.setValue({int(props.get('value',50))})", f"        self.{name}.setWrapping({bool(props.get('wrapping',False))!r})", f"        self.{name}.setNotchesVisible({bool(props.get('notches',True))!r})"]
            elif node_type == "ToolButton":
                lines += [f"        self.{name} = QToolButton(self.central)", f"        self.{name}.setText({py_string(props.get('text','Инструмент'))})", f"        self.{name}.setCheckable({bool(props.get('checkable',False))!r})", f"        self.{name}.setChecked({bool(props.get('checked',False))!r})"]
            elif node_type == "PlainTextEdit":
                lines += [f"        self.{name} = QPlainTextEdit(self.central)", f"        self.{name}.setPlainText({py_string(props.get('text',''))})", f"        self.{name}.setPlaceholderText({py_string(props.get('placeholder',''))})", f"        self.{name}.setReadOnly({bool(props.get('read_only',False))!r})", f"        self.{name}.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth if {bool(props.get('line_wrap',True))!r} else QPlainTextEdit.LineWrapMode.NoWrap)"]
            elif node_type == "DoubleSpinBox":
                lines += [f"        self.{name} = QDoubleSpinBox(self.central)", f"        self.{name}.setRange({float(props.get('minimum',0.0))!r}, {float(props.get('maximum',100.0))!r})", f"        self.{name}.setSingleStep({float(props.get('step',0.1))!r})", f"        self.{name}.setDecimals({int(props.get('decimals',2))})", f"        self.{name}.setValue({float(props.get('value',0.0))!r})"]
            elif node_type == "ScrollBar":
                orientation = "Vertical" if str(props.get("orientation","Horizontal")) == "Vertical" else "Horizontal"
                lines += [f"        self.{name} = QScrollBar(Qt.Orientation.{orientation}, self.central)", f"        self.{name}.setRange({int(props.get('minimum',0))}, {int(props.get('maximum',100))})", f"        self.{name}.setSingleStep({int(props.get('step',1))})", f"        self.{name}.setPageStep({int(props.get('page_step',10))})", f"        self.{name}.setValue({int(props.get('value',0))})"]
            elif node_type == "TimeEdit":
                lines += [f"        self.{name} = QTimeEdit(self.central)", f"        self.{name}.setTime(QTime.fromString({py_string(props.get('time','12:00:00'))}, 'HH:mm:ss'))", f"        self.{name}.setDisplayFormat({py_string(props.get('format','HH:mm:ss'))})"]
            elif node_type == "DateTimeEdit":
                lines += [f"        self.{name} = QDateTimeEdit(self.central)", f"        self.{name}.setDateTime(QDateTime.fromString({py_string(props.get('datetime','2026-09-22T12:00:00'))}, Qt.DateFormat.ISODate))", f"        self.{name}.setDisplayFormat({py_string(props.get('format','dd.MM.yyyy HH:mm:ss'))})", f"        self.{name}.setCalendarPopup({bool(props.get('calendar_popup',True))!r})"]
            elif node_type == "TextBrowser":
                lines += [f"        self.{name} = QTextBrowser(self.central)", f"        self.{name}.setHtml({py_string(props.get('html',''))})", f"        self.{name}.setOpenExternalLinks({bool(props.get('open_external_links',True))!r})"]
            elif node_type == "FontComboBox":
                lines += [f"        self.{name} = QFontComboBox(self.central)", f"        self.{name}.setCurrentFont(QFont({py_string(props.get('family','Segoe UI'))}))"]
            elif node_type == "KeySequenceEdit":
                lines += [f"        self.{name} = QKeySequenceEdit(self.central)", f"        self.{name}.setKeySequence(QKeySequence({py_string(props.get('sequence','Ctrl+Shift+S'))}))"]
            elif node_type == "CommandLinkButton":
                lines += [f"        self.{name} = QCommandLinkButton({py_string(props.get('text','Продолжить'))}, self.central)", f"        self.{name}.setDescription({py_string(props.get('description',''))})"]
            elif node_type == "DialogButtonBox":
                valid_buttons = {
                    "Ok", "Save", "SaveAll", "Open", "Yes", "YesToAll",
                    "No", "NoToAll", "Abort", "Retry", "Ignore", "Close",
                    "Cancel", "Discard", "Help", "Apply", "Reset",
                    "RestoreDefaults",
                }
                button_names = [
                    part.strip()
                    for part in str(props.get("buttons", "Ok|Cancel")).split("|")
                    if part.strip() in valid_buttons
                ] or ["Ok", "Cancel"]
                button_expression = " | ".join(
                    f"QDialogButtonBox.StandardButton.{button}"
                    for button in button_names
                )
                orientation = (
                    "Vertical"
                    if str(props.get("orientation", "Horizontal")) == "Vertical"
                    else "Horizontal"
                )
                lines += [
                    f"        self.{name} = QDialogButtonBox(self.central)",
                    f"        self.{name}.setStandardButtons({button_expression})",
                    f"        self.{name}.setOrientation(Qt.Orientation.{orientation})",
                    f"        self.{name}.setCenterButtons({bool(props.get('center_buttons', False))!r})",
                ]
            elif node_type == "Frame":
                shape = str(props.get('shape','StyledPanel')); shadow = str(props.get('shadow','Sunken'))
                qt_class = str(props.get("_qt_class", ""))
                if qt_class == "QMdiArea":
                    lines += [
                        f"        self.{name} = QMdiArea(self.central)",
                        f"        self.{name}.setViewMode(QMdiArea.ViewMode.SubWindowView)",
                    ]
                elif qt_class == "QMdiSubWindow":
                    lines += [
                        f"        self.{name}_content = QWidget()",
                        # Let QMdiArea create and own the QMdiSubWindow
                        # wrapper.  Constructing a standalone QMdiSubWindow
                        # and adding it afterwards can leave it as a separate
                        # top-level window on some Qt versions.
                        f"        self.{name} = {parent_ref}.addSubWindow(self.{name}_content)",
                        f"        self.{name}.setWindowTitle({py_string(props.get('mdi_title', props.get('title', 'Дочернее окно')))})",
                    ]
                elif qt_class == "QGraphicsView":
                    lines += [
                        f"        self.{name} = QGraphicsView(self.central)",
                        f"        self.{name}.setScene(QtWidgets.QGraphicsScene())",
                    ]
                elif qt_class == "QScrollArea":
                    lines += [
                        f"        self.{name} = QScrollArea(self.central)",
                        f"        self.{name}.setWidgetResizable(True)",
                        f"        self.{name}_inner = QWidget()",
                        f"        self.{name}.setWidget(self.{name}_inner)",
                    ]
                else:
                    lines += [
                        f"        self.{name} = QFrame(self.central)",
                        f"        self.{name}.setFrameShape(QFrame.Shape.{shape})",
                        f"        self.{name}.setFrameShadow(QFrame.Shadow.{shadow})",
                        f"        self.{name}.setLineWidth({int(props.get('line_width',1))})",
                    ]
                    if (
                        not props.get("style")
                        and qt_class in {"QOpenGLWidget", "QQuickWidget"}
                    ):
                        lines.append(
                            f"        self.{name}.setStyleSheet("
                            "'background:#A7A7A7; border:1px solid #777777;')"
                        )
            elif node_type == "HorizontalLine":
                line_shape = "VLine" if bool(props.get("vertical", False)) else "HLine"
                lines += [f"        self.{name} = QFrame(self.central)", f"        self.{name}.setFrameShape(QFrame.Shape.{line_shape})", f"        self.{name}.setFrameShadow(QFrame.Shadow.Sunken)", f"        self.{name}.setLineWidth({int(props.get('line_width',1))})"]
            elif node_type in {"Gauge","Speedometer","Tachometer","Thermometer","LevelMeter","LEDIndicator","Compass","BatteryIndicator","SignalIndicator","Sparkline","AnalogClock","Knob","LineChart","BarChart","PieChart","RadarChart","Oscilloscope","VUMeter","SevenSegmentDisplay","LEDMatrix","XYPlot","HeatMap","Timeline","WaterfallChart","GeoMap","Waveform","SpectrumAnalyzer","MultiSegmentDisplay","CustomInstrument"}:
                mode={"Gauge":"gauge","Speedometer":"speedometer","Tachometer":"tachometer","Thermometer":"thermometer","LevelMeter":"level","LEDIndicator":"led","Compass":"compass","BatteryIndicator":"battery","SignalIndicator":"signal","Sparkline":"sparkline","AnalogClock":"clock","Knob":"knob","LineChart":"linechart","BarChart":"barchart","PieChart":"piechart","RadarChart":"radarchart","Oscilloscope":"oscilloscope","VUMeter":"vumeter","SevenSegmentDisplay":"sevensegment","LEDMatrix":"ledmatrix","XYPlot":"xyplot","HeatMap":"heatmap","Timeline":"timeline","WaterfallChart":"waterfall","GeoMap":"geomap","Waveform":"waveform","SpectrumAnalyzer":"spectrum","MultiSegmentDisplay":"multisegment","CustomInstrument":"custom"}[node_type]
                lines += [f"        self.{name} = InstrumentWidget({mode!r}, self.central)",f"        self.{name}.setRange({float(props.get('minimum',0.0))!r}, {float(props.get('maximum',100.0))!r})",f"        self.{name}.warning = {float(props.get('warning',70.0))!r}",f"        self.{name}.critical = {float(props.get('critical',90.0))!r}",f"        self.{name}.precision = {int(props.get('precision',1))}",f"        self.{name}.history_size = {int(props.get('history_size',80))}",f"        self.{name}.setTitle({py_string(props.get('title',COMPONENTS[node_type].caption))})",f"        self.{name}.setUnit({py_string(props.get('unit',''))})",f"        self.{name}.setColors(primary={py_string(props.get('primary_color','#35C2FF'))}, secondary={py_string(props.get('secondary_color','#26364A'))}, needle={py_string(props.get('needle_color','#FF5252'))}, background={py_string(props.get('background_color','#101820'))}, text={py_string(props.get('text_color','#F4F7FB'))}, warning={py_string(props.get('warning_color','#FFB020'))}, alarm={py_string(props.get('alarm_color','#FF3B30'))}, border={py_string(props.get('border_color','#52667A'))})",f"        self.{name}.setValue({float(props.get('value',0.0))!r})"]
                if node_type in {"XYPlot","HeatMap","Timeline","WaterfallChart","GeoMap","Waveform","SpectrumAnalyzer","MultiSegmentDisplay","CustomInstrument"}:
                    lines += [f"        self.{name}.configureAdvanced(grid_rows={int(props.get('grid_rows',8))}, grid_columns={int(props.get('grid_columns',12))}, line_width={int(props.get('line_width',2))}, bands={int(props.get('bands',24))}, segments={int(props.get('segments',14))}, digits={int(props.get('digits',8))})", f"        self.{name}.configurePlot(x_axis_title={py_string(props.get('x_axis_title','X'))}, y_axis_title={py_string(props.get('y_axis_title','Y'))}, show_legend={bool(props.get('show_legend',True))!r}, auto_scale={bool(props.get('auto_scale',True))!r}, legend_position={py_string(props.get('legend_position','TopRight'))}, series_palette={py_string(props.get('series_palette','#35C2FF|#FFB020|#59FF88'))})"]
                    if node_type == "GeoMap": lines += [f"        self.{name}.setPosition({float(props.get('latitude',55.7558))}, {float(props.get('longitude',37.6173))}, {int(props.get('zoom',8))})"]
                    if node_type == "CustomInstrument": lines += [f"        self.{name}.setDesign({py_string(props.get('design','{}'))})"]
                    try: _initial_series = json.loads(str(props.get('initial_series','{}')) or '{}')
                    except (TypeError, ValueError): _initial_series = {}
                    if isinstance(_initial_series, dict):
                        for _series_name, _series_values in _initial_series.items():
                            lines += [f"        self.{name}.setSeriesData({py_string(_series_name)}, {py_string(json.dumps(_series_values, ensure_ascii=False))})"]
            elif node_type == "TetrisGame":
                game_config = {
                    "field": {"cols": int(props.get("columns",10)), "rows": int(props.get("rows",20)), "cell": int(props.get("cell",28)), "background": props.get("background_color","#0B1020"), "grid": props.get("grid_color","#18233D"), "border": props.get("border_color","#35C2FF"), "ghost": bool(props.get("show_ghost",True))},
                    "speed": {"base_ms": int(props.get("base_ms",500)), "step_ms": int(props.get("step_ms",35)), "min_ms": int(props.get("min_ms",70)), "lines_per_level": int(props.get("lines_per_level",10)), "slider": True},
                    "controls": {"left":["Left","A"], "right":["Right","D"], "rotate":["Up","W"], "soft_drop":["Down","S"], "hard_drop":["Space"], "pause":["P"], "restart":["R"], "help": (["←/→ или A/D — движение", "↑/W — поворот, ↓/S — ускорить", "Space — сброс, P — пауза, R — заново"] if props.get("show_help",True) else [])},
                    "panel": {"title": props.get("title","Неоновый Тетрис"), "score":True, "lines":True, "level":True, "speed":True, "next":True, "buttons":True, "help":bool(props.get("show_help",True))},
                }
                lines += [f"        self.{name} = TetrisWidget({game_config!r}, self.central)"]
            elif node_type == "DashboardCanvas":
                lines += [f"        self.{name} = DashboardCanvasWidget(self.central)", f"        self.{name}.background_color = {py_string(props.get('background_color','#101820'))}", f"        self.{name}.grid_color = {py_string(props.get('grid_color','#26364A'))}", f"        self.{name}.show_grid = {bool(props.get('show_grid',True))!r}", f"        self.{name}.grid_size = {int(props.get('grid_size',20))}", f"        self.{name}.antialiasing = {bool(props.get('antialiasing',True))!r}", f"        self.{name}.setZoom({float(props.get('zoom',1.0))!r})", f"        self.{name}.setScene({py_string(props.get('scene','[]'))})"]
            elif node_type == "GridCanvas":
                initial_grid = props.get("initial_grid", "")
                lines += [
                    f"        self.{name} = GridCanvasWidget(self.central)",
                    f"        self.{name}.columns = {int(props.get('columns',10))}",
                    f"        self.{name}.rows = {int(props.get('rows',20))}",
                    f"        self.{name}.cell_size = {int(props.get('cell_size',24))}",
                    f"        self.{name}.fit_to_widget = {bool(props.get('fit_to_widget',True))!r}",
                    f"        self.{name}.show_grid = {bool(props.get('show_grid',True))!r}",
                    f"        self.{name}.show_values = {bool(props.get('show_values',False))!r}",
                    f"        self.{name}.interactive = {bool(props.get('interactive',True))!r}",
                    f"        self.{name}.empty_value = {py_string(props.get('empty_value','0'))}",
                    f"        self.{name}.background_color = {py_string(props.get('background_color','#101820'))}",
                    f"        self.{name}.grid_color = {py_string(props.get('grid_color','#26364A'))}",
                    f"        self.{name}.setPalette({py_string(props.get('palette','{}'))})",
                    f"        self.{name}.setGrid({py_string(initial_grid)})",
                ]
            elif node_type == "LCDNumber":
                lines += [
                    f"        self.{name} = QLCDNumber({int(props.get('digits', 5))}, self.central)",
                    f"        self.{name}.display({float(props.get('value', 0))})",
                ]
            # All ordinary Qt constructors in the branches above use the
            # historical self.central expression.  Replace only this node's
            # freshly generated lines, preserving unrelated runtime helpers.
            for line_index in range(node_lines_start, len(lines)):
                lines[line_index] = lines[line_index].replace(
                    "(self.central)", f"({creation_parent})"
                )
            if parent_id in names and str(props.get("_qt_class", "")) != "QMdiSubWindow":
                lines.append(f"        self.{name}.setParent({parent_ref})")
            if props.get("_qt_class") == "QMdiSubWindow" and parent_id in names:
                lines.append(f"        self.{name}.show()")
                lines.append(f"        self.{name}.showNormal()")
                lines.append(f"        self.{name}.raise_()")
                lines.append(f"        self.{name}_content.show()")
            lines += [
                f"        self.{name}.setGeometry({x}, {y}, {width}, {height})",
                f"        self.{name}.setObjectName({py_string(props.get('name', name))})",
                f"        self.{name}.setEnabled({bool(props.get('enabled', True))!r})",
                f"        self.{name}.setVisible({bool(props.get('visible', True))!r})",
                f"        self.{name}.setAcceptDrops({bool(props.get('accept_drops', False))!r})",
                f"        self.{name}.setMouseTracking({bool(props.get('mouse_tracking', False))!r})",
                f"        self.{name}.setAccessibleName({py_string(props.get('accessible_name', ''))})",
                f"        self.{name}.setAccessibleDescription({py_string(props.get('accessible_description', ''))})",
            ]
            if props.get("tooltip"):
                lines.append(f"        self.{name}.setToolTip({py_string(props.get('tooltip', ''))})")
            if props.get("whats_this"):
                lines.append(f"        self.{name}.setWhatsThis({py_string(props.get('whats_this', ''))})")
            lines += [
                f"        self.{name}.setMinimumSize({int(props.get('min_width', 0) or 0)}, {int(props.get('min_height', 0) or 0)})",
                f"        self.{name}.setMaximumSize({int(props.get('max_width', 16777215) or 16777215)}, {int(props.get('max_height', 16777215) or 16777215)})",
            ]
            if props.get("style"):
                lines.append(f"        self.{name}.setStyleSheet({py_string(props.get('style', ''))})")
            if props.get("font_family") or props.get("font_size"):
                lines += [
                    f"        _font_{name} = QFont({py_string(props.get('font_family', 'Segoe UI'))}, {int(props.get('font_size', 10) or 10)})",
                    f"        _font_{name}.setBold({bool(props.get('font_bold', False))!r})",
                    f"        _font_{name}.setItalic({bool(props.get('font_italic', False))!r})",
                    f"        _font_{name}.setUnderline({bool(props.get('font_underline', False))!r})",
                    f"        self.{name}.setFont(_font_{name})",
                ]
            if node_type == "Button":
                lines += [
                    f"        self.{name}.setDefault({bool(props.get('default', False))!r})",
                    f"        self.{name}.setAutoRepeat({bool(props.get('auto_repeat', False))!r})",
                ]
            # Apply the expanded inspector properties to real Qt widgets.
            if node_type in {"Button", "ToolButton"}:
                lines += [
                    f"        self.{name}.setCheckable({bool(props.get('checkable', False))!r})",
                    f"        self.{name}.setChecked({bool(props.get('checked', False))!r})",
                    f"        self.{name}.setAutoRepeat({bool(props.get('auto_repeat', False))!r})",
                    f"        self.{name}.setAutoRepeatDelay({int(props.get('auto_repeat_delay', 300) or 300)})",
                    f"        self.{name}.setAutoRepeatInterval({int(props.get('auto_repeat_interval', 100) or 100)})",
                ]
                if props.get("icon_path"):
                    lines += [
                        f"        self.{name}.setIcon(QIcon({py_string(props.get('icon_path'))}))",
                        f"        self.{name}.setIconSize(QSize({int(props.get('icon_size', 16) or 16)}, {int(props.get('icon_size', 16) or 16)}))",
                    ]
            if node_type == "ComboBox":
                lines += [
                    f"        self.{name}.setMaxVisibleItems({int(props.get('max_visible_items', 10) or 10)})",
                    f"        self.{name}.setDuplicatesEnabled({bool(props.get('duplicates_enabled', False))!r})",
                ]
                if props.get("placeholder"):
                    lines.append(f"        self.{name}.setPlaceholderText({py_string(props.get('placeholder'))})")
            if node_type == "ListWidget":
                lines += [
                    f"        self.{name}.setAlternatingRowColors({bool(props.get('alternating_rows', False))!r})",
                    f"        self.{name}.setDragEnabled({bool(props.get('drag_enabled', False))!r})",
                ]
            if node_type == "ProgressBar":
                lines += [
                    f"        self.{name}.setFormat({py_string(props.get('format', '%p%'))})",
                    f"        self.{name}.setTextVisible({bool(props.get('text_visible', props.get('show_text', True)))!r})",
                    f"        self.{name}.setInvertedAppearance({bool(props.get('inverted_appearance', False))!r})",
                ]
            if node_type in {"Slider", "Dial"}:
                lines += [
                    f"        self.{name}.setPageStep({int(props.get('page_step', 10) or 10)})",
                    f"        self.{name}.setTracking({bool(props.get('tracking', True))!r})",
                    f"        self.{name}.setInvertedAppearance({bool(props.get('inverted_appearance', False))!r})",
                    f"        self.{name}.setInvertedControls({bool(props.get('inverted_controls', False))!r})",
                ]
            if node_type == "SpinBox":
                lines += [
                    f"        self.{name}.setPrefix({py_string(props.get('prefix', ''))})",
                    f"        self.{name}.setSuffix({py_string(props.get('suffix', ''))})",
                    f"        self.{name}.setWrapping({bool(props.get('wrapping', False))!r})",
                    f"        self.{name}.setKeyboardTracking({bool(props.get('keyboard_tracking', True))!r})",
                ]
            if node_type == "TableWidget":
                lines += [
                    f"        self.{name}.setSortingEnabled({bool(props.get('sorting_enabled', False))!r})",
                    f"        self.{name}.setAlternatingRowColors({bool(props.get('alternating_rows', False))!r})",
                    f"        self.{name}.setShowGrid({bool(props.get('grid_visible', True))!r})",
                ]
            if node_type == "TableView":
                lines += [
                    f"        self.{name}.setSortingEnabled({bool(props.get('sorting_enabled', False))!r})",
                    f"        self.{name}.setAlternatingRowColors({bool(props.get('alternating_rows', False))!r})",
                    f"        self.{name}.setShowGrid({bool(props.get('grid_visible', True))!r})",
                    f"        self.{name}.horizontalHeader().setVisible({bool(props.get('horizontal_header', True))!r})",
                    f"        self.{name}.verticalHeader().setVisible({bool(props.get('vertical_header', True))!r})",
                ]
            if node_type == "TreeWidget":
                lines += [
                    f"        self.{name}.setSortingEnabled({bool(props.get('sorting_enabled', False))!r})",
                    f"        self.{name}.setAlternatingRowColors({bool(props.get('alternating_rows', False))!r})",
                    f"        self.{name}.setRootIsDecorated({bool(props.get('root_decorated', True))!r})",
                    f"        self.{name}.setUniformRowHeights({bool(props.get('uniform_rows', False))!r})",
                    f"        self.{name}.setIndentation({int(props.get('indentation', 20) or 20)})",
                    f"        self.{name}.setAnimated({bool(props.get('animated', False))!r})",
                ]
            if node_type == "DateEdit":
                lines += [
                    f"        self.{name}.setReadOnly({bool(props.get('read_only', False))!r})",
                    f"        self.{name}.setWrapping({bool(props.get('wrapping', False))!r})",
                ]
            if node_type == "Calendar":
                lines += [
                    f"        self.{name}.setGridVisible({bool(props.get('grid_visible', props.get('grid', True)))!r})",
                    f"        self.{name}.setNavigationBarVisible({bool(props.get('navigation_visible', True))!r})",
                    f"        self.{name}.setDateEditEnabled({bool(props.get('date_edit_enabled', True))!r})",
                ]
            if node_type == "GroupBox":
                lines.append(f"        self.{name}.setFlat({bool(props.get('flat', False))!r})")
            if node_type in {"TextEdit", "PlainTextEdit"}:
                lines.append(f"        self.{name}.setTabChangesFocus({bool(props.get('tab_changes_focus', False))!r})")
            if node_type == "Label":
                lines.append(f"        self.{name}.setWordWrap({bool(props.get('word_wrap', False))!r})")
                lines.append(
                    f"        self.{name}.setTextInteractionFlags("
                    f"Qt.TextInteractionFlag.TextSelectableByMouse if "
                    f"{bool(props.get('selectable', False))!r} else "
                    "Qt.TextInteractionFlag.NoTextInteraction)"
                )
            lines.append("")
        elif (
            node_type.startswith("Delphi::")
            and COMPONENTS[node_type].visual
        ):
            spec = COMPONENTS[node_type]
            original = node_type.split("::", 1)[1].lower()
            caption = str(
                property_lookup(
                    props, "Text", "Caption", "String",
                    default=spec.caption,
                )
            )
            x = int(property_lookup(props, "Left", "x", default=0) or 0)
            y = int(property_lookup(props, "Top", "y", default=0) or 0)
            width = int(
                property_lookup(props, "Width", "width", default=120) or 120
            )
            height = int(
                property_lookup(props, "Height", "height", default=32) or 32
            )
            if (
                "led" in original
                and "ladder" not in original
                and "number" not in original
            ):
                led_state = bool(
                    property_lookup(
                        props, "Value", "State", "Checked", default=False
                    )
                )
                radius = max(4, min(width, height) // 2)
                led_color = normalized_delphi_color(
                    property_lookup(
                        props,
                        "ColorOn" if led_state else "ColorOff",
                        default="#35D05B" if led_state else "#52605A",
                    ),
                    "#35D05B" if led_state else "#52605A",
                )
                lines += [
                    f"        self.{name} = QLabel('', self.central)",
                    f"        self.{name}.setProperty('ledState', {led_state!r})",
                    f"        self.{name}.setStyleSheet("
                    f"'border: 2px solid #26352e; border-radius: {radius}px; "
                    f"background: {led_color};')",
                ]
            elif any(token in original for token in ("button", "bitbtn", "imgbtn")):
                lines.append(
                    f"        self.{name} = QPushButton({caption!r}, self.central)"
                )
            elif "checkbox" in original:
                lines.append(
                    f"        self.{name} = QCheckBox({caption!r}, self.central)"
                )
            elif any(token in original for token in ("radiobutton", "radio")):
                lines.append(
                    f"        self.{name} = QRadioButton({caption!r}, self.central)"
                )
            elif any(token in original for token in ("lednumber", "lcd")):
                value = float(
                    property_lookup(props, "Value", "Position", default=0) or 0
                )
                digits = int(
                    property_lookup(props, "Digits", "DigitCount", default=5)
                    or 5
                )
                lines += [
                    f"        self.{name} = QLCDNumber({digits}, self.central)",
                    f"        self.{name}.display({value!r})",
                ]
            elif any(token in original for token in ("gauge", "dial", "knob")):
                minimum = int(
                    property_lookup(props, "Min", "Minimum", default=0) or 0
                )
                maximum = int(
                    property_lookup(props, "Max", "Maximum", default=100) or 100
                )
                value = int(
                    property_lookup(props, "Value", "Position", default=0) or 0
                )
                lines += [
                    f"        self.{name} = QDial(self.central)",
                    f"        self.{name}.setRange({minimum}, {maximum})",
                    f"        self.{name}.setValue({value})",
                ]
            elif "combobox" in original:
                lines += [
                    f"        self.{name} = QComboBox(self.central)",
                    f"        self.{name}.addItems("
                    f"{[item for item in str(property_lookup(props, 'Strings', 'Items', default='')).split('|') if item]!r})",
                ]
            elif "listbox" in original:
                lines += [
                    f"        self.{name} = QListWidget(self.central)",
                    f"        self.{name}.addItems("
                    f"{[item for item in str(property_lookup(props, 'Strings', 'Items', default='')).split('|') if item]!r})",
                ]
            elif "progress" in original:
                lines.append(
                    f"        self.{name} = QProgressBar(self.central)"
                )
            elif any(token in original for token in ("trackbar", "scrollbar")):
                lines.append(
                    f"        self.{name} = QSlider("
                    "Qt.Orientation.Horizontal, self.central)"
                )
            elif any(token in original for token in ("updown", "spin")):
                lines.append(
                    f"        self.{name} = QSpinBox(self.central)"
                )
            elif original == "label":
                lines.append(
                    f"        self.{name} = ClickableLabel({caption!r}, self.central)"
                )
            elif any(token in original for token in ("memo", "richedit")):
                lines += [
                    f"        self.{name} = QTextEdit(self.central)",
                    f"        self.{name}.setPlainText({caption!r})",
                ]
            elif "edit" in original:
                lines += [
                    f"        self.{name} = QLineEdit(self.central)",
                    f"        self.{name}.setText({caption!r})",
                ]
            elif any(token in original for token in ("stringtable", "grid", "table")):
                rows = int(property_lookup(props, "RowCount", "Rows", default=5) or 5)
                columns = int(
                    property_lookup(props, "ColCount", "Columns", default=3) or 3
                )
                lines.append(
                    f"        self.{name} = QTableWidget({rows}, {columns}, self.central)"
                )
            elif any(token in original for token in ("treeview", "tree")):
                lines += [
                    f"        self.{name} = QTreeWidget(self.central)",
                    f"        self.{name}.setHeaderLabel({caption!r})",
                ]
            elif any(token in original for token in ("groupbox", "panel")):
                lines.append(
                    f"        self.{name} = QGroupBox({caption!r}, self.central)"
                )
            elif any(
                token in original
                for token in ("image", "paintbox", "shape", "picture")
            ):
                lines += [
                    f"        self.{name} = QLabel('', self.central)",
                    f"        self.{name}.setStyleSheet("
                    "'border: 1px solid #88939b; background: #f3f7fa;')",
                ]
            else:
                lines += [
                    f"        self.{name} = QLabel({caption!r}, self.central)",
                    f"        self.{name}.setAlignment(Qt.AlignmentFlag.AlignCenter)",
                    f"        self.{name}.setStyleSheet("
                    "'border: 1px solid #B8B7B4; background: #F7F4FB;')",
                ]
            if parent_id in names:
                lines.append(f"        self.{name}.setParent({parent_ref})")
            lines += [
                f"        self.{name}.setGeometry({x}, {y}, {width}, {height})",
                f"        self.{name}.setEnabled("
                f"{bool(property_lookup(props, 'Enabled', 'enabled', default=True))!r})",
                f"        self.{name}.setVisible("
                f"{bool(property_lookup(props, 'Visible', 'visible', default=True))!r})",
            ]
            if original == "edit":
                lines += [
                    f"        self.{name}.setReadOnly({bool(property_lookup(props, 'ReadOnly', default=False))!r})",
                    f"        self.{name}.setMaxLength({int(property_lookup(props, 'MaxLenField', 'MaxLength', default=32767) or 32767)})",
                ]
                if bool(property_lookup(props, "Password", default=False)):
                    lines.append(f"        self.{name}.setEchoMode(QLineEdit.EchoMode.Password)")
            if original == "label":
                lines.append(
                    f"        self.{name}.setWordWrap({not bool(property_lookup(props, 'AutoSize', default=True))!r})"
                )
            if (
                "Color" in props
                and not (
                    "led" in original
                    and "ladder" not in original
                    and "number" not in original
                )
            ):
                background = normalized_delphi_color(
                    props.get("Color"), "#F0F0F0"
                )
                lines.append(
                    f"        self.{name}.setStyleSheet("
                    f"'background-color: {background};')"
                )
            if "Font" in props:
                family, point_size, bold, italic, underline, strikeout = (
                    normalized_delphi_font(props.get("Font"))
                )
                lines += [
                    f"        font_{name} = QFont({family!r}, {point_size})",
                    f"        font_{name}.setBold({bold!r})",
                    f"        font_{name}.setItalic({italic!r})",
                    f"        font_{name}.setUnderline({underline!r})",
                    f"        font_{name}.setStrikeOut({strikeout!r})",
                    f"        self.{name}.setFont(font_{name})",
                ]
            output_names = [
                port.name for port in spec.ports if port.kind == "data_out"
            ]
            event_names = [
                port.name for port in spec.ports if port.kind == "event_out"
            ]
            lines += [
                f"        {attribute(node_id, 'delphi_')} = "
                f"DelphiCompatibilityRuntime("
                f"{node_type.split('::', 1)[1]!r}, {props!r}, "
                f"{output_names!r}, {event_names!r})",
                "",
            ]
        elif node_type in {"ForRange", "ForEach", "WhileLoop"}:
            lines += [f"        {attribute(node_id, 'loop_index_')} = -1", f"        {attribute(node_id, 'loop_item_')} = None", f"        {attribute(node_id, 'loop_break_')} = False", f"        {attribute(node_id, 'loop_limit_')} = False"]
        elif node_type == "EventGate": lines.append(f"        {attribute(node_id, 'gate_')} = {bool(props.get('open',True))!r}")
        elif node_type == "Once": lines.append(f"        {attribute(node_id, 'once_')} = False")
        elif node_type == "Debounce": lines += [f"        self.{name} = QTimer(self)", f"        self.{name}.setSingleShot(True)", f"        self.{name}.setInterval({int(props.get('interval',250))})"]
        elif node_type == "Throttle": lines.append(f"        {attribute(node_id, 'throttle_')} = 0.0")
        elif node_type == "DictStore":
            try: initial=json.loads(str(props.get("initial","{}")))
            except Exception: initial={}
            if not isinstance(initial,dict): initial={}
            lines.append(f"        {attribute(node_id, 'dict_')} = {initial!r}")
        elif node_type == "ConvertValue": lines += [f"        {attribute(node_id, 'convert_')} = {python_literal(props.get('default',None))}", f"        {attribute(node_id, 'convert_error_')} = ''"]
        elif node_type == "Geometry2D": lines += [f"        {attribute(node_id, 'geometry_result_')} = False", f"        {attribute(node_id, 'geometry_distance_')} = 0.0", f"        {attribute(node_id, 'geometry_x_')} = 0.0", f"        {attribute(node_id, 'geometry_y_')} = 0.0"]
        elif node_type == "MouseInput": lines += [f"        {attribute(node_id, 'mouse_x_')} = 0", f"        {attribute(node_id, 'mouse_y_')} = 0", f"        {attribute(node_id, 'mouse_button_')} = ''"]
        elif node_type == "RepeatLoop":
            lines += [f"        {attribute(node_id, 'loop_index_')} = -1", f"        {attribute(node_id, 'loop_break_')} = False"]
        elif node_type == "ListStore":
            try:
                initial_list = json.loads(str(props.get("initial", "[]")))
            except (TypeError, ValueError):
                initial_list = []
            if not isinstance(initial_list, list): initial_list = []
            lines += [f"        {attribute(node_id, 'list_')} = {initial_list!r}", f"        {attribute(node_id, 'list_item_')} = None"]
        elif node_type == "GridState":
            columns, rows = int(props.get("columns",10)), int(props.get("rows",20))
            empty = props.get("empty", 0)
            lines += [f"        {attribute(node_id, 'grid_')} = [[{python_literal(empty)} for _ in range({columns})] for _ in range({rows})]", f"        {attribute(node_id, 'cleared_lines_')} = 0"]
        elif node_type == "GridBatchWriter":
            lines += [
                f"        {attribute(node_id, 'grid_batch_')} = []",
                f"        {attribute(node_id, 'grid_batch_changed_')} = 0",
                f"        {attribute(node_id, 'grid_batch_error_')} = ''",
            ]
        elif node_type == "KeyboardInput":
            lines += [f"        {attribute(node_id, 'key_')} = ''", f"        {attribute(node_id, 'key_repeat_')} = False"]
        elif node_type == "TwoWayBinding":
            lines += [
                f"        {attribute(node_id, 'binding_value_')} = {python_literal(props.get('initial', ''))}",
                f"        {attribute(node_id, 'binding_guard_')} = False",
            ]
        elif node_type == "Memory":
            lines.append(f"        {attribute(node_id, 'memory_')} = {python_literal(props.get('default', ''))}")
        elif node_type in {"Math", "FormatStr"}:
            lines.append(f"        {attribute(node_id, 'result_')} = None")
        elif node_type == "FileRead":
            lines += [f"        {attribute(node_id, 'text_')} = ''", f"        {attribute(node_id, 'error_')} = ''"]
        elif node_type == "FileWrite":
            lines.append(f"        {attribute(node_id, 'error_')} = ''")
        elif node_type == "Timer":
            lines += [
                f"        self.{name} = QTimer(self)",
                f"        self.{name}.setInterval({int(props.get('interval', 1000))})",
                f"        self.{name}.setSingleShot({bool(props.get('single_shot', False))!r})",
            ]
        elif node_type == "Counter":
            lines.append(f"        {attribute(node_id, 'counter_')} = {int(props.get('start', 0))}")
        elif node_type == "Random":
            lines.append(f"        {attribute(node_id, 'result_')} = 0")
        elif node_type in {"OpenFileDialog", "SaveFileDialog"}:
            lines.append(f"        {attribute(node_id, 'filename_')} = ''")
        elif node_type == "HTTPGet":
            lines += [
                f"        {attribute(node_id, 'text_')} = ''",
                f"        {attribute(node_id, 'status_')} = 0",
                f"        {attribute(node_id, 'error_')} = ''",
            ]
        elif node_type == "RunProcess":
            lines += [
                f"        {attribute(node_id, 'output_')} = ''",
                f"        {attribute(node_id, 'exitcode_')} = 0",
                f"        {attribute(node_id, 'error_')} = ''",
            ]
        elif node_type == "JSONParse":
            lines += [f"        {attribute(node_id, 'value_')} = None", f"        {attribute(node_id, 'error_')} = ''"]
        elif node_type == "JSONStringify":
            lines.append(f"        {attribute(node_id, 'text_')} = ''")
        elif node_type == "SQLiteQuery":
            lines += [f"        {attribute(node_id, 'rows_')} = []", f"        {attribute(node_id, 'error_')} = ''"]
        elif node_type == "Clipboard":
            lines.append(f"        {attribute(node_id, 'clipboard_')} = ''")
        elif node_type == "MessageBox":
            lines.append(f"        {attribute(node_id, 'message_result_')} = ''")
        elif node_type.startswith("Delphi::"):
            spec = COMPONENTS[node_type]
            instance_ports = effective_ports(node_type, props)
            output_names = [
                port.name for port in instance_ports if port.kind == "data_out"
            ]
            event_names = [
                port.name for port in instance_ports if port.kind == "event_out"
            ]
            lines.append(
                f"        {attribute(node_id, 'delphi_')} = "
                f"DelphiCompatibilityRuntime("
                f"{node_type.split('::', 1)[1]!r}, {props!r}, "
                f"{output_names!r}, {event_names!r})"
            )

    signal_map: dict[tuple[str, str], str] = {}
    signal_specs = {
        ("Button", "onClick"): "clicked",
        ("LineEdit", "onChange"): "textChanged",
        ("LineEdit", "onReturn"): "returnPressed",
        ("TextEdit", "onChange"): "textChanged",
        ("CheckBox", "onChange"): "stateChanged",
        ("ComboBox", "onChange"): "currentIndexChanged",
        ("ListWidget", "onSelect"): "currentRowChanged",
        ("Slider", "onChange"): "valueChanged",
        ("SpinBox", "onChange"): "valueChanged",
        ("TableWidget", "onSelect"): "itemSelectionChanged",
        ("TreeWidget", "onSelect"): "itemSelectionChanged",
        ("DateEdit", "onChange"): "dateChanged",
        ("Calendar", "onSelect"): "selectionChanged",
        ("Timer", "onTimer"): "timeout",
        ("Button","onPressed"):"pressed", ("Button","onReleased"):"released", ("Button","onToggle"):"toggled",
        ("LineEdit","onEditingFinished"):"editingFinished", ("LineEdit","onSelection"):"selectionChanged",
        ("TextEdit","onCursor"):"cursorPositionChanged", ("TextEdit","onSelection"):"selectionChanged",
        ("CheckBox","onClick"):"clicked", ("CheckBox","onToggle"):"toggled",
        ("ComboBox","onTextChange"):"currentTextChanged", ("ComboBox","onActivated"):"activated",
        ("ListWidget","onClick"):"itemClicked", ("ListWidget","onDoubleClick"):"itemDoubleClicked",
        ("Slider","onPressed"):"sliderPressed", ("Slider","onReleased"):"sliderReleased", ("Slider","onMoved"):"sliderMoved",
        ("SpinBox","onEditingFinished"):"editingFinished",
        ("TableWidget","onClick"):"cellClicked", ("TableWidget","onDoubleClick"):"cellDoubleClicked", ("TableWidget","onCellChange"):"cellChanged",
        ("TableView","onClick"):"clicked", ("TableView","onDoubleClick"):"doubleClicked", ("TableView","onActivated"):"activated",
        ("TreeWidget","onClick"):"itemClicked", ("TreeWidget","onDoubleClick"):"itemDoubleClicked",
        ("RadioButton","onClick"):"clicked", ("RadioButton","onToggle"):"toggled",
        ("GroupBox","onToggle"):"toggled", ("Dial","onChange"):"valueChanged", ("Dial","onPressed"):"sliderPressed", ("Dial","onReleased"):"sliderReleased",
        ("ToolButton","onClick"):"clicked", ("ToolButton","onPressed"):"pressed", ("ToolButton","onReleased"):"released",
        ("PlainTextEdit","onChange"):"textChanged", ("PlainTextEdit","onCursor"):"cursorPositionChanged",
        ("DoubleSpinBox","onChange"):"valueChanged", ("DoubleSpinBox","onEditingFinished"):"editingFinished",
        ("ScrollBar","onChange"):"valueChanged", ("ScrollBar","onMoved"):"sliderMoved",
        ("TimeEdit","onChange"):"timeChanged", ("DateTimeEdit","onChange"):"dateTimeChanged",
        ("TextBrowser","onAnchor"):"anchorClicked", ("FontComboBox","onChange"):"currentFontChanged",
        ("KeySequenceEdit","onChange"):"keySequenceChanged", ("CommandLinkButton","onClick"):"clicked",
        ("DialogButtonBox","onAccepted"):"accepted",
        ("DialogButtonBox","onRejected"):"rejected",
        ("DialogButtonBox","onHelp"):"helpRequested",
    }
    for _type in ("Gauge","Speedometer","Tachometer","Thermometer","LevelMeter","LEDIndicator","Compass","BatteryIndicator","SignalIndicator","Sparkline","AnalogClock","Knob","LineChart","BarChart","PieChart","RadarChart","Oscilloscope","VUMeter","SevenSegmentDisplay","LEDMatrix","XYPlot","HeatMap","Timeline","WaterfallChart","GeoMap","Waveform","SpectrumAnalyzer","MultiSegmentDisplay","CustomInstrument"):
        signal_specs[(_type,"onChange")]="valueChanged"
        signal_specs[(_type,"onAlarm")]="alarmChanged"
    signal_specs[("DashboardCanvas","onChange")]="sceneChanged"
    signal_specs[("GridCanvas","onCellClick")]="cellClicked"
    lines.append("")
    for node in nodes:
        node_type, node_id = node["type"], node["id"]
        for (expected_type, port), signal_name in signal_specs.items():
            if node_type == expected_type and event_connections.get((node_id, port)):
                signal_map[(node_id, port)] = f"{attribute(node_id)}.{signal_name}"
                lines.append(f"        {attribute(node_id)}.{signal_name}.connect(self.{event_method(node_id, port)})")
        if (
            node_type.startswith("Delphi::")
            and COMPONENTS[node_type].visual
        ):
            original = node_type.split("::", 1)[1].lower()
            candidates: dict[str, str] = {}
            if any(token in original for token in ("button", "bitbtn", "imgbtn")):
                candidates["onClick"] = "clicked"
            elif original == "label":
                candidates["onClick"] = "clicked"
            elif "checkbox" in original:
                candidates.update({"onClick": "clicked", "onCheck": "toggled", "onChange": "toggled"})
            elif any(token in original for token in ("edit", "memo", "richedit")):
                candidates["onChange"] = "textChanged"
                if original == "edit":
                    candidates["onEnter"] = "returnPressed"
            elif "combobox" in original:
                candidates.update({"onChange": "currentIndexChanged", "onSelect": "currentIndexChanged"})
            elif "listbox" in original:
                candidates.update({"onChange": "currentRowChanged", "onSelect": "currentRowChanged"})
            elif any(token in original for token in ("progress", "trackbar", "scrollbar", "updown", "spin")):
                candidates["onChange"] = "valueChanged"
            for port, signal_name in candidates.items():
                if event_connections.get((node_id, port)):
                    signal_map[(node_id, port)] = (
                        f"{attribute(node_id)}.{signal_name}"
                    )
                    lines.append(
                        f"        {attribute(node_id)}.{signal_name}.connect("
                        f"self.{event_method(node_id, port)})"
                    )

    # Game and keyboard event sources are attached after widgets exist.
    for node in nodes:
        if node.get("type") == "TetrisGame" and (event_connections.get((node["id"], "onChange")) or event_connections.get((node["id"], "onGameOver"))):
            lines.append(f"        {attribute(node['id'])}.board.changed.connect(self.{event_method(node['id'], 'onChange')})")
    for node in nodes:
        if node.get("type") == "Debounce" and event_connections.get((node["id"], "onEvent")):
            lines.append(f"        {attribute(node['id'])}.timeout.connect(self.{event_method(node['id'], 'onEvent')})")
    if any(node.get("type") in {"KeyboardInput", "MouseInput"} for node in nodes):
        lines.append("        QApplication.instance().installEventFilter(self)")

    # Two-way bindings are attached after every widget has been created.
    for node in nodes:
        if node.get("type") != "TwoWayBinding":
            continue
        node_id = node["id"]
        props = node.get("properties", {})
        target_name = safe_name(str(props.get("target", "")), "")
        property_name = str(props.get("property", "text"))
        signal_name = {"text": "textChanged", "value": "valueChanged", "checked": "toggled", "currentIndex": "currentIndexChanged"}.get(property_name, "")
        if target_name and signal_name:
            lines += [
                f"        self.{target_name}.{signal_name}.connect(self.{method_token(node_id, 'changed', 'binding')})",
                f"        self._write_binding(self.{target_name}, {property_name!r}, {attribute(node_id, 'binding_value_')})",
            ]

    delayed_events: list[tuple[str, str]] = []
    for node in nodes:
        if node["type"] == "Start" and event_connections.get((node["id"], "onStart")):
            delayed_events.append((node["id"], "onStart"))
        if node["type"] == "Form" and event_connections.get((node["id"], "onCreate")):
            delayed_events.append((node["id"], "onCreate"))
        if node["type"] == "Timer" and node.get("properties", {}).get("active", False):
            lines.append(f"        {attribute(node['id'])}.start()")
    for node_id, port in delayed_events:
        lines.append(f"        QTimer.singleShot(0, self.{event_method(node_id, port)})")
    lines.append("")

    action_targets = {
        (connection["to_node"], connection["to_port"])
        for group in event_connections.values()
        for connection in group
    }

    def action_body(node: dict[str, Any], port: str) -> list[str]:
        node_type, node_id = node["type"], node["id"]
        props, ref = node.get("properties", {}), attribute(node_id)
        body: list[str] = []

        def event(port_name: str, indent: str = "        "):
            body.extend(dispatch_lines(node_id, port_name, indent))

        if node_type in visual_types and port in {"doShow","doHide","doEnable","doDisable","doFocus","doRaise","doLower","doMove","doResize","doSetStyle"}:
            if port == "doShow": body.append(f"        {ref}.show()")
            elif port == "doHide": body.append(f"        {ref}.hide()")
            elif port == "doEnable": body.append(f"        {ref}.setEnabled(True)")
            elif port == "doDisable": body.append(f"        {ref}.setEnabled(False)")
            elif port == "doFocus": body.append(f"        {ref}.setFocus()")
            elif port == "doRaise": body.append(f"        {ref}.raise_()")
            elif port == "doLower": body.append(f"        {ref}.lower()")
            elif port == "doMove": body.append(f"        {ref}.move(int({input_expression(node,'X',props.get('x',0),True)}), int({input_expression(node,'Y',props.get('y',0),True)}))")
            elif port == "doResize": body.append(f"        {ref}.resize(int({input_expression(node,'Width',props.get('width',120),True)}), int({input_expression(node,'Height',props.get('height',32),True)}))")
            elif port == "doSetStyle": body.append(f"        {ref}.setStyleSheet(str({input_expression(node,'StyleValue',props.get('style',''))}))")
        elif node_type == "ForRange":
            if port=="doBreak": body.append(f"        {attribute(node_id,'loop_break_')} = True")
            elif port=="doLoop":
                a=input_expression(node,"Start",props.get("start",0),True); b=input_expression(node,"Stop",props.get("stop",10),True); step=input_expression(node,"Step",props.get("step",1),True)
                body += [f"        {attribute(node_id,'loop_break_')} = False",f"        for _index in range(int({a}),int({b}),int({step}) or 1):",f"            {attribute(node_id,'loop_index_')} = _index",f"            if {attribute(node_id,'loop_break_')}: break"] + (dispatch_lines(node_id,"onIteration","            ") or ["            pass"]); event("onDone")
        elif node_type == "ForEach":
            if port=="doBreak": body.append(f"        {attribute(node_id,'loop_break_')} = True")
            elif port=="doLoop":
                items=input_expression(node,"Items",props.get("items","[]")); body += [f"        {attribute(node_id,'loop_break_')} = False",f"        _items={items}","        _iterator=_items.items() if isinstance(_items,dict) else enumerate(_items or [])","        for _index,_item in _iterator:",f"            {attribute(node_id,'loop_index_')}=_index",f"            {attribute(node_id,'loop_item_')}=_item",f"            if {attribute(node_id,'loop_break_')}: break"] + (dispatch_lines(node_id,"onIteration","            ") or ["            pass"]); event("onDone")
        elif node_type == "WhileLoop":
            if port=="doBreak": body.append(f"        {attribute(node_id,'loop_break_')} = True")
            elif port=="doLoop":
                cond=input_expression(node,"Condition",props.get("condition",True),True); limit=max(1,int(props.get("max_iterations",1000))); body += [f"        {attribute(node_id,'loop_break_')}=False",f"        {attribute(node_id,'loop_limit_')}=False",f"        for _index in range({limit}):",f"            if not bool({cond}) or {attribute(node_id,'loop_break_')}: break",f"            {attribute(node_id,'loop_index_')}=_index"] + (dispatch_lines(node_id,"onIteration","            ") or ["            pass"]) + ["        else:",f"            {attribute(node_id,'loop_limit_')}=True"]; event("onDone")
        elif node_type == "Sequence" and port=="doRun":
            for output in ("onStep1","onStep2","onStep3","onStep4","onDone"): event(output)
        elif node_type == "EventGate":
            if port=="doOpen": body.append(f"        {attribute(node_id,'gate_')}=True")
            elif port=="doClose": body.append(f"        {attribute(node_id,'gate_')}=False")
            elif port=="doToggle": body.append(f"        {attribute(node_id,'gate_')}=not {attribute(node_id,'gate_')}")
            elif port=="doInput": body += [f"        if {attribute(node_id,'gate_')}:"] + (dispatch_lines(node_id,"onPass","            ") or ["            pass"])
        elif node_type == "Once":
            if port=="doReset": body.append(f"        {attribute(node_id,'once_')}=False")
            elif port=="doInput": body += [f"        if not {attribute(node_id,'once_')}:",f"            {attribute(node_id,'once_')}=True"] + (dispatch_lines(node_id,"onFirst","            ") or ["            pass"]) + ["        else:"] + (dispatch_lines(node_id,"onRepeat","            ") or ["            pass"])
        elif node_type == "Debounce":
            if port=="doCancel": body.append(f"        {ref}.stop()")
            elif port=="doInput": body.append(f"        {ref}.start(max(1,int({input_expression(node,'Interval',props.get('interval',250),True)})))")
        elif node_type == "Throttle":
            if port=="doReset": body.append(f"        {attribute(node_id,'throttle_')}=0.0")
            elif port=="doInput":
                interval=input_expression(node,"Interval",props.get("interval",100),True); body += ["        _now=time.monotonic()",f"        if (_now-{attribute(node_id,'throttle_')})*1000 >= max(1,float({interval})):",f"            {attribute(node_id,'throttle_')}=_now"] + (dispatch_lines(node_id,"onEvent","            ") or ["            pass"]) + ["        else:"] + (dispatch_lines(node_id,"onSkipped","            ") or ["            pass"])
        elif node_type == "DictStore":
            d=attribute(node_id,"dict_"); key=input_expression(node,"Key",""); value=input_expression(node,"Value","")
            if port=="doSet": body.append(f"        {d}[{key}]={value}")
            elif port=="doRemove": body.append(f"        {d}.pop({key},None)")
            elif port=="doClear": body.append(f"        {d}.clear()")
            event("onChange")
        elif node_type == "ConvertValue" and port=="doConvert":
            value=input_expression(node,"Value",""); target=str(props.get("target_type","string")); result=attribute(node_id,"convert_"); error=attribute(node_id,"convert_error_"); conv={"string":f"str({value})","integer":f"int({value})","float":f"float({value})","boolean":f"bool({value})","list":f"list({value})","dictionary":f"dict({value})","json":f"json.loads(str({value}))"}.get(target,value)
            body += ["        try:",f"            {result}={conv}",f"            {error}=''" ] + (dispatch_lines(node_id,"onResult","            ") or ["            pass"]) + ["        except Exception as exc:",f"            {result}={python_literal(props.get('default',None))}",f"            {error}=str(exc)"] + (dispatch_lines(node_id,"onError","            ") or ["            pass"])
        elif node_type == "Geometry2D" and port=="doCalculate":
            v={n:input_expression(node,n,0,True) for n in ("AX","AY","AWidth","AHeight","BX","BY","BWidth","BHeight")}; op=str(props.get("operation","intersects")); rr=attribute(node_id,"geometry_result_"); dd=attribute(node_id,"geometry_distance_"); xx=attribute(node_id,"geometry_x_"); yy=attribute(node_id,"geometry_y_")
            body += [f"        _ax,_ay,_aw,_ah=map(float,({v['AX']},{v['AY']},{v['AWidth']},{v['AHeight']}))",f"        _bx,_by,_bw,_bh=map(float,({v['BX']},{v['BY']},{v['BWidth']},{v['BHeight']}))",f"        {dd}=math.hypot(_bx-_ax,_by-_ay)"]
            if op=="intersects": body.append(f"        {rr}=_ax<_bx+_bw and _ax+_aw>_bx and _ay<_by+_bh and _ay+_ah>_by")
            elif op=="contains": body.append(f"        {rr}=_ax<=_bx and _ay<=_by and _bx+_bw<=_ax+_aw and _by+_bh<=_ay+_ah")
            elif op=="clamp_point": body += [f"        {xx}=min(max(_bx,_ax),_ax+_aw)",f"        {yy}=min(max(_by,_ay),_ay+_ah)",f"        {rr}=True"]
            else: body.append(f"        {rr}=True")
            event("onResult")
        elif node_type == "RepeatLoop":
            if port == "doBreak":
                body.append(f"        {attribute(node_id, 'loop_break_')} = True")
            elif port == "doLoop":
                count = input_expression(node, "Count", props.get("count", 10), True)
                body += [f"        {attribute(node_id, 'loop_break_')} = False", f"        for _index in range(max(0, int({count}))):", f"            {attribute(node_id, 'loop_index_')} = _index", f"            if {attribute(node_id, 'loop_break_')}: break"]
                body += dispatch_lines(node_id, "onIteration", "            ") or ["            pass"]
                event("onDone")
        elif node_type == "ListStore":
            index = input_expression(node, "Index", 0, True); value = input_expression(node, "Value", "")
            if port == "doAdd": body.append(f"        {attribute(node_id, 'list_')}.append({value})")
            elif port == "doSet":
                body += [f"        _index = int({index})", f"        if -len({attribute(node_id, 'list_')}) <= _index < len({attribute(node_id, 'list_')}):", f"            {attribute(node_id, 'list_')}[_index] = {value}", f"            {attribute(node_id, 'list_item_')} = {attribute(node_id, 'list_')}[_index]"]
            elif port == "doRemove":
                body += [f"        _index = int({index})", f"        if -len({attribute(node_id, 'list_')}) <= _index < len({attribute(node_id, 'list_')}):", f"            {attribute(node_id, 'list_item_')} = {attribute(node_id, 'list_')}.pop(_index)"]
            elif port == "doClear": body.append(f"        {attribute(node_id, 'list_')}.clear()")
            event("onChange")
        elif node_type == "GridState":
            col=input_expression(node,"Column",0,True); row=input_expression(node,"Row",0,True); value=input_expression(node,"Value",props.get("empty",0))
            grid=attribute(node_id,'grid_')
            if port in {"doSetCell","doClearCell"}:
                cell_value = value if port == "doSetCell" else python_literal(props.get("empty",0))
                body += [f"        _col, _row = int({col}), int({row})", f"        if 0 <= _row < len({grid}) and 0 <= _col < len({grid}[_row]):", f"            {grid}[_row][_col] = {cell_value}"]
                event("onChange")
            elif port == "doClear":
                body += [f"        for _row in {grid}:", f"            _row[:] = [{python_literal(props.get('empty',0))}] * len(_row)"]
                event("onChange")
            elif port == "doClearLines":
                empty=python_literal(props.get("empty",0)); cleared=attribute(node_id,'cleared_lines_')
                body += [f"        _width = len({grid}[0]) if {grid} else 0", f"        _kept = [_row for _row in {grid} if not all(_cell != {empty} for _cell in _row)]", f"        {cleared} = len({grid}) - len(_kept)", f"        {grid}[:] = [[{empty}] * _width for _ in range({cleared})] + _kept"]
                event("onLines"); event("onChange")
        elif node_type == "GridBatchWriter" and port in {"doWrite", "doClear"}:
            grid_value = input_expression(node, "Grid", [])
            points_value = input_expression(node, "Points", [])
            offset_column = input_expression(node, "OffsetColumn", 0, True)
            offset_row = input_expression(node, "OffsetRow", 0, True)
            write_value = (
                python_literal(props.get("empty", 0))
                if port == "doClear"
                else input_expression(node, "Value", 1)
            )
            target = attribute(node_id, "grid_batch_")
            changed = attribute(node_id, "grid_batch_changed_")
            error = attribute(node_id, "grid_batch_error_")
            body += [
                f"        {target} = {grid_value}",
                f"        {changed} = 0",
                f"        {error} = ''",
                "        try:",
                f"            _points = {points_value}",
                "            if isinstance(_points, str):",
                "                _points = json.loads(_points or '[]')",
                "            if not isinstance(_points, (list, tuple)):",
                "                raise ValueError('Набор координат должен быть списком')",
                f"            _offset_column = int({offset_column})",
                f"            _offset_row = int({offset_row})",
                "            for _point in _points:",
                "                if isinstance(_point, dict):",
                "                    _column = int(_point.get('x', 0)) + _offset_column",
                "                    _row = int(_point.get('y', 0)) + _offset_row",
                "                elif isinstance(_point, (list, tuple)) and len(_point) >= 2:",
                "                    _column = int(_point[0]) + _offset_column",
                "                    _row = int(_point[1]) + _offset_row",
                "                else:",
                "                    continue",
                f"                if 0 <= _row < len({target}) and 0 <= _column < len({target}[_row]):",
                f"                    {target}[_row][_column] = {write_value}",
                f"                    {changed} += 1",
            ]
            body += dispatch_lines(
                node_id, "onDone", "            "
            ) or ["            pass"]
            body += [
                "        except Exception as exc:",
                f"            {error} = str(exc)",
            ]
            body += dispatch_lines(
                node_id, "onError", "            "
            ) or ["            pass"]
        elif node_type == "TetrisGame":
            methods={"doStart":"start", "doPause":"toggle_pause", "doRestart":"reset", "doLeft":"move(-1, 0)", "doRight":"move(1, 0)", "doRotate":"rotate", "doSoftDrop":"soft_drop", "doHardDrop":"hard_drop"}
            call=methods.get(port)
            if call:
                body.append(f"        {ref}.board.{call}()" if "(" not in call else f"        {ref}.board.{call}")
                body.append(f"        {ref}.board.setFocus()")
        elif node_type == "TwoWayBinding":
            target_name = safe_name(str(props.get("target", "")), "")
            property_name = str(props.get("property", "text"))
            if port == "doSet":
                body += [
                    f"        if not {attribute(node_id, 'binding_guard_')}:",
                    f"            {attribute(node_id, 'binding_guard_')} = True",
                    "            try:",
                    f"                {attribute(node_id, 'binding_value_')} = {input_expression(node, 'Value', props.get('initial', ''))}",
                    f"                self._write_binding(self.{target_name}, {property_name!r}, {attribute(node_id, 'binding_value_')})",
                    "            finally:",
                    f"                {attribute(node_id, 'binding_guard_')} = False",
                ]
                event("onChange")
            elif port == "doRefresh":
                body.append(f"        {attribute(node_id, 'binding_value_')} = self._read_binding(self.{target_name}, {property_name!r})")
                event("onChange")
        elif node_type == "Hub" and port == "doEvent":
            for output in ("onEvent1", "onEvent2", "onEvent3"):
                event(output)
        elif node_type == "EventHub" and port.startswith("doInput"):
            for output in (p.name for p in effective_ports(node_type, props) if p.kind == "event_out"):
                event(output)
        elif node_type == "IfElse" and port == "doCompare":
            op1 = input_expression(node, "Op1", props.get("op1", ""))
            op2 = input_expression(node, "Op2", props.get("op2", ""))
            body.append(f"        if {op1} {props.get('operator', '==')} {op2}:")
            body += dispatch_lines(node_id, "onTrue", "            ") or ["            pass"]
            body.append("        else:")
            body += dispatch_lines(node_id, "onFalse", "            ") or ["            pass"]
        elif node_type == "Memory":
            if port == "doValue":
                body.append(f"        {attribute(node_id, 'memory_')} = {input_expression(node, 'Data', props.get('default', ''))}")
                event("onData")
            elif port == "doClear":
                body.append(f"        {attribute(node_id, 'memory_')} = None")
                event("onData")
        elif node_type == "Math" and port == "doOperation":
            op1 = input_expression(node, "Op1", float(props.get("op1", 0)), True)
            op2 = input_expression(node, "Op2", float(props.get("op2", 0)), True)
            body.append(f"        {attribute(node_id, 'result_')} = {op1} {props.get('operator', '+')} {op2}")
            event("onResult")
        elif node_type == "FormatStr" and port == "doFormat":
            values = [input_expression(node, f"Data{i}", "") for i in range(1, 4)]
            body.append(f"        {attribute(node_id, 'result_')} = {py_string(props.get('template', '{0}'))}.format({', '.join(values)})")
            event("onResult")
        elif node_type == "Timer":
            if port == "doStart":
                interval = input_expression(node, "Interval", int(props.get("interval", 1000)), True)
                body.append(f"        {ref}.start(int({interval}))")
            elif port == "doStop":
                body.append(f"        {ref}.stop()")
        elif node_type == "FileRead" and port == "doRead":
            path = input_expression(node, "Path", props.get("path", ""))
            encoding = py_string(props.get("encoding", "utf-8"))
            body += ["        try:", f"            {attribute(node_id, 'text_')} = Path({path}).read_text(encoding={encoding})", f"            {attribute(node_id, 'error_')} = ''"]
            body += dispatch_lines(node_id, "onRead", "            ") or ["            pass"]
            body += ["        except Exception as exc:", f"            {attribute(node_id, 'error_')} = str(exc)"]
            body += dispatch_lines(node_id, "onError", "            ") or ["            pass"]
        elif node_type == "FileWrite" and port == "doWrite":
            path = input_expression(node, "Path", props.get("path", ""))
            text = input_expression(node, "Text", props.get("text", ""))
            encoding = py_string(props.get("encoding", "utf-8"))
            mode = "'a'" if props.get("append", False) else "'w'"
            body += ["        try:", f"            with Path({path}).open({mode}, encoding={encoding}) as stream:", f"                stream.write(str({text}))", f"            {attribute(node_id, 'error_')} = ''"]
            body += dispatch_lines(node_id, "onWrite", "            ") or ["            pass"]
            body += ["        except Exception as exc:", f"            {attribute(node_id, 'error_')} = str(exc)"]
            body += dispatch_lines(node_id, "onError", "            ") or ["            pass"]
        elif node_type == "DebugPrint" and port == "doPrint":
            value = (
                input_expression(node, "Data", "")
                if (node_id, "Data") in data_connections
                else "(_data if _data is not None else '')"
            )
            body.append(
                f"        print({py_string(props.get('prefix', ''))} "
                f"+ str({value}), flush=True)"
            )
            event("onPrint")
        elif node_type == "Label":
            if port == "doSetText":
                body.append(f"        {ref}.setText(str({input_expression(node, 'Text', props.get('text', ''))}))")
            elif port == "doClear": body.append(f"        {ref}.clear()")
            elif port == "doShow": body.append(f"        {ref}.show()")
            elif port == "doHide": body.append(f"        {ref}.hide()")
        elif node_type == "Button":
            if port == "doClick": body.append(f"        {ref}.click()")
            elif port == "doSetText": body.append(f"        {ref}.setText(str({input_expression(node, 'Text', props.get('text', ''))}))")
            elif port == "doEnable": body.append(f"        {ref}.setEnabled(True)")
        elif node_type == "LineEdit":
            if port == "doSetText": body.append(f"        {ref}.setText(str({input_expression(node, 'Value', props.get('text', ''))}))")
            elif port == "doClear": body.append(f"        {ref}.clear()")
            elif port == "doFocus": body.append(f"        {ref}.setFocus()")
        elif node_type == "TextEdit":
            value = input_expression(node, "Value", props.get("text", ""))
            if port == "doSetText": body.append(f"        {ref}.setPlainText(str({value}))")
            elif port == "doAppend": body.append(f"        {ref}.append(str({value}))")
            elif port == "doClear": body.append(f"        {ref}.clear()")
        elif node_type == "CheckBox":
            if port == "doCheck": body.append(f"        {ref}.setChecked(bool({input_expression(node, 'State', props.get('checked', False))}))")
            elif port == "doToggle": body.append(f"        {ref}.toggle()")
        elif node_type == "ComboBox":
            if port == "doSelect": body.append(f"        {ref}.setCurrentIndex(int({input_expression(node, 'Index', props.get('current_index', 0))}))")
            elif port == "doAdd": body.append(f"        {ref}.addItem(str({input_expression(node, 'Item', '')}))")
            elif port == "doClear": body.append(f"        {ref}.clear()")
        elif node_type == "ListWidget":
            if port == "doAdd":
                body.append(f"        {ref}.addItem(str({input_expression(node, 'Item', '')}))")
            elif port == "doClear":
                body.append(f"        {ref}.clear()")
            elif port == "doSelect":
                body.append(f"        {ref}.setCurrentRow(int({input_expression(node, 'Index', props.get('current_index', 0))}))")
        elif node_type == "ProgressBar" and port == "doValue":
            body.append(f"        {ref}.setValue(int({input_expression(node, 'Value', props.get('value', 0))}))")
        elif node_type == "Slider" and port == "doValue":
            body.append(f"        {ref}.setValue(int({input_expression(node, 'NewValue', props.get('value', 0))}))")
        elif node_type == "SpinBox" and port == "doValue":
            body.append(f"        {ref}.setValue(int({input_expression(node, 'NewValue', props.get('value', 0))}))")
        elif node_type in {"OpenFileDialog", "SaveFileDialog"}:
            expected_port = "doOpen" if node_type == "OpenFileDialog" else "doSave"
            if port == expected_port:
                dialog_method = "getOpenFileName" if node_type == "OpenFileDialog" else "getSaveFileName"
                body.append(
                    f"        {attribute(node_id, 'filename_')}, _ = QFileDialog.{dialog_method}("
                    f"self, {py_string(props.get('title', 'Выбор файла'))}, "
                    f"{py_string(props.get('directory', ''))}, {py_string(props.get('filter', 'Все файлы (*.*)'))})"
                )
                body.append(f"        if {attribute(node_id, 'filename_')}:")
                body += dispatch_lines(node_id, "onSelect", "            ") or ["            pass"]
                body.append("        else:")
                body += dispatch_lines(node_id, "onCancel", "            ") or ["            pass"]
        elif node_type == "Delay" and port == "doStart":
            interval = input_expression(node, "Interval", int(props.get("interval", 1000)), True)
            body.append(
                f"        QTimer.singleShot(int({interval}), self.{event_method(node_id, 'onDone')})"
            )
        elif node_type == "Counter":
            if port == "doNext":
                body.append(f"        {attribute(node_id, 'counter_')} += {int(props.get('step', 1))}")
                event("onValue")
            elif port == "doReset":
                body.append(f"        {attribute(node_id, 'counter_')} = {int(props.get('start', 0))}")
                event("onValue")
        elif node_type == "Random" and port == "doRandom":
            minimum = input_expression(node, "Minimum", int(props.get("minimum", 0)), True)
            maximum = input_expression(node, "Maximum", int(props.get("maximum", 100)), True)
            body.append(
                f"        {attribute(node_id, 'result_')} = random.randint(int({minimum}), int({maximum}))"
            )
            event("onResult")
        elif node_type == "HTTPGet" and port == "doRequest":
            url = input_expression(node, "URL", props.get("url", ""))
            timeout = int(props.get("timeout", 15))
            encoding = py_string(props.get("encoding", "utf-8"))
            body += [
                "        try:",
                f"            with urllib.request.urlopen(str({url}), timeout={timeout}) as response:",
                f"                {attribute(node_id, 'status_')} = int(response.status)",
                f"                {attribute(node_id, 'text_')} = response.read().decode({encoding}, errors='replace')",
                f"            {attribute(node_id, 'error_')} = ''",
            ]
            body += dispatch_lines(node_id, "onSuccess", "            ") or ["            pass"]
            body += [
                "        except Exception as exc:",
                f"            {attribute(node_id, 'error_')} = str(exc)",
            ]
            body += dispatch_lines(node_id, "onError", "            ") or ["            pass"]
        elif node_type == "RunProcess" and port == "doRun":
            program = input_expression(node, "Program", props.get("program", ""))
            arguments = input_expression(node, "Arguments", props.get("arguments", ""))
            timeout = int(props.get("timeout", 30))
            body += [
                "        try:",
                f"            command = [str({program})] + shlex.split(str({arguments}))",
                f"            result = subprocess.run(command, capture_output=True, text=True, timeout={timeout})",
                f"            {attribute(node_id, 'output_')} = result.stdout",
                f"            {attribute(node_id, 'exitcode_')} = result.returncode",
                f"            {attribute(node_id, 'error_')} = result.stderr",
            ]
            body += dispatch_lines(node_id, "onDone", "            ") or ["            pass"]
            body += [
                "        except Exception as exc:",
                f"            {attribute(node_id, 'error_')} = str(exc)",
            ]
            body += dispatch_lines(node_id, "onError", "            ") or ["            pass"]
        elif node_type == "TableWidget":
            if port == "doSetCell":
                row = input_expression(node, "Row", 0, True)
                column = input_expression(node, "Column", 0, True)
                value = input_expression(node, "Value", "")
                body += [f"        row, column = int({row}), int({column})", f"        if row >= {ref}.rowCount(): {ref}.setRowCount(row + 1)", f"        if column >= {ref}.columnCount(): {ref}.setColumnCount(column + 1)", f"        {ref}.setItem(row, column, QTableWidgetItem(str({value})))"]
            elif port == "doClear":
                body.append(f"        {ref}.clearContents()")
        elif node_type == "TreeWidget":
            if port == "doAdd":
                body.append(f"        {ref}.addTopLevelItem(QTreeWidgetItem([str({input_expression(node, 'Item', '')})]))")
            elif port == "doClear":
                body.append(f"        {ref}.clear()")
        elif node_type in {"DateEdit", "Calendar"} and port == "doSetDate":
            value = input_expression(node, "Date", props.get("date", "2026-01-01"))
            method = "setDate" if node_type == "DateEdit" else "setSelectedDate"
            body.append(f"        {ref}.{method}(QDate.fromString(str({value}), 'yyyy-MM-dd'))")
        elif node_type == "LCDNumber" and port == "doValue":
            body.append(f"        {ref}.display(float({input_expression(node, 'Value', props.get('value', 0), True)}))")
        elif node_type == "JSONParse" and port == "doParse":
            text = input_expression(node, "Text", props.get("text", "{}"))
            body += ["        try:", f"            {attribute(node_id, 'value_')} = json.loads(str({text}))", f"            {attribute(node_id, 'error_')} = ''"]
            body += dispatch_lines(node_id, "onSuccess", "            ") or ["            pass"]
            body += ["        except Exception as exc:", f"            {attribute(node_id, 'error_')} = str(exc)"]
            body += dispatch_lines(node_id, "onError", "            ") or ["            pass"]
        elif node_type == "JSONStringify" and port == "doEncode":
            data = input_expression(node, "Data", {})
            body.append(f"        {attribute(node_id, 'text_')} = json.dumps({data}, ensure_ascii={bool(props.get('ensure_ascii', False))!r}, indent={int(props.get('indent', 2))})")
            event("onResult")
        elif node_type == "SQLiteQuery" and port == "doQuery":
            database = input_expression(node, "Database", props.get("database", "data.db"))
            sql = input_expression(node, "SQL", props.get("sql", "SELECT 1"))
            body += ["        try:", f"            with sqlite3.connect(str({database})) as connection:", f"                cursor = connection.execute(str({sql}))", f"                {attribute(node_id, 'rows_')} = cursor.fetchall() if cursor.description else []"]
            if props.get("commit", True): body.append("                connection.commit()")
            body += [f"            {attribute(node_id, 'error_')} = ''"]
            body += dispatch_lines(node_id, "onSuccess", "            ") or ["            pass"]
            body += ["        except Exception as exc:", f"            {attribute(node_id, 'error_')} = str(exc)"]
            body += dispatch_lines(node_id, "onError", "            ") or ["            pass"]
        elif node_type == "Clipboard":
            if port == "doSet":
                body.append(f"        QApplication.clipboard().setText(str({input_expression(node, 'Text', props.get('text', ''))}))")
            elif port == "doGet":
                body.append(f"        {attribute(node_id, 'clipboard_')} = QApplication.clipboard().text()")
                event("onText")
            elif port == "doClear":
                body.append("        QApplication.clipboard().clear()")
        elif node_type == "MessageBox" and port == "doShow":
            text = input_expression(node, "Text", props.get("text", "Готово"))
            dialog_title = input_expression(node, "Title", props.get("title", "Сообщение"))
            body.append(
                f"        {attribute(node_id, 'message_result_')} = "
                f"QMessageBox.information(self, str({dialog_title}), str({text})).name"
            )
            event("onResult")
        elif node_type == "RadioButton":
            if port == "doCheck": body.append(f"        {ref}.setChecked(bool({input_expression(node,'State',props.get('checked',False))}))")
            elif port == "doToggle": body.append(f"        {ref}.toggle()")
        elif node_type == "GroupBox":
            if port == "doSetTitle": body.append(f"        {ref}.setTitle(str({input_expression(node,'Title',props.get('title','Группа'))}))")
            elif port == "doCheck": body.append(f"        {ref}.setChecked(bool({input_expression(node,'State',props.get('checked',True))}))")
        elif node_type == "Dial" and port == "doValue": body.append(f"        {ref}.setValue(int({input_expression(node,'NewValue',props.get('value',50))}))")
        elif node_type == "ToolButton":
            if port == "doClick": body.append(f"        {ref}.click()")
            elif port == "doSetText": body.append(f"        {ref}.setText(str({input_expression(node,'Text',props.get('text',''))}))")
        elif node_type == "PlainTextEdit":
            value=input_expression(node,'Value',props.get('text',''))
            if port == "doSetText": body.append(f"        {ref}.setPlainText(str({value}))")
            elif port == "doAppend": body.append(f"        {ref}.appendPlainText(str({value}))")
            elif port == "doClear": body.append(f"        {ref}.clear()")
        elif node_type == "DoubleSpinBox" and port == "doValue":
            body.append(f"        {ref}.setValue(float({input_expression(node,'NewValue',props.get('value',0.0),True)}))")
        elif node_type == "ScrollBar" and port == "doValue":
            body.append(f"        {ref}.setValue(int({input_expression(node,'NewValue',props.get('value',0),True)}))")
        elif node_type == "TimeEdit" and port == "doSetTime":
            body.append(f"        {ref}.setTime(QTime.fromString(str({input_expression(node,'Time',props.get('time','12:00:00'))}), 'HH:mm:ss'))")
        elif node_type == "DateTimeEdit" and port == "doSetDateTime":
            body.append(f"        {ref}.setDateTime(QDateTime.fromString(str({input_expression(node,'DateTime',props.get('datetime','2026-09-22T12:00:00'))}), Qt.DateFormat.ISODate))")
        elif node_type == "TextBrowser":
            value=input_expression(node,'Value',props.get('html',''))
            if port == "doSetHtml": body.append(f"        {ref}.setHtml(str({value}))")
            elif port == "doSetText": body.append(f"        {ref}.setPlainText(str({value}))")
            elif port == "doClear": body.append(f"        {ref}.clear()")
        elif node_type == "FontComboBox" and port == "doSetFont":
            body.append(f"        {ref}.setCurrentFont(QFont(str({input_expression(node,'Family',props.get('family','Segoe UI'))})))")
        elif node_type == "KeySequenceEdit":
            if port == "doSetSequence": body.append(f"        {ref}.setKeySequence(QKeySequence(str({input_expression(node,'Sequence',props.get('sequence',''))})))")
            elif port == "doClear": body.append(f"        {ref}.clear()")
        elif node_type == "CommandLinkButton":
            if port == "doClick": body.append(f"        {ref}.click()")
            elif port == "doSetText": body.append(f"        {ref}.setText(str({input_expression(node,'Text',props.get('text',''))}))")
            elif port == "doSetDescription": body.append(f"        {ref}.setDescription(str({input_expression(node,'Description',props.get('description',''))}))")
        elif node_type in {"Gauge","Speedometer","Tachometer","Thermometer","LevelMeter","LEDIndicator","Compass","BatteryIndicator","SignalIndicator","Sparkline","AnalogClock","Knob","LineChart","BarChart","PieChart","RadarChart","Oscilloscope","VUMeter","SevenSegmentDisplay","LEDMatrix","XYPlot","HeatMap","Timeline","WaterfallChart","GeoMap","Waveform","SpectrumAnalyzer","MultiSegmentDisplay","CustomInstrument"}:
            if port == "doValue": body.append(f"        {ref}.setValue(float({input_expression(node,'NewValue',props.get('value',0.0),True)}))")
            elif port == "doSetRange": body.append(f"        {ref}.setRange(float({input_expression(node,'Minimum',props.get('minimum',0.0),True)}), float({input_expression(node,'Maximum',props.get('maximum',100.0),True)}))")
            elif port == "doSetTitle": body.append(f"        {ref}.setTitle(str({input_expression(node,'Title',props.get('title',''))}))")
            elif port == "doAddValue": body.append(f"        {ref}.appendValue(float({input_expression(node,'Sample',props.get('value',0.0),True)}))")
            elif port == "doReset": body.append(f"        {ref}.reset()")
            elif port == "doAddPoint": body.append(f"        {ref}.appendPoint(float({input_expression(node,'XValue',0.0,True)}), float({input_expression(node,'YValue',props.get('value',0.0),True)}))")
            elif port == "doSetCell": body.append(f"        {ref}.setHeatCell(int({input_expression(node,'Row',0,True)}), int({input_expression(node,'Column',0,True)}), float({input_expression(node,'Intensity',props.get('value',0.0),True)}))")
            elif port == "doAddEvent": body.append(f"        {ref}.appendTimeline(str({input_expression(node,'Timestamp','')}), str({input_expression(node,'EventText','')}), float({input_expression(node,'Sample',props.get('value',0.0),True)}))")
            elif port == "doSetPosition": body.append(f"        {ref}.setPosition(float({input_expression(node,'Latitude',props.get('latitude',55.7558),True)}), float({input_expression(node,'Longitude',props.get('longitude',37.6173),True)}), int({input_expression(node,'Zoom',props.get('zoom',8),True)}))")
            elif port == "doSetDesign": body.append(f"        {ref}.setDesign({input_expression(node,'Design',props.get('design','{}'))})")
            elif port == "doAddSeriesPoint": body.append(f"        {ref}.appendSeriesPoint(str({input_expression(node,'SeriesName','Серия 1')}), float({input_expression(node,'SeriesX',0.0,True)}), float({input_expression(node,'SeriesY',0.0,True)}))")
            elif port == "doSetSeriesData": body.append(f"        {ref}.setSeriesData(str({input_expression(node,'SeriesName','Серия 1')}), {input_expression(node,'SeriesData','[]')})")
            elif port == "doClearSeries": body.append(f"        {ref}.clearSeries()")
            elif port == "doExportImage": body.append(f"        {ref}.exportImage(str({input_expression(node,'ExportPath','chart.png')}))"); event("onExport")
        elif node_type == "DashboardCanvas":
            if port == "doSetScene": body.append(f"        {ref}.setScene({input_expression(node,'Scene',props.get('scene','[]'))})")
            elif port == "doAddShape": body.append(f"        {ref}.addShape(str({input_expression(node,'ShapeType','rect')}), float({input_expression(node,'ShapeX',10,True)}), float({input_expression(node,'ShapeY',10,True)}), float({input_expression(node,'ShapeWidth',80,True)}), float({input_expression(node,'ShapeHeight',50,True)}), str({input_expression(node,'ShapeText','')}), str({input_expression(node,'ShapeColor','#35C2FF')}), float({input_expression(node,'ShapeRotation',0,True)}), int({input_expression(node,'ShapeLayer',0,True)}))")
            elif port == "doRemoveLast": body.append(f"        {ref}.removeLast()")
            elif port == "doClear": body.append(f"        {ref}.clearScene()")
            elif port == "doSetZoom": body.append(f"        {ref}.setZoom(float({input_expression(node,'Zoom',props.get('zoom',1.0),True)}))")
            elif port == "doExportImage": body.append(f"        {ref}.exportImage(str({input_expression(node,'ExportPath','dashboard.png')}))"); event("onExport")
        elif node_type == "GridCanvas":
            if port == "doSetGrid":
                body.append(
                    f"        {ref}.setGrid({input_expression(node,'Grid',props.get('initial_grid',''))})"
                )
            elif port == "doSetPalette":
                body.append(
                    f"        {ref}.setPalette({input_expression(node,'Palette',props.get('palette','{}'))})"
                )
            elif port == "doClear":
                body.append(f"        {ref}.clearGrid()")
            elif port == "doRefresh":
                body.append(f"        {ref}.update()")
        elif node_type == "Form":
            if port == "doShow": body.append("        self.show()")
            elif port == "doHide": body.append("        self.hide()")
            elif port == "doSetTitle": body.append(f"        self.setWindowTitle(str({input_expression(node,'Title',props.get('title',''))}))")
            elif port == "doMinimize": body.append("        self.showMinimized()")
            elif port == "doMaximize": body.append("        self.showMaximized()")
            elif port == "doFullScreen": body.append("        self.showFullScreen()")
            elif port == "doClose": body.append("        self.close()")
        elif node_type.startswith("Delphi::"):
            spec = COMPONENTS[node_type]
            instance_ports = effective_ports(node_type, props)
            inputs = {
                item.name: input_expression(
                    node, item.name, props.get(item.name)
                )
                for item in instance_ports
                if item.kind == "data_in"
            }
            if port == "doFont" and spec.visual:
                inputs["Font"] = "_data"
            elif port.startswith("do") and node_type != "Delphi::Font":
                inputs[port[2:]] = "_data"
            input_code = ", ".join(
                f"{name!r}: {expression}"
                for name, expression in inputs.items()
            )
            body.append(f"        inputs = {{{input_code}}}")
            if (
                node_type == "Delphi::Font"
                and port == "doFont"
                and bool(props.get("FontDialog", False))
            ):
                body += [
                    f"        selected_font, accepted = QFontDialog.getFont("
                    f"delphi_qfont({attribute(node_id, 'delphi_')}.get('Font')), "
                    f"self, 'Выбор шрифта')",
                    "        if accepted:",
                    "            style = (1 if selected_font.bold() else 0)",
                    "            style |= (2 if selected_font.italic() else 0)",
                    "            style |= (4 if selected_font.underline() else 0)",
                    "            style |= (8 if selected_font.strikeOut() else 0)",
                    "            inputs.update({",
                    "                'Name': selected_font.family(),",
                    "                'Size': max(1, selected_font.pointSize()),",
                    "                'Style': style,",
                    "            })",
                    f"            events = {attribute(node_id, 'delphi_')}.invoke("
                    f"{port!r}, inputs)",
                    "        else:",
                    "            events = ['onCancel']",
                ]
            else:
                body.append(
                    f"        events = {attribute(node_id, 'delphi_')}.invoke("
                    f"{port!r}, inputs)"
                )
            if spec.visual:
                body.append(
                    f"        apply_delphi_widget_action("
                    f"{ref}, {port!r}, {attribute(node_id, 'delphi_')}, inputs)"
                )
            for event_port in (
                item.name
                for item in instance_ports
                if item.kind == "event_out"
                and event_connections.get((node_id, item.name))
            ):
                body.append(f"        if {event_port!r} in events:")
                argument = (
                    f"{attribute(node_id, 'delphi_')}.get('Font')"
                    if node_type == "Delphi::Font"
                    and event_port == "onFont"
                    else (
                        "_data"
                        if node_type == "Delphi::Hub"
                        else None
                    )
                )
                body.extend(dispatch_lines(
                    node_id, event_port, "            ", argument
                ))
        return body or ["        pass"]

    lines += [
        "    @staticmethod",
        "    def _grid_cell(grid, column, row):",
        "        return grid[row][column] if 0 <= row < len(grid) and 0 <= column < len(grid[row]) else None",
        "",
        "    @staticmethod",
        "    def _key_name(event):",
        "        key = event.key()",
        "        names = {Qt.Key.Key_Left:'LEFT', Qt.Key.Key_Right:'RIGHT', Qt.Key.Key_Up:'UP', Qt.Key.Key_Down:'DOWN', Qt.Key.Key_Space:'SPACE', Qt.Key.Key_Return:'ENTER', Qt.Key.Key_Enter:'ENTER', Qt.Key.Key_Escape:'ESCAPE'}",
        "        return names.get(key, event.text().upper() or str(key))",
        "",
    ]
    keyboard_nodes = [node for node in nodes if node.get("type") == "KeyboardInput"]
    mouse_nodes = [node for node in nodes if node.get("type") == "MouseInput"]
    if keyboard_nodes or mouse_nodes:
        lines += ["    def eventFilter(self, watched, event):"]
        if keyboard_nodes:
            lines += ["        if event.type() in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):", "            _key = self._key_name(event)"]
            for node in keyboard_nodes:
                node_id=node["id"]; props=node.get("properties",{}); allowed=[x.strip().upper() for x in str(props.get("keys","")).replace(";",",").split(",") if x.strip()]
                condition=f"_key in {allowed!r}" if allowed else "True"
                lines += [f"            if {condition} and ({bool(props.get('accept_auto_repeat',True))!r} or not event.isAutoRepeat()):", f"                {attribute(node_id,'key_')}=_key", f"                {attribute(node_id,'key_repeat_')}=event.isAutoRepeat()", "                if event.type()==QEvent.Type.KeyPress:"]
                lines += dispatch_lines(node_id,"onPress","                    ") or ["                    pass"]
                lines += ["                else:"] + (dispatch_lines(node_id,"onRelease","                    ") or ["                    pass"])
        if mouse_nodes:
            lines += ["        if event.type() in (QEvent.Type.MouseButtonPress,QEvent.Type.MouseButtonRelease,QEvent.Type.MouseMove):", "            _point=event.position() if hasattr(event,'position') else event.pos()"]
            for node in mouse_nodes:
                node_id=node["id"]; props=node.get("properties",{})
                lines += [f"            {attribute(node_id,'mouse_x_')}=int(_point.x())", f"            {attribute(node_id,'mouse_y_')}=int(_point.y())", f"            {attribute(node_id,'mouse_button_')}=getattr(event.button(),'name',str(event.button()))", "            if event.type()==QEvent.Type.MouseButtonPress:"]
                lines += dispatch_lines(node_id,"onPress","                ") or ["                pass"]
                lines += ["            elif event.type()==QEvent.Type.MouseButtonRelease:"] + (dispatch_lines(node_id,"onRelease","                ") or ["                pass"])
                if bool(props.get("track_move",True)): lines += ["            else:"] + (dispatch_lines(node_id,"onMove","                ") or ["                pass"])
        lines += ["        return super().eventFilter(watched,event)", ""]
    lines += [
        "    @staticmethod",
        "    def _read_binding(widget, property_name):",
        "        if property_name == 'text': return widget.text() if hasattr(widget, 'text') else widget.toPlainText()",
        "        if property_name == 'value': return widget.value()",
        "        if property_name == 'checked': return widget.isChecked()",
        "        if property_name == 'currentIndex': return widget.currentIndex()",
        "        raise ValueError(f'Unsupported binding property: {property_name}')",
        "",
        "    @staticmethod",
        "    def _write_binding(widget, property_name, value):",
        "        blocker = QSignalBlocker(widget)",
        "        try:",
        "            if property_name == 'text':",
        "                (widget.setText if hasattr(widget, 'setText') else widget.setPlainText)(str(value))",
        "            elif property_name == 'value': widget.setValue(value)",
        "            elif property_name == 'checked': widget.setChecked(bool(value))",
        "            elif property_name == 'currentIndex': widget.setCurrentIndex(int(value))",
        "        finally:",
        "            del blocker",
        "",
    ]
    for node in nodes:
        if node.get("type") != "TwoWayBinding":
            continue
        node_id = node["id"]
        props = node.get("properties", {})
        target_name = safe_name(str(props.get("target", "")), "")
        property_name = str(props.get("property", "text"))
        lines += [
            f"    def {method_token(node_id, 'changed', 'binding')}(self, *_args):",
            f"        if {attribute(node_id, 'binding_guard_')}: return",
            f"        {attribute(node_id, 'binding_guard_')} = True",
            "        try:",
            f"            {attribute(node_id, 'binding_value_')} = self._read_binding(self.{target_name}, {property_name!r})",
            "        finally:",
            f"            {attribute(node_id, 'binding_guard_')} = False",
            *dispatch_lines(node_id, "onChange"),
            "",
        ]

    # Native Python data nodes are evaluated lazily when a lower property
    # is requested. Their inputs therefore keep true HiAsm semantics.
    for node in nodes:
        node_type, node_id = node.get("type", ""), node.get("id", "")
        if not str(node_type).startswith("Python::"):
            continue
        spec = COMPONENTS.get(node_type)
        if spec is None:
            continue
        key = str(node_type).split("::", 1)[1]
        kwargs = []
        for item in spec.ports:
            if item.kind == "data_in":
                fallback = node.get("properties", {}).get(item.name)
                kwargs.append(f"{item.name!r}: {input_expression(node, item.name, fallback)}")
        output_names = [item.name for item in spec.ports if item.kind == "data_out"]
        lines += [
            f"    def {method_token(node_id, 'value', 'py')}(self):",
            f"        _spec = _PYTHON_NODE_SPECS.get({key!r})",
            "        if _spec is None or _spec.fn is None:",
            f"            return {{{', '.join(repr(n)+': None' for n in output_names)}}}",
            f"        _raw = _spec.fn(**{{{', '.join(kwargs)}}})",
            f"        _names = {output_names!r}",
            "        if isinstance(_raw, dict) and set(_raw).issubset(set(_names)):",
            "            return {name: _raw.get(name) for name in _names}",
            "        if len(_names) == 1:",
            "            return {_names[0]: _raw}",
            "        if isinstance(_raw, (list, tuple)):",
            "            return {name: (_raw[i] if i < len(_raw) else None) for i, name in enumerate(_names)}",
            "        return {name: (_raw if i == 0 else None) for i, name in enumerate(_names)}",
            "",
        ]

    for node_id, port in sorted(action_targets):
        node = by_id.get(node_id)
        if node:
            lines += [
                f"        # VPB_NODE id={node_id} type={node.get('type', '')}",
                f"    def {action_method(node_id, port)}(self, _data=None):",
                *action_body(node, port),
                "",
            ]

    root_events = set(event_connections.keys()) | set(signal_map) | set(delayed_events)
    for node_id, port in sorted(root_events):
        source = by_id.get(node_id, {})
        source_type = str(source.get("type", ""))
        argument = None
        prelude: list[str] = []
        epilogue: list[str] = []
        if source_type == "Form" and port == "onCreate":
            prelude.append("        _vpb_wait_start()")
        if source_type == "TetrisGame" and port == "onChange":
            prelude = []
            epilogue = dispatch_lines(node_id, "onGameOver")
            if epilogue:
                epilogue = [f"        if {attribute(node_id)}.board.over:"] + [line.replace("        ", "            ", 1) for line in epilogue]
        elif source_type == "Delphi::Edit" and port in {"onChange", "onEnter"}:
            # QLineEdit signals do not carry the HiAsm ARG(Text) payload for
            # returnPressed. Read the current text explicitly, synchronize the
            # runtime property/output and only then continue the event chain.
            prelude = [
                f"        _value = {attribute(node_id)}.text()",
                f"        {attribute(node_id, 'delphi_')}.properties['Text'] = _value",
                f"        {attribute(node_id, 'delphi_')}.outputs['Text'] = _value",
            ]
            argument = "_value"
            if port == "onEnter" and bool(source.get("properties", {}).get("ClearAfterEnter", False)):
                epilogue.append(f"        {attribute(node_id)}.clear()")
        elif source_type.startswith("Delphi::"):
            argument = f"{attribute(node_id, 'delphi_')}.get('Data')"
        # Native Qt signals often carry the changed value. Keep it as a
        # fallback payload, while explicit top/bottom data wires remain the
        # authoritative source for target inputs.
        if argument is None and source_type in {"LineEdit", "CheckBox", "ComboBox", "ListWidget", "Slider", "SpinBox", "RadioButton", "Dial", "DoubleSpinBox", "ScrollBar", "TimeEdit", "DateTimeEdit", "FontComboBox", "KeySequenceEdit", "Gauge", "Speedometer", "Tachometer", "Thermometer", "LevelMeter", "LEDIndicator", "Compass", "BatteryIndicator", "SignalIndicator", "Sparkline", "AnalogClock", "Knob", "LineChart", "BarChart", "PieChart", "RadarChart", "Oscilloscope", "VUMeter", "SevenSegmentDisplay", "LEDMatrix", "XYPlot", "HeatMap", "Timeline", "WaterfallChart", "GeoMap", "Waveform", "SpectrumAnalyzer", "MultiSegmentDisplay", "CustomInstrument", "DashboardCanvas", "GridCanvas"}:
            argument = "(_args[0] if _args else None)"
        body = prelude + dispatch_lines(node_id, port, argument=argument) + epilogue
        lines += [
            f"    # VPB_NODE id={node_id} type={source_type}",
            f"    def {event_method(node_id, port)}(self, *_args):",
            *(body or ["        pass"]),
            "",
        ]

    if form and event_connections.get((form["id"], "onClose")):
        lines += [
            "    def closeEvent(self, event):",
            f"        self.{event_method(form['id'], 'onClose')}()",
            "        event.accept()",
            "",
        ]

    show_window = bool(form_props.get("visible", True))
    lines += [
        "",
        "threading.Thread(target=_vpb_command_reader, daemon=True).start()",
        "",
        "def _write_runtime_error(exc_type, exc_value, exc_tb):",
        "    text = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))",
        "    path = Path(tempfile.gettempdir()) / 'visual_python_builder_runtime_error.log'",
        "    try:",
        "        path.write_text(text, encoding='utf-8')",
        "    except Exception:",
        "        pass",
        "    print('[RUNTIME_ERROR_LOG] ' + str(path), file=sys.stderr)",
        "    print(text, file=sys.stderr)",
        "",
        "def _debug_excepthook(exc_type, exc_value, exc_tb):",
        "    _write_runtime_error(exc_type, exc_value, exc_tb)",
        "    sys.__excepthook__(exc_type, exc_value, exc_tb)",
        "",
        "def main():",
        "    sys.excepthook = _debug_excepthook",
        "    app = QApplication(sys.argv)",
        "    window = MainWindow()",
        "    _geometry = os.environ.get('VPB_DEBUG_GEOMETRY', '')",
        "    if _geometry:",
        "        try:",
        "            _gx, _gy, _gw, _gh = (int(value) for value in _geometry.split(','))",
        "            window.setGeometry(_gx, _gy, _gw, _gh)",
        "        except Exception:",
        "            pass",
        *(["    window.show()"] if show_window else []),
        "    sys.exit(app.exec())", "", "",
        'if __name__ == "__main__":', "    main()", "",
    ]
    return "\n".join(lines)
