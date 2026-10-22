import unittest, tempfile, sys, subprocess, csv, json
from pathlib import Path
import numpy as np
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import analyze,load_raw,spectrum,Tracker,binary
from processing import derive,save_revision,default_config
from test_v12 import fixture

class TestIntegration(unittest.TestCase):
 def test_fourier_branch_does_not_reverse_small_slope(self):
  y,x=np.indices((128,192));im=lambda phase,ky:110+60*np.cos(2*np.pi*(8*x/192+ky*y/128+phase))
  for ky in [-1,0,1]:
   tracker=Tracker(im(0,ky),spectrum(im(0,ky)));rows=np.array([tracker.push(im(p,ky)) for p in np.linspace(0,3,151)])
   self.assertAlmostEqual(np.sum(rows[:,0]),3,delta=.04)
 def test_csv_matches_signed_selected_summary(self):
  m,a=fixture();c=default_config(m);c.update(sign=-1,start=2,end=7);r=derive(m,a,c)
  with tempfile.TemporaryDirectory() as tmp:
   rev=save_revision(tmp,r);rows=list(csv.DictReader((Path(tmp)/'revisions'/rev/'fringe_counts.csv').read_text(encoding='utf-8-sig').splitlines()))
   value=sum(float(row['processed_delta']) for row in rows if row['in_selected_interval']=='True' and row['processed_delta'])
   self.assertAlmostEqual(value,r['summary']['conditional_net_cycles'],places=10)
   session=json.loads((Path(tmp)/'session.json').read_text());self.assertEqual(derive(m,a,session['config'])['summary'],r['summary'])
 def test_temporary_and_permanent_outage_do_not_get_accepted(self):
  m,a=fixture();a['reason'][90:110]=8;a['delta'][90:110]=np.nan;c=default_config(m);c['cleaning']=True;r=derive(m,a,c);self.assertIsNone(r['summary']['accepted_net_cycles']);self.assertEqual(r['summary']['unresolved_steps'],20)
 def test_actual_video_geometry_cache(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);video=p/'known.avi';h,w,n=256,384,180;y,x=np.indices((h,w));phase=np.r_[np.linspace(0,2.4,90),np.linspace(2.4,1.2,91)[1:]]
   process=subprocess.Popen([binary('ffmpeg'),'-v','error','-y','-f','rawvideo','-pix_fmt','gray','-s',f'{w}x{h}','-r','30','-i','-','-c:v','ffv1',str(video)],stdin=subprocess.PIPE)
   for z in phase:process.stdin.write((110+60*np.cos(2*np.pi*(x/14+y/41+z))).astype('uint8').tobytes())
   process.stdin.close();self.assertEqual(process.wait(),0)
   rois=[dict(id='r0',label='ROI 1',x=20,y=20,w=180,h=100),dict(id='r1',label='ROI 2',x=200,y=110,w=160,h=120)]
   analyze(video,p/'one',rois=rois,preview_s=30);m,a=load_raw(p/'one');self.assertEqual(a['delta'].shape,(n,2));self.assertAlmostEqual(a['delta'][:,0].sum(),1.2,delta=.025)
   rois[1]['x']=190;analyze(video,p/'two',rois=rois,previous=p/'one');m2,a2=load_raw(p/'two');self.assertEqual(m2['cache']['reused'],['r0']);self.assertEqual(m2['cache']['recomputed'],['r1']);np.testing.assert_array_equal(a['delta'][:,0],a2['delta'][:,0]);self.assertEqual(m2['rois'][1]['x'],190);self.assertEqual(m2['rois'][0]['w'],180);self.assertNotIn('frame_near_repeat',a2);self.assertFalse((p/'two'/'.tracking_tmp').exists())
   with patch('core.probe',side_effect=AssertionError('unchanged cache must not decode timestamps')):
    analyze(video,p/'three',rois=rois,previous=p/'two',analysis_mode='full')
   m3,a3=load_raw(p/'three');self.assertEqual(m3['cache']['recomputed'],[]);np.testing.assert_array_equal(a2['delta'],a3['delta'])
 def test_clean_off_restores_same_selected_raw_exactly(self):
  m,a=fixture(600);a['delta'][:]=.002;a['delta'][0]=0;a['delta'][200:220]=.25;c=default_config(m);c['enabled']=['r0','r1','r2','r3'];raw=derive(m,a,c);c['cleaning']=True;c['stitches']=[dict(start_s=6.5,end_s=7.5,pre_window_s=3,post_window_s=3)];derive(m,a,c);c['cleaning']=False;restored=derive(m,a,c);self.assertEqual(raw['summary'],restored['summary']);self.assertEqual(raw['track'],restored['track'])
if __name__=='__main__':unittest.main()
