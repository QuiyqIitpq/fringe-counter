"""Multiscale spatial branch evidence. Never promotes a model to original data.

Small wrapped anchors remain a sampling assumption: a shared integer shift is
not observable from an image pair. The graph resolves relative branches only.
"""
from pathlib import Path
import json, subprocess, math
import numpy as np
from core import Tracker, spectrum, binary, dump
METHOD = '1.6-spatial-graph-1'

def measure(im0,im1,q,orientation):
 x,y,w,h=q;a=im0[y:y+h,x:x+w].astype(float);b=im1[y:y+h,x:x+w].astype(float);s0=spectrum(a);s1=spectrum(b)
 if s0['reason'] or s1['reason']:return None
 if min(s0['modulation'],s1['modulation'])<6 or min(s0['snr'],s1['snr'])<2.5:return None
 tr=Tracker(a,s0);ft0=tr.transform(a);ft1=tr.transform(b);values=[];quality=[];grads=[]
 for s in (s0,s1):
  k=np.array([s['kx'],s['ky']]);k=k*(1 if np.dot(k/np.array([w,h]),orientation)>=0 else -1)
  for factor in (.8,1.,1.2):
   result,m0,m1=tr.pair(ft0,ft1,tr.filter(k,s['bw']*factor));d,coh,sc,raw,gx,gy=result
   if min(m0,m1)<6 or m0/max(s0['noise'],1)<2.5 or m1/max(s1['noise'],1)<2.5 or coh<.98 or sc>.03:return None
   values.append(d);grads.append([gx,gy]);quality.append(sc)
 base=values[0];offsets=(np.asarray(values)-base+.5)%1-.5
 if np.ptp(offsets)>.02:return None
 return dict(x=x+w/2,y=y+h/2,q=q,phase=float((base+np.median(offsets)+.5)%1-.5),grad=np.median(grads,axis=0),scatter=max(quality),spread=float(np.ptp(offsets)),modulation=min(s0['modulation'],s1['modulation']))

def solve(nodes,edge_tol=.055,grad_tol=.12):
 xy=np.array([[q['x'],q['y']] for q in nodes]);p=np.array([q['phase'] for q in nodes]);g=np.array([q['grad'] for q in nodes]);N=len(nodes);edges=[]
 for j in range(N):
  for k in range(j+1,N):
   dv=xy[k]-xy[j];dist=np.linalg.norm(dv)
   if dist>76 or dist<5:continue
   preds=np.array([g[j]@dv,g[k]@dv]);guess=float(np.mean(preds));raw=p[k]-p[j];shift=int(round(guess-raw));res=abs(raw+shift-guess)
   if res>edge_tol or abs(preds[0]-preds[1])>grad_tol or max(abs(preds))>.4:continue
   edges.append((res+max(nodes[j]['scatter'],nodes[k]['scatter']),j,k,shift))
 # Quality-first constraints, reject any path inconsistent with an established loop.
 edges.sort();parent=list(range(N));off=np.zeros(N,int);conflicts=[];links=[]
 def root(i):
  if parent[i]!=i:
   p0=parent[i];parent[i],delta=root(p0);off[i]+=delta
  return parent[i],int(off[i])
 for quality,j,k,shift in edges:
  rj,oj=root(j);rk,ok=root(k)
  if rj==rk:
   if ok-oj!=shift:conflicts.append([j,k,shift,ok-oj])
   continue
  parent[rk]=rj;off[rk]=oj+shift-ok;links.append([j,k,shift,quality])
 if not N:return {}
 root0,o0=root(0);component=[j for j in range(N) if root(j)[0]==root0];relative=np.array([root(j)[1]-o0 for j in component]);vals=p[component]+relative
 votes=[]
 for j,n in zip(component,relative):
  if abs(p[j])<.25:votes.append((j,int(-n)))
 hist={v:sum(v==q for j,q in votes) for _,v in votes};winner=max(hist,key=hist.get) if hist else None
 return dict(component=component,relative_integers=relative.tolist(),unwrapped_relative=vals.tolist(),votes=votes,vote_counts=hist,reference_candidates=[float(p[0]+v) for v in sorted(hist)],chosen=float(p[0]+winner) if winner is not None else None,links=links,conflicts=conflicts)

