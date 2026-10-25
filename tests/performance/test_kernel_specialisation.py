"""A named-entry experiment still requires identical completed physical work."""

import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.performance.kernel_specialisation import accepted, verify
from tools.performance.compact_trace import analyse


class SpecialisationTests(unittest.TestCase):
    def test_failures_and_wrong_execution_cannot_be_admitted_as_speedups(self):
        process = {"exit_code": 0, "timed_out": False, "interrupted": False}
        document = {"completed_steps": "480", "status": "completed", "failures": [],
                    "metadata": {"debug_assertions": False},
                    "execution": {"mode": "cuda", "device": 0, "threads": 128}}
        accepted(process, document, None, 480)
        for changes in ({"completed_steps": "479"}, {"status": "failed"},
                        {"execution": {"mode": "serial"}}, {"failures": ["failed attempt"]},
                        {"metadata": {"debug_assertions": True}}):
            candidate = copy.deepcopy(document)
            candidate.update(changes)
            with self.assertRaises(ValueError):
                accepted(process, candidate, None, 480)
        for key in ("timed_out", "interrupted"):
            with self.assertRaises(ValueError):
                accepted({**process, key: True}, document, None, 480)
        with patch("tools.performance.kernel_specialisation.compare", return_value={"passed": False}):
            with self.assertRaises(ValueError):
                accepted(process, document, document, 480)

    def test_changed_source_and_escaping_paths_fail_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            (work / "candidate").mkdir()
            (work / "candidate/source").write_text("changed")
            for name in ("source", "../outside"):
                with self.assertRaises(ValueError):
                    verify(work, {"candidate": {"files_sha256": {name: "wrong"}}})

    def test_invalid_entry_tables_fail_before_trace_io(self):
        for names in (("only-one",), ("",) * 13, (None,) * 13):
            with self.assertRaisesRegex(ValueError, "thirteen non-empty"):
                analyse(Path("missing"), 110592, 480, "compact-stages", entry_names=names)

    def test_one_function_can_serve_several_operation_ids(self):
        # Repeated names are legitimate for shared dispatch. They must reach
        # trace loading rather than being rejected as an invalid entry map.
        with patch("tools.performance.compact_trace.sqlite3.connect", side_effect=OSError("trace read")) as read:
            with self.assertRaisesRegex(OSError, "trace read"):
                analyse(Path("missing"), 110592, 480, "compact-stages", entry_names=("solver",) * 13)
            read.assert_called_once()


if __name__ == "__main__":
    unittest.main()
