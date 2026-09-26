from __future__ import annotations
import glob, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
def fail(text): raise SystemExit("RELEASE CHECK FAILED: " + text)
def main():
    from version import APP_VERSION
    demo = ROOT / "examples/14_Лаборатория_сигналов_отладка.json"
    if not demo.exists(): fail("нет демонстрационной лаборатории в examples")
    if (ROOT / "requirements.txt").exists():
        fail("requirements.txt не должен возвращаться в корень")
    if (ROOT / "demo_project.json").exists():
        fail("демо не должно лежать в корне")
    if list(ROOT.glob("CHANGES_*.md")):
        fail("отдельные CHANGES_*.md запрещены: история хранится в README_RU.md")
    project = json.loads(demo.read_text(encoding="utf-8"))
    types = {n.get("type") for n in project.get("nodes", [])}
    required = {"Form","Start","Slider","Dial","ForRange","DataHub","EventHub","ConvertValue","FormatStr","Button"}
    if required - types: fail("в демо отсутствуют ноды: " + ", ".join(sorted(required-types)))
    kinds = {c.get("signal_type") for c in project.get("connections", [])}
    if not {"data","event","request","response","error"} <= kinds:
        fail("в демо нет всех типов цветовых сигналов")
    node_by_id = {node.get("id"): node for node in project.get("nodes", [])}
    occupied_inputs = {}
    for connection in project.get("connections", []):
        target = node_by_id.get(connection.get("to_node"), {})
        target_type = target.get("type")
        # A generated input receives one source. Fan-in must use separate
        # dynamic hub ports, never several wires on the same target point.
        key = (connection.get("to_node"), connection.get("to_port"))
        if key in occupied_inputs:
            fail(
                "в демо несколько источников на точке "
                f"{connection.get('to_node')}:{connection.get('to_port')}"
            )
        occupied_inputs[key] = connection
    canvas = (ROOT / "builder_ui/canvas.py").read_text(encoding="utf-8")
    window = (ROOT / "builder_ui/main_window.py").read_text(encoding="utf-8")
    state = json.loads((ROOT / "PROJECT_STATE.json").read_text(encoding="utf-8"))
    readme = (ROOT / "README_RU.md").read_text(encoding="utf-8")
    generator_text = (ROOT / "generator.py").read_text(encoding="utf-8")
    container_text = (ROOT / "container_support.py").read_text(encoding="utf-8")
    contract_text = (ROOT / "model_contract.py").read_text(encoding="utf-8")
    panel_text = (ROOT / "builder_ui/property_panel.py").read_text(encoding="utf-8")
    importer_text = (ROOT / "ui_importer.py").read_text(encoding="utf-8")
    version_text = (ROOT / "version.py").read_text(encoding="utf-8")
    user_help_text = (ROOT / "user_help.py").read_text(encoding="utf-8")
    python_catalog_text = (ROOT / "python_catalog.py").read_text(encoding="utf-8")
    container_library_text = (ROOT / "container_library.py").read_text(encoding="utf-8")
    connection_advisor_text = (ROOT / "connection_advisor.py").read_text(encoding="utf-8")
    if state.get("version") != APP_VERSION:
        fail("PROJECT_STATE.json не совпадает с единым источником версии")
    if f'APP_VERSION = "{APP_VERSION}"' not in version_text:
        fail("version.py не содержит ожидаемую APP_VERSION")
    if APP_VERSION not in readme:
        fail("README_RU.md не содержит текущую версию")
    if "def debug_icon_button" not in window or "setIcon(self.style().standardIcon" not in window:
        fail("панель отладки вернулась к текстовым кнопкам")
    for old_button in (
        'self.debug_start_button = QPushButton("',
        'self.debug_continue_button = QPushButton("',
        'self.debug_step_button = QPushButton("',
        'self.debug_stop_button = QPushButton("',
    ):
        if old_button in window:
            fail("найдена старая текстовая кнопка отладки: " + old_button)
    if "_VPB_DEBUG_ENABLED" not in generator_text or "if not _VPB_DEBUG_ENABLED" not in generator_text:
        fail("обычный F5 не защищён от отладочных trace-событий")
    for needle, text in (
        ("debug_position", canvas),
        ("HelperItem", canvas),
        ("HelperPaletteListWidget", window),
        ("application/x-visual-python-helper", canvas),
        ("BreakFlagItem", canvas),
        ("Сделать разрыв", canvas),
        ("Помощники", window),
        ("debug_run_button", window),
        ("smart_layout_and_route", canvas),
        ("QMdiArea", generator_text),
        ("QMdiSubWindow", generator_text),
        ("_content_top_offset", (ROOT / "builder_ui/form_editor.py").read_text(encoding="utf-8")),
        ("#BDBDBD", canvas),
        ("QGraphicsLineItem", (ROOT / "builder_ui/common.py").read_text(encoding="utf-8")),
        ("Палитра…", canvas),
        ("fill_alpha", canvas),
        ("inner_helpers", container_text),
        ("is_container_bridge", canvas),
        ("update_container_interface_frame", canvas),
        ("_frame_route_points", canvas),
        ("addSubWindow(self.", generator_text),
        ("ShowAlphaChannel", canvas),
        ("_near_resize_handle", canvas),
        ("_clamp_node_position", canvas),
        ("helper:text", window),
        ("helper:shape", window),
        ("AlignHCenter", canvas),
        ("быстрым маршрутом", canvas),
        ("self.problems_dock.show()", window),
        ('dock.setObjectName("problemsDock")', window),
        ("def validate_component_catalog", contract_text),
        ("def normalize_node_model", contract_text),
        ("def component_passport", contract_text),
        ("def property_group_name", contract_text),
        ("def port_identifier", contract_text),
        ("def split_port_identifier", contract_text),
        ("def diagnose_node_model", contract_text),
        ("def repair_mdi_parentage", contract_text),
        ("port_identifier(port.name, port.kind)", contract_text),
        ("def port_for", canvas),
        ("port_for(model[\"from_port\"], outgoing=True)", canvas),
        ("port_for(model[\"to_port\"], outgoing=False)", canvas),
        ("normalize_node_model(model)", panel_text),
        ("property_group_name(prop)", panel_text),
        ("UserRole + 3", panel_text),
        ("Описание выбранного свойства", panel_text),
        ("_property_selection_changed", panel_text),
        ("diagnose_node_model(node)", window),
        ("property_status", panel_text),
        ("_set_diagnostic_status", panel_text),
        ("property_errors", panel_text),
        ('prop.kind in {"enum", "choice"}', panel_text),
        ('prop.kind in {"multiline", "code", "table"}', panel_text),
        ('passport["support_status"]', panel_text),
        ('passport.get("hiasm"', panel_text),
        ('"support_status": spec.support_status', contract_text),
        ("imported_qt = bool(properties.get", contract_text),
        ("setClearButtonEnabled", panel_text),
        ("UserRole + 4", panel_text),
        ("def _has_mdi_ancestor", importer_text),
        ("has_explicit_geometry", importer_text),
        ("use_runtime=not in_mdi_tree", importer_text),
        ("APP_VERSION", window),
        ("repair_mdi_parentage(project)", generator_text),
        ("repair_mdi_parentage(project)", canvas),
        ("def _frame_port_point", canvas),
        ("def container_frame_anchor", canvas),
        ("def _point_on_container_frame", canvas),
        ("def _show_points_dialog", canvas),
        ("panel.tabs.setCurrentIndex(1)", canvas),
        ("def _near_container_frame", canvas),
        ("def _container_proxy_definition", canvas),
        ("def _container_drop_anchor", canvas),
        ("def _create_container_point_from_wire", canvas),
        ("start = self._frame_port_point(self.source)", canvas),
        ("end = self._frame_port_point(self.target)", canvas),
        ("QTableView", importer_text),
        ('"QTableView": "TableView"', importer_text),
        ("self.{name} = QTableView", generator_text),
        ("skipped_wrapper", importer_text),
        ("parent_is_scroll_area", importer_text),
        ("skipped_structure", importer_text),
        ("promoted_widget", importer_text),
        ('"QDialogButtonBox": "DialogButtonBox"', importer_text),
        ("QDialogButtonBox.StandardButton", generator_text),
        ("parent_is_mdi_subwindow", importer_text),
        ('name.lower() == "centralwidget"', importer_text),
        ("def _layout_imported_graph", importer_text),
        ("_layout_imported_graph(importer.nodes)", importer_text),
        ('form_props["scrollable"] = False', importer_text),
        ("Qt.ScrollBarPolicy.ScrollBarAsNeeded", generator_text),
        ('orientation", "Horizontal")) == "Vertical"', (ROOT / "builder_ui/form_editor.py").read_text(encoding="utf-8")),
        ("self.properties.set_node(None)", window),
        ('props.get("vertical", False)', (ROOT / "builder_ui/form_editor.py").read_text(encoding="utf-8")),
        ('node_type == "ProgressBar"', (ROOT / "builder_ui/form_editor.py").read_text(encoding="utf-8")),
        ('props.get("shape", "StyledPanel")) == "VLine"', (ROOT / "builder_ui/form_editor.py").read_text(encoding="utf-8")),
        ("def _menu_bar_structure", importer_text),
        ("QAction", generator_text),
        ("def emit_menu", generator_text),
        ("_form_menu_titles", (ROOT / "builder_ui/form_editor.py").read_text(encoding="utf-8")),
        ("component_search_text(spec)", window),
        ("format_component_help", window),
        ("BEGINNER_GUIDE", window),
        ("DYNAMIC_GAME_GUIDE", window),
        ("КАК ЧИТАТЬ НОДУ", user_help_text),
        ("ТОЧКИ ПОДКЛЮЧЕНИЯ", user_help_text),
        ('"Game."', python_catalog_text),
        ('"GridCanvas"', (ROOT / "components.py").read_text(encoding="utf-8")),
        ("class GridCanvasWidget", (ROOT / "instruments_runtime.py").read_text(encoding="utf-8")),
        ('node_type == "GridCanvas"', generator_text),
        ('("GridCanvas","onCellClick")', generator_text),
        ("ContainerPaletteListWidget", window),
        ('palette_tabs.addTab(', window),
        ('"Контейнеры"', window),
        ("save_container_template", window),
        ("instantiate_container_template", window),
        ("application/x-visual-python-container", canvas),
        ("def discover_container_library", container_library_text),
        ("def instantiate_container_template", container_library_text),
        ('"GridBatchWriter"', (ROOT / "components.py").read_text(encoding="utf-8")),
        ("def point_set", (ROOT / "python_library/nodes/grid_nodes.py").read_text(encoding="utf-8")),
        ("def can_place", (ROOT / "python_library/nodes/grid_nodes.py").read_text(encoding="utf-8")),
        ('node_type == "GridBatchWriter"', generator_text),
        ("Паспорт и внешний интерфейс", canvas),
        ("def _edit_container_passport", window),
        ("apply_container_interface", window),
        ("def validate_container_model", container_library_text),
        ("def apply_container_interface", container_library_text),
        ("data_type=p.type or", python_catalog_text),
        ("def advise_connection", connection_advisor_text),
        ("Python::Data.to_number", connection_advisor_text),
        ("def _insert_connection_adapter", canvas),
        ("Нужно преобразовать данные", canvas),
        ("class ConnectionNodePicker", canvas),
        ("def _connection_node_candidates", canvas),
        ("def _pick_and_connect_node", canvas),
        ("if source is not None and not rewiring", canvas),
        ('excluded = CONTAINER_PROXY_TYPES | {"UserContainer"}', canvas),
        ("def infer_port_data_type", (ROOT / "components.py").read_text(encoding="utf-8")),
        ("INTERFACE_DATA_TYPES", container_library_text),
        ('"Тип данных"', window),
        ('data_type=str(item.get("data_type") or "any")', (ROOT / "components.py").read_text(encoding="utf-8")),
        ("def diagnose_event_flow", contract_text),
        ("diagnose_event_flow(project)", window),
        ('QDockWidget("Проверка схемы"', window),
        ("advice = advise_connection(", window),
        ("Что сделать:", contract_text),
        ("def to_list", (ROOT / "python_library/nodes/data_nodes.py").read_text(encoding="utf-8")),
        ("def to_dict", (ROOT / "python_library/nodes/data_nodes.py").read_text(encoding="utf-8")),
        ("def to_color", (ROOT / "python_library/nodes/data_nodes.py").read_text(encoding="utf-8")),
        ("def to_file", (ROOT / "python_library/nodes/data_nodes.py").read_text(encoding="utf-8")),
        ("Python::Data.to_list", connection_advisor_text),
        ("Python::Data.to_dict", connection_advisor_text),
        ("def connection_passport", connection_advisor_text),
        ("def passport_text", canvas),
        ("Паспорт связи…", canvas),
        ("Перейти к началу нити", canvas),
        ("Перейти к концу нити", canvas),
        ("QTimer.singleShot(550", canvas),
        ("def node_instance_search_text", user_help_text),
        ("def _create_navigator", window),
        ("navigatorDock", window),
        ("QKeySequence.StandardKey.Find", window),
        ("def _navigator_item_activated", window),
        ("project_loaded = Signal()", canvas),
        ("def project_node_records", user_help_text),
        ("Искать внутри вложенных контейнеров", window),
        ("def _navigator_root_project", window),
        ("self._commit_all_containers()", window),
        ("build_interface(inner, previous_interface)", window),
        ("def build_interface(", container_text),
        ("old_by_proxy", container_text),
        ("containerPathBar", window),
        ("← На уровень выше", window),
        ("def _update_container_breadcrumb", window),
        ("def _navigate_container_depth", window),
        ('self.tabs.addTab(self.scheme_page, "Схема")', window),
        ("def _reset_container_navigation", window),
        ('props["data_type"] = normalize_data_type(', canvas),
        ("data_type_source", canvas),
        ("proxy-нода хранит", container_library_text),
        ("advise_connection(", container_library_text),
        ("Выбран вручную в паспорте", window),
        ("data_type_source", container_text),
    ):
        if needle not in text: fail("пропало улучшение: " + needle)
    from components import COMPONENTS
    from model_contract import validate_component_catalog
    if any(key.startswith("Python::Game.") for key in COMPONENTS):
        fail("в палитру вернулись узкопредметные игровые ноды")
    catalog_errors = validate_component_catalog()
    if catalog_errors:
        fail("ошибки каталога компонентов: " + "; ".join(catalog_errors[:5]))
    if "Добавьте хотя бы один визуальный компонент." in window:
        fail("пустое окно снова запрещено валидатором")
    from generator import generate_python
    files = sorted(glob.glob(str(ROOT / "examples/*.json")))
    for filename in files:
        try: compile(generate_python(json.loads(Path(filename).read_text(encoding="utf-8"))), filename, "exec")
        except Exception as exc: fail(f"ошибка генерации {Path(filename).name}: {exc}")
    print(f"release-check-ok: demo, {len(files)} examples, helpers, selection, markers, breaks")
if __name__ == "__main__": main()
