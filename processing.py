"""Pure, reproducible post-processing. Raw measurements never overwritten."""
from pathlib import Path
from itertools import combinations
import csv, json, uuid, time
import numpy as np
from core import clean_json,dump,groups,REASONS,VERSION,ENGINE_REVISION

def default_config(meta):
 return dict(enabled=[q['id'] for q in meta['rois']],visible=[q['id'] for q in meta['rois']],exclusion_mode='suggest',applied=[],rejected=[],cleaning=False,stitches=[],reference_point_px=meta['reference_point_px'],start=0,end=None,sign=1,smooth_display=False,show_conditional=False,show_mean=True,show_original=True,direct_reference=True,local_reference=True,joint_recovery=True,recovery_window=.6)

def checked_config(meta,config,t):
 c=default_config(meta);c.update(config or {});ids={q['id'] for q in meta['rois']}
 for field in ['enabled','visible']:
  if not isinstance(c[field],list) or len(c[field])!=len(set(c[field])) or not set(c[field])<=ids:raise ValueError('区域开关包含不存在或重复的 ID。')
 if c['exclusion_mode'] not in ['off','suggest','auto'] or c['sign'] not in [-1,1]:raise ValueError('处理设置无效。')
 ref=np.array(c['reference_point_px'],float)
 if ref.shape!=(2,) or not np.isfinite(ref).all():raise ValueError('参考点无效。')
 c['start']=float(c['start']);c['end']=float(t[-1]) if c['end'] is None else float(c['end'])
 if not np.isfinite([c['start'],c['end']]).all() or c['start']<0 or c['end']<=c['start'] or c['end']>t[-1]+1e-5:raise ValueError('时间范围无效。')
 if c['recovery_window'] not in [.3,.6,1.2,2.]:raise ValueError('趋势窗口无效。')
 if not isinstance(c['joint_recovery'],bool):raise ValueError('联合解缠开关无效。')
 if len(c['stitches'])>30:raise ValueError('拼接事件过多。')
 return c

def spans(t,mask):
 return [dict(start_s=float(t[max(0,a-1)]),end_s=float(t[b-1]),first_frame=int(a),last_frame=int(b-1)) for a,b in groups(mask)]

def windows(t):
 for seconds in [1.,3.]:
  for start in np.arange(t[0],t[-1]-seconds,.5):
   ix=np.flatnonzero((t>=start)&(t<=start+seconds))
   if len(ix)>3:yield ix

def diagnose(meta,a):
 t=a['time'];d=a['delta'];r=a['reason'];n,k=d.shape;suggestions=[];valid=(r==0)&np.isfinite(d);bad=~valid
 for j,q in enumerate(meta['rois']):
  fraction=float(np.mean(bad[1:,j]));severe=np.mean((r[1:,j]&7)!=0)
  if severe>.65:
   suggestions.append(dict(id=f'global:{q["id"]}',roi_id=q['id'],kind='global',confidence='high',reason='超过 65% 帧过暗、过曝或周期结构不清',bad_fraction=fraction))
  else:
   for s in spans(t,bad[:,j]):
    suggestions.append(dict(id=f'local:{q["id"]}:{s["first_frame"]}:{s["last_frame"]}',roi_id=q['id'],kind='interval',confidence='high',reason='此段原始相位质量未通过；恢复后需重新连接',**s))
 # Compare windowed increments, not cumulative offsets after an interruption.
 discrepancy=np.zeros_like(valid);observed=np.zeros(k);outlying=np.zeros(k)
 if k>=3:
  for ix in windows(t):
   ok=np.mean(valid[ix],axis=0)>.95;count=np.sum(np.where(valid[ix],d[ix],0),axis=0)
   if np.sum(ok)<3:continue
   vals=count[ok];center=np.median(vals);mad=np.median(abs(vals-center));tol=max(.12,5*1.4826*mad)
   near=ok&(abs(count-center)<=tol)
   if np.sum(near)<3 or np.sum(near)<.6*np.sum(ok):continue
   # Real spatial gradients can explain different increments: flag as a suggestion,
   # not a high-confidence deletion when the raw signal is otherwise good.
   suspect=ok&~near;observed+=ok;outlying+=suspect;discrepancy[np.ix_(ix,np.flatnonzero(suspect))]=True
  for j,q in enumerate(meta['rois']):
   if outlying[j] and outlying[j]/max(observed[j],1)>.5:
    suggestions.append(dict(id=f'trend:{q["id"]}',roi_id=q['id'],kind='global',confidence='review',reason='多个时间窗与主要趋势分离；需检查空间倾斜，不能仅凭变化少删除',bad_fraction=float(outlying[j]/max(observed[j],1))))
   elif np.any(discrepancy[:,j]):
    for s in spans(t,discrepancy[:,j]):suggestions.append(dict(id=f'trend:{q["id"]}:{s["first_frame"]}',roi_id=q['id'],kind='interval',confidence='review',reason='局部时间窗趋势分歧',**s))
 # Temporal events: structure changes, rapid motion, and multi-region loss.
 event=(np.sum((r&(8|16|32|64))!=0,axis=1)>=max(1,int(np.ceil(k*.4))))
 event|=np.mean(~valid,axis=1)>.6
 # Merge small gaps and require an event to last at least two frames.
 fps=1/max(np.median(np.diff(t)),1e-9);radius=max(1,int(.20*fps));merged=event.copy()
 for first,last in groups(event):merged[max(1,first-radius):min(n,last+radius)]=True
 events=[]
 for s in spans(t,merged):
  if s['last_frame']-s['first_frame']<2:continue
  s.update(id=f'event:{s["first_frame"]}:{s["last_frame"]}',reason='相位失锁/速度风险/结构变化；不等于已证实桌面抖动',pre_window_s=3.,post_window_s=3.);events.append(s)
 return suggestions,events

