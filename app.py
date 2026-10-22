"""Local web application for v1.2; immutable jobs and versioned processing revisions."""
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import argparse,io,json,secrets,threading,time,urllib.parse,webbrowser,shutil
import numpy as np
from PIL import Image,ImageDraw
from core import probe,get_frame,binary,analyze,propose,load_raw,clean_json,dump,font
from processing import derive,default_config,save_revision
from legacy_io import review_pair

ROOT=Path(__file__).resolve().parent
DEFAULT=None

def standalone(report,path):
 html=(ROOT/'index.html').read_text();css=(ROOT/'style.css').read_text();js=(ROOT/'ui.js').read_text();i18n=(ROOT/'i18n.js').read_text()
 html=html.replace('<script src="/i18n.js"></script>','<script>'+i18n+'</script>')
 html=html.replace('<link rel="stylesheet" href="/style.css">','<style>'+css+'</style>').replace('<script src="/ui.js"></script>','<script>window.FIXED_REPORT='+json.dumps(report,ensure_ascii=False).replace('<','\\u003c')+';</script><script>'+js+'</script>')
 Path(path).write_text(html)

def finish_analysis(folder,meta,arrays,started,progress):
 """Full mode adds dense review; balanced mode never silently applies cached proof."""
 dense_start=time.perf_counter()
 if meta.get('analysis_mode')=='full':
  from spatial_recovery import build
  proof=build(folder,meta,arrays,progress=progress)
  if proof:meta['spatial_evidence']=proof
 else:meta.pop('spatial_evidence',None)
 meta['performance']=dict(analysis_seconds=time.perf_counter()-started,dense_review_seconds=time.perf_counter()-dense_start,mode=meta.get('analysis_mode','balanced'),scope='Video probing, tracking and optional dense review; excludes ROI proposal, final fusion and export.')
 dump(Path(folder)/'performance.json',meta['performance'])

class State:
 def __init__(self):self.jobs={};self.lock=threading.Lock();self.busy=False;self.token=secrets.token_urlsafe(24)
 def history(self):
  rows=[]
  for base in [ROOT/'results']:
   if not base.exists():continue
   for path in sorted(base.iterdir(),reverse=True):
    f=path/'raw.json' if (path/'raw.json').exists() else path/'result.json'
    if not f.exists():continue
    try:
     m=json.loads(f.read_text());
     if m.get('version')=='1.7.0' and not (path/'session.json').exists():continue
     rows.append(dict(folder=str(path),name=Path(m['video']['path']).name,version=m.get('version','legacy'),created=path.name))
    except (KeyError,ValueError):continue
  return rows
 def open(self,folder):
  p=Path(folder).resolve();known={Path(x['folder']).resolve() for x in self.history()}
  if p not in known:raise ValueError('请从历史任务列表选择。')
  meta,a=load_raw(p);c=default_config(meta)
  if (p/'session.json').exists():c=json.loads((p/'session.json').read_text())['config']
  jid=secrets.token_hex(6);self.jobs[jid]=dict(status='complete',folder=str(p),save_folder=str(p) if p.parent==ROOT/'results' else str(ROOT/'results'/('import_'+time.strftime('%Y%m%d_%H%M%S')+'_'+jid)),meta=meta,arrays=a,revision=None)
  return jid,derive(meta,a,c)

