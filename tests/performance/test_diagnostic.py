"""Diagnostic traffic needs its own identity without changing historical models."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.performance.capture import digest
from tools.performance.compact_trace import completion_count
from tools.performance.sort_batch import prepare
from tools.performance.diagnostic_report import summarise


class DiagnosticTests(unittest.TestCase):
    def test_confirmation_retains_outliers_and_all_original_samples(self):
        samples = [{"solver_s": n} for n in (1, 2, 3, 4, 100)]
        result = summarise(samples)
        self.assertEqual(result["median_solver_s"], 3)
        self.assertEqual(result["minimum_s"], 1)
        self.assertEqual(result["maximum_s"], 100)
        self.assertEqual(result["samples"], samples)
        self.assertEqual(len(summarise(samples * 2)["samples"]), 10)
        for values in ([], [{"solver_s": 0}] * 5, [{"solver_s": float("nan")}] * 5,
                       [{"solver_s": True}] * 5):
            with self.assertRaises(ValueError):
                summarise(values)

    def test_diagnostic_completions_do_not_rewrite_sort_or_bitset_models(self):
        self.assertEqual(completion_count(8000, 480, "compact-diagnostic"), 39840)
        self.assertEqual(completion_count(8000, 480, "compact-atomic"), 39841)
        self.assertEqual(completion_count(8000, 480, "compact-stages"), 24481)
        self.assertEqual(completion_count(1, 1, "compact-stages"), 51)
        self.assertEqual(completion_count(8000, 480, "compact-batched"), 65280)
        self.assertEqual(completion_count(8000, 480, "compact"), 108480)
        self.assertEqual(completion_count(1, 1, "compact-diagnostic"), 82)
        self.assertEqual(completion_count(3, 1, "compact-diagnostic"), 83)

    def test_unknown_experiment_is_rejected_before_destination_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(ValueError):
                prepare(root, root, root, root / "protocol", experiment="unknown")
            self.assertFalse((root / "results").exists())

    def test_prepare_separates_diagnostic_and_sort_revisions_and_allocation(self):
        for experiment, prefix, extra in (("sort-batch-v1", "sort", 0), ("diagnostic-v1", "diagnostic", 8),
                                           ("diagnostic-atomic-v1", "diagnostic-atomic", 8),
                                           ("stage-batch-v1", "stage-batch", 32)):
            with self.subTest(experiment=experiment), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                baseline, previous = root / "baseline", root / "previous"
                for side in (4, 6, 8, 10, 12, 16, 20):
                    (baseline / f"baseline/serial-grid/{side**3:06}/warmup").mkdir(parents=True)
                for side in (20, 32, 48, 64, 80):
                    (previous / f"capacity/{side**3:06}/core").mkdir(parents=True)
                for directory in (baseline, previous):
                    (directory / "campaign.json").write_text("{}")
                for variant in ("control", "candidate"):
                    source = root / variant
                    (source / "target/release").mkdir(parents=True)
                    (source / "target/release/maelstrom").write_bytes(b"synthetic executable")
                    (source / "source.txt").write_bytes(b"synthetic source")
                    (root / f"{variant}-source.json").write_text(json.dumps({
                        "tree_sha256": variant, "files_sha256": {"source.txt": digest(b"synthetic source")}}))
                protocol = root / "protocol.md"
                protocol.write_text("Synthetic protocol")
                with patch("tools.performance.sort_batch.invoke", return_value=({"exit_code": 0}, None)):
                    output = prepare(root, baseline, previous, protocol, experiment=experiment)
                campaign = json.loads((output / "campaign.json").read_bytes())
                self.assertEqual(campaign["experiment"], experiment)
                self.assertEqual(campaign["diagnostic_bytes"], extra)
                self.assertEqual(campaign["implementations"]["control"]["revision"], f"{prefix}-control-control")
                self.assertEqual(campaign["implementations"]["candidate"]["revision"], f"{prefix}-candidate-candidate")


if __name__ == "__main__":
    unittest.main()
