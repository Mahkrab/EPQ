# /// script
# dependencies = ["matplotlib==3.11.2"]
# ///
"""Export the measured cost/quality trade-offs without implying qualification."""
import argparse
import json
from pathlib import Path
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main(root):
    rows=json.loads((root/'frontier.json').read_text())
    fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    for scene in ['resolved','hydro','collision','surface','large']:
        chosen=[x for x in rows if x['scene']==scene and not x['label'].startswith(('long-','admission'))]
        axes[0,0].scatter([x['cost_s_per_sim_s'] for x in chosen],[100*x['p95_compression_peak'] for x in chosen],label=scene,alpha=.75,s=28)
    axes[0,0].axhline(5,color='black',ls='--',lw=1);axes[0,0].axvline(1,color='grey',ls=':',lw=1)
    axes[0,0].set(xlabel='Production solver wall s / simulated s',ylabel='Worst sampled p95 compression (%)',title='Independent-control screen: no combined pass',yscale='log');axes[0,0].legend(fontsize=8)
    selected=['dt-0.008333333333333333','anchor','dt-0.0020833333333333333','dt-0.0010416666666666667']
    hydro=sorted([x for x in rows if x['scene']=='hydro' and x['policy']['id'] in selected and not x['label'].startswith('long-')],key=lambda x:x['policy']['dt'],reverse=True)
    axes[0,1].plot([1/x['policy']['dt'] for x in hydro],[100*x['hydro_centroid_error'] for x in hydro],'-o',label='Hydrostatic centroid error')
    axes[0,1].axhline(10,color='black',ls='--',lw=1);axes[0,1].set(xlabel='Steps per simulated second',ylabel='Centroid error (%)',title='Smaller dt: closer height, larger energy injection')
    twin=axes[0,1].twinx();twin.plot([1/x['policy']['dt'] for x in hydro],[100*x['energy_excess_peak'] for x in hydro],'s--',color='tab:red');twin.set_ylabel('Peak excess mechanical energy (%)',color='tab:red')
    shear=sorted([x for x in rows if x['scene']=='shear' and x['policy']['id'] in selected],key=lambda x:x['policy']['dt'],reverse=True)
    axes[1,0].plot([1/x['policy']['dt'] for x in shear],[x['final']['shear_projection'] for x in shear],'-o',label='PBF: fixed scale 0.5, εh²=2')
    dfpath=root/'dfsph-summary.json'
    if dfpath.exists():
        df=json.loads(dfpath.read_text())['shear'];axes[1,0].plot([x['rate'] for x in df],[x['final']['shear_projection'] for x in df],'-s',label='Author DFSPH exploratory probe')
    axes[1,0].axhspan(.8,1.2,color='tab:green',alpha=.1);axes[1,0].axhline(1,color='black',lw=1);axes[1,0].set(xlabel='Steps per simulated second',ylabel='Retained shear-mode projection',title='Velocity accuracy is separate from density');axes[1,0].legend(fontsize=8)
    resident=json.loads((root/'residency-results.json').read_text());ax=axes[1,1]
    for i,(case,cadence,label) in enumerate([('large--production',8,'480 Hz, 8 iterations'),('large--dt-0.008333333333333333',2,'120 Hz, 8 iterations'),('large--iterations-2',4,'240 Hz, 2 iterations')]):
        for mode,shift,color in [('normal',-.18,'tab:blue'),('device',.18,'tab:orange')]:
            values=[x['cost_s_per_sim_s'] for x in resident if x['case']==case and x['checkpoint_period']==cadence and x['mode']==mode and not x['warmup']]
            ax.bar(i+shift,statistics.median(values),width=.34,color=color,label=mode if i==0 else None);ax.scatter([i+shift]*len(values),values,color='black',s=8,zorder=3)
    ax.axhline(1,color='black',ls='--',lw=1);ax.set(xticks=range(3),xticklabels=['Production policy','Fails density','Fails density'],ylabel='Wall s / simulated s',title='110,592 particles, 60 Hz observations, first second');ax.legend(fontsize=8)
    fig.savefig(root/'frontier.svg');fig.savefig(root/'frontier.png',dpi=180);plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);main(p.parse_args().root)
