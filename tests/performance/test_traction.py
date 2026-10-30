"""Analytical shear, rigid motion and wall invariants qualify isolated operators."""
import json
import os
from pathlib import Path
import subprocess
import struct
import tempfile
import unittest
import numpy as np
from tools.performance.traction_operator import evaluate, edge_matrix, gradient
from tools.performance.traction_audit import periodic_density, vertical_fraction, density_boundary
from tools.performance.traction_prefix import screen
from tools.performance.traction_jacobian import run as check_pressure_jacobian


class ContinuumOperatorTests(unittest.TestCase):
    def test_incomplete_prefix_is_retained_without_a_full_run_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'states.raw';p=np.array([[.05,.0125,.05],[.15,.0375,.15]])
            v=np.zeros_like(p);v[:,0]=.01*np.sin(np.pi*p[:,1]/.1)
            header=struct.pack('<4I11d',0x50424634,2,0,2,.001,.05,1000,1,.2,.1,.2,2,.025,.0125,.01275)
            raw=header+struct.pack('<I',0)+p.astype('<f8').tobytes()+v.astype('<f8').tobytes()+b'partial'
            path.write_bytes(raw);result=screen(path)
            self.assertEqual(result['complete_frames'],1);self.assertEqual(result['planned_steps'],2)
            self.assertEqual(result['unassessed_trailing_bytes'],7)
            self.assertLess(result['records'][0]['L2_velocity_error_over_initial_rms'],1e-14)
            self.assertNotIn('pass',result);self.assertEqual(path.read_bytes(),raw)

    def test_prefix_reader_rejects_truncated_header(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'states.raw';path.write_bytes(b'incomplete')
            with self.assertRaisesRegex(ValueError,'incomplete channel header'):screen(path)

    def test_boundary_identity_is_explicit_for_instrumented_and_unknown_sources(self):
        self.assertEqual(density_boundary({'command':['/synthetic/traction-pbf-axis']}),'mirrored')
        with self.assertRaisesRegex(ValueError,'explicitly'):
            density_boundary({'command':['/synthetic/unknown-mirror-name']} )

    def test_same_physical_horizontal_mode_is_accurate_at_two_layers(self):
        # The old omitted-neighbour pair operator missed this amplitude by 39%.
        for mode in ['horizontal-natural','horizontal-slip']:
            result=evaluate(2,mode,L=.6)
            self.assertLess(abs(result['amplitude_relative_error_at_tau']),.05)
            self.assertLess(abs(result['rate_relative_error']),.05)

    def test_vertical_modes_require_resolved_depth(self):
        for mode in ['vertical-slip','vertical-noslip']:
            coarse=evaluate(4,mode);fine=evaluate(8,mode)
            self.assertGreater(abs(coarse['amplitude_relative_error_at_tau']),.05)
            self.assertLess(abs(fine['amplitude_relative_error_at_tau']),.05)
            self.assertLess(fine['traction_relative_error_initial'],.05)

    def test_mixed_wall_traction_excludes_misleading_two_layer_pass(self):
        coarse=evaluate(2,'vertical-mixed');fine=evaluate(4,'vertical-mixed')
        self.assertLess(abs(coarse['amplitude_relative_error_at_tau']),.05)
        self.assertGreater(coarse['traction_relative_error_initial'],.05)
        self.assertLess(fine['traction_relative_error_initial'],.05)

    def test_edge_strain_removes_nodal_checkerboard_null_mode(self):
        count=4;initial=np.zeros(3*count);initial[::3]=(-1.)**np.arange(count)
        _,d,_=gradient(count,.05/count,2,0,0,'noslip','noslip')
        self.assertLess(np.linalg.norm(d@initial),1e-10)
        matrix,_=edge_matrix(count,.05/count,2,0,0,'noslip','noslip',.001)
        self.assertGreater(float((initial@matrix@initial/count).real),1.)
        self.assertGreater(np.linalg.eigvalsh(matrix)[0],0)

    def test_one_natural_layer_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'rank-deficient'):
            gradient(1,.05,2,0,1,'natural','natural')

    def test_periodic_tree_density_matches_brute_minimum_image(self):
        p=np.array([[.001,.01,.04],[.199,.02,.04],[.08,.03,.18]])
        queries=np.array([[0,.015,.04],[.1,.025,.199]])
        from tools.performance.spatial_audit import kernel
        d=queries[:,None,:]-p[None,:,:];d[:,:,[0,2]]-=np.rint(d[:,:,[0,2]]/.2)*.2
        expected=2*np.sum(kernel(np.linalg.norm(d,axis=2),.05),axis=1)
        np.testing.assert_allclose(periodic_density(p,queries,.05,2),expected,rtol=1e-14)

    def test_continuum_halfspace_has_half_kernel_mass_at_surface(self):
        self.assertAlmostEqual(vertical_fraction(0,0,.1,.02),.5,places=12)
        self.assertAlmostEqual(vertical_fraction(.05,0,.1,.02),1.,places=12)


class NativeOperatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary=tempfile.TemporaryDirectory();cls.root=Path(cls.temporary.name)
        cls.source=Path(__file__).resolve().parents[2]/'tools/performance'
        for source in ['traction_invariants','traction_pbf','traction_pbf_mirror']:
            subprocess.run(['c++','-std=c++17','-O2','-Wall','-Wextra','-Werror','-fopenmp','-ffp-contract=off',str(cls.source/(source+'.cpp')),'-o',str(cls.root/source)],check=True)
        subprocess.run(['c++','-std=c++17','-O2','-fopenmp','-ffp-contract=off','-DMAELSTROM_DUMP_PRESSURE_JACOBIAN',str(cls.source/'traction_pbf_mirror.cpp'),'-o',str(cls.root/'pressure-probe')],check=True)

    @classmethod
    def tearDownClass(cls):cls.temporary.cleanup()

    def invariant(self,profile,jitter):
        return json.loads(subprocess.check_output([str(self.root/'traction_invariants'),str(jitter),profile,str(self.root/(profile+str(jitter)+'.bin')),'1'],text=True,env={**os.environ,'OMP_WAIT_POLICY':'PASSIVE'}))

    def test_rigid_motion_is_not_arbitrarily_damped_on_disordered_cloud(self):
        for profile in ['translation','rotation']:
            result=self.invariant(profile,.08)
            self.assertLess(result['power'],1e-25)
            self.assertLess(result['maximum_acceleration'],1e-10)

    def test_affine_strain_uses_physical_constitutive_power(self):
        for jitter in [0,.08]:
            result=self.invariant('affine',jitter)
            self.assertAlmostEqual(result['power'],.00096,places=12)

    def test_actual_mirror_constraint_jacobian_matches_finite_differences(self):
        result=check_pressure_jacobian(self.root/'jacobian',self.root/'pressure-probe')
        self.assertLess(max(result['maximum_directional_derivative_errors_per_m']),1e-5)
        self.assertLess(result['maximum_tangential_gradient_sum_per_m'],1e-10)

    def test_adjoint_conserves_internal_impulses_and_removes_energy(self):
        result=self.invariant('nonlinear',.08)
        self.assertLess(max(map(abs,result['linear']+result['angular'])),1e-10)
        self.assertGreater(result['power'],0)
        self.assertAlmostEqual(result['power'],-result['work'],places=12)
        self.assertAlmostEqual(result['finite_difference'],result['adjoint_derivative'],places=8)

    def test_mirrored_pressure_removes_flat_bed_tangential_pressure_impulse(self):
        totals={}
        for solver in ['traction_pbf','traction_pbf_mirror']:
            ledger=self.root/(solver+'.ledger')
            command=[str(self.root/solver),'channel-mixed','4','.01',str(1/480),'.025','24','1','.5','1','self','1','.001','1','1','9.81',str(ledger),'-','1','2','2','geometric']
            subprocess.run(command,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,env={**os.environ,'OMP_WAIT_POLICY':'PASSIVE'})
            records=[json.loads(line) for line in ledger.read_text().splitlines()]
            totals[solver]=sum(r['density']['impulse_per_kg'][0] for r in records)
            for r in records:
                self.assertLess(abs(r['viscosity']['dK']+r['physical_viscous_loss']+r['viscous_time_loss']),1e-9)
                self.assertLessEqual(r['viscosity']['dK'],1e-12)
        self.assertGreater(abs(totals['traction_pbf']),1e-6)
        self.assertLess(abs(totals['traction_pbf_mirror']),1e-10)


if __name__=='__main__':unittest.main()