def segmented_curve(d,valid):
 curve=np.full(len(d),np.nan);segment=np.full(len(d),-1,int);sid=-1;value=0.;previous=False
 for i in range(len(d)):
  if i==0:curve[i]=0.;segment[i]=0;sid=0;previous=True;continue
  if not valid[i] or not np.isfinite(d[i]):previous=False;continue
  if not previous:sid+=1;value=0.
  else:value+=d[i]
  curve[i]=value;segment[i]=sid;previous=True
 return curve,segment

def summarize(t,d,valid,start,end,sign=1,estimated=None):
 a=max(0,int(np.searchsorted(t,start-1e-6)));b=min(len(t)-1,int(np.searchsorted(t,end+1e-6,side='right')-1))
 if b<=a:raise ValueError('时间区间至少包含两个视频帧。')
 steps=d[a+1:b+1]*sign;ok=valid[a+1:b+1]&np.isfinite(steps);finite=np.isfinite(steps)
 conditional=float(np.sum(steps[finite])) if finite.any() else None
 estimate=bool(np.any(estimated[a+1:b+1])) if estimated is not None else False
 return dict(start_s=float(t[a]),end_s=float(t[b]),conditional_net_cycles=conditional,accepted_net_cycles=conditional if ok.all() and not estimate else None,positive_cycles=float(np.sum(steps[finite&(steps>0)])) if finite.any() else None,negative_cycles=float(np.sum(steps[finite&(steps<0)])) if finite.any() else None,unresolved_steps=int((~ok).sum()),total_steps=len(steps),qualified_net_cycles=float(np.sum(steps[ok])) if ok.any() else None,excluded_finite_steps=int((finite&~ok).sum()),estimated=estimate,status='trend_estimate' if estimate else ('continuous_under_sampling_assumption' if ok.all() else 'ambiguous_total'),note='包含断点时条件和不是完整总数；正负方向未标定为物理位移。')

def within_hull(points,p):
 # Membership by triangles (small ROI sets, numpy only).
 if len(points)<3:return False
 for ids in combinations(range(len(points)),3):
  q=points[list(ids)];mat=np.vstack([q.T,np.ones(3)])
  if abs(np.linalg.det(mat))<1e-9:continue
  w=np.linalg.solve(mat,np.r_[p,1.])
  if np.min(w)>=-1e-6:return True
 return False

