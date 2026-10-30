"""Independent fixtures for DFSPH evidence and solid-volume quadrature."""
import json
import math
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from tools.performance.dfsph_audit import load_trace
from tools.performance.dfsph_campaign import invoke
from tools.performance.dfsph_quality import wendland, unbounded


class Evidence(unittest.TestCase):
    def test_truncated_failure_trace_is_explicit_and_raw_unchanged(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'trace';raw='{"step":1}\n{"step":2,"energy":';path.write_text(raw)
            rows,errors=load_trace(path)
            self.assertEqual(rows,[{'step':1}]);self.assertEqual(errors[0]['line'],2);self.assertEqual(path.read_text(),raw)

    def test_nonfinite_trace_does_not_become_a_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            p=Path(temporary)/'trace';p.write_text('{"energy":NaN}\n')
            rows,errors=load_trace(p);self.assertEqual(rows,[]);self.assertEqual(len(errors),1)

    def test_failed_subprocess_and_repeated_output_are_retained(self):
        with tempfile.TemporaryDirectory() as temporary:
            p=Path(temporary)/'failed';command=[sys.executable,'-c','import sys; print("rejected",file=sys.stderr); sys.exit(7)']
            row=invoke(command,p);self.assertEqual(row['exit_code'],7);self.assertEqual((p/'stderr.txt').read_text(),'rejected\n');self.assertEqual(json.loads((p/'process.json').read_text())['command'],command)
            with self.assertRaises(FileExistsError):invoke(command,p)


class Quadrature(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.root=Path(cls.tmp.name);wendland(cls.root/'reader.cpp')
        subprocess.run(['c++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(cls.root/'reader.cpp'),'-o',str(cls.root/'reader')],check=True)
        unbounded(cls.root/'unbounded.cpp','wendland')
        subprocess.run(['c++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(cls.root/'unbounded.cpp'),'-o',str(cls.root/'unbounded')],check=True)

    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def read(self,points,wall):
        raw=b''.join(struct.pack('<3f',*p) for p in points)+bytes(len(points)*12);(self.root/'state').write_bytes(raw)
        (self.root/'wall').write_bytes(struct.pack('<I',len(wall))+b''.join(struct.pack('<4f',*p) for p in wall))
        command=[str(self.root/'reader'),str(self.root/'state'),str(len(points)),'1','1','1000','0','.5','4,4,4',str(self.root/'state'),'.125',str(self.root/'wall')]
        return json.loads(subprocess.check_output(command))

    def test_wendland_self_and_boundary_volume_have_independent_weights(self):
        value=self.read([(1,1,1)],[(1.5,1,1,.5)])
        self.assertAlmostEqual(value['mean_density_ratio'],21/(2*math.pi)*(1+.5*3/16),places=12)

    def test_support_is_strict_and_self_is_present(self):
        value=self.read([(1,1,1)],[(2,1,1,1)])
        self.assertAlmostEqual(value['mean_density_ratio'],21/(2*math.pi),places=12)

    def test_unbounded_volume_does_not_clip_a_translated_cube(self):
        self.read([(-1,1,1)],[])
        command=[str(self.root/'unbounded'),str(self.root/'state'),'1','1','1','1000','0','.5','4,4,4',str(self.root/'state'),'.125',str(self.root/'wall')]
        value=json.loads(subprocess.check_output(command))
        self.assertEqual(value['occupied_support_volume'],.125)
        self.assertEqual(value['boundary_violation'],1)

    def test_exploded_coordinates_do_not_enter_integer_volume_search(self):
        self.read([(1,1,1)],[])
        (self.root/'state').write_bytes(struct.pack('<6f',1e20,1,1,0,0,0))
        command=[str(self.root/'unbounded'),str(self.root/'state'),'1','1','1','1000','0','.5','4,4,4',str(self.root/'state'),'.125',str(self.root/'wall')]
        process=subprocess.run(command,capture_output=True,text=True)
        self.assertEqual(process.returncode,1)
        self.assertIn('representable volume domain',process.stderr)

    def test_filled_solid_continuation_matches_bulk_lattice(self):
        dx=.05;h=.1
        def weight(x,y,z):
            q=math.sqrt(x*x+y*y+z*z)/h
            return 0 if q>=1 else 8/(math.pi*h**3)*(6*q**3-6*q*q+1 if q<=.5 else 2*(1-q)**3)
        fluid=sum(dx**3*weight(i*dx,j*dx,k*dx) for i in range(-2,3) for j in range(0,3) for k in range(-2,3))
        solid=sum(dx**3*weight(i*dx,j*dx,k*dx) for i in range(-2,3) for j in range(-2,0) for k in range(-2,3))
        self.assertAlmostEqual(fluid+solid,.999972466091043,places=13)
        self.assertGreater(fluid,0);self.assertGreater(solid,0)
