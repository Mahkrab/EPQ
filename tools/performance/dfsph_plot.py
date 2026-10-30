# /// script
# dependencies = ["matplotlib==3.11.2"]
# ///
"""Export cost, work and failed physical-convergence evidence as one figure."""
import argparse
import json
from pathlib import Path
import struct
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main(root):
    assessment=json.loads((root/'assessment.json').read_text());quality=json.loads((root/'quality-results.json').read_text())
    fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained');ax=axes[0,0]
    for i,scene in enumerate(['resolved','large']):
        for method,offset,color in [('pbf',-.18,'tab:blue'),('dfsph',.18,'tab:orange')]:
            row=next(x for x in assessment['timing'] if x['scene']==scene and x['method']==method)
            ax.bar(i+offset,row['median'],width=.34,color=color,label=method.upper() if i==0 else None);ax.scatter([i+offset]*5,row['samples'],s=12,color='black',zorder=4);ax.text(i+offset,row['max']+.08,f"{row['median']:.3f}",ha='center',fontsize=9)
    ax.axhline(1,color='black',ls='--',lw=1);ax.set(xticks=[0,1],xticklabels=['8,000 particles','110,592 particles'],ylabel='Wall seconds / simulated second',title='Five paired samples; both policies unqualified',ylim=(0,4.9));ax.legend(fontsize=9)
    ax=axes[0,1]
    values=[('PBF\n110,592',3840,0),('DFSPH\n8,000',1294.5,399),('DFSPH\n110,592',5152,352.8),('Wendland repair\n110,592',55216/5,2921/5)]
    ax.bar(range(4),[x[1] for x in values],label='Density / Jacobi',color='tab:orange');ax.bar(range(4),[x[2] for x in values],bottom=[x[1] for x in values],label='Divergence',color='tab:green');ax.axhline(3840,color='black',ls='--',lw=1);ax.set(xticks=range(4),xticklabels=[x[0] for x in values],ylabel='Iterations / simulated second',title='Lower timestep rate does not ensure less work');ax.legend(fontsize=8)
    ax=axes[1,0];rows=[next(x for x in quality if x['label']==f'hydro--cubic-{rate}-e01') for rate in [120,240,480]]
    ax.plot([120,240,480],[100*x['p95_compression_peak'] for x in rows],'-o',color='tab:blue');ax.axhline(5,color='tab:blue',ls=':',lw=1);ax.set(xlabel='Steps / simulated second',ylabel='Worst sampled p95 compression (%)',title='Tank: density improves; particle pairing persists',ylim=(0,5.5))
    twin=ax.twinx();twin.plot([120,240,480],[x['min_separation_over_dx'] for x in rows],'s--',color='tab:red');twin.axhline(.5,color='tab:red',ls=':',lw=1);twin.set(ylabel='Minimum separation / spacing',ylim=(0,.6))
    ax=axes[1,1];raw=(root/'preview-hydro.bin').read_bytes();n=len(raw)//24;points=list(struct.iter_unpack('<3f',raw[:n*12]));ax.scatter([x[0] for x in points],[x[1] for x in points],s=4,alpha=.35,rasterized=True)
    ax.axhline(.4,color='tab:green',ls='--',label='Mass-based equilibrium height');ax.axhline(0,color='black');ax.set(xlim=(-.02,1.02),ylim=(-.02,.46),xlabel='x (m)',ylabel='y (m)',title='Repaired Wendland: centroid close, sites clustered');ax.legend(fontsize=8)
    fig.savefig(root/'dfsph-prototype.svg');fig.savefig(root/'dfsph-prototype.png',dpi=180);plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);main(p.parse_args().root)
