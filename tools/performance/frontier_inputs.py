"""Immutable scenes and independently controlled PBF policies for the frontier.

Resolution, mass calibration, support and artificial pressure stay fixed. Scene
generation is separate from numerical-policy selection, and refinement is disabled.
"""
import argparse
import json
import math
from pathlib import Path


def policies():
    anchor={'dt':1/240,'iterations':8,'scale':.5,'epsilon':2.}
    rows=[('production',{'dt':1/480,'iterations':8,'scale':.0625,'epsilon':20.}),('anchor',anchor)]
    for key,values in [('dt',[1/120,1/480,1/960]),('iterations',[2,4,16]),('scale',[.0625,.25,1.]),('epsilon',[.02,.2,20.])]:
        for value in values:rows.append((f'{key}-{value}',{**anchor,key:value}))
    production=rows[0][1]
    for label,change in [('production-dt120',{'dt':1/120}),('production-dt240',{'dt':1/240}),('production-scale.5',{'scale':.5}),('production-eps2',{'epsilon':2.})]:
        rows.append((label,{**production,**change}))
    return [{'id':label,**value} for label,value in rows]


def generate(root):
    configs=root/'config';scenes=root/'scenes';configs.mkdir();scenes.mkdir()
    config_source=Path(__file__).resolve().parents[2]/'Maelstrom/config/defaults-v4.toml'
    base=config_source.read_text().replace('schema_version = 1','schema_version = 2').replace('fixed_timestep_s = 0.008333334','fixed_timestep_s = 0.0020833334').replace('correction_scale = 1.0','correction_scale = 0.0625')
    definitions={
        'resolved':{'groups':[((.2,.4,.2),(20,20,20),(0,0,0))],'upper':(1.4,1.6,1.4),'gravity':True,'duration':2.},
        'large':{'groups':[((.2,.4,.2),(48,48,48),(0,0,0))],'upper':(2.8,3.,2.8),'gravity':True,'duration':5.},
        'hydro':{'groups':[((.025,.025,.025),(20,8,20),(0,0,0))],'upper':(1.,1.,1.),'gravity':True,'duration':2.},
        'collision':{'groups':[((.1,.2,.2),(12,12,12),(1.,0,0)),((.9,.2,.2),(12,12,12),(-1.,0,0))],'upper':(1.6,1.4,1.),'gravity':True,'duration':2.},
        'surface':{'groups':[((.5,.025,.5),(20,8,20),(0,0,0))],'upper':(2.,1.5,2.),'gravity':True,'duration':2.},
        'shear':{'groups':[((.2,.2,.2+.05*z),(20,20,1),(.5*math.sin(2*math.pi*z/20),0,0)) for z in range(20)],'upper':(3.,3.,3.),'gravity':False,'duration':.2}}
    for name,d in definitions.items():
        text=base if d['gravity'] else base.replace('[0.0, -9.81, 0.0]','[0.0, 0.0, 0.0]')
        (configs/(name+'.toml')).write_text(text)
        lines=['schema_version = 2',f'name = "frontier-{name}"','description = "Isolated fixed-geometry PBF policy experiment"','randomness = "none"','', '[configuration]','source = "file"',f'path = "../config/{name}.toml"','', '[container]','min_m = [0.0, 0.0, 0.0]',f'max_m = {list(d["upper"])}','', '[particles]','construction = "groups"']
        for i,(origin,counts,velocity) in enumerate(d['groups']):
            lines+=['','[[particles.groups]]',f'name = "group-{i}"','construction = "lattice"',f'origin_m = {list(origin)}',f'counts = {list(counts)}','endpoint_rule = "counted_half_open"','order = "x_then_y_then_z"',f'initial_velocity_m_s = {list(velocity)}']
        (scenes/(name+'.toml')).write_text('\n'.join(lines)+'\n')
        d['particles']=sum(math.prod(counts) for _,counts,_ in d['groups'])
    (root/'scenes.json').write_text(json.dumps(definitions,indent=2)+'\n');(root/'policies.json').write_text(json.dumps(policies(),indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);generate(p.parse_args().root)
