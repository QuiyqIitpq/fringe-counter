"""Local-only web interface and command-line runner for recorded fringe videos."""
from __future__ import annotations
import argparse
import io
import json
import secrets
import threading
import time
import urllib.parse
import webbrowser
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np
from core import analyze, get_frame, probe, range_summary, review_pair

ROOT = Path(__file__).resolve().parent
DEFAULT_VIDEO = None

@lru_cache(maxsize=24)
def cached_review(folder, frame, roi_index):
    result=json.loads((Path(folder)/"result.json").read_text(encoding="utf-8"))
    if not 1 <= frame < result["frames_decoded"] or not 0 <= roi_index < len(result["rois"]):
        raise ValueError("请选择有效帧号和区域。")
    im=review_pair(result["video"]["path"],frame,result["rois"][roi_index])
    b=io.BytesIO();im.save(b,format="PNG");return b.getvalue()


def report_data(folder):
    folder=Path(folder)
    r=json.loads((folder/"result.json").read_text(encoding="utf-8"))
    with np.load(folder/"tracks.npz") as z:
        r["track"]={"time":z["time"].tolist(),"delta":[float(v) if np.isfinite(v) else None for v in z["delta"]],
                    "reason":z["reason"].tolist(),"dispersion":[float(v) if np.isfinite(v) else None for v in z["dispersion"]],
                    "roi_curves":np.cumsum(z["roi_delta"],axis=0).T.tolist()}
    r["folder"]=str(folder)
    return r


def save_html_report(folder):
    data=report_data(folder)
    data["preview_url"]="selected_regions.png"
    content=(ROOT/"index.html").read_text(encoding="utf-8")
    script="<script>window.FIXED_REPORT="+json.dumps(data,ensure_ascii=False).replace("<","\\u003c")+";</script>"
    content=content.replace("<!--BOOTSTRAP-->",script)
    (Path(folder)/"report.html").write_text(content,encoding="utf-8")


class State:
    def __init__(self, default):
        self.default=str(default) if default and Path(default).is_file() else ""
        self.token=secrets.token_urlsafe(24)
        self.jobs={}
        self.lock=threading.Lock()
        self.active=False


