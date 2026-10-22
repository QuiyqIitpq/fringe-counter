"""Exact parallel ROI tracking: all frames, same rectangles and phase checks.

The producer decodes once. Workers keep each ROI's temporal state in order.
Temporary byte maps are only a transport; no pixel quantization is introduced
because input / BOX-reduced patches in core are already uint8-valued.
"""
from pathlib import Path
import multiprocessing as mp
import time,subprocess,traceback,shutil
import numpy as np

def worker(index,path,out,shape,initial_stats,ready,done,progress,errors):
 try:
  from core import Tracker
  frames=np.memmap(path,dtype=np.uint8,mode='r',shape=shape)
  tr=Tracker(np.zeros(shape[1:]),initial_stats);rows=np.empty((shape[0],17),float);i=0
  while i<shape[0]:
   upto=ready.value
   if upto<=i:
    if done.value:break
    time.sleep(.005);continue
   while i<upto:
    rows[i]=tr.push(np.asarray(frames[i],float));i+=1
    if i%64==0:progress[index]=i
   progress[index]=i
  if i!=shape[0]:raise ValueError(f'Incomplete decoded input: {i}/{shape[0]}')
  np.save(out,rows)
 except BaseException:errors.put((index,traceback.format_exc()));raise

def track(video,info,rois,initial_stats,progress_callback,folder,workers=5):
 from core import patch_of,binary
 if not rois or workers<1:raise ValueError('至少需要一个计数框和一个工作进程')
 n=info['frame_count'];shapes=[];maps=[];processes=[];start=time.perf_counter()
 temp=Path(folder)/'.tracking_tmp';temp.mkdir()
 needed=sum(n*max(1,round(q['h']*min(1.,192/max(q['w'],q['h']))))*max(1,round(q['w']*min(1.,192/max(q['w'],q['h'])))) for q in rois)
 if shutil.disk_usage(temp).free<needed+256*1024**2:
  temp.rmdir();raise ValueError(f'临时追踪缓存约需 {needed/1024**3:.1f} GB，请释放空间或减少框数。完成后缓存会自动删除。')
 ctx=mp.get_context('spawn');ready=ctx.Value('i',0);done=ctx.Value('b',False);progress=ctx.Array('i',len(rois));errors=ctx.Queue()
 try:
  for j,q in enumerate(rois):
   scale=min(1.,192/max(q['w'],q['h']));shape=(n,max(1,round(q['h']*scale)),max(1,round(q['w']*scale)));shapes.append(shape)
   path=temp/f'roi{j}.bin';maps.append(np.memmap(path,dtype=np.uint8,mode='w+',shape=shape))
  # Bound concurrent processes; batches read the same maps, no extra video decode.
  def launch(j):
   p=ctx.Process(target=worker,args=(j,str(temp/f'roi{j}.bin'),str(temp/f'roi{j}.npy'),shapes[j],initial_stats[j],ready,done,progress,errors));p.start();processes.append((j,p))
  pending=list(range(len(rois)));active=[]
  while pending and len(active)<workers:
   j=pending.pop(0);launch(j);active.append(j)
  proc=subprocess.Popen([binary('ffmpeg'),'-v','error','-i',str(video),'-vf','format=gray','-fps_mode','passthrough','-f','rawvideo','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  previous=None;repeats=[];i=0
  try:
   while True:
    raw=proc.stdout.read(info['width']*info['height'])
    if not raw:break
    if len(raw)!=info['width']*info['height'] or i>=n:raise ValueError('解码帧数与时间戳不一致')
    frame=np.frombuffer(raw,np.uint8).reshape(info['height'],info['width']);patches=[patch_of(frame,q) for q in rois]
    near=previous is not None and all(np.mean(d:=abs(x-y))<.8 and np.percentile(d,90)<=2 for x,y in zip(patches,previous))
    repeats.append(near);previous=patches
    for j,patch in enumerate(patches):maps[j][i]=patch
    i+=1
    if i%16==0:ready.value=i
    if i%150==0:
     if not errors.empty():raise RuntimeError(errors.get()[1])
     progress_callback(min(88,5+82*sum(progress)/(n*len(rois))),f'已读取 {i}/{n} 帧；并行追踪 {sum(progress)}/{n*len(rois)} 框帧')
   if proc.wait():raise ValueError(proc.stderr.read().decode()[-600:])
   if i!=n:raise ValueError('解码帧数与时间戳不一致')
  finally:
   ready.value=i;done.value=True
   if proc.poll() is None:proc.kill()
   proc.stdout.close();proc.stderr.close()
  decode_seconds=time.perf_counter()-start
  last_update=0
  while active:
   for j,p in list(processes):
    if j in active and not p.is_alive():
     p.join();active.remove(j)
     if p.exitcode:raise RuntimeError(errors.get(timeout=2)[1] if not errors.empty() else '并行追踪进程失败')
     if pending:
      nj=pending.pop(0);launch(nj);active.append(nj)
   if time.perf_counter()-last_update>1:
    progress_callback(min(90,5+85*sum(progress)/(n*len(rois))),f'并行追踪 {sum(progress)}/{n*len(rois)} 框帧（不跳帧）');last_update=time.perf_counter()
   if active:time.sleep(.05)
  rows={j:np.load(temp/f'roi{j}.npy') for j in range(len(rois))}
  return rows,np.asarray(repeats,bool),dict(decode_seconds=decode_seconds,tracking_seconds=time.perf_counter()-start,workers=min(workers,len(rois)),frames=n)
 finally:
  done.value=True
  for _,p in processes:
   if p.is_alive():p.terminate()
   p.join()
  maps.clear();shutil.rmtree(temp,ignore_errors=True)
