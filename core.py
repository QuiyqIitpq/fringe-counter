"""v1.2 raw tracking. Immutable per-ROI measurements; no post-hoc edits here."""
from pathlib import Path
import hashlib, json, subprocess, uuid, time
import numpy as np
from functools import lru_cache
from PIL import Image, ImageDraw
from legacy_io import probe, get_frame, binary, font, groups

VERSION='1.7.0'
ENGINE_REVISION='20261013-adaptive-pair-2'
PALETTE=['#007f8b','#e88727','#6e61b6','#cd5168','#538742','#9b704e','#377ab5','#9b548c','#8b8b32']
REASONS={1:'过暗/调制信号不足',2:'过曝',4:'周期结构不清',8:'相位失锁',16:'每帧半条风险',32:'条纹结构改变/重新捕获',64:'时间戳异常',128:'缺少新质量指标，旧版待复算'}

def clean_json(value):
 if isinstance(value,dict):return {str(k):clean_json(v) for k,v in value.items()}
 if isinstance(value,(list,tuple)):return [clean_json(v) for v in value]
 if isinstance(value,np.ndarray):return clean_json(value.tolist())
 if isinstance(value,(np.integer,np.bool_)):return value.item()
 if isinstance(value,(float,np.floating)):return float(value) if np.isfinite(value) else None
 return value

def dump(path,obj):
 path=Path(path);tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(clean_json(obj),ensure_ascii=False,indent=2));tmp.replace(path)

def normalize_rois(rois,info):
 if not isinstance(rois,list) or not 1<=len(rois)<=20:raise ValueError('请选择 1–20 个计数框。')
 out=[];seen=set()
 for k,row in enumerate(rois):
  q={key:int(row[key]) for key in ('x','y','w','h')}
  if min(q['x'],q['y'])<0 or min(q['w'],q['h'])<64 or q['x']+q['w']>info['width'] or q['y']+q['h']>info['height']:raise ValueError('计数框必须在画面内，宽高至少 64 原始像素。')
  if max(q['w'],q['h'])/min(q['w'],q['h'])>8:raise ValueError('计数框长宽比超过 8，窄边不足以验证周期条纹；请扩大窄边。')
  rid=str(row.get('id',f'roi-{k+1}'))
  if rid in seen:raise ValueError('计数框 ID 重复。')
  seen.add(rid);q.update(id=rid,label=str(row.get('label',f'ROI {k+1}')),color=row.get('color',PALETTE[k%len(PALETTE)]),source=row.get('source','manual'))
  out.append(q)
 return out

def reduce_patch(a):
 # Isotropic area reduction, rectangular geometry is never stretched to a square.
 h,w=a.shape;scale=min(1.,192/max(w,h))
 if scale<1:a=np.asarray(Image.fromarray(np.asarray(a,np.uint8)).resize((max(1,round(w*scale)),max(1,round(h*scale))),Image.Resampling.BOX))
 return np.asarray(a,float)

@lru_cache(maxsize=32)
def spectral_geometry(shape):
 h,w=shape;yy,xx=np.indices(shape);cx=xx-xx.mean();cy=yy-yy.mean()
 win=np.outer(np.hanning(h),np.hanning(w));fx=np.fft.fftfreq(w)*w;fy=np.fft.fftfreq(h)*h;gx,gy=np.meshgrid(fx,fy);rr=np.hypot(gx,gy)
 allowed=((gx>0)|((gx==0)&(gy>0)))&(rr>=3.5)&(rr<=min(h,w)*.32)
 return cx,cy,win,fx,fy,gx,gy,rr,allowed,max((cx**2).sum(),1),max((cy**2).sum(),1)

@lru_cache(maxsize=64)
def cached_filter(shape,kx,ky,bw):
 h,w=shape;fx=np.fft.fftfreq(w)*w;fy=np.fft.fftfreq(h)*h
 result=np.exp(-((fx[None,:]-kx)**2+(fy[:,None]-ky)**2)/(2*bw*bw));result.flags.writeable=False;return result

