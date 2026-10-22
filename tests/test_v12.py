import unittest,sys,tempfile,json
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import Tracker,spectrum,normalize_rois,load_raw
from processing import derive,default_config,stitch,conservative_repair

def fixture(n=300,k=5):
 t=np.arange(n)/30;phase=.04*np.arange(n)+.1*np.sin(np.arange(n)/10);d=np.tile(np.diff(phase,prepend=phase[0])[:,None],(1,k));zero=np.zeros_like(d)
 xy=[(0,0),(100,0),(0,100),(100,100),(50,50)]
 m=dict(video=dict(path='synthetic',width=400,height=400,duration_s=t[-1]),rois=[dict(id=f'r{i}',label=f'ROI {i+1}',color='#123456',x=xy[i][0],y=xy[i][1],w=96,h=96,source='manual') for i in range(k)],reference_point_px=[98,98],legacy=False)
 a=dict(time=t,delta=d,reason=zero.astype('uint16'),coherence=zero+1,modulation=zero+15,brightness=zero+100,snr=zero+5,clipping=zero,scatter=zero,concentration=zero+.25,kx=zero+.1,ky=zero+.03)
 return m,a

class TestV12(unittest.TestCase):
 def test_rectangular_forward_reverse(self):
  h,w=80,160;y,x=np.indices((h,w));phase=np.r_[np.linspace(0,6.25,200),np.linspace(6.25,4.15,100)[1:]];im=lambda p:100+60*np.cos(2*np.pi*(8*x/w+3*y/h+p))
  s=spectrum(im(0));self.assertEqual(s['reason'],0);tr=Tracker(im(0),s);rows=np.array([tr.push(im(p)) for p in phase]);self.assertAlmostEqual(rows[:,0].sum(),4.15,delta=.03);self.assertEqual(tr.shape,(h,w))
 def test_dark_texture_rejected(self):
  y,x=np.indices((96,96));s=spectrum(13+3*np.cos(2*np.pi*x/8));self.assertTrue(s['reason']&1)
 def test_sparse_signal_or_explicit_reject(self):
  y,x=np.indices((160,160));s=spectrum(110+65*np.cos(2*np.pi*(3*x/160+2*y/160)));self.assertEqual(s['reason'],0)
 def test_visibility_never_changes_numbers(self):
  m,a=fixture();r=derive(m,a);c=default_config(m);c['visible']=[];s=derive(m,a,c);self.assertEqual(r['summary'],s['summary']);self.assertEqual(r['track']['delta'],s['track']['delta'])
 def test_all_off_and_one(self):
  m,a=fixture();c=default_config(m);c['enabled']=[];r=derive(m,a,c);self.assertIsNone(r['summary']['conditional_net_cycles']);c['enabled']=['r0'];r=derive(m,a,c);self.assertAlmostEqual(r['summary']['conditional_net_cycles'],a['delta'][:,0].sum());self.assertIn('单框',r['track']['reason'][1])
 def test_toggling_is_reversible(self):
  m,a=fixture();c=default_config(m);raw=derive(m,a,c);c['enabled']=['r0','r1','r2'];derive(m,a,c);c=default_config(m);self.assertEqual(raw,derive(m,a,c))
 def test_missing_never_zero_filled(self):
  m,a=fixture();a['delta'][100:120]=np.nan;a['reason'][100:120]=8;r=derive(m,a);self.assertIsNone(r['summary']['accepted_net_cycles']);self.assertGreater(r['summary']['unresolved_steps'],15);self.assertIsNone(r['track']['curve'][105]);self.assertNotEqual(r['track']['segments'][99],r['track']['segments'][125])
 def test_global_gap_not_conservatively_repaired(self):
  m,a=fixture();a['reason'][100:103]=8;a['delta'][100:103]=np.nan;c=default_config(m);c['cleaning']=True;r=derive(m,a,c);self.assertFalse(r['changes']);self.assertIsNone(r['summary']['accepted_net_cycles'])
 def test_real_permanent_change_preserved(self):
  m,a=fixture();a['delta'][150]+=.1;c=default_config(m);c['cleaning']=True;r=derive(m,a,c);self.assertAlmostEqual(r['summary']['conditional_net_cycles'],a['delta'][:,0].sum(),places=8)
 def test_signed_zero_and_reversal_not_excluded(self):
  m,a=fixture();a['delta'][:150]=.03;a['delta'][150:]=-.03;a['delta'][0]=0;a['delta'][-1]=0;r=derive(m,a);self.assertAlmostEqual(r['summary']['conditional_net_cycles'],0,places=7);self.assertFalse([s for s in r['suggestions'] if s['id'].startswith('trend:')])
 def test_saturation_suggested(self):
  m,a=fixture();a['reason'][:,3]=2;r=derive(m,a);self.assertTrue(any(s['roi_id']=='r3' and s['kind']=='global' for s in r['suggestions']))
 def test_stitch_is_explicit_and_preserves_later_slopes(self):
  m,a=fixture(600);d=np.ones_like(a['delta'])*.002;d[0]=0;v=np.ones_like(d,bool);d[200:220]=np.nan;v[200:220]=False;fixed,ok,est,records=stitch(d,v,a['time'],dict(start_s=6.5,end_s=7.5,pre_window_s=3,post_window_s=3));self.assertTrue(records);np.testing.assert_array_equal(fixed[230:],d[230:]);self.assertTrue(np.any(est));self.assertTrue(np.isnan(d[205]).all())
 def test_unstable_stitch_rejected(self):
  m,a=fixture(600);a['reason'][100:250]=8;with_error=False
  with self.assertRaises(ValueError):stitch(a['delta'],a['reason']==0,a['time'],dict(start_s=6,end_s=7))
 def test_fixed_reference_no_extrapolation(self):
  m,a=fixture();c=default_config(m);c['reference_point_px']=[900,900];r=derive(m,a,c);self.assertIsNone(r['summary']['accepted_net_cycles']);self.assertGreater(r['summary']['unresolved_steps'],0)
 def test_real_spatial_gradient(self):
  m,a=fixture();centers=np.array([[q['x']+48,q['y']+48] for q in m['rois']]);a['delta']+=.00005*(centers[:,0]-98);a['delta'][0]=0;r=derive(m,a);base=(a['delta'][:,0]+a['delta'][:,-2])/2;self.assertAlmostEqual(r['summary']['conditional_net_cycles'],base.sum(),places=7)
 def test_duplicate_or_outside_roi(self):
  q=dict(id='a',x=0,y=0,w=100,h=80)
  with self.assertRaises(ValueError):normalize_rois([q,q],dict(width=200,height=200))
 def test_no_mutation_by_cleaning(self):
  m,a=fixture();before={k:v.copy() for k,v in a.items()};c=default_config(m);c['cleaning']=True;derive(m,a,c)
  for key in a:np.testing.assert_array_equal(a[key],before[key])
if __name__=='__main__':unittest.main(verbosity=2)
