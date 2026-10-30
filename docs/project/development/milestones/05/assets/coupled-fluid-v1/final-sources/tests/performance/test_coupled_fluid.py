"""Physical invariants and independent geometry oracles for the coupled prototype."""
import unittest
import numpy as np
from tools.performance.coupled_grid import Grid
from tools.performance.coupled_model import State,step
from tools.performance.coupled_transport import rectangle_fraction,reconstruction,reconstructed_y_moment,geometric_potential,phase_transport
from tools.performance.coupled_reference import circle_fraction,interface_fraction,wave_frequency
from tools.performance.feasible_pressure import mac
from tools.performance.coupled_rawcheck import validate


class CoupledFluid(unittest.TestCase):
    def test_half_plane_geometry_and_subcell_moment(self):
        self.assertAlmostEqual(float(rectangle_fraction(.5,.5,.5,0,1,0,1)),.5)
        self.assertAlmostEqual(float(rectangle_fraction(-.5,-.5,-.5,0,1,0,1)),.5)
        self.assertAlmostEqual(float(rectangle_fraction(0.,1.,.25,0,1,0,1)),.25)
        for nx in [1e-6,1e-8,1e-10,1e-12]:
            self.assertAlmostEqual(float(rectangle_fraction(nx,1.,.9,0,1,0,1)),.9-nx/2,places=14)
        np.testing.assert_allclose(reconstructed_y_moment(np.full((8,8),.25),False),.25**2/2,atol=1e-14)
        rng=np.random.default_rng(4070);alpha=rng.uniform(size=(16,16));nx,ny,a=reconstruction(alpha,True)
        np.testing.assert_allclose(rectangle_fraction(nx,ny,a,0,1,0,1),alpha,atol=1e-12)

    def test_flat_material_potential_uses_subcell_centroid(self):
        g=Grid(32,16);height=.05+.25*g.hy;a=interface_fraction(g,lambda x:np.full_like(x,height))
        expected=9.81*g.lx*(g.rho_gas*g.ly**2+(g.rho_liquid-g.rho_gas)*height**2)/2
        self.assertAlmostEqual(geometric_potential(a,g,9.81),expected,places=12)

    def test_uniform_translation_preserves_material_velocity_and_momentum(self):
        g=Grid(32,16,periodic_y=True);a=circle_fraction(g,[(.07,.05)],.018);u=np.full_like(a,.1);v=np.full_like(a,.03)
        before=g.diagnostics(a,u,v);after,_=step(State(a,u,v,np.zeros_like(a)),.004,g)
        np.testing.assert_allclose(after.u,u,atol=1e-12);np.testing.assert_allclose(after.v,v,atol=1e-12)
        out=g.diagnostics(after.alpha,after.u,after.v)
        for key in ['mass','liquid_volume','momentum_x','momentum_y','kinetic']:
            self.assertAlmostEqual(out[key],before[key],places=11)

    def test_pressure_work_nullspace_and_periodic_momentum(self):
        g=Grid(16,8,periodic_y=True);rng=np.random.default_rng(2008);a=rng.uniform(size=(8,16))
        self.assertEqual(np.max(abs(g.C.T@np.ones(128))),0)
        u=rng.normal(size=a.shape);v=rng.normal(size=a.shape);before=g.diagnostics(a,u,v)
        ou,ov,_,record=g.project(a,u,v,.002);after=g.diagnostics(a,ou,ov)
        self.assertLess(record['relative_residual'],1e-8);self.assertLess(record['divergence_dt_max'],1e-8)
        self.assertLessEqual(after['kinetic'],before['kinetic']+1e-12)
        self.assertAlmostEqual(after['momentum_x'],before['momentum_x'],places=12)
        self.assertAlmostEqual(after['momentum_y'],before['momentum_y'],places=12)
        shear=np.broadcast_to(np.cos(2*np.pi*g.y[:,None]/g.ly),a.shape)
        rx,_=g.face_density(a);self.assertLess(abs(g.volume*np.sum(rx*shear*(ou-u))),1e-12)

    def test_rectangular_solver_matches_admitted_three_dimensional_operator(self):
        g=Grid(8,4);a=np.ones((4,8));u=.2*np.sin(2*np.pi*np.arange(1,9)[None,:]/8)+np.zeros_like(a)
        v=.1*np.sin(np.pi*np.arange(1,5)[:,None]/4)+np.zeros_like(a);v[-1]=0
        _,_,p,_=g.project(a,u,v,.002,'rectangular-direct')
        reference=mac((8,4,4),lengths=(.2,.1,.1),kind='closed')
        xyz=reference.position
        predicted=np.where(reference.axis==0,.2*np.sin(2*np.pi*xyz[:,0]/.2),np.where(reference.axis==1,.1*np.sin(np.pi*xyz[:,1]/.1),0))
        _,expected,_=reference.project(predicted,.002)
        expected=expected.reshape(8,4,4).mean(axis=2).T;np.testing.assert_allclose(p,expected,atol=1e-9,rtol=1e-10)

    def test_variable_density_hydrostatic_rest_survives_coupling(self):
        g=Grid(32,16);a=interface_fraction(g,lambda x:np.full_like(x,.05));zero=np.zeros_like(a);s=State(a,zero,zero,zero)
        for i in range(4):s,_=step(s,.001,g,gravity=9.81,order=i)
        np.testing.assert_allclose(s.alpha,a,atol=1e-12)
        self.assertLess(max(abs(s.u).max(),abs(s.v).max()),1e-10)

    def test_finite_gas_wave_reference_has_correct_vacuum_limit(self):
        g=Grid(32,16,rho_gas=1e-9);k=2*np.pi/g.lx
        self.assertAlmostEqual(wave_frequency(g,.05),np.sqrt(9.81*k*np.tanh(k*.05)),places=9)

    def test_invalid_pressure_and_transport_requests(self):
        with self.assertRaises(ValueError):Grid(1,4)
        g=Grid(8,4);a=np.tile(np.linspace(0,1,8),(4,1));zero=np.zeros_like(a)
        with self.assertRaisesRegex(ValueError,'constant density'):
            g.project(a,zero,zero,.001,'rectangular-direct')
        with self.assertRaisesRegex(ValueError,'positive timestep'):g.project(a,zero,zero,0)
        with self.assertRaisesRegex(ValueError,'CFL'):phase_transport(a,np.ones_like(a),zero,1.,g)

    def test_failed_step_preserves_accepted_state(self):
        g=Grid(8,4,periodic_y=True);a=np.full((4,8),.5);u=np.ones_like(a);v=np.zeros_like(a);p=np.zeros_like(a)
        state=State(a,u,v,p);saved=np.stack([a,u,v,p]).copy()
        with self.assertRaisesRegex(ValueError,'CFL'):step(state,1.,g)
        np.testing.assert_array_equal(np.stack([state.alpha,state.u,state.v,state.p]),saved)

    def test_independent_raw_reader_rejects_false_conservation_summary(self):
        g=Grid(8,4);a=np.full((4,8),.5);u=np.full_like(a,2.);v=np.zeros_like(a);p=np.zeros_like(a)
        rho=(1000+1.2)/2;mass=.2*.1*rho
        record={'liquid_volume':.01,'mass':mass,'momentum_x':2*mass,'momentum_y':0.,'kinetic':2*mass,'divergence_max':0.,'alpha_min':.5,'alpha_max':.5}
        validate(g,np.stack([a,u,v,p]),record)
        record['mass']*=1.01
        with self.assertRaisesRegex(ValueError,'raw diagnostic mismatch: mass'):validate(g,np.stack([a,u,v,p]),record)


if __name__=='__main__':unittest.main()