@lru_cache(maxsize=32)
def plane_basis(shape):
 h,w=shape;yy,xx=np.indices(shape);x=(xx-(w-1)/2)/max(w-1,1);y=(yy-(h-1)/2)/max(h-1,1)
 return x,y,[np.ones_like(x),x,y]

def spectrum(a):
 h,w=a.shape;cx,cy,win,fx,fy,xx,yy,rr,allowed,sx,sy=spectral_geometry(a.shape)
 ac=a-a.mean();ac-=((ac*cx).sum()/sx)*cx;ac-=((ac*cy).sum()/sy)*cy
 ft=np.fft.fft2(ac*win)
 energy=abs(ft)**2; e=np.where(allowed,energy,0);iy,ix=np.unravel_index(np.argmax(e),e.shape)
 kx,ky=float(fx[ix]),float(fy[iy]); bw=max(.6,min(1.8,np.hypot(kx,ky)/4))
 filt=cached_filter(a.shape,kx,ky,bw);z=np.fft.ifft2(ft*filt)
 ey=max(3,int(h*.22));ex=max(3,int(w*.22));mid=z[ey:-ey,ex:-ex]
 modulation=float(2*np.median(abs(mid)));noise=float(np.median(abs(a[1:-1,1:-1]-(a[:-2,1:-1]+a[2:,1:-1]+a[1:-1,:-2]+a[1:-1,2:])/4))*1.4826)
 concentration=float((energy*filt).sum()/max(energy[rr>=2].sum(),1e-9))
 mean=float(a.mean());clip=float(np.mean(a>=250));snr=modulation/max(noise,1)
 reason=0
 if mean<20 or modulation<4 or snr<1.8:reason|=1
 if clip>=.10:reason|=2
 if concentration<.12 or np.hypot(kx,ky)<3.5:reason|=4
 return dict(kx=kx,ky=ky,bw=bw,mean=mean,modulation=modulation,noise=noise,snr=snr,concentration=concentration,clipping=clip,reason=reason,score=modulation*concentration*min(snr,10)*(1-clip))

def patch_of(frame,roi):return reduce_patch(frame[roi['y']:roi['y']+roi['h'],roi['x']:roi['x']+roi['w']])

def sample_frames(video,info,preview_s):
 times=sorted(set([max(0,min(float(preview_s),info['duration_s']-.1))]+[max(0,info['duration_s']*x) for x in [.1,.3,.5,.7,.9]]))
 return times,[np.asarray(get_frame(video,t)) for t in times]

def propose(video,selection=None,max_rois=7,preview_s=30):
 info=probe(video);max_rois=max(1,min(20,int(max_rois)));times,full=sample_frames(video,info,preview_s)
 # Search at half size; return only exact rectangles in original coordinates.
 factor=min(.5,1100/info['width']);sw=round(info['width']*factor);sh=round(info['height']*factor)
 frames=[np.array(Image.fromarray(a).resize((sw,sh),Image.Resampling.BOX)) for a in full]
 if selection:
  x,y,w,h=map(float,selection)
  if min(x,y)<0 or min(w,h)<64 or x+w>info['width'] or y+h>info['height']:raise ValueError('搜索范围无效。')
 else:x,y,w,h=0,0,info['width'],info['height']
 x0,y0,x1,y1=round(x*factor),round(y*factor),round((x+w)*factor),round((y+h)*factor)
 candidates=[]
 for size in [96,160,240]:
  if size>min(x1-x0,y1-y0):continue
  step=max(48,round(size*.65))
  for cy in sorted(set(list(range(y0,y1-size+1,step))+[y1-size])):
   for cx in sorted(set(list(range(x0,x1-size+1,step))+[x1-size])):
    ps=[a[cy:cy+size,cx:cx+size] for a in frames]
    if np.median([a.mean() for a in ps])<20:continue
    stats=[spectrum(reduce_patch(a)) for a in ps];good=[s for s in stats if not s['reason']]
    if len(good)<max(3,int(np.ceil(len(stats)*.83))):continue
    ks=np.array([[s['kx'],s['ky']] for s in good]);base=ks[np.argmax([s['score'] for s in good])];agreement=np.abs(ks@base)/(np.linalg.norm(ks,axis=1)*np.linalg.norm(base))
    if np.median(agreement)<.9:continue
    score=float(np.percentile([s['score'] for s in good],25))
    q=dict(x=round(cx/factor),y=round(cy/factor),w=round(size/factor),h=round(size/factor),score=score,quality=stats)
    q['w']=min(q['w'],info['width']-q['x']);q['h']=min(q['h'],info['height']-q['y']);candidates.append(q)
 selected=[]
 for q in sorted(candidates,key=lambda a:a['score'],reverse=True):
  if any(max(0,min(q['x']+q['w'],p['x']+p['w'])-max(q['x'],p['x']))*max(0,min(q['y']+q['h'],p['y']+p['h'])-max(q['y'],p['y']))>.20*min(q['w']*q['h'],p['w']*p['h']) for p in selected):continue
  k=len(selected);q.update(id='roi-'+uuid.uuid4().hex[:8],label=f'ROI {k+1}',color=PALETTE[k%len(PALETTE)],source='auto');selected.append(q)
  if len(selected)>=max_rois:break
 return dict(rois=selected,sample_times=times,message=f'找到 {len(selected)} 个合格候选框（上限 {max_rois}）。不足时不补入暗区。',video=info)