def vote(field, bound, size):
 nodes=field['nodes'];g=field['graph'];comp=g['component']
 pairs=[(j,-k) for j,k in zip(comp,g['relative_integers']) if abs(nodes[j]['phase'])<bound]
 if not pairs:return dict(qualified=False,reason='no_anchor')
 hist={v:sum(v==k for j,k in pairs) for _,v in pairs};winner=max(hist,key=hist.get);chosen=[]
 for j,v in sorted(pairs,key=lambda p:-nodes[p[0]]['modulation']):
  if v==winner and all(math.hypot(nodes[j]['x']-nodes[k]['x'],nodes[j]['y']-nodes[k]['y'])>=size for k in chosen):chosen.append(j)
 fraction=hist[winner]/len(pairs);coverage=len(comp)/len(nodes)
 good=len(chosen)>=3 and fraction>=.9 and coverage>=.7 and not g['conflicts']
 return dict(integer=int(winner),qualified=good,fraction=fraction,anchors=chosen,coverage=coverage)

def qualify(record):
 """Require two predeclared anchor bounds and two distinct grid scales.
 The grids share pixels, so this is sensitivity testing, not independence of noise.
 """
 if 'field96' not in record:return dict(qualified=False,reason=record.get('reason','missing_field'))
 evidence=[]
 for bound in [.20,.25,.30,.35]:
  v=[vote(record['field96'],bound,96),vote(record['field80'],bound,80)]
  ok=all(q['qualified'] for q in v) and v[0]['integer']==v[1]['integer']
  evidence.append(dict(bound=bound,qualified=ok,integer=v[0]['integer'] if ok else None,votes=v))
 successes=[q for q in evidence if q['qualified']]
 # .35 is a veto-only sensitivity check, not a way to increase recoveries.
 good=len([q for q in successes if q['bound']<=.30])>=2 and len({q['integer'] for q in successes})==1
 variants=record['reference_variants'];ref=variants[-1];base=record['original_reference_delta']
 # Legacy diagnostic records stored the reason separately only in raw data.
 readable=record.get('original_reference_readable',True)
 if not readable:base=ref['phase']
 if len(variants)<2 or abs((base-ref['phase']+.5)%1-.5)>.035:good=False
 offsets=(np.array([v['phase'] for v in variants])-ref['phase']+.5)%1-.5
 if np.ptp(offsets)>.035:good=False
 integer=successes[0]['integer'] if successes else None
 estimate=None if integer is None else float(base+round(ref['phase']+integer-base))
 return dict(qualified=bool(good),estimate=estimate,reason='multiscale_spatial_support' if good else 'insufficient_consensus',evidence=evidence)

def field(left,right,orientation,reference,step,size):
 nodes=[reference]
 for y in range(0,left.shape[0]-size+1,step):
  for x in range(0,left.shape[1]-size+1,step):
   if min(left[y:y+size,x:x+size].mean(),right[y:y+size,x:x+size].mean())<20:continue
   q=measure(left,right,(x,y,size,size),orientation)
   if q is not None:nodes.append(q)
 return dict(nodes=nodes,graph=solve(nodes))

def examine(left,right,frame,meta,a,anchor):
 rx,ry=meta['reference_point_px'];orientation=np.array([a['kx'][frame,anchor],a['ky'][frame,anchor]])
 variants=[]
 for size in [64,80,96,112,128]:
  x,y=int(round(rx-size/2)),int(round(ry-size/2))
  if x<0 or y<0 or x+size>left.shape[1] or y+size>left.shape[0]:continue
  # Never silently move a half-pixel reference.
  if abs(x+size/2-rx)>.01 or abs(y+size/2-ry)>.01:continue
  q=measure(left,right,(x,y,size,size),orientation)
  if q is not None:variants.append(q)
 record=dict(frame=int(frame),time_s=float(a['time'][frame]),original_reference_delta=float(a['delta'][frame,anchor]),original_reference_readable=(int(a['reason'][frame,anchor])&~16)==0,reference_variants=variants)
 if len(variants)<2:return dict(record,qualified=False,reason='insufficient_reference_scales')
 ref=variants[-1];offsets=(np.array([v['phase'] for v in variants])-ref['phase']+.5)%1-.5
 if np.ptp(offsets)>.035:return dict(record,qualified=False,reason='reference_scale_disagreement')
 record.update(field96=field(left,right,orientation,ref,48,96),field80=field(left,right,orientation,ref,40,80))
 record.update(qualify(record));return record

