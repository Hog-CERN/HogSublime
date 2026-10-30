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

