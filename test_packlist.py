"""Tests for packlist."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import packlist


class TestBuildList(unittest.TestCase):
    def test_base_items_always_present(self):
        items = packlist.build_list(1, [], [])
        names = [i.name for i in items]
        self.assertIn("passport / ID", names)
        self.assertIn("phone + charger", names)

    def test_per_day_items_scale_and_cap(self):
        items = packlist.build_list(3, [], [])
        socks = next(i for i in items if i.name == "socks")
        self.assertEqual(socks.qty, 3)
        items = packlist.build_list(30, [], [])
        socks = next(i for i in items if i.name == "socks")
        self.assertEqual(socks.qty, 7)  # capped

    def test_climate_items_added(self):
        items = packlist.build_list(2, ["cold"], [])
        names = [i.name for i in items]
        self.assertIn("warm jacket", names)
        self.assertNotIn("sunscreen", names)

    def test_unknown_climate_rejected(self):
        with self.assertRaises(ValueError):
            packlist.build_list(2, ["volcanic"], [])

    def test_unknown_activity_rejected(self):
        with self.assertRaises(ValueError):
            packlist.build_list(2, [], ["skydiving"])

    def test_zero_days_rejected(self):
        with self.assertRaises(ValueError):
            packlist.build_list(0, [], [])

    def test_custom_items_and_weight(self):
        items = packlist.build_list(
            1, [], [], custom=[{"name": "camera", "weight_g": 650,
                                "category": "gear", "qty": 2}])
        camera = next(i for i in items if i.name == "camera")
        self.assertEqual(camera.total_g, 1300)

    def test_carry_on_check(self):
        light = packlist.build_list(1, [], [])
        self.assertLessEqual(packlist.total_weight_g(light), 7000)
        heavy = packlist.build_list(10, ["cold"], ["hiking", "formal"])
        self.assertGreater(packlist.total_weight_g(heavy), 7000)
        text = packlist.render_text(heavy, 10, 7000)
        self.assertIn("OVER", text)

    def test_combo_warning(self):
        warnings = packlist.warnings_for(["cold", "rain"], [])
        self.assertEqual(len(warnings), 1)
        self.assertIn("waterproof shell", warnings[0])
        self.assertEqual(packlist.warnings_for(["hot"], []), [])

    def test_cli_json_output(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json",
                                         delete=False) as fh:
            json.dump({"days": 2, "climates": ["rain"],
                       "activities": ["swimming"]}, fh)
            path = fh.name
        try:
            result = subprocess.run(
                [sys.executable, "packlist.py", path, "--json"],
                capture_output=True, text=True,
                cwd=os.path.dirname(os.path.abspath(__file__)))
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertEqual(data["days"], 2)
            names = [i["name"] for i in data["items"]]
            self.assertIn("rain jacket", names)
            self.assertIn("swimsuit", names)
            self.assertGreater(data["total_weight_g"], 0)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
