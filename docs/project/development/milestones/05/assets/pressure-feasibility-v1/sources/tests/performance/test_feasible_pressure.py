"""Independent physical invariants for the isolated pressure feasibility study."""
import unittest
import numpy as np
from tools.performance.feasible_pressure import mac, metrics, analytic_pressure
from tools.performance.feasible_volume import volume_screen, wls_screen


class CompatiblePressure(unittest.TestCase):
    def test_pressure_offset_and_linear_gradient(self):
        grid=mac((8,4,8),fraction=.37)
        np.testing.assert_allclose(grid.gradient(np.full(len(grid.volume),17.),17.),0,atol=1e-13)
        # Linear hydrostatic pressure is an independent continuum reference.
        p=1000*9.81*(.05-grid.cells[:,1])
        np.testing.assert_allclose(grid.gradient(p),np.where(grid.axis==1,-9.81,0),atol=1e-12)

    def test_affine_solenoidal_field_interior(self):
        grid=mac((8,8,8),kind='periodic')
        tensor=np.array([[.4,.2,-.3],[.1,-.1,.2],[.3,-.4,-.3]])
        v=(grid.position@tensor.T)[np.arange(len(grid.axis)),grid.axis]
        divergence=(grid.D@v).reshape(grid.shape)
        # The affine field is not periodic. Only cells away from the periodic
        # seam have the manufactured physical boundary flux.
        np.testing.assert_allclose(divergence[1:-1,1:-1,1:-1],0,atol=1e-12)

    def test_projection_energy_work_and_momentum(self):
        grid=mac((8,8,8),kind='periodic')
        rng=np.random.default_rng(1407)
        p=rng.normal(size=len(grid.volume));v=rng.normal(size=len(grid.area))
        self.assertLess(abs(p@(grid.volume*(grid.D@v))+(grid.G@p)@(grid.mass*v)),1e-12)
        after,_,_=grid.project(v,.002)
        self.assertLessEqual(np.dot(grid.mass*after,after),np.dot(grid.mass*v,v)+1e-12)
        self.assertLess(np.max(np.abs(grid.D@after)),1e-7)
        for axis in range(3):
            select=grid.axis==axis
            self.assertLess(abs(np.sum(grid.mass[select]*(after-v)[select])),1e-12)

    def test_hydrostatic_shear_and_fractional_surface(self):
        for fraction in [1.,.37,.1]:
            with self.subTest(fraction=fraction):
                result,_=metrics(mac((16,4,16),fraction=fraction))
                self.assertEqual(result['shear_preservation_relative'],0)
                self.assertLess(result['gravity_supported_vertical_shear_relative_error'],1e-10)
                self.assertLess(result['hydrostatic_pressure_relative'],1e-10)
                self.assertLess(result['bed_force_relative_error'],1e-10)
                self.assertLess(abs(result['free_surface_volume_rate_m3_s']),1e-12)
                self.assertAlmostEqual(result['volume_m3'],.002,places=14)

    def test_manufactured_spatial_convergence(self):
        errors=[metrics(mac((4*n,n,4*n)))[0]['manufactured_pressure_error'] for n in [4,8,12]]
        self.assertLess(errors[0],.01)
        self.assertLess(errors[1],errors[0]/3.9)
        self.assertLess(errors[2],errors[1]/2.2)

    def test_pressure_consistency_is_not_a_small_timestep_artefact(self):
        grid=mac((16,4,16),fraction=.37)
        shear=np.where(grid.axis==0,.5*np.sin(2*np.pi*grid.position[:,2]/.2),0.)
        _,gradient=analytic_pressure(grid.position)
        force=gradient[np.arange(len(grid.axis)),grid.axis]/1000
        relative=[];pressures=[]
        for dt in [.004,.001]:
            after,p,_=grid.project(shear+dt*force,dt)
            relative.append(np.sqrt(np.sum(grid.mass*(after-shear)**2)/np.sum(grid.mass*(dt*force)**2)))
            pressures.append(p)
        self.assertLess(max(relative),.01)
        self.assertAlmostEqual(relative[0],relative[1],places=9)
        np.testing.assert_allclose(pressures[0],pressures[1],atol=1e-7,rtol=1e-9)

    def test_meshless_shortcuts_have_decisive_counterexamples(self):
        regular,_=wls_screen(16,0.)
        perturbed,_=wls_screen(16,.1)
        self.assertLess(regular['constant_pressure_force_rms'],1e-10)
        self.assertGreater(perturbed['constant_pressure_force_rms'],1)
        volume,_=volume_screen(16,.1)
        self.assertLess(volume['sum_area_error'],1e-12)
        self.assertGreater(volume['affine_material_volume_change_per_strain'],.05)

    def test_invalid_geometry_and_timestep(self):
        for args in [((1,4,4),{}),((4,4,4),{'fraction':0}),((4,4,4),{'kind':'periodic','fraction':.5})]:
            with self.assertRaises(ValueError):mac(args[0],**args[1])
        grid=mac((4,4,4))
        with self.assertRaisesRegex(ValueError,'positive timestep'):
            grid.project(np.zeros(len(grid.area)),0)


if __name__=='__main__':unittest.main()