def phase_plane(unit,weight):
 """Center phase and residual after a resolved spatial phase ramp.

 The ramp is an observed wavefront tilt, not temporal interpolation. A
 conservative branch gate rejects ambiguous/wide phase fields. Wrapped
 center increments still require the < half-fringe sampling assumption.
 """
 v=np.sum(weight*unit)/max(weight.sum(),1e-12);base=np.angle(v)/(2*np.pi)
 res=np.angle(unit*np.exp(-1j*np.angle(v)))/(2*np.pi)
 raw=float(np.sqrt(np.sum(weight*res**2)/max(weight.sum(),1e-12)))
 h,w=res.shape;x,y,basis=plane_basis(res.shape)
 # Nine sufficient statistics avoid constructing thousands of design rows.
 sw=max(weight.sum(),1e-12)
 mat=np.array([[(weight*b*c).sum()/sw for c in basis] for b in basis])
 vec=np.array([(weight*b*res).sum()/sw for b in basis])
 try:beta=np.linalg.solve(mat,vec)
 except np.linalg.LinAlgError:return float(base),float(abs(v)),raw,raw,0.,0.
 fitted=beta[0]+beta[1]*x+beta[2]*y;error=res-fitted
 scatter=float(np.sqrt(np.sum(weight*error**2)/sw));coh=float(abs(np.sum(weight*np.exp(2j*np.pi*error))/sw))
 # If the raw circular field straddles a branch too broadly, a plane fit is
 # not a license to unwrap it. Keep the old conservative loss decision.
 if abs(v)<.80 or np.max(abs(fitted))>.30 or np.sum(weight*(abs(res)>.40))/sw>.01:
  return float(base),float(abs(v)),max(raw,.056),raw,0.,0.
 delta=float((base+beta[0]+.5)%1-.5)
 return delta,coh,scatter,raw,float(beta[1]/max(w-1,1)),float(beta[2]/max(h-1,1))

