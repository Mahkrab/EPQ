# /// script
# dependencies = ["numpy==2.5.4", "matplotlib==3.11.2"]
# ///
"""Plot physical error and decay without treating low compression as accuracy."""
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main(root):
    report=json.loads((root/'assessment.json').read_text())
    fig,axes=plt.subplots(2,2,figsize=(12,8.2),layout='constrained')
    ax=axes[0,0]
    for mode,label in [('horizontal-slip','Horizontal, L=0.2 m'),('vertical-noslip','No-slip / no-slip'),('vertical-mixed','No-slip / free surface')]:
        selected=[r for r in report['operator'] if r['mode']==mode]
        ax.semilogy([r['layers'] for r in selected],[100*r['windows_in_e_folds']['2']['maximum_amplitude_relative_error'] for r in selected],'o-',label=label)
    ax.axhline(5,color='black',ls='--',lw=1);ax.set(xlabel='Layers across H = 0.05 m',ylabel='Maximum amplitude error (%)',title='Isolated viscosity: two decay times');ax.legend(fontsize=8)
    ax=axes[0,1]
    selected=[('mirror-mixed-n4-g0','4 layers, g=0'),('mirror-mixed-n4-g9.81','4 layers, gravity'),('mirror-mixed-n8-g9.81','8 layers, gravity'),('mirror-mixed-n12-g9.81','12 layers, gravity')]
    for label,title in selected:
        data=json.loads((root/'audits-final'/(label+'.audit.json')).read_text())['records']
        ax.plot([r['time_s'] for r in data],[r['amplitude'] for r in data],label=title)
    time=np.linspace(0,1.0125,201);ax.plot(time,np.exp(-.001*(np.pi/.1)**2*time),'k--',label='Analytical shear');ax.axhline(0,color='grey',lw=.7)
    ax.set(xlabel='Time (s)',ylabel='Shear amplitude / initial amplitude',title='Full PBF: gravity spoils correct viscous decay');ax.legend(fontsize=8)
    ax=axes[1,0]
    reference=json.loads((root/'pressure-gradient-reference.json').read_text())['records']
    for r in reference:
        if r['spacing']!=.01 or r['support_over_spacing'] not in [2,3,4]:continue
        ax.plot([v['shear'] for v in r['samples']],[100*v['tangential_over_normal_pressure_force'] for v in r['samples']],'o-',label=f"h / spacing = {r['support_over_spacing']}")
    ax.axhline(0,color='black',ls='--',lw=1);ax.set(xlabel='Volume-preserving shear strain',ylabel='Unwanted tangential / normal force (%)',title='Independent pressure-gradient quadrature');ax.legend(fontsize=8)
    ax=axes[1,1];data=json.loads((root/'audits-final/mirror-rest-n4-g9.81.audit.json').read_text())['records']
    ax.semilogy([r['time_s'] for r in data],np.maximum([r['kinetic_J_kg'] for r in data],1e-20),label='Hydrostatic control')
    ax.axhline(.00125,color='black',ls='--',label='Original quietness threshold');ax.axvspan(5,6,color='grey',alpha=.15)
    ax.set(xlabel='Time (s)',ylabel='Kinetic energy (J/kg)',title='Quietness passes; settled field accuracy fails');ax.legend(fontsize=8)
    for ax in axes.flat:ax.grid(alpha=.2)
    fig.savefig(root/'physical-qualification.png',dpi=180);fig.savefig(root/'physical-qualification.svg');plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);main(p.parse_args().root)
