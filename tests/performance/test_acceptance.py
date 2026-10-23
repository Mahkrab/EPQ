"""A partial probe or a selected sample cannot justify an acceptance optimisation."""

import unittest

from tools.performance.acceptance import COMPONENTS, diagnostic_summary, historical_screen, probes, screen
from tools.performance.acceptance_codegen import inspect
from tests.performance.audit_acceptance import validate_confirmation, validate_screen


class AcceptanceTests(unittest.TestCase):
    def test_component_summary_does_not_apply_an_opportunity_cutoff(self):
        sample = {"solver_s": 10, "components_s": {k: 0.01 for k in COMPONENTS}}
        result = diagnostic_summary([sample] * 3)
        self.assertTrue(result["assessment_required"])
        self.assertNotIn("plane_candidate_admitted", result)

    def test_probe_pairs_keep_components_and_step_order(self):
        rows = probes("notice\nACCEPT_CUDA,8,0.01,0.02,0.03,0.04\nACCEPT_HOST,1,0.05,0.06,0.07\n", 8, 1)
        self.assertEqual(rows, [{"velocity_reconstruction": 0.01, "position_download": 0.02,
            "velocity_download": 0.03, "particle_reconstruction": 0.04, "particle_validation": 0.05,
            "plane_validation": 0.06, "commit": 0.07}])

    def test_truncated_wrong_particle_duplicate_and_reordered_probes_fail(self):
        cuda = "ACCEPT_CUDA,8,1,2,3,4\n"
        host = "ACCEPT_HOST,1,5,6,7\n"
        for text in ("", cuda, host, cuda + cuda + host, cuda + host.replace(",1,", ",2,"),
                     cuda.replace(",8,", ",9,") + host, cuda + host + "ACCEPT_UNKNOWN,1\n"):
            with self.assertRaises(ValueError):
                probes(text, 8, 1)

    def test_negative_and_nonfinite_probe_values_are_not_measurements(self):
        for value in ("-1", "nan", "inf"):
            with self.assertRaises(ValueError):
                probes(f"ACCEPT_CUDA,8,{value},0,0,0\nACCEPT_HOST,1,0,0,0\n", 8, 1)

    def test_historical_screen_keeps_the_superseded_rule_reproducible(self):
        self.assertTrue(historical_screen([10, 10.1, 10.2], [9, 9.1, 9.2])["admitted"])
        self.assertFalse(historical_screen([10, 10.1, 10.2], [9, 9.1, 11])["admitted"])
        self.assertFalse(historical_screen([10] * 3, [9.9] * 3)["admitted"])
        for control, candidate in (([10] * 2, [9] * 3), ([True] * 3, [9] * 3), ([10] * 3, [float("inf")] * 3)):
            with self.assertRaises(ValueError):
                historical_screen(control, candidate)

    def test_screen_reports_overlap_without_deciding_continuation(self):
        result = screen([10, 20, 30], [9, 18, 27])
        self.assertTrue(result["assessment_required"])
        self.assertTrue(result["performance_evidence"]["ranges_overlap"])
        self.assertEqual(result["performance_evidence"]["faster_pairs"], 3)
        self.assertNotIn("admitted", result)

    def test_codegen_resolves_relative_and_direct_calls_without_counting_other_helpers(self):
        assembly = '''00001000 <maelstrom::boundary::Plane::contains>:
  1000: ret
00002000 <maelstrom::simulation::Simulation::step_inner>:
  2000: call *0x123(%rip) # 5000 <some_slot>
  2006: call 1000 <maelstrom::boundary::Plane::contains>
  200b: call 3000 <maelstrom::boundary::Plane::constraint>
'''
        result = inspect(assembly, "00005000 000008 R_X86_64_RELATIVE 1000")
        self.assertEqual(len(result["acceptance_contains_call_sites"]), 2)
        self.assertEqual(result["relative_slots_resolved"], 1)
        self.assertEqual(len(inspect(assembly, "")['acceptance_contains_call_sites']), 1)
        self.assertEqual(inspect("00002000 <maelstrom::simulation::Simulation::step_inner>:\n  2000: ret", "")['acceptance_contains_call_sites'], [])

    def test_independent_screen_reader_rejects_false_admission_and_filtered_values(self):
        values = {"control": [10, 10, 10], "candidate": [9, 9, 9]}
        good = {"control_s": [10, 10, 10], "candidate_s": [9, 9, 9], "solver_speedup": 10 / 9,
                "admitted": True, "primary_qualification": False}
        validate_screen(values, good)
        for change in ({"admitted": False}, {"candidate_s": [9, 9]}, {"solver_speedup": 2}):
            with self.assertRaises(ValueError):
                validate_screen(values, dict(good, **change))

    def test_confirmation_does_not_discard_an_outlier_or_accept_a_false_decision(self):
        values = {name: {"control": [10.] * 5, "candidate": [9.] * 5} for name in ("primary", "paired_large")}
        def summary():
            return {**{name: {variant: {"samples": [{"solver_s": v} for v in durations],
                "median_solver_s": durations[0], "minimum_s": min(durations), "maximum_s": max(durations),
                "standard_deviation_s": 0.} for variant, durations in sides.items()} for name, sides in values.items()},
                "decision": {"retained": True, "clear_gain": {"8000": True, "110592": True},
                             "both_median_regressions_at_most_three_percent": True}}
        good = summary()
        self.assertTrue(validate_confirmation(values, good)["retained"])
        good["decision"]["retained"] = False
        with self.assertRaisesRegex(ValueError, "false confirmation retention"):
            validate_confirmation(values, good)
        good = summary()
        values["primary"]["candidate"][-1] = 11.
        with self.assertRaisesRegex(ValueError, "samples differ"):
            validate_confirmation(values, good)


if __name__ == "__main__":
    unittest.main()