class Tracker:
 def __init__(self,a,stats):
  self.shape=a.shape;self.previous_image=None;self.previous_stats=None;self.previous_ft=None;self.previous_fields={};self.stats=stats;self.frame=0
  h,w=self.shape;self.win=np.outer(np.hanning(h),np.hanning(w));self.fx=np.fft.fftfreq(w)*w;self.fy=np.fft.fftfreq(h)*h
  yy,xx=np.indices(self.shape);self.xx=xx-xx.mean();self.yy=yy-yy.mean();self.ey=max(3,int(h*.22));self.ex=max(3,int(w*.22));self.set_carrier(stats)
 def set_carrier(self,s):
  self.k=np.array([s['kx'],s['ky']]);self.bw=s['bw'];self.filt=self.filter(self.k,self.bw)
 def filter(self,k,bw):
  return cached_filter(self.shape,float(k[0]),float(k[1]),float(bw))
 def transform(self,a):
  ac=a-a.mean();ac=ac-(ac*self.xx).sum()/max((self.xx*self.xx).sum(),1)*self.xx-(ac*self.yy).sum()/max((self.yy*self.yy).sum(),1)*self.yy
  return np.fft.fft2(ac*self.win)
 def field(self,ft,filt):
  cache=self.previous_fields if ft is self.previous_ft else (getattr(self,'current_fields',None) if ft is getattr(self,'current_ft',None) else None)
  if cache is not None and id(filt) in cache:return cache[id(filt)][1]
  z=np.fft.ifft2(ft*filt)[self.ey:-self.ey,self.ex:-self.ex]
  if cache is not None:cache[id(filt)]=(filt,z)
  return z
 def analytic(self,a):return self.field(self.transform(a),self.filt)
 def signed_stats(self,s):
  return dict(s,kx=-s['kx'],ky=-s['ky']) if np.dot(self.k,[s['kx'],s['ky']])<0 else s
 def pair(self,left,right,filt):
  cache=getattr(self,'pair_cache',None)
  if cache is not None and id(filt) in cache:return cache[id(filt)][1]
  z0=self.field(left,filt);z1=self.field(right,filt);a0=abs(z0);a1=abs(z1)
  result=phase_plane(z1*np.conj(z0)/np.maximum(a0*a1,1e-12),np.minimum(a0,a1))
  output=(result,float(2*np.median(a0)),float(2*np.median(a1)))
  if cache is not None:cache[id(filt)]=(filt,output)
  return output
 def local_check(self,left,right,s0,s1,delta):
  # Independent carrier choices on BOTH observed images, with three fixed
  # bandwidths. Agreement is a sensitivity check, not an accuracy certificate.
  if s0['reason'] or s1['reason'] or abs(delta)>.35:return 0.,np.nan
  values=[];passed=True
  for s in (s0,s1):
   for factor in (.8,1.,1.2):
    result,m0,m1=self.pair(left,right,self.filter([s['kx'],s['ky']],s['bw']*factor));d,coh,scatter,*_=result;values.append(d)
    passed &= min(m0,m1)>=6 and m0/max(s0['noise'],1)>=2.5 and m1/max(s1['noise'],1)>=2.5 and coh>=.98 and scatter<=.03 and abs(d)<=.35
  offsets=(np.asarray(values)-delta+.5)%1-.5;spread=float(np.ptp(offsets))
  return float(passed and spread<=.02 and np.max(abs(offsets))<=.02),spread
 def push(self,a):
  # Fresh spectral evidence every frame: a carrier can leave a narrow filter
  # without crossing the old 26-degree / 40-percent change thresholds.
  self.pair_cache={}
  s=self.signed_stats(spectrum(a));carrier_changed=False;candidate=np.array([s['kx'],s['ky']])
  if not s['reason'] and np.linalg.norm(candidate-self.k)>.5*min(self.bw,s['bw']):
   self.set_carrier(s);carrier_changed=True
  ft=self.transform(a);self.current_ft=ft;self.current_fields={};z=self.field(ft,self.filt);mod=float(2*np.median(abs(z)));reason=int(s['reason']&6)
  mean=float(a.mean());clip=float(np.mean(a>=250));noise=max(s['noise'],1.);coh=1.;scatter=0.;delta=0.;raw_scatter=0.;slope_x=0.;slope_y=0.;local=0.;spread=np.nan
  if mean<20 or mod<4 or mod/noise<1.8:reason|=1
  if self.previous_ft is not None:
   # Always use the SAME filter on the two original frames. Re-evaluate left
   # quality after an update instead of inheriting the stale-filter bad flag.
   result,m0,mod=self.pair(self.previous_ft,ft,self.filt);delta,coh,scatter,raw_scatter,slope_x,slope_y=result;s0=self.previous_stats
   if s0['reason']&6 or s0['mean']<20 or m0<4 or m0/max(s0['noise'],1)<1.8:reason|=8
   if coh<.95 or scatter>.055:reason|=8
   if abs(delta)>.38:reason|=16
   if reason==0:local,spread=self.local_check(self.previous_ft,ft,s0,s,delta)
  self.previous_fields=self.current_fields;self.previous_ft=ft;self.previous_image=a.copy();self.previous_stats=s;self.stats=s;self.frame+=1
  return [delta,reason,mean,mod,mod/noise,clip,coh,scatter,s['concentration'],self.k[0]/a.shape[1],self.k[1]/a.shape[0],raw_scatter,slope_x,slope_y,local,spread,int(carrier_changed)]

