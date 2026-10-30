"""Analytic fixtures check the independent oracle and parameter isolation."""
import math
import struct
import unittest

from tools.performance.physical_accuracy import LAYOUT, encode, lattice_rest
from tools.performance.physical_reference import stage


class PhysicalReferenceTests(unittest.TestCase):
    def test_lattice_mass_matches_independent_published_project_anchor(self):
        rest = lattice_rest(.05, .1)
        self.assertAlmostEqual(rest, 8078.201335157481, places=9)
        self.assertAlmostEqual(1000/rest, .123789932748, places=12)
        self.assertAlmostEqual(lattice_rest(.1, .2), rest/8, places=10)

    def test_single_particle_has_self_density_and_no_direction(self):
        points = [(0., 0., 0.)]
        result, metrics = stage(points, 1., 315/(64*math.pi), 20., .001, .5)
        self.assertEqual(result, points)
        self.assertEqual(metrics["mean_squared_constraint"], 0.)
        self.assertEqual(metrics["gradient_denominator_max"], 0.)

    def test_pair_correction_preserves_centre_and_rejects_outside_support(self):
        points = [(-.025, 0., 0.), (.025, 0., 0.)]
        result, _ = stage(points, .1, lattice_rest(.05,.1), 2000., 0., .0625)
        self.assertAlmostEqual(result[0][0]+result[1][0], 0., places=15)
        self.assertGreater(result[0][0], points[0][0])  # Signed under-density attracts.
        separate = [(0.,0.,0.), (.1,0.,0.)]
        self.assertEqual(stage(separate,.1,8000.,2000.,.001,1.)[0], separate)

    def test_timestep_and_scale_are_independent_and_baseline_bytes_survive(self):
        values = [2,2,0,0,1/480,.1,8078.19921875,1999.9998779296875,
                  .001,1386.0992431640625,4.,.0625,1000/8078.19921875,0.,-9.81,0.,
                  .125,0,0,0,0.,0.]
        source = LAYOUT.pack(*values)+bytes(48)
        self.assertEqual(encode(source,dt=values[4],scale=.0625),source)
        changed = LAYOUT.unpack_from(encode(source,dt=1/960,scale=.0625))
        original = LAYOUT.unpack_from(source)
        self.assertEqual(changed[5:],original[5:])
        self.assertEqual(changed[:4],original[:4])


if __name__ == "__main__":
    unittest.main()
