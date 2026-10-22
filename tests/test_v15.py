import unittest,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import Tracker,spectrum,FIELDS
from processing import derive,default_config
from test_v12 import fixture

class V15Tests(unittest.TestCase):
 def test_subthreshold_rotation_refresh_without_false_phase_jump(self):
  h,w=96,128;y,x=np.indices((h,w));x=(x-(w-1)/2)/w;y=(y-(h-1)/2)/h
  rows=[];tr=None;phases=np.r_[np.linspace(0,1.4,70),np.linspace(1.4,.6,50)[1:]]
  for i,p in enumerate(phases):
   f=i/(len(phases)-1);im=110+65*np.cos(2*np.pi*((7-2*f)*x+(-6-3*f)*y+p))
   if tr is None:tr=Tracker(im,spectrum(im))
   rows.append(tr.push(im))
  rows=np.array(rows);self.assertGreater(rows[:,-1].sum(),0);self.assertAlmostEqual(rows[:,0].sum(),.6,delta=.02)
  self.assertTrue((rows[1:,1]==0).all());self.assertGreater(rows[:,FIELDS.index('local_verified')].mean(),.9)
 def test_blank_frame_and_reappearance_do_not_bridge(self):
  y,x=np.indices((96,128));im=lambda p:110+65*np.cos(2*np.pi*(x/12+y/30+p));tr=Tracker(im(0),spectrum(im(0)))
  tr.push(im(0));bad=tr.push(np.zeros((96,128)));back=tr.push(im(.2));good=tr.push(im(.22))
  self.assertNotEqual(bad[1],0);self.assertNotEqual(back[1],0);self.assertEqual(good[1],0);self.assertAlmostEqual(good[0],.02,delta=.002)
 def conflict(self):
  m,a=fixture();a['delta'][100]=[.28,-.23,.12,.02,-.08];a['local_verified']=np.ones_like(a['delta']);return m,a
 def test_local_fallback_is_observed_at_fixed_point_not_a_plane(self):
  m,a=self.conflict();r=derive(m,a);self.assertTrue(r['track']['valid'][100]);self.assertEqual(r['track']['delta'][100],-.08);self.assertEqual(r['track']['used'][100],1);self.assertEqual(r['audit']['local_reference_steps'],1)
  c=default_config(m);c['local_reference']=False;q=derive(m,a,c);self.assertFalse(q['track']['valid'][100]);c['local_reference']=True;self.assertEqual(r,derive(m,a,c))
 def test_no_missing_metric_or_quality_override(self):
  m,a=self.conflict();del a['local_verified'];self.assertFalse(derive(m,a)['track']['valid'][100]);a['local_verified']=np.ones_like(a['delta']);a['reason'][100,4]=16;self.assertFalse(derive(m,a)['track']['valid'][100])
 def test_local_fallback_does_not_extrapolate_or_use_hidden_excluded_roi(self):
  m,a=self.conflict();c=default_config(m);c['reference_point_px']=[99,98];self.assertFalse(derive(m,a,c)['track']['valid'][100]);c=default_config(m);c['enabled']=c['enabled'][:4];self.assertFalse(derive(m,a,c)['track']['valid'][100])
if __name__=='__main__':unittest.main()
