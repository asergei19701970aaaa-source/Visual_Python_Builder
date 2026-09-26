import copy
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
from components import COMPONENTS, effective_ports
from model_contract import (
    component_passport,
    diagnose_event_flow,
    diagnose_node_model,
    normalize_node_model,
    port_identifier,
    property_group_name,
    split_port_identifier,
    validate_component_catalog,
)
from user_help import (
    component_search_text,
    format_component_help,
    node_instance_label,
    node_instance_search_text,
    project_node_records,
)
from container_support import build_interface
from generator import generate_python
from container_library import (
    apply_container_interface,
    delete_user_template,
    discover_container_library,
    instantiate_container_template,
    load_user_library,
    save_container_template,
    validate_container_model,
)
from connection_advisor import advise_connection, connection_passport


class StabilityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.window = (ROOT / "builder_ui/main_window.py").read_text(encoding="utf-8")
        cls.canvas = (ROOT / "builder_ui/canvas.py").read_text(encoding="utf-8")
        cls.generator = (ROOT / "generator.py").read_text(encoding="utf-8")
        cls.state = json.loads((ROOT / "PROJECT_STATE.json").read_text(encoding="utf-8"))

    def test_version_and_state_are_aligned(self):
        from version import APP_VERSION
        self.assertEqual(self.state["version"], APP_VERSION)
        self.assertIn("APP_VERSION", self.window)
        self.assertIn(APP_VERSION, (ROOT / "README_RU.md").read_text(encoding="utf-8"))

    def test_palette_search_and_help_are_beginner_friendly(self):
        spec = COMPONENTS["GridState"]
        search = component_search_text(spec)
        self.assertIn("двумерное поле", search)
        self.assertIn("удалить заполненные строки", search)
        self.assertIn("столбец", search)
        help_text = format_component_help("GridState")
        for marker in (
            "КАК ЧИТАТЬ НОДУ",
            "ТОЧКИ ПОДКЛЮЧЕНИЯ",
            "СВОЙСТВА",
            "ПРОВЕРКА",
            "Записать ячейку",
        ):
            self.assertIn(marker, help_text)

    def test_connection_advisor_explains_and_uses_general_converters(self):
        direct = advise_connection(
            "data_out", "data_in", "number", "number"
        )
        self.assertTrue(direct.allowed)
        converted = advise_connection(
            "data_out", "data_in", "text", "number"
        )
        self.assertFalse(converted.allowed)
        self.assertTrue(converted.needs_adapter)
        self.assertEqual(
            converted.adapter_type, "Python::Data.to_number"
        )
        wrong_side = advise_connection(
            "event_out", "data_in", "any", "number"
        )
        self.assertFalse(wrong_side.allowed)
        self.assertIn("событие", wrong_side.message.lower())
        self.assertIn("_insert_connection_adapter", self.canvas)
        self.assertIn("универсальный преобразователь", self.canvas)
        expected_adapters = {
            "list": "Python::Data.to_list",
            "dict": "Python::Data.to_dict",
            "color": "Python::Data.to_color",
            "file": "Python::Data.to_file",
        }
        for target_type, adapter_type in expected_adapters.items():
            advice = advise_connection(
                "data_out", "data_in", "text", target_type
            )
            self.assertTrue(advice.needs_adapter)
            self.assertEqual(advice.adapter_type, adapter_type)

    def test_connection_passport_explains_route_type_and_fix(self):
        direct = connection_passport(
            "Клавиатура", "Клавиша", "data_out", "text",
            "Формат строки", "Данные 1", "data_in", "any",
        )
        for marker in (
            "Передача данных",
            "Откуда: Клавиатура · Клавиша",
            "Куда: Формат строки · Данные 1",
            "Тип: текст → любые данные",
            "прямое соединение",
        ):
            self.assertIn(marker, direct)
        converted = connection_passport(
            "Поле", "Поле", "data_out", "list",
            "Надпись", "Текст", "data_in", "text",
        )
        self.assertIn("нужен преобразователь «В текст»", converted)
        for marker in (
            "def passport_text",
            "Паспорт связи…",
            "Перейти к началу нити",
            "Перейти к концу нити",
            "QTimer.singleShot(550",
        ):
            self.assertIn(marker, self.canvas)

    def test_node_navigator_searches_instances_and_focuses_results(self):
        model = {
            "id": "score_label",
            "type": "Label",
            "properties": {
                "name": "scoreText",
                "text": "Очки игрока",
                "subgraph": {"secret_inner_node": True},
            },
        }
        search = node_instance_search_text(model)
        for marker in (
            "score_label", "scoretext", "очки игрока", "надпись",
        ):
            self.assertIn(marker, search)
        self.assertNotIn("secret_inner_node", search)
        self.assertEqual(
            node_instance_label(model), "Надпись · scoreText"
        )
        for marker in (
            "def _create_navigator",
            "Найти установленную ноду…",
            "def _navigator_item_activated",
            "QKeySequence.StandardKey.Find",
            "self.view.centerOn(node)",
            "self.scene.project_loaded.connect",
        ):
            self.assertIn(marker, self.window)

    def test_project_navigator_keeps_nested_paths(self):
        project = {
            "nodes": [
                {
                    "id": "outer",
                    "type": "UserContainer",
                    "properties": {
                        "name": "Игровая логика",
                        "subgraph": {
                            "nodes": [
                                {
                                    "id": "inner_math",
                                    "type": "Math",
                                    "properties": {},
                                },
                            ],
                            "connections": [],
                        },
                    },
                },
                {
                    "id": "root_button",
                    "type": "Button",
                    "properties": {"name": "startButton"},
                },
            ],
            "connections": [],
        }
        records = project_node_records(project)
        by_id = {
            record["model"]["id"]: record
            for record in records
        }
        self.assertEqual(by_id["root_button"]["path_ids"], ())
        self.assertEqual(by_id["inner_math"]["path_ids"], ("outer",))
        self.assertIn(
            "Игровая логика",
            " ".join(by_id["inner_math"]["path_names"]),
        )
        for marker in (
            "Искать внутри вложенных контейнеров",
            "def _navigator_root_project",
            "path_ids != current_ids",
            "self._commit_all_containers()",
            "self._open_user_container(container.model)",
        ):
            self.assertIn(marker, self.window)

    def test_container_return_preserves_interface_passport(self):
        subgraph = {
            "nodes": [
                {
                    "id": "proxy",
                    "type": "ContainerDataInput",
                    "properties": {
                        "name": "Координаты",
                        "data_type": "list",
                    },
                },
            ],
            "connections": [],
        }
        previous = [
            {
                "port": "Points",
                "caption": "Координаты",
                "kind": "data_in",
                "proxy_id": "proxy",
                "data_type": "list",
                "description": "Относительные координаты фигуры.",
            },
        ]
        rebuilt = build_interface(subgraph, previous)
        self.assertEqual(rebuilt[0]["port"], "Points")
        self.assertEqual(rebuilt[0]["data_type"], "list")
        self.assertEqual(
            rebuilt[0]["description"],
            "Относительные координаты фигуры.",
        )

    def test_container_data_types_have_sources_and_conflicts_are_reported(self):
        templates, _categories = discover_container_library()
        template = next(
            item for item in templates
            if item["id"] == "builtin-coordinate-transform"
        )
        model = instantiate_container_template(template, 0, 0)
        data_points = [
            item for item in model["properties"]["interface"]
            if item["kind"] in {"data_in", "data_out"}
        ]
        self.assertTrue(data_points)
        self.assertTrue(all(
            str(item.get("data_type_source", "")).strip()
            for item in data_points
        ))
        changed = copy.deepcopy(data_points)
        changed[0]["data_type"] = "dict"
        apply_container_interface(model, changed)
        current = model["properties"]["interface"][0]
        self.assertEqual(
            current["data_type_source"],
            "Выбран вручную в паспорте",
        )
        proxy = next(
            node
            for node in model["properties"]["subgraph"]["nodes"]
            if node["id"] == current["proxy_id"]
        )
        self.assertEqual(proxy["properties"]["data_type"], "dict")

        proxy["properties"]["data_type"] = "list"
        errors = validate_container_model(model)
        self.assertTrue(any(
            "proxy-нода хранит" in error for error in errors
        ))
        self.assertIn(
            'props["data_type"] = normalize_data_type(',
            self.canvas,
        )

    def test_canvas_has_persistent_clickable_container_breadcrumbs(self):
        for marker in (
            "containerPathBar",
            "← На уровень выше",
            "def _update_container_breadcrumb",
            "def _navigate_container_depth",
            "Сохранить изменения и перейти к этому уровню",
            "self.tabs.addTab(self.scheme_page, \"Схема\")",
            "def _reset_container_navigation",
        ):
            self.assertIn(marker, self.window)
        self.assertNotIn(
            "self.tabs.setCurrentWidget(self.view)", self.window
        )

    def test_python_data_ports_keep_declared_types(self):
        source = COMPONENTS["Python::Data.to_text"]
        by_kind = {port.kind: port for port in source.ports}
        self.assertEqual(by_kind["data_in"].data_type, "any")
        self.assertEqual(by_kind["data_out"].data_type, "text")
        passport = component_passport("Python::Data.to_text")
        self.assertEqual(
            next(
                port["data_type"] for port in passport["ports"]
                if port["kind"] == "data_out"
            ),
            "text",
        )
        self.assertIn("Тип: текст", format_component_help("Python::Data.to_text"))

    def test_native_general_nodes_expose_safe_data_types(self):
        expected = {
            ("Math", "Op1"): "number",
            ("Math", "Result"): "number",
            ("GridState", "Grid"): "list",
            ("GridCanvas", "Palette"): "dict",
            ("GridCanvas", "Column"): "number",
            ("KeyboardInput", "Key"): "text",
            ("KeyboardInput", "IsAutoRepeat"): "bool",
            ("Memory", "Value"): "any",
        }
        for (type_name, port_name), data_type in expected.items():
            port = next(
                item for item in effective_ports(type_name)
                if item.name == port_name
            )
            self.assertEqual(
                port.data_type, data_type,
                f"{type_name}.{port_name}",
            )

    def test_general_collection_color_and_path_converters(self):
        from python_library.loader import discover
        specs, errors = discover()
        self.assertEqual(errors, [])
        self.assertEqual(
            specs["Data.to_list"].fn("a, b, c", ",", "values"),
            ["a", "b", "c"],
        )
        self.assertEqual(
            specs["Data.to_list"].fn(
                '{"a": 1, "b": 2}', ",", "items"
            ),
            [["a", 1], ["b", 2]],
        )
        self.assertEqual(
            specs["Data.to_dict"].fn(
                "name=Anna\nage=30", "\n", "="
            ),
            {"name": "Anna", "age": "30"},
        )
        self.assertEqual(
            specs["Data.to_dict"].fn(
                [["x", 10], ["y", 20]], "\n", "="
            ),
            {"x": 10, "y": 20},
        )
        self.assertEqual(
            specs["Data.to_color"].fn([53, 194, 255]),
            "#35C2FF",
        )
        self.assertEqual(
            specs["Data.to_file"].fn("~/demo.txt", False, False),
            "~/demo.txt",
        )
        component_types = [
            "Python::Data.to_list",
            "Python::Data.to_dict",
            "Python::Data.to_color",
            "Python::Data.to_file",
        ]
        project = {
            "format": 1,
            "name": "General converters",
            "nodes": [
                {
                    "id": "form", "type": "Form",
                    "x": 0, "y": 0, "properties": {},
                },
                *[
                    {
                        "id": f"convert_{index}",
                        "type": type_name,
                        "x": 100 * index,
                        "y": 100,
                        "properties": {},
                    }
                    for index, type_name in enumerate(
                        component_types, 1
                    )
                ],
            ],
            "connections": [],
        }
        compile(
            generate_python(project),
            "general_converters_contract.py",
            "exec",
        )

    def test_new_wire_can_create_only_a_user_selected_compatible_node(self):
        for marker in (
            "class ConnectionNodePicker",
            "def _connection_node_candidates",
            "def _pick_and_connect_node",
            "Показываются только ноды, которые можно соединить напрямую",
            "if source is not None and not rewiring",
            "if self.rewire_backup is None",
        ):
            self.assertIn(marker, self.canvas)
        self.assertIn(
            'excluded = CONTAINER_PROXY_TYPES | {"UserContainer"}',
            self.canvas,
        )
        self.assertIn("component_search_text(spec)", self.canvas)
        self.assertIn("if not advice.allowed:", self.canvas)

    def test_event_flow_diagnostics_give_beginner_actions(self):
        disconnected = {
            "nodes": [
                {
                    "id": "start", "type": "Start",
                    "properties": {}, "enabled_ports": ["onStart"],
                },
            ],
            "connections": [],
        }
        messages = diagnose_event_flow(disconnected)
        self.assertEqual(len(messages), 1)
        self.assertIn("Что сделать:", messages[0])
        self.assertIn("оранжевую нить", messages[0])

        unreachable_cycle = {
            "nodes": [
                {
                    "id": "counter", "type": "Counter",
                    "properties": {}, "enabled_ports": [
                        "doNext", "onValue", "Value",
                    ],
                },
                {
                    "id": "delay", "type": "Delay",
                    "properties": {}, "enabled_ports": [
                        "doStart", "onDone", "Interval",
                    ],
                },
            ],
            "connections": [
                {
                    "from_node": "counter", "from_port": "onValue",
                    "to_node": "delay", "to_port": "doStart",
                },
                {
                    "from_node": "delay", "from_port": "onDone",
                    "to_node": "counter", "to_port": "doNext",
                },
            ],
        }
        messages = diagnose_event_flow(unreachable_cycle)
        self.assertEqual(len(messages), 2)
        self.assertTrue(all("не начинается" in item for item in messages))

        reachable = {
            "nodes": [
                disconnected["nodes"][0],
                unreachable_cycle["nodes"][0],
            ],
            "connections": [
                {
                    "from_node": "start", "from_port": "onStart",
                    "to_node": "counter", "to_port": "doNext",
                },
            ],
        }
        self.assertEqual(diagnose_event_flow(reachable), [])

    def test_specialized_tetris_nodes_are_not_in_palette(self):
        self.assertNotIn("TetrisGame", COMPONENTS)
        self.assertFalse(
            any(key.startswith("Python::Game.") for key in COMPONENTS),
            "Узкопредметные игровые ноды не должны заменять общие примитивы.",
        )

    def test_grid_canvas_is_general_and_generated(self):
        spec = COMPONENTS["GridCanvas"]
        self.assertTrue(spec.visual)
        self.assertNotIn("тетрис", (spec.caption + spec.description).lower())
        port_names = {port.name for port in spec.ports}
        self.assertTrue({
            "doSetGrid", "onCellClick", "Grid", "Column", "Row",
            "CellValue",
        }.issubset(port_names))
        project = {
            "name": "Grid Canvas contract",
            "nodes": [
                {
                    "id": "form", "type": "Form", "x": 0, "y": 0,
                    "properties": {"title": "Grid"},
                },
                {
                    "id": "grid", "type": "GridState", "x": 100, "y": 0,
                    "properties": {
                        "name": "field", "columns": 10, "rows": 20,
                        "empty": "0",
                    },
                },
                {
                    "id": "canvas", "type": "GridCanvas", "x": 300, "y": 0,
                    "properties": {
                        "name": "field_view", "x": 20, "y": 20,
                        "width": 300, "height": 540,
                    },
                },
            ],
            "connections": [
                {
                    "from_node": "grid", "from_port": "Grid",
                    "to_node": "canvas", "to_port": "Grid",
                },
                {
                    "from_node": "grid", "from_port": "onChange",
                    "to_node": "canvas", "to_port": "doSetGrid",
                },
            ],
        }
        code = generate_python(project)
        compile(code, "grid_canvas_contract.py", "exec")
        for marker in (
            "class GridCanvasWidget",
            "self.field_view = GridCanvasWidget",
            "self.field_view.setGrid(",
            "cellClicked = Signal(int, int, object)",
        ):
            self.assertIn(marker, code)

    def test_container_library_is_transparent_and_reusable(self):
        templates, _categories = discover_container_library()
        ids = {item["id"] for item in templates}
        self.assertIn("builtin-interactive-grid", ids)
        self.assertIn("builtin-counter-panel", ids)
        template = next(
            item for item in templates
            if item["id"] == "builtin-interactive-grid"
        )
        first = instantiate_container_template(template, 100, 200)
        second = instantiate_container_template(template, 500, 200)
        self.assertEqual(first["type"], "UserContainer")
        self.assertNotEqual(first["id"], second["id"])
        first_ids = {
            node["id"]
            for node in first["properties"]["subgraph"]["nodes"]
        }
        second_ids = {
            node["id"]
            for node in second["properties"]["subgraph"]["nodes"]
        }
        self.assertTrue(first_ids.isdisjoint(second_ids))
        project = {
            "format": 1,
            "name": "Container library",
            "nodes": [
                {
                    "id": "form", "type": "Form", "x": 0, "y": 0,
                    "properties": {"title": "Containers"},
                },
                first,
            ],
            "connections": [],
        }
        compile(
            generate_python(project),
            "container_library_contract.py",
            "exec",
        )

    def test_user_can_create_categories_save_and_delete_template(self):
        templates, _categories = discover_container_library()
        source = next(
            item["model"] for item in templates
            if item["id"] == "builtin-counter-panel"
        )
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "library.json"
            template_id = save_container_template(
                source,
                "Мой счётчик",
                "Мои панели",
                "Учебные",
                "Изменяемый пример",
                path,
            )
            library = load_user_library(path)
            self.assertEqual(library["templates"][0]["category"], "Мои панели")
            self.assertIn(
                "Учебные", library["categories"][0]["subgroups"]
            )
            self.assertTrue(delete_user_template(template_id, path))
            self.assertEqual(load_user_library(path)["templates"], [])

    def test_small_grid_nodes_transform_check_and_read(self):
        from python_library.loader import discover
        specs, errors = discover()
        self.assertEqual(errors, [])
        required = {
            "Grid.point_set",
            "Grid.transform_points",
            "Grid.point_bounds",
            "Grid.can_place",
            "Grid.cell_values",
        }
        self.assertTrue(required.issubset(specs))
        transformed = specs["Grid.transform_points"].fn(
            [[0, 0], [1, 0]], 4, 5, "90", False, False
        )
        self.assertEqual(transformed, [[4, 5], [4, 6]])
        can_place, collisions, inside = specs["Grid.can_place"].fn(
            [[0, 1], [0, 0]], [[0, 0], [1, 0]], 0, 0, 0, True
        )
        self.assertFalse(can_place)
        self.assertEqual(collisions, [[1, 0]])
        self.assertEqual(inside, 2)

    def test_grid_batch_writer_generates_bounded_mutation(self):
        project = {
            "format": 1,
            "name": "Grid batch",
            "nodes": [
                {
                    "id": "form", "type": "Form", "x": 0, "y": 0,
                    "properties": {},
                },
                {
                    "id": "start", "type": "Start", "x": 0, "y": 0,
                    "properties": {},
                },
                {
                    "id": "writer", "type": "GridBatchWriter",
                    "x": 200, "y": 0, "properties": {"empty": "0"},
                },
            ],
            "connections": [
                {
                    "from_node": "start", "from_port": "onStart",
                    "to_node": "writer", "to_port": "doWrite",
                },
            ],
        }
        code = generate_python(project)
        compile(code, "grid_batch_writer_contract.py", "exec")
        for marker in (
            "Набор координат должен быть списком",
            "if 0 <= _row < len(",
            "_grid_batch_changed_",
        ):
            self.assertIn(marker, code)

    def test_grid_containers_are_built_from_general_nodes(self):
        templates, _categories = discover_container_library()
        expected = {
            "builtin-coordinate-transform",
            "builtin-can-place",
            "builtin-grid-batch-writer",
        }
        self.assertTrue(expected.issubset({item["id"] for item in templates}))
        forbidden = {"TetrisGame"}
        for item in templates:
            if item["id"] not in expected:
                continue
            types = {
                node["type"]
                for node in item["model"]["properties"]["subgraph"]["nodes"]
            }
            self.assertTrue(types.isdisjoint(forbidden))

    def test_container_passport_editor_contract(self):
        templates, _categories = discover_container_library()
        template = next(
            item for item in templates
            if item["id"] == "builtin-counter-panel"
        )
        model = instantiate_container_template(template, 0, 0)
        self.assertEqual(validate_container_model(model), [])
        value_interface = next(
            item for item in model["properties"]["interface"]
            if item["kind"] == "data_out"
        )
        self.assertEqual(value_interface["data_type"], "number")
        self.assertEqual(
            next(
                port for port in effective_ports(
                    "UserContainer", model["properties"]
                )
                if port.name == value_interface["port"]
            ).data_type,
            "number",
        )
        rows = [
            {
                **item,
                "port": str(item["port"]) + "_new",
                "description": "Понятное назначение точки.",
            }
            for item in model["properties"]["interface"]
        ]
        rows.append(
            {
                "caption": "Сброс",
                "port": "Reset",
                "kind": "work_in",
                "description": "Сбрасывает состояние.",
                "proxy_id": "",
            }
        )
        rename_map = apply_container_interface(model, rows)
        self.assertIn("Значение", rename_map)
        self.assertEqual(validate_container_model(model), [])
        reset = next(
            item for item in model["properties"]["interface"]
            if item["port"] == "Reset"
        )
        proxy = next(
            node for node in model["properties"]["subgraph"]["nodes"]
            if node["id"] == reset["proxy_id"]
        )
        self.assertEqual(proxy["type"], "ContainerEventInput")
        self.assertEqual(
            proxy["properties"]["data_type"], "any"
        )
        self.assertEqual(
            next(
                item for item in model["properties"]["interface"]
                if item["port"] == "Reset"
            )["description"],
            "Сбрасывает состояние.",
        )

    def test_broken_container_proxy_is_reported_before_run(self):
        model = {
            "id": "broken",
            "type": "UserContainer",
            "properties": {
                "subgraph": {"nodes": [], "connections": []},
                "interface": [
                    {
                        "port": "Value",
                        "caption": "Значение",
                        "kind": "data_out",
                        "proxy_id": "missing",
                    }
                ],
            },
        }
        errors = diagnose_node_model(model)
        self.assertTrue(any("proxy-нода потеряна" in error for error in errors))

    def test_error_dock_is_not_hidden_by_run(self):
        self.assertIn("self.problems_dock.show()", self.window)
        self.assertNotIn("self.problems_dock.hide()", self.window)

    def test_helper_split_and_resize_are_present(self):
        for marker in ("helper:text", "helper:shape", "_near_resize_handle"):
            self.assertIn(marker, self.window + self.canvas)

    def test_container_routing_has_safe_path_and_bounds(self):
        for marker in (
            "_clamp_node_position",
            "_frame_route_points",
            "_frame_port_point",
            "container_frame_anchor",
            "_point_on_container_frame",
            "содержит контейнер",
        ):
            self.assertIn(marker, self.canvas)

    def test_context_points_use_canonical_property_panel(self):
        self.assertIn("PropertyPanel", self.canvas)
        self.assertIn("def _show_points_dialog", self.canvas)
        self.assertIn("panel.tabs.setCurrentIndex(1)", self.canvas)
        self.assertNotIn('points_menu = menu.addMenu("Точки")', self.canvas)

    def test_wire_drop_creates_typed_container_interface_point(self):
        for marker in (
            "def _near_container_frame",
            "def _container_proxy_definition",
            "def _container_drop_anchor",
            "def _create_container_point_from_wire",
            '"ContainerEventOutput", "doEvent", "right"',
            '"ContainerDataOutput", "Data", "bottom"',
            '"ContainerEventInput", "onEvent", "left"',
            '"ContainerDataInput", "Data", "top"',
        ):
            self.assertIn(marker, self.canvas)

    def test_mdi_generation_uses_owned_subwindow(self):
        self.assertIn("addSubWindow(self.", self.generator)

    def test_project_state_has_required_invariants(self):
        required = {
            "helpers_are_not_nodes",
            "container_nodes_stay_inside_frame",
            "container_autoroute_is_bounded",
            "property_groups_are_contract_driven",
            "point_help_uses_port_kind",
            "property_help_is_visible",
        }
        self.assertTrue(required.issubset(set(self.state["core_invariants"])))

    def test_component_catalog_and_node_normalization(self):
        self.assertEqual(validate_component_catalog(), [])
        model = normalize_node_model({
            "type": "Button",
            "properties": {"text": "OK"},
            "enabled_ports": ["not-a-port"],
        })
        self.assertEqual(model["properties"]["text"], "OK")
        self.assertNotIn("not-a-port", model["enabled_ports"])
        passport = component_passport("Button", model["properties"])
        self.assertEqual(passport["type"], "Button")
        self.assertTrue(any(port["name"] == "onClick" for port in passport["ports"]))
        self.assertEqual(
            property_group_name(next(
                item for item in COMPONENTS["Button"].properties
                if item.name == "width"
            )),
            "Положение и размер",
        )

    def test_port_identity_keeps_same_name_in_both_directions(self):
        self.assertEqual(
            port_identifier("items", "data_in"),
            "data_in:items",
        )
        self.assertEqual(
            split_port_identifier("data_out:items"),
            ("items", "data_out"),
        )
        passport = component_passport("Python::List.sort")
        item_ids = {
            port["id"] for port in passport["ports"] if port["name"] == "items"
        }
        self.assertEqual(item_ids, {"data_in:items", "data_out:items"})

    def test_node_diagnostics_reports_property_and_port_precisely(self):
        errors = diagnose_node_model({
            "id": "button_1",
            "type": "Button",
            "properties": {"width": 2},
            "enabled_ports": ["missing"],
        })
        self.assertTrue(any("Ширина" in error and "минимума" in error for error in errors))
        self.assertTrue(any("missing" in error for error in errors))
        self.assertEqual(
            diagnose_node_model({
                "id": "button_1",
                "type": "Button",
                "properties": {"width": 140},
                "enabled_ports": ["onClick"],
            }),
            [],
        )

    def test_property_panel_exposes_contract_status(self):
        panel = (ROOT / "builder_ui/property_panel.py").read_text(encoding="utf-8")
        self.assertIn("property_status", panel)
        self.assertIn("_set_diagnostic_status", panel)
        self.assertIn("property_errors", panel)

    def test_property_panel_uses_specialized_value_editors(self):
        panel = (ROOT / "builder_ui/property_panel.py").read_text(encoding="utf-8")
        self.assertIn('prop.kind in {"enum", "choice"}', panel)
        self.assertIn('prop.kind in {"multiline", "code", "table"}', panel)

    def test_component_passport_contains_support_metadata(self):
        passport = component_passport("Button")
        self.assertIn("support_status", passport)
        self.assertIn("hiasm", passport)
        self.assertIn("class", passport["hiasm"])

    def test_property_search_uses_metadata_and_values(self):
        panel = (ROOT / "builder_ui/property_panel.py").read_text(encoding="utf-8")
        self.assertIn("техническому имени", panel)
        self.assertIn("UserRole + 4", panel)
        self.assertIn("setClearButtonEnabled", panel)

    def test_imported_qt_geometry_is_not_rejected_by_palette_minimums(self):
        errors = diagnose_node_model({
            "id": "ui_label",
            "type": "Label",
            "properties": {
                "_qt_class": "QLabel",
                "width": 22,
                "height": 14,
            },
        })
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
