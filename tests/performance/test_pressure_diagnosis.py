"""Manufactured counterexamples distinguish pressure consistency from convergence."""
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
import numpy as np
from tools.performance.pressure_operator import assemble,manufactured
from tools.performance.pressure_constitutive import curvature
from tools.performance.pressure_audit import trace,sparse_check
from tools.performance.spatial_audit import frames


class PressureReferenceTests(unittest.TestCase):
    def test_layer_derivative_matches_independent_density_finite_difference(self):
        for closure in ['free','closed','periodic']:
            op=assemble(8,2,.1,closure,profile='periodic' if closure=='periodic' else 'mixed')
            direction=np.zeros_like(op.positions);direction[:,0]=np.sin(np.arange(8));direction[:,1]=np.cos(np.arange(8)*.37)
            epsilon=1e-8
            values=[]
            for sign in [-1,1]:values.append(assemble(8,2,.1,closure,layer_positions=op.positions+sign*epsilon*direction).constraint)
            np.testing.assert_allclose((values[1]-values[0])/(2*epsilon),op.jacobian@direction.ravel(),atol=1e-5,rtol=1e-6)

    def test_rigid_parallel_translation_and_total_internal_force_are_preserved(self):
        op=assemble(12,2,.3,'periodic',profile='periodic');v=np.zeros((12,3));v[:,0]=1
        np.testing.assert_allclose(op.jacobian@v.ravel(),0,atol=1e-10)
        force=(op.jacobian.T@np.cos(np.arange(12))).reshape(12,3)
        np.testing.assert_allclose(force.sum(axis=0),0,atol=1e-10)

    def test_current_constraint_has_a_constant_pressure_counterexample(self):
        regular=assemble(12,2,0,'periodic',profile='periodic');sheared=assemble(12,2,.01,'periodic',profile='periodic')
        self.assertLess(np.linalg.norm(regular.jacobian.T@np.ones(12)),1e-9)
        self.assertGreater(np.linalg.norm(sheared.jacobian.T@np.ones(12)),.01)
        # The physical reference is zero force for either isochoric map. This
        # asserts the existence of the diagnosed defect, not physical admission.

    def test_exact_constraint_solve_does_not_establish_velocity_accuracy(self):
        op=assemble(12,2,.01,'periodic',profile='periodic');result,_=manufactured(op,.01,'periodic',profile='periodic')
        self.assertTrue(np.all(op.constraint>0))
        self.assertLess(result['exact_projection_residual_relative'],1e-9)
        self.assertGreater(result['exact_projection_mode_loss'],.99)
        self.assertLess(result['zero_mean_row_diagnostic_mode_loss'],1e-4)

    def test_frozen_neighbours_do_not_remove_the_counterexample(self):
        initial=assemble(12,2,0,'periodic',profile='periodic')
        full=assemble(12,2,.01,'periodic',profile='periodic')
        frozen=assemble(12,2,.01,'periodic',profile='periodic',frozen_edges=initial.edges)
        np.testing.assert_allclose(full.jacobian,frozen.jacobian,atol=1e-12)
        self.assertGreater(np.linalg.norm(frozen.jacobian.T@np.ones(12)),.01)

    def test_free_surface_deficiency_is_separate_from_closed_density_calibration(self):
        free=assemble(12,2,0,'free');closed=assemble(12,2,0,'closed')
        self.assertLess(free.constraint[-1],-.1)
        np.testing.assert_allclose(closed.constraint,0,atol=1e-13)
        strained=assemble(12,2,.3,'closed')
        result,_=manufactured(strained,.3,'closed')
        self.assertGreater(result['exact_projection_mode_loss'],.05)

    def test_independent_hessian_predicts_artificial_shear_response(self):
        b=curvature(2)
        self.assertAlmostEqual(b['dimensionless_shear_curvature'],b['finite_difference_curvature'],delta=2e-6)
        n=24;op=assemble(n,2,.001,'periodic',profile='periodic');k=2*np.pi/.05
        actual=-(op.jacobian.T@np.full(n,9.81*.05)).reshape(n,3)[:,0]
        predicted=-9.81*.05*b['dimensionless_shear_curvature']*k*k*op.positions[:,0]
        self.assertLess(np.linalg.norm(actual-predicted)/np.linalg.norm(predicted),.01)
        self.assertGreater(np.linalg.norm(actual),.001)


class NativePressureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary=tempfile.TemporaryDirectory();cls.root=Path(cls.temporary.name)
        cls.source=Path(__file__).resolve().parents[2]/'tools/performance'
        for source in ['pressure_probe','traction_pbf_mirror']:
            subprocess.run(['c++','-std=c++17','-O2','-fopenmp','-ffp-contract=off','-DMAELSTROM_DUMP_PRESSURE_JACOBIAN',str(cls.source/(source+'.cpp')),'-o',str(cls.root/source)],check=True)

    @classmethod
    def tearDownClass(cls):cls.temporary.cleanup()

    def run_case(self,label,dt=1/480,original=False):
        dx=.0125;axis=(np.arange(16)+.5)*dx;y=(np.arange(4)+.5)*dx
        p=np.stack(np.meshgrid(axis,y,axis,indexing='ij'),axis=-1).reshape(-1,3);p[:,0]+=.3*np.sin(np.pi*p[:,1]/.1)/(np.pi/.1);p[:,0]%=.2
        initial=self.root/(label+'.input');initial.write_bytes(struct.pack('<I',len(p))+p.astype('<f8').tobytes()+np.zeros_like(p).tobytes())
        ledger=self.root/(label+'.ledger');raw=self.root/(label+'.raw');binary=self.root/('traction_pbf_mirror' if original else 'pressure_probe')
        command=[str(binary),'channel-mixed','4','0',str(dt),str(dt),'24','1','.5','1','self','1','0','0','1','0',str(ledger),str(initial),'1','2','2','geometric']
        if not original:command+=['.02','1']
        with raw.open('xb') as stream:subprocess.run(command,check=True,stdout=stream,stderr=subprocess.DEVNULL,env={**os.environ,'OMP_WAIT_POLICY':'PASSIVE'})
        return raw,ledger

    def test_instrumentation_reproduces_existing_reference(self):
        a,_=self.run_case('original',original=True);b,_=self.run_case('instrumented')
        self.assertEqual(a.read_bytes(),b.read_bytes())

    def test_native_full_row_norm_and_action_match_layer_reduction(self):
        _,ledger=self.run_case('layer-check');_,_,p,c,load,correction=next(trace(Path(str(ledger)+'.trace')))
        J,diag,_,_,error=sparse_check(Path(str(ledger)+'.jac'),len(p),4,load,correction)
        reference=assemble(4,2,.3,'free')
        np.testing.assert_allclose(J,reference.jacobian,atol=1e-9)
        np.testing.assert_allclose(diag,reference.full_row_norm2,atol=1e-8)
        self.assertGreater(np.max(np.abs(diag-np.sum(J*J,axis=1))),1)
        self.assertLess(error,1e-12)

    def test_smaller_dt_doubles_false_velocity_from_same_density_restoration(self):
        a,_=self.run_case('dt');b,_=self.run_case('halfdt',dt=1/960)
        fa=list(frames(a))[-1];fb=list(frames(b))[-1]
        np.testing.assert_array_equal(fa[3],fb[3])
        np.testing.assert_array_equal(2*fa[4],fb[4])
        self.assertGreater(np.max(np.abs(fa[4])),1e-5)

    def test_truncated_iteration_trace_is_rejected(self):
        bad=self.root/'bad.trace';bad.write_bytes(b'bad')
        with self.assertRaisesRegex(ValueError,'truncated pressure trace header'):list(trace(bad))


if __name__=='__main__':unittest.main()
