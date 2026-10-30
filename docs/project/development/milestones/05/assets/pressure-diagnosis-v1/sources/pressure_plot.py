# /// script
# dependencies = ["numpy==2.5.4", "matplotlib==3.11.2"]
# ///
"""Plot the distinction between a converged discrete model and correct fluid pressure."""
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main(root):
    coefficients=json.loads((root/'constitutive-results.json').read_text())
    operators=json.loads((root/'verified-operators/operator-results.json').read_text())['records']
    native=json.loads((root/'native-results.json').read_text())['records']
    fig,axes=plt.subplots(2,2,figsize=(11.8,8),layout='constrained')
    ax=axes[0,0];values=coefficients['coefficients'][:3]
    ax.bar([str(v['support']) for v in values],[v['G_at_mean_hydrostatic_Pa'] for v in values],color=['tab:red','tab:orange','tab:blue'])
    ax.axhline(0,color='black',lw=1);ax.set(xlabel='Pressure support / spacing',ylabel='Artificial shear modulus (Pa)',title='Pressure creates a non-Newtonian shear response')
    ax=axes[0,1]
    for q in [2,3,4]:
        chosen=sorted([r for r in operators if r['closure']=='periodic' and r['gamma']==.3 and abs(r['support']-q)<1e-9],key=lambda r:r['layers'])
        ax.semilogy([r['layers'] for r in chosen],[100*r['pressure_tangent_rms_over_g'] for r in chosen],'o-',label=f'h / spacing = {q}')
    ax.set(xlabel='Layers across fixed H = 0.05 m',ylabel='False tangential force / g (%)',title='Constant pressure: exact physical force is zero');ax.legend(fontsize=8)
    ax=axes[1,0];chosen=[r for r in coefficients['records'] if r['support']==2]
    ax.semilogy([r['layers'] for r in chosen],[100*r['predicted_force_L2_relative_error'] for r in chosen],'o-')
    ax.set(xlabel='Layers across fixed H = 0.05 m',ylabel='Error against predicted artificial force (%)',title='Refinement converges to the wrong constitutive law')
    ax=axes[1,1];by={r['label']:r for r in native};chosen=[by[k] for k in ['one-iteration','base','96-iterations']]
    x=[1,24,96];ax.semilogy(x,[r['final_p95_compression'] for r in chosen],'o-',color='tab:blue',label='Density residual')
    ax.set(xlabel='Pressure iterations',ylabel='p95 compression (fraction)',title='Smaller density residual does not preserve shear')
    right=ax.twinx();right.plot(x,[-1e6*r['pressure_mode_displacement_m'] for r in chosen],'s-',color='tab:red');right.set_ylabel('False shear displacement removed (micrometres)',color='tab:red')
    for ax in axes.flat:ax.grid(alpha=.2)
    fig.savefig(root/'pressure-diagnosis.png',dpi=180);fig.savefig(root/'pressure-diagnosis.svg');plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);main(p.parse_args().root)
