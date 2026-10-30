"""Checks that syntax_test files cannot express: behaviour on line 1 (where the
SYNTAX TEST header lives), file associations and preferences.

Run by UnitTesting inside Sublime Text (see tests/run_syntax_tests.sh).
"""
import sublime
from unittest import TestCase

LIST_SYNTAX = "Packages/Hog/Hog.sublime-syntax"
CONF_SYNTAX = "Packages/Hog/Hog Conf.sublime-syntax"


class ViewTestCase(TestCase):
    def setUp(self):
        self.view = sublime.active_window().new_file()
        self.view.set_scratch(True)

    def tearDown(self):
        self.view.close()

    def load(self, syntax, text):
        self.view.assign_syntax(syntax)
        self.view.run_command("append", {"characters": text})

    def scope_at(self, text):
        """Scope of the first character of the first occurrence of text."""
        point = self.view.substr(sublime.Region(0, self.view.size())).index(text)
        return self.view.scope_name(point)


class TestListDirective(ViewTestCase):
    def test_simulator_directive_on_first_line(self):
        self.load(LIST_SYNTAX, "#Simulator xsim\n[files]\ntb.vhd\n")
        self.assertIn("meta.directive.hog", self.scope_at("#Simulator"))
        self.assertIn("keyword.other.directive.hog", self.scope_at("Simulator"))
        self.assertIn("support.constant.simulator.hog", self.scope_at("xsim"))
        self.assertIn("comment.line.number-sign.hog", self.scope_at("xsim"))

    def test_first_line_without_directive_is_a_file_line(self):
        self.load(LIST_SYNTAX, "tb.vhd nosim\n")
        self.assertIn("entity.name.file.hog", self.scope_at("tb.vhd"))
        self.assertIn("storage.modifier.hog", self.scope_at("nosim"))



class TestConfDirective(ViewTestCase):
    def test_tool_and_version_on_first_line(self):
        self.load(CONF_SYNTAX, "#vivado vitis_classic 2023.1\n[main]\nPART = x\n")
        self.assertIn("meta.directive.hog-conf", self.scope_at("#vivado"))
        self.assertIn("comment.line.number-sign.hog-conf", self.scope_at("2023.1"))
        self.assertIn("support.constant.tool.hog-conf", self.scope_at("vivado"))
        self.assertIn("support.constant.tool.hog-conf", self.scope_at("vitis_classic"))
        self.assertIn("constant.numeric.version.hog-conf", self.scope_at("2023.1"))

    def test_tool_without_version(self):
        self.load(CONF_SYNTAX, "#vivado\n[main]\n")
        self.assertIn("support.constant.tool.hog-conf", self.scope_at("vivado"))
        self.assertIn("entity.name.section.hog-conf", self.scope_at("main"))

    def test_version_with_suffix(self):
        self.load(CONF_SYNTAX, "#vivado 2020.1_AR75210\n")
        self.assertIn("constant.numeric.version.hog-conf", self.scope_at("2020.1_AR75210"))

    def test_first_line_without_directive(self):
        self.load(CONF_SYNTAX, "[main]\nPART = x\n")
        self.assertIn("entity.name.section.hog-conf", self.scope_at("main"))


class TestFileAssociation(TestCase):
    def syntax_for(self, path):
        syntax = sublime.find_syntax_for_file(path)
        return syntax.path if syntax else None

    def test_hog_conf(self):
        self.assertEqual(self.syntax_for("/repo/Top/proj/hog.conf"), CONF_SYNTAX)

    def test_sim_conf(self):
        self.assertEqual(self.syntax_for("/repo/Top/proj/sim.conf"), CONF_SYNTAX)

    def test_other_conf_files_are_not_hog(self):
        self.assertNotIn(self.syntax_for("/etc/nginx/nginx.conf"), (CONF_SYNTAX, LIST_SYNTAX))

    def test_list_files(self):
        for ext in ("src", "sim", "con", "lst", "ext", "ipb"):
            with self.subTest(ext=ext):
                self.assertEqual(self.syntax_for("/repo/Top/proj/list/x." + ext), LIST_SYNTAX)

    def test_sub_is_not_associated(self):
        self.assertNotEqual(self.syntax_for("/repo/Top/proj/list/x.sub"), LIST_SYNTAX)
