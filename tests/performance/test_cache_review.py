"""Evidence checks must reject changed outputs and invalid process clocks."""

import json
from pathlib import Path
import tempfile
import unittest

from tools.performance.cache_review import prepare, process_record
from tools.performance.cache_review_checks import toml_settings


class ProcessRecordTests(unittest.TestCase):
    def test_prepare_refuses_git_checkout_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".git").write_text("gitdir: elsewhere\n")
            with self.assertRaisesRegex(ValueError, "not a Git checkout"):
                prepare(root)
            self.assertEqual([p.name for p in root.iterdir()], [".git"])

    def test_successful_measured_process_and_resource_units_survive(self):
        record = {"returncode": 0, "wall_s": 2.5, "user_s": 1.25, "system_s": 0.5, "max_rss_kib": 2048}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "process.json"
            path.write_text(json.dumps(record))
            self.assertEqual(process_record(path), record)

    def test_failed_nonfinite_or_negative_measurements_are_rejected(self):
        good = {"returncode": 0, "wall_s": 2.5, "user_s": 1.25, "system_s": 0.5, "max_rss_kib": 2048}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "process.json"
            for key, value in [("returncode", 1), ("wall_s", 0), ("wall_s", float("nan")),
                               ("wall_s", float("inf")), ("user_s", -1), ("max_rss_kib", -1)]:
                with self.subTest(key=key, value=value):
                    path.write_text(json.dumps(good | {key: value}))
                    with self.assertRaises(ValueError):
                        process_record(path)

    def test_alternative_view_fixture_preserves_camera_and_colour_fields(self):
        import tomllib
        fixture = {"schema_version": 2, "width": 640, "height": 480, "format": "png", "step_stride": 4,
                   "camera": {"eye_m": [1.0, 2.0, 3.0], "near_m": 0.001},
                   "particles": {"colour_mode": "kinetic_energy", "max_energy_j": 1.962}}
        self.assertEqual(tomllib.loads(toml_settings(fixture)), fixture)


if __name__ == "__main__":
    unittest.main()