def robust_fuse(meta,a,d,valid,enabled,reference,direct_reference=True,local_reference=True):
 n,k=d.shape;out=np.full(n,np.nan);good=np.zeros(n,bool);reason=np.full(n,'无可用测量',object);used=np.zeros(n,int)
 if not enabled:return out,good,reason,used
 centers=np.array([[q['x']+q['w']/2,q['y']+q['h']/2] for q in meta['rois']]);ref=np.asarray(reference);scale=max(np.ptp(centers,axis=0).max(),1);design=np.c_[np.ones(k),(centers-ref)/scale]
 weights=np.clip(a.get('modulation',np.ones_like(d)*8),1,30)*np.clip(a['coherence'],0,1)**2
 hull_cache={}
 anchor=int(np.argmin(np.linalg.norm(centers-ref,axis=1)))
 exact_anchor=np.linalg.norm(centers[anchor]-ref)<=.5
 def direct(i,ids,spatial_conflict=False):
  if direct_reference and exact_anchor and anchor in ids and abs(d[i,anchor])<=.38:
   if spatial_conflict and (not local_reference or 'local_verified' not in a or a['local_verified'][i,anchor]!=1 or abs(d[i,anchor]-a['delta'][i,anchor])>1e-12 or abs(d[i,anchor])>.35):return False
   out[i]=d[i,anchor];good[i]=True;reason[i]='参考点局部复核通过；空间模型不适用' if spatial_conflict else '参考点直接测量；多框支持不足';used[i]=1;return True
  return False
 for i in range(1,n):
  ids=np.array([j for j in enabled if valid[i,j] and np.isfinite(d[i,j])],int)
  if 'kx' in a and len(enabled)>1:
   ks=np.c_[a['kx'][i],a['ky'][i]];ka=ks[anchor];alignment=(ks@ka)/np.maximum(np.linalg.norm(ks,axis=1)*np.linalg.norm(ka),1e-12)
   ids=ids[alignment[ids]>.80]  # only compatible signed local carriers
  used[i]=len(ids)
  if not len(ids):continue
  vals=d[i,ids];w=weights[i,ids];w=np.minimum(w,max(np.median(w)*2,1))
  if len(enabled)==1:
   out[i]=vals[0];good[i]=True;reason[i]='单框结果，未经多框校验';continue
  if len(ids)<3:
   if not direct(i,ids):reason[i]='少于三个有效区域'
   continue
  # A fixed reference is retained, no extrapolation outside available support.
  key=tuple(ids)
  if key not in hull_cache:hull_cache[key]=within_hull(centers[ids],ref)
  if not hull_cache[key]:
   if not direct(i,ids):reason[i]='参考位置缺少有效区域包围'
   continue
  x=design[ids];beta=None
  if len(ids)>=4 and np.linalg.matrix_rank(x)==3 and np.linalg.cond(x)<80:
   ww=w.copy()
   for _ in range(4):
    beta=np.linalg.lstsq(x*np.sqrt(ww[:,None]),vals*np.sqrt(ww),rcond=None)[0];res=vals-x@beta;s=max(.003,1.4826*np.median(abs(res-np.median(res))));ww=w*np.minimum(1,1.5*s/np.maximum(abs(res),1e-9))
   residual=vals-x@beta
   if np.max(abs(residual))>.08 or np.sqrt(np.average(residual**2,weights=ww))>.025:
    if not direct(i,ids,True):reason[i]='空间拟合残差过大'
    continue
   out[i]=float(beta[0]);good[i]=True;reason[i]='稳健空间融合'
  else:
   # No fitted slope when the geometry is rank deficient: only admit agreement.
   med=np.median(vals)
   if np.max(abs(vals-med))>.012:
    if not direct(i,ids):reason[i]='几何不足且区域变化分歧'
    continue
   out[i]=float(med);good[i]=True;reason[i]='一致增量融合（近似共同相位）'
  if abs(out[i])>.38:good[i]=False;reason[i]='融合步长接近半条'
 out[0]=0.;good[0]=True;reason[0]='起点';return out,good,reason,used

