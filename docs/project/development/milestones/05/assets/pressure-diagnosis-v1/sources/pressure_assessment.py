# /// script
# dependencies = ["numpy==2.5.4", "scipy==1.18.1"]
# ///
"""Summarise controlled exclusions without treating constraint residual as accuracy."""
import argparse
import json
from pathlib import Path
from tools.performance.pressure_campaign import write_json


def assess(root):
    operators=json.loads((root/'verified-operators/operator-results.json').read_text())['records']
    native=json.loads((root/'native-results.json').read_text())['records'];by={r['label']:r for r in native}
    constitutive=json.loads((root/'constitutive-results.json').read_text())
    attribution=json.loads((root/'multiplier-attribution.json').read_text())['records']
    replay=next(r for r in attribution if r['label']=='replay')
    def case(n,q):return next(r for r in operators if r['closure']=='periodic' and r['layers']==n and abs(r['support']-q)<1e-9 and r['gamma']==.3)
    controls={'frozen_replay_relative_change':abs(by['replay-frozen']['pressure_mode_velocity_change_m_s']/by['replay']['pressure_mode_velocity_change_m_s']-1),
        'epsilon_zero_replay_relative_change':abs(by['replay-eps0']['pressure_mode_velocity_change_m_s']/by['replay']['pressure_mode_velocity_change_m_s']-1),
        'halfdt_velocity_ratio':by['halfdt']['pressure_mode_velocity_change_m_s']/by['base']['pressure_mode_velocity_change_m_s'],
        '96_vs_24_density_residual_ratio':by['96-iterations']['final_p95_compression']/by['base']['final_p95_compression'],
        '96_vs_24_false_displacement_ratio':by['96-iterations']['pressure_mode_displacement_m']/by['base']['pressure_mode_displacement_m'],
        'constant_multiplier_fraction_in_captured_replay':replay['constant_multiplier_component']/replay['pressure_mode_delta_v']}
    verification={'max_native_sparse_action_error_m':max(r['sparse_native_action_error_m'] for r in native),
        'max_reduced_native_action_error_m':max(r['reduced_native_action_error_m'] for r in native),
        'max_reduced_J_error_per_m':max(r['reduced_J_error_per_m'] for r in native),
        'max_point_finite_difference_error_per_m':max(r.get('native_directional_finite_difference_error_per_m',0) for r in native),
        'max_nonzero_manufactured_exact_projection_residual':max(r['exact_projection_residual_relative'] for r in operators if r['gamma'])}
    report={'controls':controls,'verification':verification,'periodic_fixed_q2':[case(n,2) for n in [8,12,24,32,64]],
        'joint_refinement':[case(n,q) for n,q in [(12,2),(24,3),(64,6)]],
        'independent_artificial_shear_curvatures':constitutive['coefficients'],
        'native_runs':len(native),'unique_manufactured_geometries':len(operators),
        'diagnosis':'The point-kernel density constraint is not shear/volume consistent at fixed support-to-spacing ratio. Its pressure adjoint gives nonzero constant-pressure forces and artificial pressure-dependent shear elasticity. Native derivatives and actions match independent references. Boundary support, regularisation, iteration limits and neighbour evolution modify the response but are not necessary for the inconsistency.',
        'limits':'Only one complete-model pressure stage was replayed, not the entire59.1% trajectory. Offline exact solves use the same Jacobian as an attribution oracle. At q2 the periodic strained constraints are all positive/active; other supports may have different compression masks. Dropping the mean density equation is diagnostic and not a valid free-surface replacement.',
        'decision':{'current_fixed_support_model':'NO-GO for production physical qualification and further performance optimisation.',
            'more_parameter_tuning':'NO-GO as a remedy for the demonstrated constitutive inconsistency.',
            'bounded_pressure_discretisation_feasibility':'GO only with a specified volume/constant-pressure/linear-pressure/shear-nullspace validation contract before full simulation.',
            'replacement_implemented':False}}
    write_json(root/'assessment.json',report)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path);assess(parser.parse_args().root)
