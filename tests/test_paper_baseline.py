"""Diagnostic replay must carry active effects and omitted unit corrections."""
import copy
import struct
import unittest

from tools.performance.paper_baseline_replay import encode_resolved, LAYOUT


class RecordedSettings(unittest.TestCase):
    def document(self):
        return {"input": {"configuration": {
            "numerical": {"fixed_timestep_s": 1/240, "artificial_pressure_enabled": True,
                          "artificial_pressure_exponent": 4, "external_acceleration_m_s2": dict(x=0,y=-9.81,z=0),
                          "xsph_viscosity_enabled": True, "xsph_viscosity_coefficient": .03,
                          "vorticity_confinement_enabled": False},
            "derived": {"support_radius_m": .1, "artificial_pressure_reference_separation_m": .02,
                        "normalised_rest_density_per_m3": 8000, "relaxation_per_m2": 2000,
                        "artificial_pressure_strength_m2": .001, "particle_mass_kg": .125}},
            "planes": [], "particles": [{"position_m": dict(x=1,y=2,z=3), "velocity_m_s": dict(x=4,y=5,z=6)}]}}

    def test_omitted_unit_correction_and_enabled_xsph_survive_without_mutation(self):
        document = self.document()
        before = copy.deepcopy(document)
        raw = encode_resolved(document)
        settings = LAYOUT.unpack(raw[:LAYOUT.size])
        self.assertEqual(document, before)
        self.assertEqual(settings[11], 1.0)
        self.assertAlmostEqual(settings[-2], .03, places=8)
        self.assertEqual(settings[-1], 0)
        self.assertEqual(struct.unpack('<6f', raw[96:]), (1,2,3,4,5,6))

    def test_inactive_effects_carry_zero_and_optional_confinement_carries_strength(self):
        document = self.document()
        model = document['input']['configuration']['numerical']
        model.update(xsph_viscosity_enabled=False, vorticity_confinement_enabled=True,
                     vorticity_confinement_strength_m_s=.2, correction_scale=.25)
        settings = LAYOUT.unpack(encode_resolved(document)[:LAYOUT.size])
        self.assertEqual(settings[11], .25)
        self.assertEqual(settings[-2], 0)
        self.assertAlmostEqual(settings[-1], .2, places=7)