def conservative_repair(meta,a,d,valid,enabled):
 fixed=d.copy();ok=valid.copy();records=[];t=a['time'];n,k=d.shape;fps=1/np.median(np.diff(t))
 for j in enabled:
  for start,end in groups(~valid[:,j]):
   if start<2 or end>=n-2 or end-start>max(1,int(.12*fps)):continue
   # Never bridge global motion/structure changes/aliasing by assuming continuity.
   if np.any(a['reason'][start:end,j]&(16|32|64|128)):continue
   before=np.arange(max(1,start-int(fps)),start);after=np.arange(end,min(n,end+int(fps)));around=np.r_[before,after]
   donors=[q for q in enabled if q!=j and np.all(valid[start:end,q]) and np.mean(valid[around,q]&valid[around,j])>.95]
   if len(donors)<3:continue
   donor=np.median(d[np.ix_(np.arange(n),donors)],axis=1)
   # Verify both nontrivial motion excitation and stable pairwise mapping.
   good=valid[around,j]&np.all(valid[np.ix_(around,donors)],axis=1);ix=around[good]
   if len(ix)<15 or np.std(donor[ix])<.005:continue
   residual=d[ix,j]-donor[ix]
   if np.max(abs(residual))>.025 or abs(np.mean(residual))>.002:continue
   if np.max(np.ptp(d[start:end][:,donors],axis=1))>.025:continue
   # Integer ambiguity remains whenever any credible channel nears half-cycle.
   if np.max(abs(d[start:end][:,donors]))>.2:continue
   fixed[start:end,j]=donor[start:end];ok[start:end,j]=True
   records.append(dict(roi_id=meta['rois'][j]['id'],start_s=float(t[start-1]),end_s=float(t[end-1]),kind='redundant_channel_estimate',donor_ids=[meta['rois'][q]['id'] for q in donors],note='短失锁的冗余通道估计；采样及稳定映射假设仍适用，不视作原始观测。'))
 return fixed,ok,records

def stitch(d,valid,t,spec):
 start=float(spec['start_s']);end=float(spec['end_s']);pre=float(spec.get('pre_window_s',3));post=float(spec.get('post_window_s',3))
 if not np.isfinite([start,end,pre,post]).all() or not 0<=start<end<=t[-1] or min(pre,post)<.5:raise ValueError('拼接区间或稳定窗口无效。')
 left=np.flatnonzero((t>=start-pre)&(t<start));right=np.flatnonzero((t>end)&(t<=end+post));mid=np.flatnonzero((t>=start)&(t<=end));out=d.copy();ok=valid.copy();estimated=np.zeros_like(valid);records=[]
 for j in range(d.shape[1]):
  # Window must exist in full; no automatic fallback to a less stringent window.
  if start-pre<0 or end+post>t[-1] or len(left)<10 or len(right)<10 or not len(mid):continue
  if not np.all(valid[left,j]) or not np.all(valid[right,j]):continue
  rates=[];stable=True
  for ix in [left,right]:
   local=np.cumsum(d[ix,j]);coef=np.polyfit(t[ix]-t[ix[0]],local,1);res=local-np.polyval(coef,t[ix]-t[ix[0]])
   if np.percentile(abs(res),95)>.1:stable=False
   rates.append(float(coef[0]))
  if not stable:continue
  speed=np.linspace(rates[0],rates[1],len(mid));replacement=speed*np.r_[np.median(np.diff(t)),np.diff(t)][mid]
  old=d[mid,j];was_missing=not valid[mid,j].all() or not np.isfinite(old).all();change=float(replacement.sum()-np.nansum(old))
  out[mid,j]=replacement;ok[mid,j]=True;estimated[mid,j]=True
  records.append(dict(roi_index=j,start_s=start,end_s=end,kind='trend_stitch',relative_to_conditional_sum_cycles=change,had_missing_steps=was_missing,net_inserted_cycles=float(replacement.sum()),pre_rate=rates[0],post_rate=rates[1],note='假设扰动区间内延续邻近缓慢趋势；调整量相对于原始条件和，不是恢复丢失条数。'))
 if not records:raise ValueError('前后窗口不足或不稳定，不能生成拼接估计。请检查边界/窗口；不能强行拉齐。')
 return out,ok,estimated,records

