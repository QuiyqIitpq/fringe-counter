import sys, unittest
from pathlib import Path
import numpy as np
for parent in Path(__file__).resolve().parents:
 candidate = parent if (parent/'core.py').is_file() else parent/'deliverables/fringe_counter'
 if (candidate/'core.py').is_file():
  program_root=candidate;break
else: raise RuntimeError('Cannot locate core.py')
sys.path.insert(0,str(program_root))
from core import CarrierTracker, fuse_steps, range_summary, TWO_PI, detect_drift

class TrackingTests(unittest.TestCase):
 def simulated(self, phase, blackout=None, noise=1.5):
  n=96; y,x=np.indices((n,n)); rng=np.random.default_rng(45214)
  carriers=[(0,11)]*5; tracker=CarrierTracker(carriers)
  rows=[]
  for i,p in enumerate(phase):
   patches=[]
   for k in range(5):
    envelope=38*(1+.15*np.cos(x/23+k))
    background=110+16*np.sin(y/37+k)+9*np.cos(x/29+k)
    amplitude=.1 if blackout and blackout[0]<=i<blackout[1] else envelope
    a=background+amplitude*np.cos(TWO_PI*(11*y/n+p+.13*k+.00008*(x-48)**2))+rng.normal(0,noise,(n,n))
    patches.append(np.clip(a,0,255))
   rows.append(tracker.push(patches))
  arrays=[np.stack([r[k] for r in rows]) for k in range(6)]
  rois=[dict(x=x,y=y,w=n,h=n) for x,y in [(0,0),(100,0),(0,100),(100,100),(50,50)]]
  t=np.arange(len(phase))/30
  return t,arrays,fuse_steps(*arrays,rois,t)
 def test_forward_reverse_fractional_net(self):
  # Ground truth: +10.35 cycles then -2.20 -> +8.15. Includes repeated jitter.
  phase=np.r_[np.linspace(0,10.35,220),np.linspace(10.35,8.15,140)[1:]]
  phase+=.12*np.sin(np.linspace(0,12*np.pi,len(phase)))
  t,a,f=self.simulated(phase)
  s=range_summary(t,f['delta'],f['reason'])
  self.assertIsNotNone(s['accepted_net_cycles'])
  self.assertAlmostEqual(s['accepted_net_cycles'],8.15,delta=.025)
  self.assertGreater(s['conditional_positive_cycles'],10)
  self.assertLess(s['conditional_negative_cycles'],-2)
  self.assertAlmostEqual(s['conditional_positive_cycles']+s['conditional_negative_cycles'],s['conditional_net_cycles'],places=10)
 def test_dropout_does_not_invent_total(self):
  phase=np.linspace(0,12,250)
  t,a,f=self.simulated(phase,blackout=(80,115))
  s=range_summary(t,f['delta'],f['reason'])
  self.assertIsNone(s['accepted_net_cycles'])
  self.assertGreater(s['unsafe_steps'],20)
  self.assertGreaterEqual(len(s['safe_segments']),2)
 def test_half_cycle_steps_flagged(self):
  phase=np.arange(100)*.46
  t,a,f=self.simulated(phase)
  self.assertGreater(np.count_nonzero(f['reason']&8),90)
  self.assertIsNone(range_summary(t,f['delta'],f['reason'])['accepted_net_cycles'])
 def test_roi_tilt_and_fixed_point(self):
  rois=[dict(x=x,y=y,w=96,h=96) for x,y in [(0,0),(100,0),(0,100),(100,100),(50,50)]]
  d=np.tile(np.array([.09,.11,.09,.11,.1]),(101,1));d[0]=0
  one=np.ones_like(d);zero=np.zeros_like(d)
  f=fuse_steps(d,one,one*.2,zero,zero,zero.astype(bool),rois,np.arange(101)/30)
  self.assertAlmostEqual(f['delta'].sum(),10,places=7)
 def test_interval_endpoints_not_one_step_off(self):
  t=np.arange(101)/30;d=np.ones(101)*.1;d[0]=0
  s=range_summary(t,d,np.zeros(101,int),start=10/30,end=40/30)
  self.assertAlmostEqual(s['conditional_net_cycles'],3.,places=8)
 def test_sign_reversal(self):
  t=np.arange(101)/30;d=np.ones(101)*.1;d[0]=0
  s=range_summary(t,d,np.zeros(101,int),sign=-1)
  self.assertAlmostEqual(s['conditional_net_cycles'],-10)
  self.assertEqual(s['sign'],-1)
 def test_rounded_endpoint_keeps_last_frame(self):
  t=np.arange(4460)/30;d=np.ones(len(t))*.1;d[0]=0
  s=range_summary(t,d,np.zeros(len(t),int),start=.033333,end=148.633333)
  self.assertEqual(s['total_steps'],4458)
  self.assertAlmostEqual(s['conditional_net_cycles'],445.8,places=8)
 def test_all_missing_is_not_zero(self):
  t=np.arange(10)/30;d=np.full(10,np.nan);d[0]=0
  s=range_summary(t,d,np.ones(10,int))
  self.assertIsNone(s['conditional_net_cycles'])
  self.assertIsNone(s['accepted_net_cycles'])
 def test_constant_jitter_is_not_heating_onset(self):
  t=np.arange(1500)/30;phase=.18*np.sin(t*2)
  d=np.diff(phase,prepend=phase[0]);det=detect_drift(t,d,np.zeros(len(t),int))
  self.assertIsNone(det['candidate_start_s'])

if __name__=='__main__':unittest.main(verbosity=2)
