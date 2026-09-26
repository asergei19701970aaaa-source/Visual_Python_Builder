import tempfile
import unittest
import json
from pathlib import Path

from ui_importer import import_ui_to_project
from generator import generate_python
from model_contract import repair_mdi_parentage


MDI_UI = """<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>MainWindow</class>
 <widget class="QMainWindow" name="MainWindow">
  <property name="geometry"><rect><x>0</x><y>0</y><width>900</width><height>600</height></rect></property>
  <property name="windowTitle"><string>MDI</string></property>
  <widget class="QWidget" name="centralwidget">
   <property name="geometry"><rect><x>0</x><y>0</y><width>900</width><height>560</height></rect></property>
   <widget class="QMdiArea" name="mdiArea">
    <property name="geometry"><rect><x>20</x><y>30</y><width>840</width><height>500</height></rect></property>
    <widget class="QMdiSubWindow" name="subWindow">
     <property name="geometry"><rect><x>50</x><y>60</y><width>420</width><height>280</height></rect></property>
     <property name="windowTitle"><string>Дочернее</string></property>
     <widget class="QWidget" name="subContent">
      <property name="geometry"><rect><x>0</x><y>0</y><width>400</width><height>240</height></rect></property>
      <widget class="QPushButton" name="button">
       <property name="geometry"><rect><x>17</x><y>29</y><width>120</width><height>32</height></rect></property>
       <property name="text"><string>OK</string></property>
      </widget>
     </widget>
    </widget>
   </widget>
  </widget>
 </widget>
</ui>
"""