def fingerprint(meta):
 return dict(identity=meta.get('identity'),reference=meta['reference_point_px'],rois=[{k:q[k] for k in ['id','x','y','w','h']} for q in meta['rois']],engine=meta.get('engine_revision'))

def build(folder,meta,a,progress=None):
 """Full video pass; fixed predeclared holdout stride. Raw tracks stay immutable."""
 from processing import derive,default_config
 cache=Path(folder)/'spatial_evidence.json'
 if cache.exists():
  saved=json.loads(cache.read_text())
  if saved.get('method')==METHOD and saved.get('fingerprint')==fingerprint(meta):return saved
 progress=progress or (lambda p,m:None);cfg=default_config(meta);cfg['joint_recovery']=True
 # Prevent an older evidence record from affecting target selection.
 mm={k:v for k,v in meta.items() if k!='spatial_evidence'};r=derive(mm,a,cfg)
 rec=r.get('recovery') or {};xy=np.array([[q['x']+q['w']/2,q['y']+q['h']/2] for q in meta['rois']])
 anchor=int(np.argmin(np.linalg.norm(xy-np.array(meta['reference_point_px']),axis=1)))
 if np.linalg.norm(xy[anchor]-meta['reference_point_px'])>.01:return None
 targets={q['frame'] for q in rec.get('records',[]) if q['category'] in ['ambiguous','missing']}
 held=set(np.flatnonzero(np.array(r['track']['valid']) & (np.arange(len(a['time']))%79==0)).tolist())-{0}
 targets|=held;records=[];previous=None;w,h=meta['video']['width'],meta['video']['height'];f=0
 proc=subprocess.Popen([binary('ffmpeg'),'-v','error','-i',meta['video']['path'],'-vf','format=gray','-fps_mode','passthrough','-f','rawvideo','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 try:
  while True:
   data=proc.stdout.read(w*h)
   if not data:break
   if len(data)!=w*h:raise ValueError('空间复核视频帧不完整')
   im=np.frombuffer(data,np.uint8).reshape(h,w)
   if f in targets and previous is not None:
    q=examine(previous,im,f,meta,a,anchor);q['held_out']=f in held;records.append(q)
    if len(records)%20==0:progress(min(99,91+8*f/len(a['time'])),f'空间复核 {len(records)}/{len(targets)} 个图像对')
   previous=im.copy();f+=1
  if proc.wait():raise ValueError(proc.stderr.read().decode()[-500:])
  if f!=len(a['time']):raise ValueError('空间复核帧数不一致')
 finally:
  if proc.poll() is None:proc.kill()
  proc.stdout.close();proc.stderr.close()
 evidence=dict(method=METHOD,fingerprint=fingerprint(meta),anchor_id=meta['rois'][anchor]['id'],frames_decoded=f,records=records,note='Relative spatial unwrapping conditional on small-phase anchors not sharing an integer alias. Auxiliary patches are checks, not user-selected averaging ROIs.')
 dump(Path(folder)/'spatial_evidence.json',evidence);return evidence

def eligible(meta,c,enabled,blocked):
 """Never reuse proof after geometry, reference, participation or exclusion changes."""
 evidence=meta.get('spatial_evidence')
 if not evidence or evidence.get('method')!=METHOD or evidence.get('fingerprint')!=fingerprint(meta):return []
 if c['reference_point_px']!=meta['reference_point_px'] or set(enabled)!=set(range(len(meta['rois']))):return []
 rows=[]
 for r in evidence['records']:
  i=r['frame']
  if r.get('qualified') and not r.get('held_out') and not np.any(blocked[i]):rows.append(r)
 return rows
