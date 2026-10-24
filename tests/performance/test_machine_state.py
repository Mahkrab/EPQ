"""An unavailable GPU reading must leave useful, explicitly limited host evidence."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.performance.machine_state import capture


class MachineStateTests(unittest.TestCase):
    def test_failed_gpu_reading_does_not_discard_linux_counters(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "before"

            def failed_reading(command, source, target, **limits):
                self.assertEqual(command[0], "nvidia-smi")
                self.assertEqual(limits, {"timeout": 30, "grace": 5})
                target.mkdir(parents=True)
                (target / "process.json").write_text('{"exit_code": 1}')
                return {"exit_code": 1}, None

            with patch("tools.performance.machine_state.invoke", side_effect=failed_reading), \
                    patch("tools.performance.machine_state.Path.read_text", side_effect=["synthetic CPU counters", "synthetic load"]), \
                    patch("tools.performance.machine_state.utc", return_value="2026-01-01T00:00:00+00:00"):
                capture(Path(temp), destination)

            self.assertEqual(json.loads((destination / "gpu/process.json").read_text()), {"exit_code": 1})
            reading = json.loads((destination / "linux.json").read_text())
            self.assertEqual(reading["cpu_counters"], "synthetic CPU counters")
            self.assertEqual(reading["load"], "synthetic load")
            self.assertIn("not a complete view of Windows workload", reading["scope"])


if __name__ == "__main__":
    unittest.main()