def derive(meta,a,config=None):
 t=a['time'];c=checked_config(meta,config,t);ids=[q['id'] for q in meta['rois']];enabled=[i for i,x in enumerate(ids) if x in c['enabled']]
 suggestions,events=diagnose(meta,a);d=a['delta'].copy();base_valid=(a['reason']==0)&np.isfinite(d);mask=base_valid.copy();blocked=np.zeros_like(mask);applied=set(c['applied']);rejected=set(c['rejected'])
 if c['exclusion_mode']=='auto':applied|={s['id'] for s in suggestions if s['confidence']=='high' and s['id'] not in rejected}
 applied-=rejected
 if c['exclusion_mode']!='off':
  for s in suggestions:
   if s['id'] not in applied:continue
   j=ids.index(s['roi_id'])
   if s['kind']=='global':
    mask[:,j]=False;blocked[:,j]=True
    if j in enabled:enabled.remove(j)
   else:
    region=(t>s['start_s'])&(t<=s['end_s']);mask[region,j]=False;blocked[region,j]=True
 raw_fused,raw_good,raw_reason,raw_used=robust_fuse(meta,a,d,mask,enabled,c['reference_point_px'],c['direct_reference'],c['local_reference'])
 changes=[];estimated=np.zeros_like(mask);explicitly_excluded=blocked
 if c['cleaning']:
  d,mask,repairs=conservative_repair(meta,a,d,mask,enabled);mask[explicitly_excluded]=False;d[blocked]=a['delta'][blocked];repairs=[rec for rec in repairs if not np.any(blocked[(t>rec['start_s'])&(t<=rec['end_s']),ids.index(rec['roi_id'])])];changes+=repairs
  for rec in repairs:
   j=ids.index(rec['roi_id']);estimated[(t>rec['start_s'])&(t<=rec['end_s']),j]=True
  previous_end=-1
  for spec in sorted(c['stitches'],key=lambda s:s['start_s']):
   if spec['start_s']<=previous_end:raise ValueError('拼接区间不可重叠。')
   d,mask,est,recs=stitch(d,mask,t,spec);mask[explicitly_excluded]=False;d[blocked]=a['delta'][blocked];est[blocked]=False;estimated|=est;changes+=recs;previous_end=spec['end_s']
 fused,good,why,used=robust_fuse(meta,a,d,mask,enabled,c['reference_point_px'],c['direct_reference'],c['local_reference'])
 mean=np.full(len(t),np.nan);mean_good=np.zeros(len(t),bool)
 if enabled:
  mean=np.mean(d[:,enabled],axis=1);mean_good=np.all(mask[:,enabled],axis=1)&np.isfinite(mean)
 est_any=np.any(estimated[:,enabled],axis=1) if enabled else np.zeros(len(t),bool)
 raw_summary=summarize(t,raw_fused,raw_good,c['start'],c['end'],c['sign']);summary=summarize(t,fused,good,c['start'],c['end'],c['sign'],est_any)
 # Even a patched small interval is not promoted to a verified original total.
 if changes:summary['accepted_net_cycles']=None
 curve,segments=segmented_curve(fused,good);raw_curve,raw_segments=segmented_curve(raw_fused,raw_good);mc,ms=segmented_curve(mean,mean_good)
 roi_reports=[]
 for j,q in enumerate(meta['rois']):
  cur,seg=segmented_curve(d[:,j],mask[:,j]);rc,rs=segmented_curve(a['delta'][:,j],base_valid[:,j]);s=summarize(t,d[:,j],mask[:,j],c['start'],c['end'],c['sign'],estimated[:,j]);ori=summarize(t,a['delta'][:,j],base_valid[:,j],c['start'],c['end'],c['sign'])
  roi_reports.append(dict(**q,enabled=q['id'] in c['enabled'],effective=j in enabled,visible=q['id'] in c['visible'],summary=s,raw_summary=ori,valid_fraction=float(np.mean(mask[1:,j])),curve=cur,segments=seg,raw_curve=rc,raw_segments=rs,conditional_curve=np.cumsum(np.nan_to_num(d[:,j])),raw_conditional_curve=np.cumsum(np.nan_to_num(a['delta'][:,j])),delta=d[:,j],raw_delta=a['delta'][:,j],valid=mask[:,j],raw_valid=base_valid[:,j],estimated=estimated[:,j],quality_reason=a['reason'][:,j],quality_summary=[label for bit,label in REASONS.items() if np.any((a['reason'][1:,j]&bit)!=0)]))
 adjustment=None if summary['conditional_net_cycles'] is None or raw_summary['conditional_net_cycles'] is None else summary['conditional_net_cycles']-raw_summary['conditional_net_cycles']
 actual_applied=sorted(applied-rejected) if c['exclusion_mode']!='off' else []
 audit=tracking_audit(meta,a,fused,good,why,used,c,estimated)

 recovery=None
 if c['joint_recovery']:
  from recovery import recover
  recovery=recover(meta,a,raw_fused,raw_good,enabled,c,blocked)
 primary=dict(mode='observed' if summary['accepted_net_cycles'] is not None else 'unavailable',net_cycles=summary['accepted_net_cycles'],positive_cycles=summary['positive_cycles'],negative_cycles=summary['negative_cycles'],label='稳健融合 · 连续可读净变化')
 if recovery and recovery.get('available') and summary['accepted_net_cycles'] is None and recovery.get('estimated_net_cycles') is not None:
  primary=dict(mode='conditional_model',net_cycles=recovery['estimated_net_cycles'],positive_cycles=recovery['positive_cycles'],negative_cycles=recovery['negative_cycles'],label='稳健融合 + 断点估计 · 条件净变化',remaining_ambiguous_steps=recovery['remaining_ambiguous_steps'],sensitivity_range=recovery['sensitivity_range'])
 if primary['mode']=='unavailable':primary['positive_cycles']=primary['negative_cycles']=None
 return clean_json(dict(version=VERSION,analysis_mode=meta.get('analysis_mode'),performance=meta.get('performance',{}),timing=meta.get('timing',{}),primary=primary,recovery=recovery,search_range=meta.get('search_range'),legacy=meta.get('legacy',False),video=meta['video'],audit=audit,reference_point_px=c['reference_point_px'],config=c,time=t,summary=summary,raw_summary=raw_summary,mean_summary=summarize(t,mean,mean_good,c['start'],c['end'],c['sign'],est_any),track=dict(delta=fused,valid=good,curve=curve,segments=segments,conditional_curve=np.cumsum(np.nan_to_num(fused)),reason=why,used=used,estimated=est_any,raw_delta=raw_fused,raw_valid=raw_good,raw_curve=raw_curve,raw_segments=raw_segments,raw_conditional_curve=np.cumsum(np.nan_to_num(raw_fused)),mean=mean,mean_valid=mean_good,mean_curve=mc,mean_segments=ms),adjustment_cycles=adjustment,rois=roi_reports,suggestions=suggestions,events=events,applied=actual_applied,changes=changes,note='断点后各段从局部零点显示。条件轨迹只用于诊断，不能跨断点确定整条计数。无质量报警不等于准确度已验证。'))

