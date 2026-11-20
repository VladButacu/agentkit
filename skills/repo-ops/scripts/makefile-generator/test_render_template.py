"""Template rendering checks."""
# Twin in skills/repo-ops/scripts/pyproject-generator; fix both or neither.

import contextlib
import io
import unittest

from render_template import (
    TEMPLATES,
    main,
    parse_settings,
    placeholders,
    render,
    template_path,
)


class RenderChecks(unittest.TestCase):
    def test_every_template_renders_from_its_own_placeholders(self):
        for path in sorted(TEMPLATES.iterdir()):
            with self.subTest(template=path.name):
                text = path.read_text(encoding="utf-8")
                values = {key: f"value-{key.lower()}" for key in placeholders(text)}
                self.assertNotIn("{{", render(text, values))

    def test_missing_value_is_rejected(self):
        with self.assertRaisesRegex(ValueError, r"missing: \['PROJECT_NAME'\]"):
            render("name = {{PROJECT_NAME}}", {})

    def test_unused_value_is_rejected(self):
        with self.assertRaisesRegex(ValueError, r"unused: \['TYPO'\]"):
            render("name = {{PROJECT_NAME}}", {"PROJECT_NAME": "a", "TYPO": "b"})

    def test_value_is_substituted_verbatim(self):
        self.assertEqual(render("a {{X}} b", {"X": "y $(z) {{Q}}"}), "a y $(z) {{Q}} b")

    def test_setting_needs_key_and_value(self):
        with self.assertRaises(ValueError):
            parse_settings(["NO_EQUALS"])
        with self.assertRaises(ValueError):
            parse_settings(["=value"])

    def test_setting_value_may_contain_equals(self):
        self.assertEqual(parse_settings(["URL=https://x.test/?a=b"]), {"URL": "https://x.test/?a=b"})

    def test_duplicate_setting_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_settings(["A=1", "A=2"])

    def test_service_name_does_not_match_its_db_variant(self):
        self.assertEqual(template_path("python-service").stem, "python-service")

    def test_unknown_template_is_rejected(self):
        with self.assertRaises(ValueError):
            template_path("no-such-type")

    def test_list_prints_the_placeholders_a_template_needs(self):
        text = template_path("python-service").read_text(encoding="utf-8")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(main(["list", "python-service"]), 0)
        self.assertEqual(output.getvalue().split(), sorted(placeholders(text)))


if __name__ == "__main__":
    unittest.main()
