from pathlib import Path
import json,gzip,hashlib,statistics,sqlite3,collections,sys
w=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/tmp/maelstrom-numerical-20261028');f=w/'validation-only';sha=lambda b:hashlib.sha256(b).hexdigest();physical={};processes=0;records=0;samples={};regressions={}
for folder in ['verification','measurements','final-profiles']:
 for p in sorted((f/folder).rglob('process.json')):
  r=json.loads(p.read_text());raw=gzip.decompress((p.parent/'stdout.gz').read_bytes());err=gzip.decompress((p.parent/'stderr.gz').read_bytes());assert r['exit']==0 and sha(raw)==r['stdout_sha256'] and sha(err)==r['stderr_sha256'];processes+=1
  try:value,_=json.JSONDecoder().raw_decode(raw.decode())
  except (ValueError,UnicodeDecodeError):continue
  if not isinstance(value,dict) or 'final_snapshot' not in value or 'measurements' not in value:continue
  m=value.pop('measurements');value['metadata'].pop('build_revision',None);assert value['completed_steps']=='480' and not value['failures'];key=sha(json.dumps({k:value[k] for k in ['input','request','execution']},sort_keys=True).encode());fp=sha(json.dumps(value,sort_keys=True,allow_nan=False).encode());assert physical.get(key,fp)==fp;physical[key]=fp;records+=1;total=sum(x['total_s'] for x in m['steps']);assert len(m['steps'])==480
  if folder=='measurements' and p.parent.parent.name.startswith('sample-'):
   g,label,v=p.parent.relative_to(f/folder).parts;samples.setdefault(g,{}).setdefault(v,[]).append(total)
  if folder=='verification' and p.parent.relative_to(f/folder).parts[0]=='regression':
   _,n,v=p.parent.relative_to(f/folder).parts;regressions.setdefault(n,{})[v]=total
assert records==70 and len(regressions)==7,(records,len(regressions))
# 14 regression + 48 warmup/primary + 8 GPU traces = 70, separate from the original198.
summary={}
for g,x in samples.items():
 assert len(x['control'])==len(x['candidate'])==5
 med={v:statistics.median(z) for v,z in x.items()};summary[g]=dict(samples_s=x,median_s=med,ranges_s={v:[min(z),max(z)] for v,z in x.items()},median_reduction_percent=100*(1-med['candidate']/med['control']),paired_reduction_percent=[100*(1-y/x) for x,y in zip(x['control'],x['candidate'])],slower_pairs=sum(y>x for x,y in zip(x['control'],x['candidate'])))
 expected=json.loads((f/'measurements/summary.json').read_text())[g];assert summary[g]['median_reduction_percent']==expected['median_reduction_percent']
db=sqlite3.connect(f/'final-profiles/activity.sqlite');stages={}
for g in ['8000','110592','8000-effects','110592-effects']:
 n=int(g.split('-')[0]);effects=g.endswith('effects');labels=['acceleration_cfl','prediction_bounds','cells']+['spatial_sort']*(7 if n==8000 else 11)+['neighbor_count','prefix_block','prefix_total','prefix_carry','neighbor_fill','row_sort']+['density_lambda_validation','publication','correction','physical_density_check','candidate','projection']*8+['velocity']+(['curl','confinement','velocity_replace','xsph','velocity_replace'] if effects else [])
 for v in ['control','candidate']:
  rows=db.execute('SELECT name,start_ns,end_ns FROM kernel WHERE workload=? AND variant=? ORDER BY start_ns',(g,v)).fetchall();assert len(rows)==480*len(labels);totals=collections.Counter()
  for i,(name,a,b) in enumerate(rows):
   label=labels[i%len(labels)];expected='observe_state' if label in ['acceleration_cfl','prediction_bounds'] else 'spatial_sort' if label=='spatial_sort' else 'prefix_counts' if label.startswith('prefix_') else 'solver';assert name==expected;assert b>=a;totals[label]+=b-a
  api=dict(db.execute('SELECT name,count(*) FROM api WHERE workload=? AND variant=? GROUP BY name',(g,v)));copies=db.execute('SELECT copy_kind,count(*),sum(bytes) FROM memcpy WHERE workload=? AND variant=? GROUP BY copy_kind',(g,v)).fetchall();download=next(x for x in copies if x[0]==2);nbytes=24*n+64*((n+127)//128)+24;assert download[1:]==(480*5,480*nbytes);waits=sum(count for name,count in api.items() if 'StreamSynchronize' in name);assert waits==480*(26 if effects else 21)
  stages[g+'/'+v]=dict(gpu_ms_per_step={k:z/480e6 for k,z in totals.items()},launches_per_step=len(labels),stream_waits_per_step=waits//480,downloads_per_step=5,download_bytes_per_step=nbytes,api_counts=api)
for v in ['control','candidate']:
 source=json.loads((f/(v+'-source.json')).read_text());assert all(sha((f/v/n).read_bytes())==h for n,h in source.items())
out=dict(exact_records=records,prior_campaign_exact_records=198,total_exact_records=198+records,process_hashes_verified=processes,timing=summary,stage_attribution=stages,regressions=regressions)
(f/'independent-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({g:x['median_reduction_percent'] for g,x in summary.items()},indent=2))
