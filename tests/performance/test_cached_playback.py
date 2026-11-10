"""Submission cadence and source time must remain distinct in retained reports."""
import json
from pathlib import Path
import tempfile
import unittest

from tools.performance.cached_playback import assess, read_trace
from tools.performance.cached_identity import check


class CachedPlaybackEvidenceTests(unittest.TestCase):
    def test_successful_build_with_another_exports_binary_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            source=root/"control"
            source.mkdir()
            for name in ["src","native","build_support","scenes","config"]:
                (source/name).mkdir()
            for name in ["Cargo.toml","Cargo.lock","build.rs"]:
                (source/name).write_text("synthetic current source")
            (root/"control-maelstrom").write_bytes(b"sha256:stale-source-from-another-export")
            with self.assertRaisesRegex(ValueError,"does not embed its expected source identity"):
                check(root,"control")

    def test_live_partial_record_is_deferred_but_complete_corruption_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"viewer.log"
            path.write_text('driver information\ncache-trace {"event":"present","wall_s":1}\ncache-trace {"event":')
            self.assertEqual(read_trace(path), [{"event":"present","wall_s":1}])
            path.write_text('cache-trace {"event":\n')
            with self.assertRaises(json.JSONDecodeError):
                read_trace(path)

    def test_loop_progress_and_repeated_submissions_do_not_become_solver_fps(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            events=[]
            for wall,index,simulation in [(1.,9,.9),(1.1,9,.9),(1.2,0,0.),(1.3,1,.1)]:
                events.append(dict(event="present",wall_s=wall,index=index,simulation_s=simulation,
                                   prepare_s=.001,upload_s=.002,submit_s=.003))
                events.append(dict(event="read",timings=dict(reading_s=.004)))
                events.append(dict(event="loaded",seconds=.005))
            (root/"viewer.log").write_text("".join("cache-trace "+json.dumps(e)+"\n" for e in events))
            (root/"protocol.json").write_text(json.dumps(dict(measure_start_s=1.,measure_end_s=1.3,terminal_s=1.,close_s=.02)))
            (root/"samples.json").write_text(json.dumps([
                dict(wall_s=0.,cpu_s=2.,peak_rss_kib=4096,rss_kib=3072),
                dict(wall_s=.3,cpu_s=2.15,peak_rss_kib=4096,rss_kib=3072)]))
            result=assess(root)
            self.assertAlmostEqual(result["submissions_per_s"],10.)
            self.assertAlmostEqual(result["timeline_simulation_s_per_wall_s"],2/3)
            self.assertAlmostEqual(result["new_states_presented_per_s"],20/3)
            self.assertAlmostEqual(result["cpu_core_equivalents"],.5)
            self.assertEqual(result["peak_rss_mib"],4.)
            self.assertEqual(result["rss_last_mib"],3.)


if __name__=="__main__":
    unittest.main()