def tracking_audit(meta,a,d,good,why,used,c,estimated):
 """Explain missing steps; report continuous segments without bridging gaps."""
 t=a['time'];selected=(t>c['start'])&(t<=c['end']);bad=selected&~good
 reasons={str(k):int(np.sum(bad&(why==k))) for k in sorted(set(why[bad]))}
 intervals=[]
 for lo,hi in groups(bad):
  items={str(k):int(np.sum(why[lo:hi]==k)) for k in set(why[lo:hi])}
  intervals.append(dict(start_s=float(t[lo-1]),end_s=float(t[hi-1]),first_frame=int(lo),last_frame=int(hi-1),steps=hi-lo,reasons=items))
 # Sum ALL valid increments of a run, including its first one. The graph
 # resets local zero visually; that must not discard the first measured step.
 runs=[]
 for lo,hi in groups(selected&good):
  if hi-lo<2:continue
  runs.append(dict(start_s=float(t[max(0,lo-1)]),end_s=float(t[hi-1]),steps=hi-lo,net_cycles=float(np.sum(d[lo:hi])*c['sign']),duration_s=float(t[hi-1]-t[max(0,lo-1)])))
 runs.sort(key=lambda q:q['duration_s'],reverse=True)
 ids=[j for j,q in enumerate(meta['rois']) if q['id'] in c['enabled']]
 near=0;weak=0;loss=0;repeated=None
 if ids:
  rr=a['reason'][:,ids];near=int(np.sum(selected&np.any((rr&16)!=0,axis=1)));weak=int(np.sum(selected&np.any((rr&7)!=0,axis=1)));loss=int(np.sum(selected&np.any((rr&(8|32|64))!=0,axis=1)))
 if 'frame_near_repeat' in a:
  repeated=int(np.sum(selected&a['frame_near_repeat'].astype(bool)))
 return dict(reason_counts=reasons,unresolved_intervals=intervals,continuous_intervals=runs,direct_reference_steps=int(np.sum(selected&(why=='参考点直接测量；多框支持不足'))),local_reference_steps=int(np.sum(selected&(why=='参考点局部复核通过；空间模型不适用'))),filter_refreshes=int(np.sum(a.get('carrier_refresh',np.zeros_like(a['delta']))[selected])),near_half_steps=near,weak_signal_steps=weak,tracking_loss_steps=loss,near_repeat_steps=repeated,engine_revision=meta.get('engine_revision'),old_engine=meta.get('engine_revision')!=ENGINE_REVISION,note='质量类别可重叠；近似重复画面不证明丢帧或原始相机帧率。所有连续计数仍以有效图像之间真实变化小于半条为条件。')

