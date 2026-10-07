"""Check subsampled-color decoding at odd processed crop coordinates."""
from pathlib import Path
import json, sys, subprocess, tempfile
import numpy as np
for parent in Path(__file__).resolve().parents:
 candidate = parent if (parent/'core.py').is_file() else parent/'deliverables/fringe_counter'
 if (candidate/'core.py').is_file():
  program_root=candidate;break
else: raise RuntimeError('Cannot locate core.py')
sys.path.insert(0,str(program_root))
from core import analyze,binary,review_pair
root=program_root
source=root/'results/synthetic_validation/known_motion.avi'
with tempfile.TemporaryDirectory(prefix='fringe-roi-') as tmp:
 p=Path(tmp);video=p/'yuv420.mp4'
 subprocess.run([binary('ffmpeg'),'-v','error','-i',str(source),'-c:v','libx264','-crf','12','-pix_fmt','yuv420p',str(video)],check=True)
 r=analyze(video,p/'analysis',selection=[202,202,540,370],max_rois=5,preview_s=5)
 error=abs(r['whole_video']['conditional_net_cycles']-8.15)
 odd=any((roi['x']//2)%2 or (roi['y']//2)%2 for roi in r['rois'])
 assert odd and error<.03,(odd,error)
 # The reviewer must extract the requested original frame, not a nearby seek frame.
 pair=review_pair(video,100,r['rois'][0]);assert pair.size==(716,388)
 result={'passed':True,'net_cycles':r['whole_video']['conditional_net_cycles'],'absolute_error_cycles':error,'unsafe_steps':r['whole_video']['unsafe_steps'],'has_odd_processed_crop':odd,'exact_frame_pair_generated':True}
 (root/'results/synthetic_validation/manual_roi_validation.json').write_text(json.dumps(result,indent=2))
 print(json.dumps(result,indent=2))
