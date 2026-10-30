"""Independent fixtures for the frontier's physical measurements and controls."""
import json
import math
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from tools.performance.frontier_inputs import policies
from tools.performance.frontier_residency import prepare
from tools.performance.frontier_dfsph_audit import generate
from tools.performance.frontier_retain import seal, verify


class Controls(unittest.TestCase):
    def test_independent_axes_and_fixed_anchor(self):
        rows=policies();anchor=rows[1]
        self.assertEqual(len(rows),18)
        for row in rows[2:14]:
            self.assertEqual(sum(row[k]!=anchor[k] for k in ['dt','iterations','scale','epsilon']),1)
        self.assertEqual(rows[0]['dt'],1/480)
        self.assertEqual(rows[0]['scale'],.0625)

    def test_overlay_refuses_a_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'residency-source';root.mkdir();(root/'.git').mkdir()
            with self.assertRaisesRegex(ValueError,'isolated'):prepare(root)

    def test_raw_seal_detects_modified_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'raw';root.mkdir();(root/'failed.stderr').write_bytes(b'rejected attempt\n');(root/'state.bin').write_bytes(bytes(range(256)))
            target=Path(tmp)/'seal';seal(root,target)
            self.assertEqual(verify(target)['files'],2)
            archive=next(target.glob('observations-*.tar.gz'));raw=archive.read_bytes();archive.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
            with self.assertRaisesRegex(ValueError,'archive bytes differ'):verify(target)


class IndependentAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.root=Path(cls.tmp.name);cls.binary=cls.root/'quality'
        subprocess.run(['c++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(Path(__file__).resolve().parents[2]/'tools/performance/frontier_quality.cpp'),'-o',str(cls.binary)],check=True)
        generate(cls.root/'cubic.cpp')
        subprocess.run(['c++','-std=c++17','-O2',str(cls.root/'cubic.cpp'),'-o',str(cls.root/'cubic')],check=True)

    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def read(self,p,v=None,initial=None,trailer=b''):
        v=v or [(0,0,0)]*len(p);path=self.root/'state.bin';reference=self.root/'initial.bin'
        raw=lambda points:b''.join(struct.pack('<3f',*a) for a in points)
        path.write_bytes(raw(p)+raw(v)+trailer);reference.write_bytes(raw(p)+raw(v) if initial is None else raw(initial[0])+raw(initial[1]))
        return subprocess.run([str(self.binary),str(path),str(len(p)),'1','1','1000','-10','.5','4,4,4',str(reference),'.125'],text=True,capture_output=True)

    def test_self_support_density_and_energy_reference(self):
        r=self.read([(1,1,1),(1.5,1,1)],[(1,0,0),(-1,0,0)]);self.assertEqual(r.returncode,0,r.stderr);d=json.loads(r.stdout)
        expected=315/(64*math.pi)*(1+.75**3)
        self.assertAlmostEqual(d['mean_density_ratio'],expected,places=12)
        self.assertAlmostEqual(d['kinetic_J_kg'],.5)
        self.assertAlmostEqual(d['potential_J_kg'],10)
        self.assertEqual(d['mechanical_excess_relative'],0)
        self.assertEqual(d['shear_projection'],1)
        self.assertAlmostEqual(d['occupied_support_volume'],.25)

    def test_clipping_and_coincidences(self):
        d=json.loads(self.read([(0,1,1),(0,1,1)]).stdout)
        self.assertEqual(d['coincidences'],2)
        self.assertEqual(d['occupied_support_volume'],.0625)

    def test_energy_injection_visible(self):
        d=json.loads(self.read([(1,1,1)],[(2,0,0)],initial=([(1,1,1)],[(1,0,0)])).stdout)
        self.assertAlmostEqual(d['mechanical_excess_relative'],1.5/10.5)
        self.assertEqual(d['shear_projection'],2)

    def test_corrupt_and_nonfinite_state_rejected(self):
        self.assertNotEqual(self.read([(1,1,1)],trailer=b'x').returncode,0)
        self.assertNotEqual(self.read([(math.nan,1,1)]).returncode,0)

    def test_cubic_boundary_volume_is_independently_weighted(self):
        self.read([(1,1,1)])
        wall=self.root/'wall.bin';wall.write_bytes(struct.pack('<I4f',1,1.5,1,1,.5))
        command=[str(self.root/'cubic'),str(self.root/'state.bin'),'1','1','1','1000','-10','.5','4,4,4',str(self.root/'initial.bin'),'.125',str(wall)]
        process=subprocess.run(command,capture_output=True,text=True,check=True)
        self.assertAlmostEqual(json.loads(process.stdout)['mean_density_ratio'],9/math.pi,places=12)
