"""Optional model-conditional integer-branch diagnosis, never raw measurement repair.

An image measures phase modulo one cycle. A common integer in every ROI is
unobservable without a motion assumption. Consequently no output here promotes
the original accepted total. Existing valid increments are kept byte-for-byte.
"""
import numpy as np
from core import groups

WINDOWS = (.3, .6, 1.2, 2.)
LABELS = dict(observed='原始可读步长', spatial='空间关系支持（依赖锚点采样条件）',
              dense_spatial='密集空间复核支持（依赖锚点采样条件）', temporal='多窗口趋势一致（模型估计）', ambiguous='整数候选仍有歧义',
              missing='缺少可靠相位', blocked='用户排除，未补值')

def trend(t, fixed, known, i, window, phase):
    """Two-sided rate prediction. Never train on our temporal replacements."""
    dt = np.r_[np.median(np.diff(t)), np.diff(t)]
    left = np.flatnonzero(known & (t < t[i]) & (t >= t[i]-window))
    right = np.flatnonzero(known & (t > t[i]) & (t <= t[i]+window))
    if min(len(left), len(right)) < 3:
        return None
    # Held-looking frames and moving frames can alternate. For readable large
    # phases use the moving population, recording this explicit model choice.
    active = bool(np.isfinite(phase) and abs(phase) > .1)
    if active:
        ll = left[abs(fixed[left]) > .04]; rr = right[abs(fixed[right]) > .04]
        if min(len(ll), len(rr)) >= 3: left, right = ll, rr
        else: active = False
    lv = fixed[left] / dt[left] * dt[i]; rv = fixed[right] / dt[right] * dt[i]
    lp, rp = np.median(lv), np.median(rv)
    # These tolerances are diagnostics, not a statistical confidence interval.
    le = max(.10, float(np.percentile(abs(lv-lp), 90)))
    re = max(.10, float(np.percentile(abs(rv-rp), 90)))
    return dict(prediction=float((lp+rp)/2), left=float(lp), right=float(rp),
                left_spread=le, right_spread=re, active_population=active)

def candidates(phase, prediction):
    values = phase + np.arange(-2, 3)
    errors = abs(values-prediction['prediction'])
    best = int(np.argmin(errors))
    # Require each side separately to select the same branch, with tight
    # dispersion. A broad/noisy trend cannot become strong evidence.
    plausible = (abs(values-prediction['left']) <= prediction['left_spread']+.06) & (abs(values-prediction['right']) <= prediction['right_spread']+.06)
    tight = max(prediction['left_spread'], prediction['right_spread']) <= .20
    unique = bool(plausible.sum() == 1 and plausible[best] and tight and best not in (0,4))
    return values, best, unique

def edge_trend(t, fixed, known, i, window):
    """Explicit one-sided endpoint extrapolation, never qualifying evidence."""
    if t[i]-t[0] >= window and t[-1]-t[i] >= window:return None
    ix=np.flatnonzero(known & (abs(t-t[i])<=window) & (t!=t[i]))
    if len(ix)<3:return None
    dt=np.r_[np.median(np.diff(t)),np.diff(t)]
    value=float(np.median(fixed[ix]/dt[ix])*dt[i])
    return dict(prediction=value,left=value,right=value,left_spread=.5,right_spread=.5,
                active_population=False,one_sided_endpoint=True)