def save_revision(folder,report,action='recompute'):
 folder=Path(folder);rid=time.strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:6];dest=folder/'revisions'/rid;dest.mkdir(parents=True)
 dump(dest/'recovery.json',report.get('recovery'));dump(dest/'primary_summary.json',report.get('primary'))
 with (dest/'recovery_steps.csv').open('w',newline='',encoding='utf-8-sig') as file:
  columns=['frame','time_s','category','label','wrapped_reference_phase_cycles','estimate_cycles','original_conditional_delta','spatial','candidates','windows']
  writer=csv.DictWriter(file,fieldnames=columns);writer.writeheader()
  for row in (report.get('recovery') or {}).get('records',[]):
   writer.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in row.items()})
 dump(dest/'diagnostics.json',report.get('audit',{}))
 for name,key in [('unresolved_intervals','unresolved_intervals'),('continuous_intervals','continuous_intervals')]:
  rows=report.get('audit',{}).get(key,[])
  columns=['start_s','end_s','first_frame','last_frame','steps','net_cycles','duration_s','reasons']
  with (dest/(name+'.csv')).open('w',newline='',encoding='utf-8-sig') as file:
   w=csv.DictWriter(file,fieldnames=columns);w.writeheader()
   for row in rows:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,dict) else v for k,v in row.items()})
 dump(dest/'result.json',report);dump(dest/'config.json',dict(report['config'],rois=[{k:q[k] for k in ['id','label','x','y','w','h','color','source']} for q in report['rois']]));dump(dest/'operations.json',dict(action=action,created_at=time.strftime('%Y-%m-%d %H:%M:%S'),applied=report['applied'],changes=report['changes'],config=report['config']))
 t=report['time'];tr=report['track'];rois=report['rois'];sign=report['config']['sign']
 selected_lo=max(0,int(np.searchsorted(t,report['config']['start']-1e-6)));selected_hi=min(len(t)-1,int(np.searchsorted(t,report['config']['end']+1e-6,side='right')-1))
 signed=lambda v:None if v is None else v*sign
 with (dest/'fringe_counts.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.writer(f);w.writerow(['frame','time_s','in_selected_interval','display_sign','raw_fused_delta','raw_valid','processed_delta','processed_valid','estimated','conditional_sum','segment','segment_curve','mean_delta','mean_valid','primary_delta','primary_valid','primary_mode','recovery_category']+[f'{q["id"]}_{key}' for q in rois for key in ['raw_delta','delta','valid','estimated']])
  rec=report.get('recovery') or {};primary=report.get('primary',{});use_model=primary.get('mode')=='conditional_model';pd=rec.get('delta') if use_model else tr['delta'];pv=rec.get('valid') if use_model else tr['valid']
  for i,sec in enumerate(t):w.writerow([i,sec,selected_lo<i<=selected_hi,sign,signed(tr['raw_delta'][i]),tr['raw_valid'][i],signed(tr['delta'][i]),tr['valid'][i],tr['estimated'][i],signed(tr['conditional_curve'][i]),tr['segments'][i],signed(tr['curve'][i]),signed(tr['mean'][i]),tr['mean_valid'][i],signed(pd[i]),pv[i],primary.get('mode'),(rec.get('category') or ['']*len(t))[i]]+[signed(q[key][i]) if key in ['raw_delta','delta'] else q[key][i] for q in rois for key in ['raw_delta','delta','valid','estimated']])
 dump(folder/'session.json',dict(latest_revision=rid,config=report['config']));return rid
