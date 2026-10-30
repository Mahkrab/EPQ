"""Independent density fixtures keep the architectural study's oracle honest."""
import json
import gzip
import hashlib
import io
import math
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import tarfile
import unittest

from tools.performance.architecture import restore_evidence, soa_access
from tests.performance.audit_architecture import read_attempt


class DensityOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        compiler = shutil.which("c++")
        if compiler is None:
            raise RuntimeError("the independent quality reader requires c++")
        source = Path(__file__).resolve().parents[2] / "tools/performance/architecture_quality.cpp"
        cls.binary = cls.root / "quality"
        subprocess.run([compiler, "-std=c++17", "-O2", str(source), "-o", str(cls.binary)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def run_reader(self, positions, *, reference="none", trailing=b""):
        fixture = self.root / self.id().rsplit(".", 1)[-1]
        raw = b"".join(struct.pack("<3f", *p) for p in positions)
        fixture.write_bytes(raw + bytes(len(raw)) + trailing)
        return subprocess.run([str(self.binary), str(fixture), str(len(positions)), "1", "1", "2,2,2", reference],
                              capture_output=True, text=True)

    def test_two_particle_density_includes_self_and_strict_support(self):
        process = self.run_reader([(0, 0, 0), (.5, 0, 0)])
        self.assertEqual(process.returncode, 0, process.stderr)
        value = json.loads(process.stdout)
        expected = 315 / (64 * math.pi) * (1 + .75 ** 3)
        self.assertAlmostEqual(value["density_ratio"]["mean"], expected, places=12)
        self.assertEqual(value["current_neighbours"], {"min": 1, "median": 1, "p95": 1, "max": 1})
        process = self.run_reader([(0, 0, 0), (1, 0, 0)])
        self.assertEqual(json.loads(process.stdout)["current_neighbours"]["max"], 0)

    def test_boundary_violation_and_coincidence_are_visible(self):
        process = self.run_reader([(-.25, 0, 0), (-.25, 0, 0)])
        value = json.loads(process.stdout)
        self.assertEqual(value["boundary_violation_m"], .25)
        self.assertEqual(value["coincident_rows"], 2)

    def test_wall_and_bulk_groups_include_empty_groups(self):
        value = json.loads(self.run_reader([(1, 1, 1)]).stdout)
        self.assertEqual(value["near_wall"], {"count": 0, "positive_density_error_p95": None})
        self.assertEqual(value["away_from_walls"]["count"], 1)
        self.assertAlmostEqual(value["away_from_walls"]["positive_density_error_p95"],
                               315 / (64 * math.pi) - 1, places=12)

    def test_nonfinite_and_trailing_bytes_fail(self):
        self.assertNotEqual(self.run_reader([(math.nan, 0, 0)]).returncode, 0)
        self.assertNotEqual(self.run_reader([(0, 0, 0)], trailing=b"x").returncode, 0)

    def test_reference_error_uses_particle_displacement(self):
        reference = self.root / "reference.bin"
        reference.write_bytes(struct.pack("<6f", 0, 0, 0, 0, 0, 0))
        value = json.loads(self.run_reader([(.5, 0, 0)], reference=str(reference)).stdout)
        self.assertEqual(value["position_rms_m"], .5)
        self.assertEqual(value["position_max_m"], .5)
        self.assertEqual(value["equal_position_components"], 2)


class LayoutOverlayTests(unittest.TestCase):
    def test_nested_indices_and_stores_preserve_expression_order(self):
        self.assertEqual(soa_access("b.position[i]=add(b.old_position[row[j]],delta);"),
                         "arch_store(b.position,i,add(arch_load(b.old_position,row[j]),delta));")

    def test_comparison_is_a_read(self):
        self.assertEqual(soa_access("b.position[i]==point;"), "arch_load(b.position,i)==point;")

    def test_unclosed_index_fails(self):
        with self.assertRaisesRegex(ValueError, "unclosed"):
            soa_access("b.position[row[i]")


class EvidenceIntegrityTests(unittest.TestCase):
    def test_changed_stdout_and_stderr_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = b'{"solver_s": 1.0}'
            compressed = gzip.compress(raw, mtime=0)
            sha = lambda b: hashlib.sha256(b).hexdigest()
            metadata = {"exit_code": 0, "parse_error": None,
                        "stdout_sha256": sha(raw), "stdout_gzip_sha256": sha(compressed),
                        "stderr_sha256": sha(b"")}
            (root / "process.json").write_text(json.dumps(metadata))
            (root / "stdout.gz").write_bytes(compressed)
            (root / "stderr.txt").write_bytes(b"")
            self.assertEqual(read_attempt(root)[1], {"solver_s": 1.0})
            (root / "stdout.gz").write_bytes(gzip.compress(b'{"solver_s": 0.1}', mtime=0))
            with self.assertRaisesRegex(ValueError, "raw process bytes"):
                read_attempt(root)
            (root / "stdout.gz").write_bytes(compressed)
            (root / "stderr.txt").write_bytes(b"failure")
            with self.assertRaisesRegex(ValueError, "raw process bytes"):
                read_attempt(root)


class EvidenceRestoreTests(unittest.TestCase):
    def fixture(self, root, name="objects/data", *, wrong_member_hash=False):
        assets = root / "assets"
        assets.mkdir()
        raw = b"retained observation"
        digest = hashlib.sha256(raw).hexdigest()
        if name == "objects/data":
            name = "objects/" + digest
        with tarfile.open(assets / "states.tar.xz", "w:xz") as archive:
            info = tarfile.TarInfo(name)
            info.size = len(raw)
            archive.addfile(info, io.BytesIO(raw))
        metadata = {"states.tar.xz": {name: {"bytes": len(raw), "sha256": "0" * 64 if wrong_member_hash else digest}}}
        (assets / "archive-members.json").write_text(json.dumps(metadata))
        (assets / "blob-index.json").write_text(json.dumps({"runs/state.bin": {"sha256": digest, "bytes": len(raw)}}))
        (assets / "file-sha256.json").write_text(json.dumps({name: hashlib.sha256((assets / name).read_bytes()).hexdigest()
                                                             for name in ("states.tar.xz", "blob-index.json", "archive-members.json")}))
        return assets, raw

    def test_restore_reconstructs_state_and_refuses_existing_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            assets, raw = self.fixture(root)
            destination = root / "restored"
            restore_evidence(assets, destination)
            self.assertEqual((destination / "runs/state.bin").read_bytes(), raw)
            with self.assertRaises(FileExistsError):
                restore_evidence(assets, destination)
            self.assertEqual((destination / "runs/state.bin").read_bytes(), raw)

    def test_archive_cannot_escape_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            assets, _ = self.fixture(root, "../outside")
            with self.assertRaisesRegex(ValueError, "unsafe"):
                restore_evidence(assets, root / "restored")
            self.assertFalse((root / "outside").exists())

    def test_changed_member_bytes_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            assets, _ = self.fixture(root, wrong_member_hash=True)
            with self.assertRaisesRegex(ValueError, "member bytes"):
                restore_evidence(assets, root / "restored")
