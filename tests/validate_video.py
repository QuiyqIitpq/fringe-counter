"""End-to-end known-motion video check: recording, decoding, ROI selection, signed sum."""
from pathlib import Path
import sys, subprocess, json
import numpy as np
for parent in Path(__file__).resolve().parents:
 candidate = parent if (parent/'core.py').is_file() else parent/'deliverables/fringe_counter'
 if (candidate/'core.py').is_file():
  program_root=candidate;break
else: raise RuntimeError('Cannot locate core.py')
sys.path.insert(0,str(program_root))
from core import analyze, binary
from app import save_html_report
root=program_root
folder=root/'results/synthetic_validation';folder.mkdir(parents=True,exist_ok=True)
w,h,fps=768,576,30
phase=np.r_[np.linspace(0,10.35,220),np.linspace(10.35,8.15,140)[1:]]
phase+=.12*np.sin(np.linspace(0,12*np.pi,len(phase)))
y,x=np.indices((h,w));rng=np.random.default_rng(514)
video=folder/'known_motion.avi'
p=subprocess.Popen([binary('ffmpeg'),'-v','error','-y','-f','rawvideo','-pixel_format','gray','-video_size',f'{w}x{h}','-framerate',str(fps),'-i','-','-c:v','ffv1',str(video)],stdin=subprocess.PIPE)
for v in phase:
 a=110+12*np.cos(x/145)+8*np.sin(y/91)+38*np.cos(2*np.pi*(y/17.45+v+.000004*(x-w/2)**2))+5*np.cos(np.hypot(x-w/2,y-h/2)*.19)+rng.normal(0,2,(h,w))
 p.stdin.write(np.clip(a,0,255).astype(np.uint8).tobytes())
p.stdin.close()
if p.wait():raise RuntimeError('Failed to create known-motion video')
r=analyze(video,folder/'analysis',preview_s=5,progress=lambda pct,msg:print(round(pct),msg,flush=True));save_html_report(folder/'analysis')
s=r['whole_video'];error=s['conditional_net_cycles']-(phase[-1]-phase[0])
result=dict(ground_truth_net_cycles=float(phase[-1]-phase[0]),reported_net_cycles=s['conditional_net_cycles'],absolute_error_cycles=abs(error),unsafe_steps=s['unsafe_steps'],passed=abs(error)<.03 and s['accepted_net_cycles'] is not None)
(folder/'validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
assert result['passed'],result
