import unittest

from components import COMPONENTS, effective_ports
from practical_help import audit_help_coverage, component_help, port_help, property_help, render_help


class PracticalHelpTests(unittest.TestCase):
    def test_every_catalog_item_has_help(self):
        self.assertEqual([], audit_help_coverage())

    def test_help_has_practical_sections(self):
        entry = component_help("Button")
        text = render_help(entry)
        for title in ("Что делает:", "Когда применять:", "Как использовать:", "Что получится:", "Следующий шаг:", "Пример:", "Частая ошибка:"):
            self.assertIn(title, text)

    def test_all_points_and_settings_are_explained(self):
        for type_name, spec in COMPONENTS.items():
            for port in effective_ports(type_name):
                self.assertTrue(port_help(type_name, port.name).purpose.strip())
            for prop in spec.properties:
                self.assertTrue(property_help(type_name, prop.name).purpose.strip())


if __name__ == "__main__":
    unittest.main()