FIELDS=['delta','reason','brightness','modulation','snr','clipping','coherence','scatter','concentration','kx','ky','raw_scatter','phase_slope_x','phase_slope_y','local_verified','filter_spread','carrier_refresh']

def video_identity(video):
 p=Path(video);s=p.stat();return dict(path=str(p.resolve()),size=s.st_size,mtime_ns=s.st_mtime_ns)

def analyze(video,output,rois=None,selection=None,max_rois=5,preview_s=30,previous=None,progress=None,reference_point_px=None,analysis_mode="balanced",workers=5):
 started=time.perf_counter();timing={}
 if analysis_mode not in ['balanced','full']:raise ValueError('分析模式无效')
 progress=progress or (lambda p,m:None);out=Path(output);out.mkdir(parents=True,exist_ok=False)
 identity=video_identity(video);old=None
 if previous and (Path(previous)/'raw.json').exists():
  old=json.loads((Path(previous)/'raw.json').read_text())
  if old.get('identity')!=identity or old.get('version')!=VERSION or old.get('engine_revision')!=ENGINE_REVISION:old=None
 if old:
  info=dict(old['video'])
  with np.load(Path(previous)/'raw_tracks.npz') as saved:times=saved['time'].copy()
 else:
  info=probe(video,True);times=info.pop('timestamps')
 if len(times)<2:raise ValueError('视频至少需要两帧可读图像')
 preview_s=max(0,min(float(preview_s),float(times[-1])-.05))
 if rois is None:rois=propose(video,selection,max_rois,preview_s)['rois']
 rois=normalize_rois(rois,info);progress(2,'检查实际计数框和缓存')
 samples=None;arrays={};cached=[];recomputed=[]
 trackers={};stats_list=[]
 old_np=np.load(Path(previous)/'raw_tracks.npz') if old else None
 for k,q in enumerate(rois):
  cache_index=next((j for j,p in enumerate(old['rois']) if all(q[z]==p[z] for z in ['id','x','y','w','h'])),None) if old else None
  if cache_index is not None:
   arrays[k]=np.column_stack([old_np[name][:,cache_index] for name in FIELDS]);cached.append(q['id']);stats_list.append(old['roi_diagnostics'][cache_index]);continue
  if samples is None:_,samples=sample_frames(video,info,preview_s)
  ps=[patch_of(a,q) for a in samples];ss=[spectrum(a) for a in ps];best=max(ss,key=lambda s:s['score'] if not s['reason'] else -1);trackers[k]=Tracker(ps[0],best);stats_list.append(ss);recomputed.append(q['id'])
 if old_np is not None:old_np.close()
 if trackers:
  from fast_tracking import track
  indices=list(trackers);stats=[trackers[k].stats for k in indices]
  computed,near_repeats,timing=track(video,dict(info,frame_count=len(times)),[rois[k] for k in indices],stats,progress,out,workers=workers)
  for j,k in enumerate(indices):arrays[k]=computed[j]
  # Repeat diagnosis is only comparable when all selected patches were decoded.
  if len(indices)!=len(rois):near_repeats=np.zeros(len(times),bool)
 all_arrays={name:np.column_stack([arrays[k][:,j] for k in range(len(rois))]) for j,name in enumerate(FIELDS)}
 if trackers and len(trackers)==len(rois):all_arrays['frame_near_repeat']=np.asarray(near_repeats,bool)
 elif old and not trackers and set(cached)=={q['id'] for q in old['rois']}:
  with np.load(Path(previous)/'raw_tracks.npz') as saved:
   if 'frame_near_repeat' in saved:all_arrays['frame_near_repeat']=saved['frame_near_repeat']
 all_arrays['reason']=all_arrays['reason'].astype(np.uint16);dt=np.diff(times);gaps=np.r_[False,dt>np.median(dt)*1.8];all_arrays['reason'][gaps]|=64
 all_arrays['reason'][0]=0;all_arrays['delta'][0]=0
 np.savez_compressed(out/'raw_tracks.npz',time=times,**all_arrays)
 centers=np.array([[q['x']+q['w']/2,q['y']+q['h']/2] for q in rois]);quality=np.mean(all_arrays['reason']==0,axis=0);scores=[np.median([s['score'] for s in rows]) for rows in stats_list];best=int(np.argmax(np.asarray(scores)*quality));reference=centers[best].tolist()
 if old and old.get('reference_point_px'):reference=old['reference_point_px']
 if reference_point_px is not None:
  reference=list(map(float,reference_point_px))
  if len(reference)!=2 or not np.isfinite(reference).all() or not (0<=reference[0]<info['width'] and 0<=reference[1]<info['height']):raise ValueError('参考点必须在画面内。')
 meta=dict(analysis_mode=analysis_mode,timing=dict(timing,raw_analysis_seconds=time.perf_counter()-started),search_range=selection,version=VERSION,engine_revision=ENGINE_REVISION,identity=identity,video=info,rois=rois,roi_diagnostics=stats_list,reference_point_px=reference,frames_decoded=len(times),reference_frame_s=float(preview_s),cache=dict(reused=cached,recomputed=recomputed),reason_bits=REASONS,legacy=False,note='Image-coordinate signed phase; not calibrated displacement. Assumes less than half a fringe per usable frame. Raw tracking is immutable.')
 if analysis_mode=='full' and old and previous and (Path(previous)/'spatial_evidence.json').exists():
  from spatial_recovery import fingerprint,METHOD
  evidence=json.loads((Path(previous)/'spatial_evidence.json').read_text())
  if evidence.get('method')==METHOD and evidence.get('fingerprint')==fingerprint(meta):dump(out/'spatial_evidence.json',evidence)
 dump(out/'raw.json',meta);draw_regions(video,preview_s,rois,reference,out/'selected_regions.png');progress(95,'原始追踪已保存，生成可撤销的统计结果')
 return meta

