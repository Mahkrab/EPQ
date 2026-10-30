"""Analytic gradients, wall support and conservation guard the isolated solver."""
import json
import math
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

from tools.performance.convergence_campaign import digest, pin_binary
from tools.performance.convergence_assessment import assess


class ConvergenceReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        source = Path(__file__).resolve().parents[2] / "tools/performance"
        for name in ("solver", "audit"):
            subprocess.run(["c++", "-std=c++17", "-O2", "-ffp-contract=off",
                            str(source/f"convergence_{name}.cpp"), "-o", str(cls.root/name)], check=True)
        probe = cls.root / "probe.cpp"
        probe.write_text('#define main experiment_main\n#include "'+str(source/"convergence_solver.cpp")+'"\n#undef main\n'
                         'int main(int argc,char **argv){if(argc>1)model_kernel=std::stoi(argv[1]);'
                         'auto g=gradient({.031,.017,-.019},true);std::cout.precision(17);'
                         'for(auto x:g)std::cout<<x<<" ";std::cout<<rest_density();}\n')
        subprocess.run(["c++", "-std=c++17", "-O2", str(probe), "-o", str(cls.root/"probe")], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def generate(self, name, duration="0"):
        process = subprocess.run([str(self.root/"solver"), name, str(1/240), duration,
                                  "8", "1", "1", ".02", ".5", "0", "1", "1"], capture_output=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        return process.stdout

    def test_poly6_gradient_matches_independent_central_difference(self):
        values = list(map(float,subprocess.check_output([str(self.root/"probe")],text=True).split()))
        p = [.031,.017,-.019]
        def weight(q):
            return 315/(64*math.pi*.1**9)*max(0.,.1**2-sum(x*x for x in q))**3
        for k in range(3):
            a,b=p.copy(),p.copy()
            a[k]+=1e-7
            b[k]-=1e-7
            numerical = (weight(a)-weight(b))/2e-7
            self.assertAlmostEqual(values[k]/numerical,1,places=8)
        self.assertAlmostEqual(values[3],8078.201335157481,places=9)

    def test_corner_wall_support_fills_lattice_without_filling_free_surface(self):
        data = self.generate("hydro")
        magic,n,w,steps=struct.unpack_from("<4I",data)
        self.assertEqual((magic,n,steps),(0x50424632,512,0))
        constants = struct.unpack_from("<7d",data,16)
        walls = list(struct.iter_unpack("<3d",data[72:72+w*24]))
        offset = 72+w*24+4
        particles = list(struct.iter_unpack("<3d",data[offset:offset+n*24]))
        self.assertEqual(len(walls),len(set(walls)))
        def density(p):
            return sum(315/(64*math.pi*.1**9)*max(0.,.01-sum((a-b)**2 for a,b in zip(p,q)))**3
                       for q in walls+particles)/constants[2]
        self.assertAlmostEqual(density(particles[0]),1.,places=12)
        self.assertLess(density((.175,.375,.175)),.9)

    def test_wendland_gradient_normalisation_and_lattice_calibration(self):
        values=list(map(float,subprocess.check_output([str(self.root/"probe"),"2"],text=True).split()))
        p=[.031,.017,-.019]
        def weight(q):
            r=math.sqrt(sum(x*x for x in q))/.1
            return 21/(2*math.pi*.1**3)*max(0.,1-r)**4*(1+4*r)
        for k in range(3):
            a,b=p.copy(),p.copy()
            a[k]+=1e-7
            b[k]-=1e-7
            self.assertAlmostEqual(values[k]/((weight(a)-weight(b))/2e-7),1,places=8)
        # Midpoint radial quadrature is independent of the implementation's
        # discrete lattice calibration and checks the 3D normalising constant.
        dr=.1/10000
        integral=sum(4*math.pi*((i+.5)*dr)**2*weight(((i+.5)*dr,0,0))*dr for i in range(10000))
        self.assertAlmostEqual(integral,1,places=8)
        self.assertAlmostEqual(values[3],8270.744069418484,places=9)

    def test_ballistic_centre_follows_semi_implicit_euler_and_internal_momentum_cancels(self):
        data=self.generate("ballistic",".05")
        raw=self.root/"ballistic.bin"
        raw.write_bytes(data)
        report=subprocess.run([str(self.root/"audit"),str(raw),"1"],capture_output=True,text=True,check=True)
        first,last=[json.loads(line) for line in report.stdout.splitlines()]
        dt=1/240
        expected_displacement=-9.81*dt*dt*12*13/2
        self.assertAlmostEqual(last["centre"][1]-first["centre"][1],expected_displacement,places=10)
        for k in (0,2):
            self.assertAlmostEqual(first["centre"][k],last["centre"][k],places=10)
            self.assertAlmostEqual(last["mean_velocity"][k],0,places=10)

    def test_auditor_rejects_truncated_state(self):
        raw=self.root/"truncated.bin"
        raw.write_bytes(self.generate("hydro")[:-1])
        report=subprocess.run([str(self.root/"audit"),str(raw),"1"],capture_output=True,text=True)
        self.assertNotEqual(report.returncode,0)
        self.assertIn("truncated",report.stderr)

    def test_parallel_requests_pin_one_complete_binary(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/"binary"
            source.write_bytes(bytes(range(256))*8192)
            with ThreadPoolExecutor(max_workers=8) as pool:
                results=list(pool.map(lambda _:pin_binary(source),range(16)))
            self.assertEqual(len(set(results)),1)
            self.assertEqual(digest(results[0]),digest(source))

    def test_invalid_kernel_is_rejected_before_observations(self):
        report=subprocess.run([str(self.root/"solver"),"hydro",".01","0","8","1","1",
                               ".02",".5","0","3","1"],capture_output=True)
        self.assertNotEqual(report.returncode,0)
        self.assertEqual(report.stdout,b"")


class PhysicalAdmissionTests(unittest.TestCase):
    def test_density_pass_cannot_admit_wrong_settled_volume(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            protocol={"criteria":{"all_checkpoints":{"p95_positive_density_error_max":.05,
                "max_positive_density_error_max":.25,"minimum_separation_m":.025,
                "boundary_violation_m_max":1e-6,"mechanical_energy_increase_J_kg_max":.004905},
                "hydrostatic":{"centroid_relative_error_max":.05,
                "p95_height_plus_half_spacing_relative_error_max":.1,
                "settled_kinetic_J_kg_max":.00125,"bulk_absolute_density_error_p95_max":.05},
                "convergence":{}}}
            (root/"protocol.json").write_text(json.dumps(protocol))
            case=root/"runs"/"wrong-volume"
            case.mkdir(parents=True)
            (case/"summary.json").write_text(json.dumps({"exit_code":0}))
            record={"p95_compression":0,"max_compression":0,"minimum_separation_m":.04,
                    "boundary_violation_m":0,"mechanical_J_kg":1,"kinetic_J_kg":0,
                    "centroid_relative_error":.2,"surface_relative_error":.2,
                    "expected_depth_m":.4,"bulk_count":8,"bulk_p95_absolute_error":0,
                    "centre":[0,.16,0],"surface_height_m":.32}
            (case/"audit.jsonl").write_text("\n".join(json.dumps(record|{"time_s":t}) for t in (0,5,6)))
            outcome=assess(root)["cases"]["wrong-volume"]
            self.assertTrue(outcome["checks"]["compression_p95"])
            self.assertTrue(outcome["checks"]["separation"])
            self.assertFalse(outcome["numerically_admitted"])


if __name__ == "__main__":
    unittest.main()
