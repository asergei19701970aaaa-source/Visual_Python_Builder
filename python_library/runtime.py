"""Синхронный событийный runtime NodeFlow 18.0.

Модель соответствует основному принципу HiAsm:

* событие справа немедленно вызывает соединённые методы слева;
* метод запрашивает верхние данные только во время своего выполнения;
* нижнее свойство вычисляется в момент запроса;
* состояние экземпляра ноды живёт столько же, сколько Runtime;
* события выполняются последовательно в порядке связей графа.

Модуль не импортирует Qt и может использоваться как интерпретатор схемы,
как эталон для генератора кода и как основа фонового исполнения.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import inspect
import time
import traceback
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from python_library.core import Graph, GraphError, Node, NodeSpec, Port


class RuntimeError(GraphError):
    """Ошибка выполнения событийной схемы."""


class RuntimeLimitError(RuntimeError):
    """Защита от бесконечного синхронного цикла."""


@dataclass
class EventFrame:
    """Один синхронный вызов метода."""

    node_id: str
    method: str
    payload: Any = None
    parent: Optional["EventFrame"] = None
    depth: int = 0
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NodeState:
    """Постоянное состояние одного экземпляра элемента."""

    values: Dict[str, Any] = field(default_factory=dict)
    properties: Dict[str, Any] = field(default_factory=dict)
    calls: int = 0
    last_method: str = ""
    last_payload: Any = None
    error: str = ""
    traceback: str = ""
    duration_ms: float = 0.0


@dataclass
class MethodResult:
    """Расширенный результат обработчика метода.

    Обычная функция ноды может по-прежнему вернуть скаляр, список или словарь.
    MethodResult нужен нодам, которые явно управляют событиями и состоянием.
    """

    properties: Dict[str, Any] = field(default_factory=dict)
    events: List[Tuple[str, Any]] = field(default_factory=list)
    state: Dict[str, Any] = field(default_factory=dict)


MethodHandler = Callable[["RuntimeContext", Any], Any]
PropertyHandler = Callable[["RuntimeContext"], Any]


class RuntimeContext:
    """Безопасный интерфейс обработчика ноды к runtime."""

    def __init__(self, runtime: "EventRuntime", node: Node,
                 spec: NodeSpec, frame: Optional[EventFrame]) -> None:
        self.runtime = runtime
        self.node = node
        self.spec = spec
        self.frame = frame

    @property
    def state(self) -> Dict[str, Any]:
        return self.runtime.state(self.node.id).values

    @property
    def payload(self) -> Any:
        return self.frame.payload if self.frame else None

    def data(self, name: str) -> Any:
        return self.runtime.get_data(self.node.id, name, self.frame)

    def emit(self, event: str, payload: Any = None) -> None:
        if payload is None and self.frame is not None:
            payload = self.frame.payload
        self.runtime.emit_event(self.node.id, event, payload, self.frame)

    def property(self, name: str) -> Any:
        return self.runtime.get_property(self.node.id, name, self.frame)


class EventRuntime:
    """Исполнитель одной схемы.

    ``method_handlers`` и ``property_handlers`` позволяют постепенно заменять
    адаптер старых Python-функций точными реализациями элементов. Ключи имеют
    вид ``("Math.counter", "doNext")`` и ``("Math.counter", "Count")``.
    """

    def __init__(
            self, graph: Graph, *,
            method_handlers: Optional[Dict[Tuple[str, str], MethodHandler]] = None,
            property_handlers: Optional[
                Dict[Tuple[str, str], PropertyHandler]] = None,
            max_depth: int = 256, max_steps: int = 10000) -> None:
        self.graph = graph
        self.method_handlers = dict(method_handlers or {})
        self.property_handlers = dict(property_handlers or {})
        self.max_depth = max(1, int(max_depth))
        self.max_steps = max(1, int(max_steps))
        self._states: Dict[str, NodeState] = {
            node_id: NodeState() for node_id in graph.nodes}
        self._steps = 0
        self._property_stack: Set[Tuple[str, str]] = set()
        self.log: List[str] = []
        self.on_event: Optional[
            Callable[[str, str, Any, Optional[EventFrame]], None]] = None

    def reset(self, *, keep_state: bool = False) -> None:
        """Очищает журнал и счётчики; при необходимости также состояние."""
        self._steps = 0
        self._property_stack.clear()
        self.log.clear()
        if not keep_state:
            self._states = {
                node_id: NodeState() for node_id in self.graph.nodes}

    def state(self, node_id: str) -> NodeState:
        if node_id not in self.graph.nodes:
            raise RuntimeError(f"Нода не найдена: {node_id}")
        return self._states.setdefault(node_id, NodeState())

    # ----------------------------------------------------------- execution
    def call_method(self, node_id: str, method: str, payload: Any = None,
                    parent: Optional[EventFrame] = None) -> Any:
        """Синхронно вызывает конкретный метод конкретной ноды."""
        node, spec, port = self._port(node_id, method, "method")
        depth = 0 if parent is None else parent.depth + 1
        if depth > self.max_depth:
            raise RuntimeLimitError(
                f"Превышена глубина событий ({self.max_depth})")
        self._tick(f"{node_id}.{method}")
        frame = EventFrame(node_id, method, payload, parent, depth)
        state = self.state(node_id)
        state.calls += 1
        state.last_method = method
        state.last_payload = payload
        state.error = state.traceback = ""
        started = time.perf_counter()
        try:
            handler = (self.method_handlers.get((spec.key, method))
                       or spec.method_handlers.get(method))
            context = RuntimeContext(self, node, spec, frame)
            raw = (handler(context, payload) if handler
                   else self._call_legacy_function(node, spec, frame, port))
            result = self._accept_result(node, spec, frame, raw)
            state.duration_ms = (time.perf_counter() - started) * 1000.0
            self.log.append(
                f"CALL {node_id}.{method} payload={payload!r} "
                f"({state.duration_ms:.2f} ms)")
            return result
        except Exception as exc:
            state.error = f"{type(exc).__name__}: {exc}"
            state.traceback = traceback.format_exc()
            state.duration_ms = (time.perf_counter() - started) * 1000.0
            node.error = state.error
            node.traceback = state.traceback
            raise

    def emit_event(self, node_id: str, event: str, payload: Any = None,
                   parent: Optional[EventFrame] = None) -> None:
        """Последовательно вызывает все методы, подключённые к событию."""
        self._port(node_id, event, "event")
        self._tick(f"{node_id}.{event}")
        self.log.append(f"EMIT {node_id}.{event} payload={payload!r}")
        if self.on_event:
            self.on_event(node_id, event, payload, parent)
        for edge in self.graph.edges.values():
            if edge.src_node == node_id and edge.src_port == event:
                self.call_method(
                    edge.dst_node, edge.dst_port, payload, parent=parent)

    # --------------------------------------------------------------- data
    def get_data(self, node_id: str, data_name: str,
                 frame: Optional[EventFrame] = None) -> Any:
        """Лениво получает значение верхней точки."""
        node, unused_spec, port = self._port(node_id, data_name, "data")
        edges = self.graph.edges_into(node_id, data_name)
        if not edges:
            return node.params.get(data_name, port.default)
        values = [
            self.get_property(edge.src_node, edge.src_port, frame)
            for edge in edges
        ]
        if port.type in ("list", "actions", "events"):
            merged: List[Any] = []
            for value in values:
                if isinstance(value, (list, tuple)):
                    merged.extend(value)
                elif value is not None:
                    merged.append(value)
            return merged
        return values[0] if values else node.params.get(data_name, port.default)

    def get_property(self, node_id: str, property_name: str,
                     frame: Optional[EventFrame] = None) -> Any:
        """Запрашивает актуальное значение нижней точки."""
        node, spec, unused_port = self._port(
            node_id, property_name, "property")
        marker = (node_id, property_name)
        if marker in self._property_stack:
            raise RuntimeError(
                f"Циклический запрос свойства: {node_id}.{property_name}")
        self._tick(f"{node_id}.{property_name}")
        self._property_stack.add(marker)
        try:
            handler = (self.property_handlers.get((spec.key, property_name))
                       or spec.property_handlers.get(property_name))
            if handler:
                value = handler(RuntimeContext(self, node, spec, frame))
                self.state(node_id).properties[property_name] = value
                return value
            # Свойства, полученные последним методом, имеют приоритет.
            state = self.state(node_id)
            if property_name in state.properties:
                return state.properties[property_name]
            raw = self._call_legacy_function(node, spec, frame, None)
            properties = self._property_values(spec, raw)
            state.properties.update(properties)
            return properties.get(property_name)
        finally:
            self._property_stack.discard(marker)

    # ------------------------------------------------------------- helpers
    def _tick(self, operation: str) -> None:
        self._steps += 1
        if self._steps > self.max_steps:
            raise RuntimeLimitError(
                f"Превышен предел {self.max_steps} операций; "
                f"последняя операция: {operation}")

    def _port(self, node_id: str, name: str, kind: str
              ) -> Tuple[Node, NodeSpec, Port]:
        node = self.graph.nodes.get(node_id)
        if node is None:
            raise RuntimeError(f"Нода не найдена: {node_id}")
        spec = self.graph.spec_of(node)
        if spec is None:
            raise RuntimeError(f"Неизвестный тип ноды: {node.spec_key}")
        port = (spec.input(name) if kind in ("method", "data")
                else spec.output(name))
        if port is None or port.kind != kind:
            raise RuntimeError(
                f"У {spec.title} нет точки {kind} «{name}»")
        return node, spec, port

    def _call_legacy_function(
            self, node: Node, spec: NodeSpec,
            frame: Optional[EventFrame], method_port: Optional[Port]) -> Any:
        if spec.fn is None:
            return None
        kwargs: Dict[str, Any] = {}
        for port in spec.inputs:
            if port.kind == "data":
                kwargs[port.name] = self.get_data(node.id, port.name, frame)
            elif port.kind == "method":
                kwargs[port.name] = (
                    frame.payload if frame and method_port
                    and port.name == method_port.name else port.default)
        try:
            signature = inspect.signature(spec.fn)
            if not any(p.kind == inspect.Parameter.VAR_KEYWORD
                       for p in signature.parameters.values()):
                kwargs = {key: value for key, value in kwargs.items()
                          if key in signature.parameters}
        except (TypeError, ValueError):
            pass
        return spec.fn(**kwargs)

    @staticmethod
    def _property_values(spec: NodeSpec, raw: Any) -> Dict[str, Any]:
        ports = [port for port in spec.outputs if port.kind == "property"]
        names = [port.name for port in ports]
        if not names:
            return {}
        if isinstance(raw, MethodResult):
            return dict(raw.properties)
        if isinstance(raw, dict) and set(raw).issubset(set(names)):
            return {name: raw.get(name) for name in names}
        if len(names) == 1:
            return {names[0]: raw}
        if isinstance(raw, (list, tuple)):
            return {name: raw[index] if index < len(raw) else None
                    for index, name in enumerate(names)}
        return {names[0]: raw, **{name: None for name in names[1:]}}

    def _accept_result(self, node: Node, spec: NodeSpec, frame: EventFrame,
                       raw: Any) -> Any:
        state = self.state(node.id)
        if isinstance(raw, MethodResult):
            state.values.update(raw.state)
            state.properties.update(raw.properties)
            node.results.update(raw.properties)
            for event, payload in raw.events:
                self.emit_event(node.id, event, payload, frame)
            return raw
        properties = self._property_values(spec, raw)
        state.properties.update(properties)
        node.results.update(properties)
        for event in spec.auto_events.get(frame.method, []):
            self.emit_event(node.id, event, frame.payload, frame)
        return raw


def run_event(graph: Graph, node_id: str, event: str,
              payload: Any = None, **runtime_options: Any) -> EventRuntime:
    """Удобный запуск одного внешнего события."""
    runtime = EventRuntime(graph, **runtime_options)
    runtime.emit_event(node_id, event, payload)
    return runtime