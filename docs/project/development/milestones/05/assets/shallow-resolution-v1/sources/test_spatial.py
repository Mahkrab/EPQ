"""Spatial experiments must preserve mass and geometry independently of solver work."""
import math
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import numpy as np
from scipy.spatial import cKDTree

from tools.performance.spatial_audit import density, fraction, frames, vertical_measure
from tools.performance.spatial_retain import verify


class SpatialReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary=tempfile.TemporaryDirectory()
        cls.root=Path(cls.temporary.name)
        source=Path(__file__).resolve().parents[2]/"tools/performance/spatial_solver.cpp"
        cls.binary=cls.root/"solver"
        subprocess.run(["c++","-std=c++17","-O2","-fopenmp","-ffp-contract=off",str(source),"-o",str(cls.binary)],check=True)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def generate(self,n,scene="collision",duration="0",threads=1,layers=1):
        data=subprocess.check_output([str(self.binary),scene,str(n),str(layers),str(1/240*(6/n)),duration,"8","1",".5",str(threads)],stderr=subprocess.DEVNULL)
        path=self.root/f"{self.id().rsplit('.',1)[-1]}-{scene}-{n}-{threads}.bin"
        path.write_bytes(data)
        return data,list(frames(path))

    def test_refinement_preserves_geometry_mass_and_consistent_scales(self):
        for n in (6,12):
            _,observations=self.generate(n)
            meta,wall,_,p,v=observations[0]
            self.assertEqual(len(p),2*n**3)
            self.assertAlmostEqual(meta["mass"]*len(p),52.23230175835605,places=11)
            self.assertEqual(meta["upper"],[1.2,1.2,.8])
            np.testing.assert_allclose(p[:n**3].mean(axis=0),[.25,.525,.35],atol=1e-13)
            np.testing.assert_allclose(p[n**3:].mean(axis=0),[.95,.525,.35],atol=1e-13)
            self.assertAlmostEqual(meta["h"]/meta["dx"],2)
            self.assertAlmostEqual(meta["inset"]/meta["dx"],.5)
            self.assertAlmostEqual(meta["contact"]/meta["dx"],.51)
            self.assertTrue(np.all((wall<0).any(axis=1) | (wall>np.array(meta["upper"])).any(axis=1)))

    def test_flattening_preserves_mass_and_initial_geometric_volume(self):
        for n in (6,12):
            _,observations=self.generate(n,"flat")
            meta,_,_,p,_=observations[0]
            self.assertEqual(len(p),2*n**3)
            self.assertAlmostEqual(p[:,1].mean(),.05625/2,places=14)
            self.assertAlmostEqual(meta["mass"]*len(p),52.23230175835605,places=11)

    def test_thread_count_cannot_change_jacobi_observations(self):
        a,_=self.generate(6,duration=".05",threads=1)
        b,_=self.generate(6,duration=".05",threads=2)
        self.assertEqual(a,b)

    def test_readback_rejects_wrong_schedule_with_valid_count_and_endpoint(self):
        raw,observations=self.generate(6,duration=".1")
        meta,wall,_,_,_=observations[0]
        altered=bytearray(raw)
        frame_bytes=4+meta["count"]*48
        second_step=104+len(wall)*24+frame_bytes
        altered[second_step:second_step+4]=(observations[1][2]+1).to_bytes(4,"little")
        root=self.root/"wrong-schedule"
        directory=root/"runs"/"case";directory.mkdir(parents=True)
        compressed=gzip.compress(altered,mtime=0)
        (directory/"states.bin.gz").write_bytes(compressed)
        (directory/"request.json").write_text(json.dumps({"parameters":{"scene":"collision"}}))
        (directory/"collection.json").write_text(json.dumps({"exit_code":0,
            "raw_sha256":hashlib.sha256(altered).hexdigest(),
            "gzip_sha256":hashlib.sha256(compressed).hexdigest(),"raw_bytes":len(altered)}))
        with self.assertRaisesRegex(ValueError,"observation steps differ from schedule"):
            verify(root)

    def test_initial_collision_follows_ballistic_centre_of_mass(self):
        _,observations=self.generate(6,duration=".05",threads=2)
        first,last=observations[0],observations[-1]
        dt=first[0]["dt"];steps=last[2]
        expected=-9.81*dt*dt*steps*(steps+1)/2
        self.assertAlmostEqual(last[3][:,1].mean()-first[3][:,1].mean(),expected,places=12)
        self.assertAlmostEqual(last[3][:,0].mean(),first[3][:,0].mean(),places=12)

    def test_off_grid_depth_keeps_equal_particle_volumes(self):
        _,a=self.generate(12,"depth",layers=1)
        _,b=self.generate(12,"depth",layers=1.25)
        first,second=a[0],b[0]
        self.assertEqual(second[0]["count"],first[0]["count"]*1.25)
        self.assertEqual(second[0]["mass"],first[0]["mass"])
        self.assertAlmostEqual(second[3][:,1].mean(),1.25*.025/2,places=14)

    def test_fitted_flat_sampler_respects_extent_without_shifting_mass_centre(self):
        _,old=self.generate(12,"flat")
        _,new=self.generate(12,"flat-valid")
        meta,_,_,p,_=new[0]
        self.assertLess(old[0][3][:,2].min(),meta["inset"])
        self.assertGreaterEqual(p.min(),meta["inset"]-1e-12)
        np.testing.assert_allclose(p.mean(axis=0),old[0][3].mean(axis=0),atol=1e-13)
        self.assertEqual(len(p),len(old[0][3]))

    def test_unrepresentable_aligned_strata_are_rejected_before_stepping(self):
        report=subprocess.run([str(self.binary),"depth-ceil-valid","12","1.25",str(1/480),"6","8","1",".5","1"],capture_output=True)
        self.assertNotEqual(report.returncode,0)
        self.assertIn(b"initial separation",report.stderr)
        path=self.root/"rejected.bin";path.write_bytes(report.stdout)
        initial=list(frames(path))
        self.assertEqual(len(initial),1)
        self.assertEqual(initial[0][2],0)

    def test_lattice_point_density_is_distinct_from_geometric_mass_density(self):
        _,observations=self.generate(12)
        meta,_,_,p,_=observations[0]
        probe=p[(6*12+6)*12+6:][:1]
        value=density(cKDTree(p),probe,meta["h"],meta["mass"])[0]
        self.assertAlmostEqual(value,1000,places=10)
        actual_bulk=meta["count"]*meta["mass"]/.054
        self.assertAlmostEqual(actual_bulk,967.2648473769639,places=9)
        self.assertLess(actual_bulk,1000)

    def test_kd_density_includes_self_and_current_support(self):
        points=np.array([[0.,0,0],[.5,0,0]])
        actual=density(cKDTree(points),points,1.,1.)
        expected=21/(2*math.pi)*(1+.5**4*3)
        np.testing.assert_allclose(actual,[expected,expected],rtol=1e-14)

    def test_boundary_quadrature_has_correct_full_and_corner_volume(self):
        total=fraction(1.,-1.,1.,1.,order=48)
        self.assertAlmostEqual(total,1,places=6)
        corner=fraction(0.,0.,1.,0.,order=48)
        self.assertAlmostEqual(corner,.125,places=6)

    def test_reconstructed_thickness_counts_detached_segments(self):
        values=np.array([[0.,1.,1.,0.],[1.,1.,0.,0.]])
        thickness,top=vertical_measure(values,np.array([0.,1.,2.,3.]),.5)
        np.testing.assert_allclose(thickness,[2.,1.5])
        np.testing.assert_allclose(top,[2.5,1.5])


if __name__=="__main__":
    unittest.main()
