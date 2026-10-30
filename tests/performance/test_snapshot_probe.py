"""Provenance reports reject changed bytes, incomplete rounds and mismatched inputs."""

import json
from pathlib import Path
import tempfile
import unittest

from tools.performance.snapshot_probe import assess


class SnapshotEvidenceTests(unittest.TestCase):
    def fixture(self, root: Path):
        (root / "micro").mkdir()
        (root / "requests").mkdir()
        states = [dict(path=f"state-{i}.bin", step=str(i), snapshot_sha256="sha256:"+"a"*64)
                  for i in range(21)]
        (root / "requests/example.json").write_text(json.dumps(dict(states=states)), encoding="utf-8")
        records = [dict(kind="equivalence", state=s["path"], step=int(s["step"]), canonical_bytes=100,
                        snapshot_sha256="a"*64, write_calls={k:dict(bytes=100,calls=20,tiny_calls=10)
                        for k in ("generic","specialised")}) for s in states]
        for algorithm in ("original","reserved","generic_stream","specialised_stream","format_only","sha_only"):
            for repeat in range(6):
                records.append(dict(kind="timing",algorithm=algorithm,repeat=repeat,warmup=repeat==0,
                    elapsed_s=999 if repeat==0 else (2 if algorithm=="specialised_stream" else 4),
                    snapshots=21,canonical_bytes=2100))
        path = root / "micro/example.jsonl"
        path.write_text("\n".join(map(json.dumps,records)),encoding="utf-8")
        return path,records

    def test_summary_excludes_warmups_and_preserves_each_algorithm_sample(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root)
            row, = assess(root)
            self.assertEqual(row["medians_s"]["specialised_stream"], 2)
            self.assertEqual(row["samples_s"]["original"], [4]*5)
            self.assertEqual(row["speedups"]["specialised_stream"], 2)
            self.assertEqual(row["canonical_bytes"], 2100)

    def test_changed_provenance_and_byte_count_are_rejected(self):
        for mutation, message in (("snapshot_sha256","provenance"),("canonical_bytes","byte counts")):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                path,records = self.fixture(root)
                records[0][mutation] = "b"*64 if mutation=="snapshot_sha256" else 99
                path.write_text("\n".join(map(json.dumps,records)),encoding="utf-8")
                with self.assertRaisesRegex(ValueError,message): assess(root)

    def test_duplicate_round_and_inconsistent_timer_workload_are_rejected(self):
        for mutation,message in (("repeat","timing identity"),("snapshots","boundary"),("elapsed_s","boundary")):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                root=Path(temporary)
                path,records=self.fixture(root)
                records[-1][mutation] = 0 if mutation!="elapsed_s" else float("inf")
                path.write_text("\n".join(map(json.dumps,records)),encoding="utf-8")
                with self.assertRaisesRegex(ValueError,message): assess(root)


if __name__ == "__main__":
    unittest.main()
