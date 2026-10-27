"""Changed work and forged timing reports must not qualify an arithmetic trial."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

from tools.performance.capture import digest
from tools.performance.gradient_reassessment import accepted, embedded_ptx, verify
from tests.performance.audit_gradient_reassessment import close, duration, physical


class GradientReassessmentTests(unittest.TestCase):
    def test_workload_admission_checks_real_complete_records(self):
        result = json.loads(Path("Maelstrom/reference/falling-block-v1.json").read_bytes())
        result["execution"] = {"mode": "cuda", "device": 0, "threads": 128}
        result["metadata"].update(debug_assertions=False, build_revision="synthetic")
        process = {"exit_code": 0, "timed_out": False, "interrupted": False}
        accepted(process, result, particles=64, revision="synthetic", reference=result)
        for key in ("timed_out", "interrupted"):
            with self.assertRaises(ValueError):
                accepted({**process, key: True}, result, particles=64, revision="synthetic")
        for changes in ({"completed_steps": "479"}, {"execution": {"mode": "serial"}},
                        {"metadata": {"debug_assertions": True, "build_revision": "synthetic"}}):
            changed = copy.deepcopy(result)
            changed.update(changes)
            with self.assertRaises(ValueError):
                accepted(process, changed, particles=64, revision="synthetic")
        changed = copy.deepcopy(result)
        changed["final_snapshot"]["particles"][0]["velocity_m_s"]["x"] += 1
        with self.assertRaises(ValueError):
            accepted(process, changed, particles=64, revision="synthetic", reference=result)
        result["final_snapshot"]["particles"][0]["velocity_m_s"]["x"] = 0.0
        changed = copy.deepcopy(result)
        changed["final_snapshot"]["particles"][0]["velocity_m_s"]["x"] = -0.0
        with self.assertRaises(ValueError):
            accepted(process, changed, particles=64, revision="synthetic", reference=result)

    def test_changed_rust_identifier_cannot_hide_stale_cuda_code(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            binary, ptx = root / "executable", root / "fresh.ptx"
            binary.write_bytes(b"new Rust revision; old CUDA code")
            ptx.write_bytes(b"new CUDA code")
            with self.assertRaisesRegex(ValueError, "absent from the executable"):
                embedded_ptx(binary, ptx)
            binary.write_bytes(b"new Rust revision; new CUDA code\0")
            self.assertEqual(embedded_ptx(binary, ptx), digest(b"new CUDA code"))

    def test_independent_reader_rejects_forged_total_and_instrumented_samples(self):
        result = {"measurements": {"schema_version": 1, "mode": "total", "failed_attempt_s": None,
                                  "steps": [{"total_s": 0.125, "stages": None} for _ in range(480)]}}
        self.assertEqual(duration(result), 60)
        close(duration(result), 60)
        with self.assertRaises(ValueError):
            close(duration(result), 59)
        for invalid in (0, -1, True, float("inf"), float("nan")):
            changed = copy.deepcopy(result)
            changed["measurements"]["steps"][0]["total_s"] = invalid
            with self.assertRaises(ValueError):
                duration(changed)
        result["measurements"]["mode"] = "stages"
        with self.assertRaises(ValueError):
            duration(result)

    def test_independent_physical_reader_keeps_signed_zero(self):
        result = json.loads(Path("Maelstrom/reference/falling-block-v1.json").read_bytes())
        result["execution"] = {"mode": "cuda", "device": 0, "threads": 128}
        result["metadata"].update(debug_assertions=False, build_revision="synthetic")
        changed = copy.deepcopy(result)
        result["final_snapshot"]["particles"][0]["velocity_m_s"]["x"] = 0.0
        changed["final_snapshot"]["particles"][0]["velocity_m_s"]["x"] = -0.0
        self.assertNotEqual(physical(result, 64, "synthetic"), physical(changed, 64, "synthetic"))

    def test_changed_source_or_binary_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            (work / "candidate").mkdir()
            (work / "bin").mkdir()
            (work / "candidate/source").write_bytes(b"source")
            (work / "bin/candidate").write_bytes(b"binary")
            identities = {"candidate": {"files_sha256": {"source": digest(b"source")},
                                        "binary_sha256": digest(b"binary")}}
            verify(work, identities)
            (work / "bin/candidate").write_bytes(b"different binary")
            with self.assertRaises(ValueError):
                verify(work, identities)
            identities["candidate"].pop("binary_sha256")
            (work / "candidate/source").write_bytes(b"different source")
            with self.assertRaises(ValueError):
                verify(work, identities)


if __name__ == "__main__":
    unittest.main()