class UiImporterContractTests(unittest.TestCase):
    def test_mdi_branch_keeps_ui_relative_coordinates_and_parent_chain(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "mdi.ui"
            path.write_text(MDI_UI, encoding="utf-8")
            project, _report = import_ui_to_project(path)

        by_name = {
            node["properties"].get("name"): node
            for node in project["nodes"]
        }
        area = by_name["mdiArea"]
        subwindow = by_name["subWindow"]
        button = by_name["button"]
        form = by_name["MainWindow"]
        self.assertNotIn("centralwidget", by_name)
        self.assertNotIn("subContent", by_name)
        self.assertEqual(area["properties"]["x"], 20)
        self.assertEqual(subwindow["properties"]["x"], 50)
        self.assertEqual(subwindow["properties"]["y"], 60)
        self.assertEqual(button["parent_id"], subwindow["id"])
        self.assertEqual(button["properties"]["x"], 17)
        self.assertEqual(button["properties"]["y"], 29)
        self.assertEqual(subwindow["properties"]["mdi_role"], "subwindow")
        self.assertFalse(form["properties"]["scrollable"])
        self.assertEqual(form["properties"]["viewport_width"], 900)
        self.assertEqual(form["properties"]["viewport_height"], 600)
        generated = generate_python(project)
        self.assertNotIn("self.content_scroll = QScrollArea(self)", generated)
        self.assertIn("self.setCentralWidget(self.central)", generated)
        graph_positions = {
            (node["x"], node["y"])
            for node in project["nodes"]
            if node["type"] != "Form"
        }
        self.assertEqual(
            len(graph_positions),
            len([node for node in project["nodes"] if node["type"] != "Form"]),
        )
        self.assertNotEqual(
            (button["x"], button["y"]),
            (button["properties"]["x"], button["properties"]["y"]),
        )

    def test_scroll_area_contents_is_not_imported_as_a_bridge_node(self):
        source = """<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>MainWindow</class>
 <widget class="QMainWindow" name="MainWindow">
  <property name="geometry"><rect><x>0</x><y>0</y><width>500</width><height>400</height></rect></property>
  <widget class="QScrollArea" name="scrollArea">
   <property name="geometry"><rect><x>10</x><y>10</y><width>300</width><height>250</height></rect></property>
   <widget class="QWidget" name="scrollAreaWidgetContents">
    <property name="geometry"><rect><x>0</x><y>0</y><width>600</width><height>500</height></rect></property>
    <widget class="QTableView" name="tableView">
     <property name="geometry"><rect><x>12</x><y>18</y><width>240</width><height>120</height></rect></property>
    </widget>
   </widget>
  </widget>
 </widget>
</ui>
"""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "scroll.ui"
            path.write_text(source, encoding="utf-8")
            project, report = import_ui_to_project(path)
        names = {
            node["properties"].get("name"): node for node in project["nodes"]
        }
        self.assertNotIn("scrollAreaWidgetContents", names)
        self.assertEqual(names["tableView"]["type"], "TableView")
        self.assertEqual(names["tableView"]["parent_id"], names["scrollArea"]["id"])
        self.assertTrue(any(row["class"] == "skipped_wrapper" for row in report))
        self.assertFalse(any(row["class"] == "unsupported_widget" for row in report))
        code = generate_python(project)
        self.assertIn("self.tableView = QTableView(", code)
        self.assertNotIn("Колонка 1", code)
        compile(code, "table_view.py", "exec")

    def test_dialog_button_box_keeps_real_standard_buttons(self):
        source = """<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>MainWindow</class>
 <widget class="QMainWindow" name="MainWindow">
  <property name="geometry"><rect><x>0</x><y>0</y><width>500</width><height>300</height></rect></property>
  <widget class="QWidget" name="centralwidget">
   <widget class="QDialogButtonBox" name="buttonBox">
    <property name="geometry"><rect><x>20</x><y>220</y><width>156</width><height>24</height></rect></property>
    <property name="orientation"><enum>Qt::Orientation::Horizontal</enum></property>
    <property name="centerButtons"><bool>true</bool></property>
    <property name="standardButtons">
     <set>QDialogButtonBox::StandardButton::Cancel|QDialogButtonBox::StandardButton::Ok</set>
    </property>
   </widget>
  </widget>
 </widget>
</ui>
"""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "buttons.ui"
            path.write_text(source, encoding="utf-8")
            project, report = import_ui_to_project(path)
        box = next(
            node for node in project["nodes"]
            if node["properties"].get("name") == "buttonBox"
        )
        self.assertEqual(box["type"], "DialogButtonBox")
        self.assertEqual(box["properties"]["buttons"], "Cancel|Ok")
        self.assertEqual(box["properties"]["orientation"], "Horizontal")
        self.assertTrue(box["properties"]["center_buttons"])
        self.assertFalse(any(row["class"] == "unsupported_widget" for row in report))
        code = generate_python(project)
        self.assertIn("self.buttonBox = QDialogButtonBox(self.central)", code)
        self.assertIn("QDialogButtonBox.StandardButton.Cancel", code)
        self.assertIn("QDialogButtonBox.StandardButton.Ok", code)
        self.assertNotIn("self.buttonBox = QFrame(", code)
        compile(code, "dialog_button_box.py", "exec")

    def test_vertical_controls_keep_orientation_in_model_and_generator(self):
        source = """<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>MainWindow</class>
 <widget class="QMainWindow" name="MainWindow">
  <property name="geometry"><rect><x>0</x><y>0</y><width>500</width><height>400</height></rect></property>
  <widget class="QWidget" name="centralwidget">
   <widget class="Line" name="verticalLine">
    <property name="geometry"><rect><x>300</x><y>40</y><width>3</width><height>180</height></rect></property>
    <property name="orientation"><enum>Qt::Orientation::Vertical</enum></property>
   </widget>
   <widget class="QProgressBar" name="verticalProgress">
    <property name="geometry"><rect><x>340</x><y>40</y><width>24</width><height>180</height></rect></property>
    <property name="orientation"><enum>Qt::Orientation::Vertical</enum></property>
    <property name="value"><number>35</number></property>
   </widget>
   <widget class="QSlider" name="verticalSlider">
    <property name="geometry"><rect><x>390</x><y>40</y><width>22</width><height>180</height></rect></property>
    <property name="orientation"><enum>Qt::Orientation::Vertical</enum></property>
   </widget>
  </widget>
 </widget>
</ui>
"""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "vertical.ui"
            path.write_text(source, encoding="utf-8")
            project, _report = import_ui_to_project(path)
        by_name = {
            node["properties"].get("name"): node for node in project["nodes"]
        }
        self.assertTrue(by_name["verticalLine"]["properties"]["vertical"])
        self.assertEqual(
            by_name["verticalProgress"]["properties"]["orientation"],
            "Vertical",
        )
        self.assertEqual(
            by_name["verticalSlider"]["properties"]["orientation"],
            "Vertical",
        )
        code = generate_python(project)
        self.assertIn("QFrame.Shape.VLine", code)
        self.assertIn(
            "self.verticalProgress.setOrientation(Qt.Orientation.Vertical)",
            code,
        )
        self.assertIn(
            "self.verticalSlider = QSlider(Qt.Orientation.Vertical",
            code,
        )
        compile(code, "vertical_controls.py", "exec")

    def test_menu_actions_are_kept_without_graph_nodes(self):
        source = """<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>MainWindow</class>
 <widget class="QMainWindow" name="MainWindow">
  <property name="geometry"><rect><x>0</x><y>0</y><width>640</width><height>480</height></rect></property>
  <widget class="QWidget" name="centralwidget"/>
  <widget class="QMenuBar" name="menubar">
   <widget class="QMenu" name="menuFile">
    <property name="title"><string>Файл</string></property>
    <addaction name="actionOpen"/>
    <addaction name="separator"/>
    <addaction name="actionAutosave"/>
   </widget>
   <addaction name="menuFile"/>
  </widget>
  <widget class="QStatusBar" name="statusbar"/>
  <action name="actionOpen">
   <property name="text"><string>Открыть</string></property>
   <property name="shortcut"><keysequence>Ctrl+O</keysequence></property>
   <property name="statusTip"><string>Открыть проект</string></property>
  </action>
  <action name="actionAutosave">
   <property name="checkable"><bool>true</bool></property>
   <property name="checked"><bool>true</bool></property>
   <property name="text"><string>Автосохранение</string></property>
  </action>
 </widget>
</ui>
"""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "menu.ui"
            path.write_text(source, encoding="utf-8")
            project, report = import_ui_to_project(path)
        form = next(node for node in project["nodes"] if node["type"] == "Form")
        properties = form["properties"]
        self.assertTrue(properties["menu_bar"])
        self.assertTrue(properties["statusbar_enabled"])
        menus = json.loads(properties["menus"])
        self.assertEqual(menus[0]["title"], "Файл")
        self.assertEqual(menus[0]["items"][0]["text"], "Открыть")
        self.assertEqual(menus[0]["items"][0]["shortcut"], "Ctrl+O")
        self.assertEqual(menus[0]["items"][1]["type"], "separator")
        self.assertTrue(menus[0]["items"][2]["checkable"])
        self.assertTrue(menus[0]["items"][2]["checked"])
        self.assertFalse(any(
            node.get("properties", {}).get("_qt_class") in {
                "QMenuBar", "QMenu", "QAction"
            }
            for node in project["nodes"]
        ))
        self.assertTrue(any(row["class"] == "imported_menu" for row in report))
        self.assertFalse(any(row["class"] == "unsupported_menu" for row in report))
        code = generate_python(project)
        self.assertIn("self.menuBar().addMenu('Файл')", code)
        self.assertIn("QAction('Открыть', self)", code)
        self.assertIn("QKeySequence('Ctrl+O')", code)
        self.assertIn(".addSeparator()", code)
        self.assertIn(".setCheckable(True)", code)
        self.assertIn("self.statusBar()", code)
        compile(code, "menu.py", "exec")

    def test_old_orphaned_mdi_subwindow_is_repaired_before_generation(self):
        project = {
            "format": 1,
            "nodes": [
                {
                    "id": "form",
                    "type": "Form",
                    "properties": {"width": 700, "height": 500},
                },
                {
                    "id": "area",
                    "type": "Frame",
                    "properties": {
                        "name": "mdiArea",
                        "_qt_class": "QMdiArea",
                        "mdi_role": "area",
                        "x": 10, "y": 10, "width": 650, "height": 440,
                    },
                },
                {
                    "id": "child",
                    "type": "Frame",
                    "properties": {
                        "name": "subwindow",
                        "_qt_class": "QMdiSubWindow",
                        "mdi_role": "subwindow",
                        "x": 40, "y": 50, "width": 320, "height": 220,
                    },
                },
            ],
            "connections": [],
        }
        repair_mdi_parentage(project)
        child = next(node for node in project["nodes"] if node["id"] == "child")
        self.assertEqual(child["parent_id"], "area")
        code = generate_python(project)
        self.assertIn("self.mdiArea.addSubWindow(self.subwindow_content)", code)
        self.assertNotIn("self.central.addSubWindow", code)
        compile(code, "repaired_mdi.py", "exec")


if __name__ == "__main__":
    unittest.main()