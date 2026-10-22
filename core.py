"""v1.2 raw tracking. Immutable per-ROI measurements; no post-hoc edits here."""
from pathlib import Path
import hashlib, json, subprocess, uuid
import numpy as np
from PIL import Image, ImageDraw
from legacy_io import probe, get_frame, binary, font, groups

VERSION='1.3.0'
ENGINE_REVISION='20261013-phase-plane-1'
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

def spectrum(a):
 h,w=a.shape;yy,xx=np.indices(a.shape)
 # Remove smooth illumination slope before searching for a fringe carrier.
 ac=a-a.mean();ac-=((ac*(xx-xx.mean())).sum()/max(((xx-xx.mean())**2).sum(),1))*(xx-xx.mean())
 ac-=((ac*(yy-yy.mean())).sum()/max(((yy-yy.mean())**2).sum(),1))*(yy-yy.mean())
 win=np.outer(np.hanning(h),np.hanning(w));ft=np.fft.fft2(ac*win)
 fx=np.fft.fftfreq(w)*w;fy=np.fft.fftfreq(h)*h;xx,yy=np.meshgrid(fx,fy);rr=np.hypot(xx,yy)
 allowed=((xx>0)|((xx==0)&(yy>0)))&(rr>=3.5)&(rr<=min(h,w)*.32)
 energy=abs(ft)**2; e=np.where(allowed,energy,0);iy,ix=np.unravel_index(np.argmax(e),e.shape)
 kx,ky=float(fx[ix]),float(fy[iy]); bw=max(.6,min(1.8,np.hypot(kx,ky)/4))
 filt=np.exp(-((xx-kx)**2+(yy-ky)**2)/(2*bw*bw));z=np.fft.ifft2(ft*filt)
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
 h,w=res.shape;yy,xx=np.indices(res.shape);x=(xx-(w-1)/2)/max(w-1,1);y=(yy-(h-1)/2)/max(h-1,1)
 # Nine sufficient statistics avoid constructing thousands of design rows.
 basis=[np.ones_like(x),x,y];sw=max(weight.sum(),1e-12)
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
  self.shape=a.shape;self.previous=None;self.previous_mod=0.;self.previous_mean=0.;self.previous_bad=True;self.stats=stats;self.set_carrier(stats);self.frame=0;self.structure_bad=0
 def set_carrier(self,s):
  h,w=self.shape;self.k=np.array([s['kx'],s['ky']]);self.win=np.outer(np.hanning(h),np.hanning(w));fx=np.fft.fftfreq(w)*w;fy=np.fft.fftfreq(h)*h
  self.filt=np.exp(-((fx[None,:]-self.k[0])**2+(fy[:,None]-self.k[1])**2)/(2*s['bw']**2));self.ey=max(3,int(h*.22));self.ex=max(3,int(w*.22))
 def analytic(self,a):
  ac=a-a.mean()
  yy,xx=np.indices(a.shape);xx=xx-xx.mean();yy=yy-yy.mean()
  ac=ac-(ac*xx).sum()/max((xx*xx).sum(),1)*xx-(ac*yy).sum()/max((yy*yy).sum(),1)*yy
  return np.fft.ifft2(np.fft.fft2(ac*self.win)*self.filt)[self.ey:-self.ey,self.ex:-self.ex]
 def push(self,a):
  reason=0;carrier_changed=False
  # Recheck spectral structure throughout the video, not just in the preview.
  if self.frame%15==0:
   s=spectrum(a);similar=abs(np.dot(self.k,[s['kx'],s['ky']]))/max(np.linalg.norm(self.k)*np.hypot(s['kx'],s['ky']),1e-9)
   changed=similar<.90 or not .7<np.hypot(s['kx'],s['ky'])/max(np.linalg.norm(self.k),1e-9)<1.4
   if changed and not s['reason']:
    if np.dot(self.k,[s['kx'],s['ky']])<0:s=dict(s,kx=-s['kx'],ky=-s['ky'])
    # Apply the same NEW filter to both original images. This preserves
    # the phase difference when an adaptive carrier changes; never splice
    # two differently filtered absolute phases.
    self.set_carrier(s);carrier_changed=True
    self.previous=self.analytic(self.previous_image) if getattr(self,'previous_image',None) is not None else None
    if self.previous is not None and 2*np.median(abs(self.previous))<4:reason|=32
   self.stats=s
  s=self.stats;z=self.analytic(a);amp=abs(z)
  mean=float(a.mean());mod=float(2*np.median(amp));clip=float(np.mean(a>=250));noise=max(s['noise'],1.);coh=1.;scatter=0.;delta=np.nan;raw_scatter=0.;slope_x=0.;slope_y=0.
  if mean<20 or mod<4 or mod/noise<1.8:reason|=1
  if clip>=.10:reason|=2
  reason|=s['reason']&4
  if self.previous is not None:
   weight=np.minimum(abs(self.previous),amp);unit=z*np.conj(self.previous)/np.maximum(abs(self.previous)*amp,1e-12)
   delta,coh,scatter,raw_scatter,slope_x,slope_y=phase_plane(unit,weight)
   if coh<.95 or scatter>.055:reason|=8
   if abs(delta)>.38:reason|=16
   if self.previous_bad:reason|=8
  elif self.frame:reason|=32
  else:delta=0.
  self.previous=z;self.previous_image=a.copy();self.previous_bad=bool(reason&7);self.frame+=1
  return [delta,reason,mean,mod,mod/noise,clip,coh,scatter,s['concentration'],self.k[0]/a.shape[1],self.k[1]/a.shape[0],raw_scatter,slope_x,slope_y,int(carrier_changed)]

