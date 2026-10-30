"""Independent invariants guard calibration, conservation and stage accounting."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import struct
import unittest

import numpy as np

from tools.performance.qualification_audit import calibration_constants,energy_audit
from tools.performance.qualification_campaign import run
from tools.performance.spatial_audit import frames


class QualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary=tempfile.TemporaryDirectory();cls.root=Path(cls.temporary.name)
        cls.source=Path(__file__).resolve().parents[2]/'tools/performance'
        cls.binary=cls.root/'solver';cls.old=cls.root/'spatial';cls.shear=cls.root/'shear';cls.slab=cls.root/'slab'
        for source,binary,extra in [('qualification_solver.cpp',cls.binary,['-fopenmp']),('spatial_solver.cpp',cls.old,['-fopenmp']),('qualification_shear.cpp',cls.shear,[]),('qualification_slab.cpp',cls.slab,[])]:
            subprocess.run(['c++','-std=c++17','-O2','-ffp-contract=off',*extra,str(cls.source/source),'-o',str(binary)],check=True)

    @classmethod
    def tearDownClass(cls):cls.temporary.cleanup()

    def experiment(self,label,**kwargs):
        root=self.root/self.id().rsplit('.',1)[-1];root.mkdir(exist_ok=True)
        (root/'protocol.json').write_text('{}')
        parameters=dict(n=6,duration=.05,threads=1);parameters.update(kwargs)
        result=run(root,self.binary,label,**parameters)
        return root/'runs'/label,result

    def test_calibration_is_exact_at_physical_rest_lattice_and_scales(self):
        for n in (6,12,24):
            dx=.3/n;mass=52.23230175835605/(2*n**3)
            bias,ratio=calibration_constants(mass,2*dx,'self')
            self.assertAlmostEqual(bias,32.23825865107778,places=9)
            raw_bias,normalizer=calibration_constants(mass,2*dx,'ratio')
            self.assertEqual(raw_bias,0)
            self.assertAlmostEqual((1000+bias)/normalizer,1000,places=10)
            self.assertEqual(ratio,1)

    def test_raw_instrumentation_preserves_prior_observations_exactly(self):
        directory,_=self.experiment('raw')
        original=subprocess.check_output([str(self.old),'collision','6','1',str(1/240),'.05','8','1','.5','1'],stderr=subprocess.DEVNULL)
        self.assertEqual(gzip.decompress((directory/'states.bin.gz').read_bytes()),original)

    def test_calibration_keeps_mass_and_initial_geometry_fixed(self):
        a,_=self.experiment('raw',calibration='raw');b,_=self.experiment('self',calibration='self')
        aa=next(frames(a/'states.bin.gz'));bb=next(frames(b/'states.bin.gz'))
        np.testing.assert_array_equal(aa[3],bb[3]);self.assertEqual(aa[0]['mass'],bb[0]['mass'])
        self.assertAlmostEqual(aa[0]['count']*aa[0]['mass'],52.23230175835605,places=11)

    def test_geometric_mass_control_changes_reference_without_changing_points(self):
        a,_=self.experiment('inherited',duration=0)
        b,_=self.experiment('geometric',duration=0,mass_scheme='geometric')
        aa=next(frames(a/'states.bin.gz'));bb=next(frames(b/'states.bin.gz'))
        np.testing.assert_array_equal(aa[3],bb[3])
        self.assertAlmostEqual(bb[0]['mass']*bb[0]['count'],54,places=10)
        bias,_=calibration_constants(bb[0]['mass'],bb[0]['h'],'self')
        self.assertAlmostEqual(bias,33.8430086773107,places=10)

    def test_freefall_energy_and_velocity_reconstruction_close_independently(self):
        directory,_=self.experiment('ballistic',boundary=False,contact=False,density=False)
        result=energy_audit(directory)
        for value in result['maximum_identity_residuals'].values():self.assertLess(value,1e-9)
        observations=list(frames(directory/'states.bin.gz'));first,last=observations[0],observations[-1]
        dt=last[0]['dt'];steps=last[2]
        self.assertAlmostEqual(last[3][:,1].mean()-first[3][:,1].mean(),-9.81*dt**2*steps*(steps+1)/2,places=12)

    def test_fault_in_stage_work_is_detected_by_independent_closure(self):
        directory,_=self.experiment('corrupt')
        path=directory/'ledger.jsonl.gz'
        lines=gzip.decompress(path.read_bytes()).decode().splitlines();record=json.loads(lines[0]);record['density']['dK']+=.01;lines[0]=json.dumps(record)
        raw=('\n'.join(lines)+'\n').encode();compressed=gzip.compress(raw,mtime=0);path.write_bytes(compressed)
        manifest=directory/'collection.json';record=json.loads(manifest.read_text())
        record['ledger'].update(raw_sha256=hashlib.sha256(raw).hexdigest(),gzip_sha256=hashlib.sha256(compressed).hexdigest(),raw_bytes=len(raw))
        manifest.write_text(json.dumps(record))
        self.assertGreater(energy_audit(directory)['maximum_identity_residuals']['closure'],.009)

    def test_window_work_excludes_interval_before_lower_endpoint(self):
        directory,_=self.experiment('window',duration=1.05,boundary=False,contact=False,density=False)
        window=energy_audit(directory)['windows']['tail']
        self.assertEqual(window['steps'],240)
        self.assertEqual(window['state_samples'],241)
        self.assertAlmostEqual(window['start_time_s'],.05)
        self.assertAlmostEqual(window['end_time_s'],1.05)
        observed=next(r for r in frames(directory/'states.bin.gz') if r[2]==12)
        self.assertAlmostEqual(window['initial']['K'],float(np.mean(np.sum(observed[4]**2,axis=1))/2),places=11)

    def test_failed_request_retains_diagnostics_and_cannot_overwrite(self):
        root=self.root/'invalid-request';root.mkdir();(root/'protocol.json').write_text('{}')
        record=run(root,self.binary,'failed',n=7,duration=0,threads=1)
        self.assertEqual(record['exit_code'],1);self.assertIsNone(record['ledger'])
        self.assertEqual(gzip.decompress((root/'runs/failed/states.bin.gz').read_bytes()),b'')
        self.assertIn('invalid spatial request',(root/'runs/failed/stderr.txt').read_text())
        before=(root/'runs/failed/collection.json').read_bytes()
        with self.assertRaises(FileExistsError):run(root,self.binary,'failed',n=6,duration=0)
        self.assertEqual(before,(root/'runs/failed/collection.json').read_bytes())

    def test_shear_decay_refines_to_physical_viscosity_without_amplitude_fit(self):
        errors=[]
        for n in (18,24,36):
            d=json.loads(subprocess.check_output([str(self.shear),str(n),'0.001','8000','4'],text=True))
            errors.append(abs(d['relative_error']))
            self.assertLess(abs(d['mean_velocity']),1e-12);self.assertLessEqual(d['maximum_energy_increase'],1e-12)
            self.assertEqual(d['rigid_rotation_error'],0)
        self.assertLess(errors[0],.05);self.assertTrue(errors[2]<errors[1]<errors[0])

    def test_unresolved_viscous_quadrature_cannot_pass_physical_gate(self):
        d=json.loads(subprocess.check_output([str(self.shear),'36','0.001','8000','2'],text=True))
        self.assertGreater(d['relative_error'],.5)

    def test_viscous_stage_dissipates_without_internal_linear_or_angular_impulse(self):
        directory,_=self.experiment('viscous',scene='flat-valid',n=12,nu=.001)
        result=energy_audit(directory)['maximum_identity_residuals']
        for name in ['viscous_increase','viscous_impulse','viscous_angular']:
            self.assertLess(result[name],1e-12)
        rows=[json.loads(line) for line in gzip.decompress((directory/'ledger.jsonl.gz').read_bytes()).splitlines()]
        self.assertTrue(any(row['viscosity']['dK']<-1e-12 for row in rows))

    def test_bulk_viscosity_success_does_not_hide_shallow_free_slip_error(self):
        d=json.loads(subprocess.check_output([str(self.slab),'24','2','8000'],text=True))
        self.assertGreater(d['relative_error'],.35)
        self.assertAlmostEqual(d['H'],.05)

    def test_slab_viscosity_refines_at_fixed_physical_geometry(self):
        errors=[]
        for n in (24,48,96,192,384):
            d=json.loads(subprocess.check_output([str(self.slab),str(n),str(n//12),'16000'],text=True))
            self.assertAlmostEqual(d['H'],.05)
            errors.append(d['relative_error'])
        self.assertTrue(all(b<a for a,b in zip(errors,errors[1:])))
        self.assertLess(errors[-1],.05)

    def test_calibrated_pressure_removes_initial_energy_source_and_scales_with_dt(self):
        ell=(52.23230175835605/432/1000)**(1/3)
        xyz=np.stack(np.meshgrid((np.arange(6)-2.5)*ell,(np.arange(6)-2.5)*ell,(np.arange(12)-5.5)*ell,indexing='ij'),axis=-1).reshape((-1,3))
        positions=xyz+[.6,.6,.4];velocity=-.5*xyz;velocity[:,0]+=2*xyz[:,1]
        initial=self.root/'strain.bin';initial.write_bytes(struct.pack('<I',432)+positions.astype('<f8').tobytes()+velocity.astype('<f8').tobytes())
        displacement={}
        for mode in ['raw','self']:
            for denominator in [480,960]:
                directory,_=self.experiment(f'{mode}-{denominator}',dt=1/denominator,gravity=0,boundary=False,contact=False,calibration=mode,restart=initial)
                result=energy_audit(directory)
                if mode=='raw':self.assertGreater(result['every_step_max_energy_above_initial'],.1)
                else:
                    self.assertLessEqual(result['every_step_max_energy_above_initial'],1e-9)
                    self.assertLess(result['windows']['all']['final']['K'],.019)
                with gzip.open(directory/'ledger.jsonl.gz','rt') as f:displacement[mode,denominator]=json.loads(next(f))['density']['max_displacement']
        self.assertGreater(displacement['raw',960]/displacement['raw',480],.9)
        self.assertTrue(.48<displacement['self',960]/displacement['self',480]<.52)


if __name__=='__main__':unittest.main()