def draw_regions(video,seconds,rois,reference,path):
 im=get_frame(video,seconds).convert('RGB');d=ImageDraw.Draw(im)
 for q in rois:
  d.rectangle((q['x'],q['y'],q['x']+q['w'],q['y']+q['h']),outline=q['color'],width=4);d.text((q['x']+5,q['y']+5),q['label'],font=font(24),fill=q['color'])
 x,y=reference;d.ellipse((x-10,y-10,x+10,y+10),outline='cyan',width=3);im.save(path)

def load_raw(folder):
 folder=Path(folder)
 if (folder/'raw.json').exists():
  m=json.loads((folder/'raw.json').read_text());z=np.load(folder/'raw_tracks.npz');a={k:z[k].copy() for k in z.files};z.close();
  if m.get('analysis_mode')!='balanced' and (folder/'spatial_evidence.json').exists():m['spatial_evidence']=json.loads((folder/'spatial_evidence.json').read_text())
  if (folder/'performance.json').exists():m['performance']=json.loads((folder/'performance.json').read_text())
  return m,a
 r=json.loads((folder/'result.json').read_text());z=np.load(folder/'tracks.npz');d=z['roi_delta'].copy();shape=d.shape
 rois=[dict(q,id=f'legacy-{i+1}',label=f'ROI {i+1}',color=PALETTE[i%len(PALETTE)],source='legacy') for i,q in enumerate(r['rois'])]
 a={name:np.zeros(shape) for name in FIELDS};a.update(time=z['time'].copy(),delta=d,reason=np.full(shape,128,np.uint16));a['reason'][0]=0
 for old,new in [('coherence','coherence'),('clipping','clipping'),('pixel_scatter','scatter')]:
  if old in z:a[new]=z[old].copy()
 z.close();m=dict(version=r.get('version','1.1'),video=r['video'],rois=rois,reference_point_px=r['reference_point_px'],frames_decoded=len(a['time']),reference_frame_s=r.get('reference_frame_s',30),legacy=True,reason_bits=REASONS)
 return m,a