FIELDS=['delta','reason','brightness','modulation','snr','clipping','coherence','scatter','concentration','kx','ky','raw_scatter','phase_slope_x','phase_slope_y','carrier_refresh']

def video_identity(video):
 p=Path(video);s=p.stat();return dict(path=str(p.resolve()),size=s.st_size,mtime_ns=s.st_mtime_ns)

def analyze(video,output,rois=None,selection=None,max_rois=7,preview_s=30,previous=None,progress=None):
 progress=progress or (lambda p,m:None);out=Path(output);out.mkdir(parents=True,exist_ok=False)
 info=probe(video,True);times=info.pop('timestamps');identity=video_identity(video);preview_s=max(0,min(float(preview_s),float(times[-1])-.05))
 if rois is None:rois=propose(video,selection,max_rois,preview_s)['rois']
 rois=normalize_rois(rois,info);progress(2,'检查实际计数框和缓存')
 _,samples=sample_frames(video,info,preview_s);old=None;arrays={};cached=[];recomputed=[]
 if previous and (Path(previous)/'raw.json').exists():
  old=json.loads((Path(previous)/'raw.json').read_text())
  if old.get('identity')!=identity or old.get('version')!=VERSION or old.get('engine_revision')!=ENGINE_REVISION:old=None
 trackers={};stats_list=[]
 old_np=np.load(Path(previous)/'raw_tracks.npz') if old else None
 for k,q in enumerate(rois):
  cache_index=next((j for j,p in enumerate(old['rois']) if all(q[z]==p[z] for z in ['id','x','y','w','h'])),None) if old else None
  if cache_index is not None:
   arrays[k]=np.column_stack([old_np[name][:,cache_index] for name in FIELDS]);cached.append(q['id']);stats_list.append(old['roi_diagnostics'][cache_index]);continue
  ps=[patch_of(a,q) for a in samples];ss=[spectrum(a) for a in ps];best=max(ss,key=lambda s:s['score'] if not s['reason'] else -1);trackers[k]=Tracker(ps[0],best);stats_list.append(ss);recomputed.append(q['id'])
 if old_np is not None:old_np.close()
 if trackers:
  # Decode each frame once; only compute changed ROIs. Original coordinate rectangles.
  p=subprocess.Popen([binary('ffmpeg'),'-v','error','-i',str(video),'-vf','format=gray','-fps_mode','passthrough','-f','rawvideo','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  rows={k:[] for k in trackers};near_repeats=[];previous_patches=None;nbytes=info['width']*info['height'];i=0
  try:
   while True:
    raw=p.stdout.read(nbytes)
    if not raw:break
    if len(raw)!=nbytes:raise ValueError('视频帧不完整。')
    frame=np.frombuffer(raw,np.uint8).reshape(info['height'],info['width'])
    patches=[patch_of(frame,q) for q in rois]
    near=False
    if previous_patches is not None:
     changes=[abs(x-y) for x,y in zip(patches,previous_patches)]
     near=all(np.mean(c)<.8 and np.percentile(c,90)<=2 for c in changes)
    near_repeats.append(near);previous_patches=patches
    for k,tracker in trackers.items():rows[k].append(tracker.push(patches[k]))
    i+=1
    if i%150==0:progress(min(90,5+85*i/len(times)),f'已解码 {i}/{len(times)} 帧；复算 {len(trackers)} 框，复用 {len(cached)} 框')
   if p.wait():raise ValueError(p.stderr.read().decode()[-600:])
  finally:
   if p.poll() is None:p.kill()
   p.stdout.close();p.stderr.close()
  if i!=len(times):raise ValueError('视频帧数与时间戳不一致。')
  for k in trackers:arrays[k]=np.asarray(rows[k])
 all_arrays={name:np.column_stack([arrays[k][:,j] for k in range(len(rois))]) for j,name in enumerate(FIELDS)}
 if trackers:all_arrays['frame_near_repeat']=np.asarray(near_repeats,bool)
 elif old:
  with np.load(Path(previous)/'raw_tracks.npz') as saved:
   if 'frame_near_repeat' in saved:all_arrays['frame_near_repeat']=saved['frame_near_repeat']
 all_arrays['reason']=all_arrays['reason'].astype(np.uint16);dt=np.diff(times);gaps=np.r_[False,dt>np.median(dt)*1.8];all_arrays['reason'][gaps]|=64
 all_arrays['reason'][0]=0;all_arrays['delta'][0]=0
 np.savez_compressed(out/'raw_tracks.npz',time=times,**all_arrays)
 centers=np.array([[q['x']+q['w']/2,q['y']+q['h']/2] for q in rois]);quality=np.mean(all_arrays['reason']==0,axis=0);scores=[np.median([s['score'] for s in rows]) for rows in stats_list];best=int(np.argmax(np.asarray(scores)*quality));reference=centers[best].tolist()
 if old and old.get('reference_point_px'):reference=old['reference_point_px']
 meta=dict(search_range=selection,version=VERSION,engine_revision=ENGINE_REVISION,identity=identity,video=info,rois=rois,roi_diagnostics=stats_list,reference_point_px=reference,frames_decoded=len(times),reference_frame_s=float(preview_s),cache=dict(reused=cached,recomputed=recomputed),reason_bits=REASONS,legacy=False,note='Image-coordinate signed phase; not calibrated displacement. Assumes less than half a fringe per usable frame. Raw tracking is immutable.')
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
  m=json.loads((folder/'raw.json').read_text());z=np.load(folder/'raw_tracks.npz');a={k:z[k].copy() for k in z.files};z.close();return m,a
 r=json.loads((folder/'result.json').read_text());z=np.load(folder/'tracks.npz');d=z['roi_delta'].copy();shape=d.shape
 rois=[dict(q,id=f'legacy-{i+1}',label=f'ROI {i+1}',color=PALETTE[i%len(PALETTE)],source='legacy') for i,q in enumerate(r['rois'])]
 a={name:np.zeros(shape) for name in FIELDS};a.update(time=z['time'].copy(),delta=d,reason=np.full(shape,128,np.uint16));a['reason'][0]=0
 for old,new in [('coherence','coherence'),('clipping','clipping'),('pixel_scatter','scatter')]:
  if old in z:a[new]=z[old].copy()
 z.close();m=dict(version=r.get('version','1.1'),video=r['video'],rois=rois,reference_point_px=r['reference_point_px'],frames_decoded=len(a['time']),reference_frame_s=r.get('reference_frame_s',30),legacy=True,reason_bits=REASONS)
 return m,a