class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 @property
 def state(self):return self.server.state
 def send(self,obj,kind='application/json; charset=utf-8',status=200):
  if isinstance(obj,(dict,list)):obj=json.dumps(clean_json(obj),ensure_ascii=False,allow_nan=False).encode()
  elif isinstance(obj,str):obj=obj.encode()
  self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(obj)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer');self.end_headers();self.wfile.write(obj)
 def do_GET(self):
  try:
   u=urllib.parse.urlparse(self.path);q=urllib.parse.parse_qs(u.query)
   if u.path=='/':return self.send((ROOT/'index.html').read_text().replace('<!--BOOT-->','<script>window.TOKEN='+json.dumps(self.state.token)+'</script>'),'text/html; charset=utf-8')
   if u.path in ['/ui.js','/i18n.js','/style.css']:return self.send((ROOT/u.path[1:]).read_bytes(),'text/javascript' if u.path.endswith('.js') else 'text/css')
   if u.path=='/api/init':return self.send(dict(default_video=str(DEFAULT) if DEFAULT and DEFAULT.exists() else '',history=self.state.history()))
   if u.path=='/api/probe':
    info=probe(q['video'][0])
    if info['duration_s']<=0:raise ValueError('视频容器缺少有效时长；若有修复版 MP4，请优先选择修复版。')
    return self.send(info)
   if u.path=='/api/frame':
    im=get_frame(q['video'][0],float(q.get('time',['0'])[0]),1200);b=io.BytesIO();im.save(b,format='PNG');return self.send(b.getvalue(),'image/png')
   if u.path=='/api/job':
    j=self.state.jobs[q['id'][0]];return self.send({k:v for k,v in j.items() if k not in ['meta','arrays']})
   if u.path=='/api/revisions':
    j=self.state.jobs[q['job'][0]];base=Path(j['save_folder'])/'revisions';rows=[]
    if base.exists():
     for f in sorted(base.glob('*/operations.json'),reverse=True):
      r=json.loads(f.read_text());rows.append(dict(id=f.parent.name,action=r.get('action','处理'),created_at=r.get('created_at',f.parent.name)))
    return self.send(rows)
   if u.path=='/api/history':return self.send(self.state.history())
   if u.path=='/api/review':
    j=self.state.jobs[q['job'][0]];r=next(x for x in j['meta']['rois'] if x['id']==q['roi'][0]);im=review_pair(j['meta']['video']['path'],int(q['frame'][0]),r);b=io.BytesIO();im.save(b,format='PNG');return self.send(b.getvalue(),'image/png')
   if u.path=='/artifact':
    j=self.state.jobs[q['job'][0]];name=q['name'][0]
    if name not in ['raw_tracks.npz','raw.json','result.json','config.json','operations.json','fringe_counts.csv','report.html','curves.svg','diagnostics.json','unresolved_intervals.csv','continuous_intervals.csv','recovery.json','recovery_steps.csv','primary_summary.json','spatial_evidence.json','performance.json']:raise ValueError('文件不在导出列表。')
    rev=q.get('revision',[j.get('revision')])[0]
    if not rev or any(c not in '0123456789abcdef_' for c in rev):raise ValueError('导出版本无效。')
    p=(Path(j['save_folder'])/'revisions'/rev/name) if name not in ['raw_tracks.npz','raw.json','spatial_evidence.json','performance.json'] else (Path(j['save_folder'])/name if (Path(j['save_folder'])/name).exists() else Path(j['folder'])/name);kind={'.html':'text/html; charset=utf-8','.svg':'image/svg+xml','.csv':'text/csv; charset=utf-8','.npz':'application/octet-stream'}.get(p.suffix,'application/json');return self.send(p.read_bytes(),kind)
   return self.send(dict(error='不存在'),status=404)
  except (ValueError,KeyError,RuntimeError,FileNotFoundError) as e:self.send(dict(error=str(e)),status=400)
  except Exception as e:self.send(dict(error=str(e)),status=500)
 def do_POST(self):
  try:
   origin=self.headers.get('Origin','');port=self.server.server_port
   if origin and origin not in [f'http://127.0.0.1:{port}',f'http://localhost:{port}']:return self.send(dict(error='只允许本机页面'),status=403)
   if self.headers.get('X-Fringe-Token')!=self.state.token:return self.send(dict(error='请刷新页面'),status=403)
   u=urllib.parse.urlparse(self.path);size=int(self.headers.get('Content-Length',0))
   if u.path=='/api/upload':
    if not 0<size<=4*1024**3:raise ValueError('文件需小于 4 GB')
    name=Path(urllib.parse.parse_qs(u.query).get('name',['video.avi'])[0]).name
    if Path(name).suffix.lower() not in ['.avi','.mp4','.mov','.mkv','.m4v']:raise ValueError('不支持此视频格式')
    p=ROOT/'results'/'uploads'/(secrets.token_hex(4)+'_'+name);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('wb') as f:
     remaining=size
     while remaining:
      chunk=self.rfile.read(min(remaining,1024**2))
      if not chunk:raise ValueError('文件传输未完成')
      f.write(chunk);remaining-=len(chunk)
    return self.send(dict(video=str(p)))
   if size>4*1024**2:raise ValueError('请求过大')
   data=json.loads(self.rfile.read(size) or '{}')
   if u.path=='/api/open':
    jid,r=self.state.open(data['folder']);return self.send(dict(job_id=jid,result=r))
   if u.path=='/api/propose':return self.send(propose(data['video'],data.get('selection'),data.get('max_rois',5),data.get('preview_s',30)))
   if u.path=='/api/analyze':
    with self.state.lock:
     if self.state.busy:raise ValueError('已有视频正在分析。')
     self.state.busy=True
    jid=secrets.token_hex(6);folder=ROOT/'results'/(time.strftime('%Y%m%d_%H%M%S')+'_'+jid);j=dict(status='running',progress=0,message='准备分析',folder=str(folder),save_folder=str(folder));self.state.jobs[jid]=j
    previous=self.state.jobs.get(data.get('previous_job'),{}).get('folder')
    def work():
     try:
      started=time.perf_counter()
      analyze(data['video'],folder,rois=data.get('rois'),selection=data.get('selection'),max_rois=data.get('max_rois',5),preview_s=data.get('preview_s',30),previous=previous,analysis_mode=data.get('analysis_mode','balanced'),reference_point_px=(data.get('config') or {}).get('reference_point_px'),progress=lambda p,m:j.update(progress=p,message=m))
      m,a=load_raw(folder)
      finish_analysis(folder,m,a,started,lambda p,msg:j.update(progress=p,message=msg))
      j.update(meta=m,arrays=a);c=data.get('config') or default_config(m);r=derive(m,a,c);revision=save_revision(folder,r,'analysis');standalone(r,folder/'revisions'/revision/'report.html');j.update(status='complete',progress=100,message='分析完成',result=r,revision=revision)
     except Exception as exc:j.update(status='failed',message=str(exc))
     finally:
      with self.state.lock:self.state.busy=False
    threading.Thread(target=work,daemon=True).start();return self.send(dict(id=jid))
   if u.path=='/api/restore':
    j=self.state.jobs[data['job_id']];rev=data['revision']
    if not rev or any(c not in '0123456789abcdef_' for c in rev):raise ValueError('版本无效')
    data['config']=json.loads((Path(j['save_folder'])/'revisions'/rev/'result.json').read_text())['config'];data['action']='恢复版本 '+rev
   if u.path in ['/api/recompute','/api/stitch_preview','/api/export','/api/restore']:
    j=self.state.jobs[data['job_id']];m,a=j['meta'],j['arrays'];r=derive(m,a,data.get('config'))
    if u.path=='/api/stitch_preview':return self.send(dict(result=r,preview=True))
    folder=Path(j['save_folder'])
    if folder!=Path(j['folder']) and not (folder/'raw.json').exists():
     folder.mkdir(parents=True,exist_ok=True);dump(folder/'raw.json',{k:v for k,v in m.items() if k!='spatial_evidence'});
     if m.get('spatial_evidence'):dump(folder/'spatial_evidence.json',m['spatial_evidence'])
     np.savez_compressed(folder/'raw_tracks.npz',**a)
    revision=save_revision(folder,r,data.get('action','recompute'));standalone(r,folder/'revisions'/revision/'report.html');j.update(result=r,revision=revision)
    if u.path=='/api/export' and data.get('svg'):
     svg=data['svg']
     # Generated SVG has no external references/scripts, never execute arbitrary SVG.
     if '<script' in svg.lower() or '<foreignobject' in svg.lower() or 'href=' in svg.lower():raise ValueError('导出图像包含不允许的内容。')
     (folder/'revisions'/revision/'curves.svg').write_text(svg)
    return self.send(dict(result=r,revision=revision,folder=str(folder/'revisions'/revision)))
   return self.send(dict(error='未知请求'),status=404)
  except (ValueError,KeyError,RuntimeError,FileNotFoundError) as e:self.send(dict(error=str(e)),status=400)
  except Exception as e:self.send(dict(error=str(e)),status=500)

def main():
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=0);p.add_argument('--headless',action='store_true');p.add_argument('--video');p.add_argument('--out');p.add_argument('--roi',nargs=4,type=int);p.add_argument('--rois-json');p.add_argument('--preview',type=float,default=30);p.add_argument('--mode',choices=['balanced','full'],default='balanced');args=p.parse_args()
 if args.out:
  if not args.video:p.error('--out 需要 --video')
  rois=json.loads(Path(args.rois_json).read_text()) if args.rois_json else None
  started=time.perf_counter();analyze(args.video,args.out,rois=rois,selection=args.roi,preview_s=args.preview,analysis_mode=args.mode,progress=lambda p,m:print(m,flush=True));m,a=load_raw(args.out);finish_analysis(Path(args.out),m,a,started,lambda p,msg:print(msg,flush=True));r=derive(m,a);rid=save_revision(args.out,r,'analysis');standalone(r,Path(args.out)/'revisions'/rid/'report.html');print(json.dumps(r['primary'],ensure_ascii=False));return
 server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler);server.state=State();url=f'http://127.0.0.1:{server.server_port}';print(url,flush=True)
 if not args.headless:webbrowser.open(url)
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close()
if __name__=='__main__':main()
