"""The production campaign must preserve settings and reject changed source."""
import hashlib
import json
from pathlib import Path
import tempfile
import tomllib
import unittest

from tools.performance.cache_pipeline import diagnostic_bits, identities, settings_toml


class CachePipelineEvidenceTests(unittest.TestCase):
    def test_diagnostic_float_spellings_match_exactly_at_the_declared_precision(self):
        value = {"completed_steps": "1", "maximum_speed_m_s": 0.04087500274181366,
                 "cfl_limit": {"kind": "finite", "seconds": 0.48929664492607117}, "warning": False}
        shortest = value | {"maximum_speed_m_s": 0.040875003,
                            "cfl_limit": {"kind": "finite", "seconds": 0.48929664}}
        self.assertEqual(diagnostic_bits(value), diagnostic_bits(shortest))
        value["maximum_speed_m_s"] = 1.0
        changed = value | {"maximum_speed_m_s": 1.0000001192092896}
        self.assertNotEqual(diagnostic_bits(value), diagnostic_bits(changed))

    def test_fixed_view_fixture_retains_explicit_camera_and_colour(self):
        settings = {"width": 1280, "height": 720, "format": "png", "step_stride": 4,
                    "camera": {"eye_m": [1.0, 2.0, 3.0], "target_m": [0.0, 0.5, 0.0], "near_m": 0.001},
                    "particles": {"colour_mode": "fixed", "colour": "#238be0"}}
        emitted = tomllib.loads(settings_toml(settings))
        self.assertEqual(emitted, settings | {"schema_version": 2, "camera_mode": "fixed"})

    def test_changed_source_fails_before_a_binary_can_be_admitted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "baseline").mkdir()
            source = root / "baseline/Cargo.toml"
            source.write_bytes(b"changed")
            (root / "baseline-source.json").write_text(json.dumps({
                "files": {"Cargo.toml": hashlib.sha256(b"original").hexdigest()}}))
            with self.assertRaisesRegex(ValueError, "changed frozen source"):
                identities(root)


if __name__ == "__main__":
    unittest.main()