class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def send(self,body,kind="application/json; charset=utf-8",status=200):
        if isinstance(body,(dict,list)):body=json.dumps(body,ensure_ascii=False,allow_nan=False).encode()
        elif isinstance(body,str):body=body.encode()
        self.send_response(status);self.send_header("Content-Type",kind)
        self.send_header("Content-Length",str(len(body)));self.send_header("Cache-Control","no-store")
        self.send_header("X-Content-Type-Options","nosniff");self.send_header("Referrer-Policy","no-referrer")
        self.end_headers();self.wfile.write(body)
    @property
    def state(self):return self.server.state
    def do_GET(self):
        try:
            url=urllib.parse.urlparse(self.path);q=urllib.parse.parse_qs(url.query)
            if url.path=="/":
                content=(ROOT/"index.html").read_text(encoding="utf-8")
                bootstrap="<script>window.APP_TOKEN="+json.dumps(self.state.token)+";</script>"
                self.send(content.replace("<!--BOOTSTRAP-->",bootstrap),"text/html; charset=utf-8")
            elif url.path=="/api/init":
                self.send({"default_video":self.state.default,"example_available":(ROOT/"results/aluminium_2026_10_02/result.json").exists()})
            elif url.path=="/api/probe":self.send(probe(q["video"][0]))
            elif url.path=="/api/frame":
                im=get_frame(q["video"][0],float(q.get("time",["0"])[0]),1100)
                b=io.BytesIO();im.save(b,format="PNG");self.send(b.getvalue(),"image/png")
            elif url.path=="/api/job":
                self.send(self.state.jobs[q["id"][0]])
            elif url.path=="/api/review":
                folder=Path(self.state.jobs[q["job_id"][0]]["folder"]) if q.get("job_id") else ROOT/"results/aluminium_2026_10_02"
                self.send(cached_review(str(folder),int(q["frame"][0]),int(q["roi"][0])),"image/png")
            elif url.path=="/api/example":
                data=report_data(ROOT/"results/aluminium_2026_10_02")
                data["preview_url"]="/example/selected_regions.png";self.send(data)
            elif url.path.startswith("/example/"):
                self.file(ROOT/"results/aluminium_2026_10_02",url.path[len("/example/"):])
            elif url.path.startswith("/job/"):
                parts=url.path.split("/",3);job=self.state.jobs[parts[2]]
                self.file(Path(job["folder"]),parts[3])
            else:self.send({"error":"页面不存在"},status=404)
        except (ValueError,KeyError,RuntimeError) as e:self.send({"error":str(e)},status=400)
        except Exception as e:self.send({"error":str(e)},status=500)
    def file(self,folder,name):
        # Serve only report artifacts, never arbitrary files or parent paths.
        allowed={"selected_regions.png","phase_over_time.png","fringe_counts.csv","unsafe_intervals.csv","result.json","report.html","tracks.npz","selected_interval.json"}
        if name not in allowed:raise ValueError("不允许访问此文件。")
        path=folder/name
        kind={".png":"image/png",".csv":"text/csv; charset=utf-8",".json":"application/json; charset=utf-8",".html":"text/html; charset=utf-8"}.get(path.suffix,"application/octet-stream")
        self.send(path.read_bytes(),kind)
    def do_POST(self):
        try:
            origin=self.headers.get("Origin","")
            if origin and origin not in (f"http://127.0.0.1:{self.server.server_port}",f"http://localhost:{self.server.server_port}"):
                return self.send({"error":"仅允许本机页面发起操作。"},status=403)
            if self.headers.get("X-Fringe-Token")!=self.state.token:
                return self.send({"error":"请刷新本机程序页面后重试。"},status=403)
            url=urllib.parse.urlparse(self.path);q=urllib.parse.parse_qs(url.query)
            length=int(self.headers.get("Content-Length","0"))
            if url.path=="/api/upload":
                if length<=0 or length>4*1024**3:raise ValueError("请选择小于 4 GB 的视频。")
                name=Path(q.get("name",["video.avi"])[0]).name
                if Path(name).suffix.lower() not in (".avi",".mp4",".mov",".mkv",".m4v"):raise ValueError("请选择视频文件。")
                folder=ROOT/"results/uploads";folder.mkdir(parents=True,exist_ok=True)
                path=folder/(secrets.token_hex(4)+"_"+name)
                remaining=length
                with path.open("wb") as f:
                    while remaining:
                        chunk=self.rfile.read(min(1024*1024,remaining))
                        if not chunk:raise ValueError("视频传入未完成。")
                        f.write(chunk);remaining-=len(chunk)
                self.send({"video":str(path)})
                return
            if length>100000:raise ValueError("请求过大。")
            data=json.loads(self.rfile.read(length) or b"{}")
            if url.path=="/api/analyze":
                video=str(Path(data["video"]).expanduser().resolve());probe(video)
                with self.state.lock:
                    if self.state.active:raise ValueError("已有视频正在分析，请等待完成。")
                    self.state.active=True
                job_id=secrets.token_hex(6)
                folder=ROOT/"results"/(time.strftime("%Y%m%d_%H%M%S")+"_"+job_id)
                self.state.jobs[job_id]={"status":"running","progress":0,"message":"准备分析","folder":str(folder)}
                def work():
                    job=self.state.jobs[job_id]
                    try:
                        def update(p,m):job.update(progress=p,message=m)
                        analyze(video,folder,selection=data.get("selection"),max_rois=int(data.get("max_rois",7)),preview_s=float(data.get("preview_s",30)),progress=update)
                        save_html_report(folder)
                        report=report_data(folder);report["preview_url"]=f"/job/{job_id}/selected_regions.png"
                        job.update(status="complete",progress=100,result=report)
                    except Exception as e:job.update(status="failed",message=str(e))
                    finally:
                        with self.state.lock:self.state.active=False
                threading.Thread(target=work,daemon=True).start();self.send({"id":job_id})
            elif url.path=="/api/save_range":
                folder=Path(self.state.jobs[data["job_id"]]["folder"]) if data.get("job_id") else ROOT/"results/aluminium_2026_10_02"
                with np.load(folder/"tracks.npz") as z:
                    summary=range_summary(z["time"],z["delta"],z["reason"],float(data["start"]),float(data["end"]),int(data.get("sign",1)))
                (folder/"selected_interval.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
                self.send(summary)
            else:self.send({"error":"未知操作"},status=404)
        except (ValueError,KeyError,RuntimeError) as e:self.send({"error":str(e)},status=400)
        except Exception as e:self.send({"error":str(e)},status=500)


def main():
    parser=argparse.ArgumentParser(description="Recorded-video signed fringe counter")
    parser.add_argument("--video",type=Path,help="视频路径；与 --out 同用时直接分析")
    parser.add_argument("--out",type=Path,help="命令行模式的结果目录")
    parser.add_argument("--roi",nargs=4,type=int,metavar=("X","Y","W","H"),help="原始视频像素中的搜索框")
    parser.add_argument("--preview",type=float,default=30,help="自动选区的参考帧时刻，默认30秒")
    parser.add_argument("--port",type=int,default=0,help="本机端口；默认自动选择")
    parser.add_argument("--headless",action="store_true",help="不自动打开浏览器")
    args=parser.parse_args()
    if args.out:
        if not args.video:parser.error("--out 需要配合 --video")
        r=analyze(args.video,args.out,selection=args.roi,preview_s=args.preview,progress=lambda p,m:print(f"{p:.0f}% {m}",flush=True))
        save_html_report(args.out)
        s=r["whole_video"]
        print(json.dumps({k:v for k,v in s.items() if k!="safe_segments"},ensure_ascii=False,indent=2))
        print("结果已保存：",args.out.resolve());return
    server=ThreadingHTTPServer(("127.0.0.1",args.port),Handler)
    server.state=State(args.video or DEFAULT_VIDEO)
    address=f"http://127.0.0.1:{server.server_port}"
    print("条纹计数程序已启动："+address,flush=True)
    print("所有视频只在本机处理。关闭此窗口或按 Ctrl+C 结束程序。",flush=True)
    if not args.headless:webbrowser.open(address)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()


if __name__=="__main__":main()