def recover(meta, a, base, valid, enabled, c, blocked):
    required = ['phase_slope_x', 'phase_slope_y', 'kx', 'ky', 'modulation']
    if not enabled:
        return dict(available=False, message='没有参与统计的区域，不能估计。')
    if any(key not in a for key in required):
        return dict(available=False, message='旧追踪缺少局部相位斜率，请重新分析视频。')
    if c.get('cleaning'):
        return dict(available=False, message='请先关闭清洗，再单独检查联合解缠估计。')
    t=a['time']; d=a['delta']; n,k=d.shape
    xy=np.array([[q['x']+q['w']/2,q['y']+q['h']/2] for q in meta['rois']])
    ref=np.array(c['reference_point_px']); span=max(np.ptp(xy,axis=0).max(),1)
    X=np.c_[np.ones(k),(xy-ref)/span]
    anchor=int(np.argmin(np.linalg.norm(xy-ref,axis=1)))
    exact=np.linalg.norm(xy[anchor]-ref)<=.5
    # Tracker slope is per reduced pixel, convert to original-pixel units.
    scale=np.array([[round(q[axis]*min(1.,192/max(q['w'],q['h'])))/q[axis]
                     for axis in ['w','h']] for q in meta['rois']])
    grad=np.stack([a['phase_slope_x'],a['phase_slope_y']],axis=-1)*scale[None,:,:]
    phase=np.full(n,np.nan); spatial=np.full(n,np.nan)
    category=np.where(valid,'observed','missing').astype(object)
    details={}; allowed=np.zeros(k,bool);allowed[enabled]=True
    entirely_blocked=np.all(blocked[:,enabled],axis=1)
    # Respect exclusion of the fixed reference, too. Do not extrapolate across
    # its explicitly excluded interval using other ROIs.
    if exact and anchor in enabled: entirely_blocked |= blocked[:,anchor]
    category[~valid & entirely_blocked]='blocked'
    from processing import within_hull
    for i in np.flatnonzero(~valid & ~entirely_blocked):
        good=((a['reason'][i].astype(int)&~16)==0)&np.isfinite(d[i])&allowed&~blocked[i]
        ks=np.c_[a['kx'][i],a['ky'][i]]
        # Use fixed-reference carrier for signed compatibility even when it is
        # temporarily unreadable; no unsigned direction averaging.
        align=ks@ks[anchor]/np.maximum(np.linalg.norm(ks,axis=1)*np.linalg.norm(ks[anchor]),1e-12)
        ids=np.flatnonzero(good&(align>.8))
        if exact and anchor in ids: phase[i]=d[i,anchor]
        if len(ids)<4 or np.linalg.matrix_rank(X[ids])<3 or np.linalg.cond(X[ids])>=80:continue
        if not within_hull(xy[ids],ref):continue
        g=grad[i,ids]
        if not np.isfinite(g).all():continue
        j=ids[np.argmax(a['modulation'][i,ids])]
        pred=d[i,j]+(xy[ids]-xy[j])@np.median(g,axis=0)
        integers=np.rint(pred-d[i,ids]).astype(int)
        lifted=d[i,ids]+integers
        b=np.linalg.lstsq(X[ids],lifted,rcond=None)[0]; residual=lifted-X[ids]@b
        # Check both between-ROI phases and independently measured local slopes.
        # A gradient mismatch of .25 cycle over the ROI span rejects this model.
        if max(abs(residual))>.06 or np.sqrt(np.mean(residual**2))>.025 or np.max(abs(g*span-b[1:]))>.25:continue
        # Require every local gradient to select the same relative branches.
        alternatives=np.rint(d[i,j]+(xy[ids]-xy[j])@g.T-d[i,ids,None]).astype(int)
        if not np.all(alternatives==integers[:,None]):continue
        if not np.isfinite(phase[i]):phase[i]=(b[0]+.5)%1-.5
        anchors=np.array([z for z,jj in enumerate(ids) if a['reason'][i,jj]==0 and abs(d[i,jj])<.30],int)
        votes=integers[anchors]
        details[int(i)]=dict(roi_ids=[meta['rois'][j]['id'] for j in ids],relative_integers=integers.tolist(),
                            spatial_residual_cycles=float(np.max(abs(residual))),anchor_votes=votes.tolist())
        if len(votes)>=2 and len(set(votes))==1:
            spatial[i]=b[0]-votes[0];category[i]='spatial'
    from spatial_recovery import eligible
    dense_rows=eligible(meta,c,enabled,blocked)
    for row in dense_rows:
        i=row['frame']
        if valid[i] or entirely_blocked[i] or category[i]=='spatial':continue
        spatial[i]=row['estimate'];phase[i]=(row['estimate']+.5)%1-.5
        category[i]='dense_spatial'
        details[int(i)]=dict(spatial_residual_cycles=max(q['spread'] for q in row['reference_variants']),
                            method='multiscale_local_graph',reference_variants=row['reference_variants'],
                            checks=row['evidence'],assumption='small-phase anchors do not share an integer alias')
    known=valid|np.isfinite(spatial);fixed=np.where(valid,base,spatial)
    phase[0]=0.; variants=np.tile(fixed,(len(WINDOWS),1)); choices={}
    for i in np.flatnonzero(~known & ~entirely_blocked):
        readable=np.isfinite(phase[i]); record=[]
        if readable:category[i]='ambiguous'
        for z,w in enumerate(WINDOWS):
            p=trend(t,fixed,known,i,w,phase[i]); narrow=p is not None
            if p is None:p=trend(t,fixed,known,i,max(3.,w),phase[i])
            if p is None:p=edge_trend(t,fixed,known,i,3.)
            if p is None:
                record.append(dict(window_s=w,value=None,unique=False));continue
            if readable:
                vals,best,unique=candidates(phase[i],p)
                # Search boundary means our finite search is inadequate: no total.
                value=float(vals[best]) if best not in (0,4) else np.nan
                integer=best-2
            else:value=p['prediction'];integer=None;unique=False
            variants[z,i]=value
            record.append(dict(window_s=w,value=float(value),integer=integer,unique=bool(unique and narrow),
                               fallback_window=not narrow,**p))
        choices[int(i)]=record
        # Require at least three window sizes to give tight two-sided support,
        # with the fourth selecting the same integer. The windows overlap and
        # are NOT independent evidence or a probability estimate. This
        # still depends on continuity; it is not promoted to observed validity.
        if readable and sum(q['unique'] for q in record)>=3 and all('integer' in q for q in record) and len({q['integer'] for q in record})==1:
            category[i]='temporal'
    selected=(t>c['start']+1e-6)&(t<=c['end']+1e-6)
    # Exactly match summarize's frame-index convention for fractional bounds.
    lo=max(0,int(np.searchsorted(t,c['start']-1e-6)));hi=min(n-1,int(np.searchsorted(t,c['end']+1e-6,side='right')-1))
    selected[:]=False;selected[lo+1:hi+1]=True
    sign=c['sign']; summaries=[]
    for z,w in enumerate(WINDOWS):
        v=variants[z,selected]*sign;complete=np.isfinite(v).all()
        summaries.append(dict(window_s=w,net_cycles=float(v.sum()) if complete else None,
                              missing_steps=int((~np.isfinite(v)).sum())))
    nets=[s['net_cycles'] for s in summaries if s['net_cycles'] is not None]
    chosen=WINDOWS.index(float(c.get('recovery_window',.6)))
    output=variants[chosen];supported=known|(category=='temporal')
    counts={key:int(np.sum(selected&(category==key))) for key in LABELS}
    rows=[]
    for i in np.flatnonzero(selected & ~valid):
        rows.append(dict(frame=int(i),time_s=float(t[i]),category=str(category[i]),label=LABELS[category[i]],
                         wrapped_reference_phase_cycles=float(phase[i])*sign,estimate_cycles=float(output[i])*sign,
                         original_conditional_delta=float(base[i])*sign,spatial=details.get(int(i)),
                         candidates=[float(x)*sign for x in phase[i]+np.arange(-2,3)] if np.isfinite(phase[i]) else [],
                         windows=[dict(q,value=q['value']*sign if q['value'] is not None else None,
                                       integer=q.get('integer')*sign if q.get('integer') is not None else None,
                                       **{key:q[key]*sign for key in ['prediction','left','right'] if key in q}) for q in choices.get(int(i),[])]))
    events=[]
    for l,h in groups(selected&~valid):
        vv=variants[:,l:h]*sign
        totals=[float(v.sum()) if np.isfinite(v).all() else None for v in vv]
        events.append(dict(first_frame=int(l),last_frame=int(h-1),start_s=float(t[l-1]),end_s=float(t[h-1]),
                           steps=h-l,still_ambiguous=int(np.sum(~supported[l:h])),model_nets=totals,
                           missing_phase_steps=int(np.sum(category[l:h]=='missing'))))
    net=summaries[chosen]['net_cycles']
    return dict(available=True,method_version='1.6.0-dense-spatial-1',window_s=WINDOWS[chosen],
                display_sign=sign,spatial_integer_orientation='raw_tracking',
                counts=counts,remaining_ambiguous_steps=int(np.sum(selected&~supported)),
                original_unresolved_steps=int(np.sum(selected&~valid)),
                estimated_net_cycles=net,accepted_net_cycles=None,
                positive_cycles=float(np.sum(output[selected][output[selected]*sign>0])*sign) if np.isfinite(output[selected]).all() else None,
                negative_cycles=float(np.sum(output[selected][output[selected]*sign<0])*sign) if np.isfinite(output[selected]).all() else None,
                dense_evidence_available=bool(meta.get('spatial_evidence')),dense_evidence_applied=len(dense_rows),
                sensitivity_models=summaries,sensitivity_range=[min(nets),max(nets)] if nets else None,
                delta=output,valid=np.isfinite(output),supported=supported,category=category,
                estimated=~valid,records=rows,events=events,
                note='模型估计，不能排除共同漏整条或扰动中的真实位移。候选搜索为每步 ±2 条；窗口范围不是误差条或真值上下界。无相位区间按相邻趋势插值；片头片尾必要时单侧外推并记录。原始已通过步长仍依赖采样假设。')
