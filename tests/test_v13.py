import unittest,sys,tempfile,json
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import phase_plane,Tracker,spectrum
from processing import derive,default_config,save_revision
from test_v12 import fixture

class V13Tests(unittest.TestCase):
 def test_resolved_tilt_center_is_not_weighted_centroid(self):
  y,x=np.indices((61,61));phase=.12+.003*(x-30)+.002*(y-30);weight=1+x/12
  d,coh,scatter,raw,*_=phase_plane(np.exp(2j*np.pi*phase),weight)
  self.assertAlmostEqual(d,.12,places=10);self.assertGreater(raw,.055);self.assertLess(scatter,1e-9);self.assertGreater(coh,.999)
 def test_nonplanar_phase_remains_invalid(self):
  rng=np.random.default_rng(34);phase=rng.uniform(-.48,.48,(61,61));d,coh,scatter,*_=phase_plane(np.exp(2j*np.pi*phase),np.ones_like(phase));self.assertTrue(coh<.95 or scatter>.055)
 def test_slow_carrier_change_reprocesses_same_pair(self):
  h,w=96,128;y,x=np.indices((h,w));phase=np.linspace(0,2.4,180);freq=np.linspace(7,12,180)
  im=lambda k,p:110+65*np.cos(2*np.pi*(k*(x-(w-1)/2)/w+2*(y-(h-1)/2)/h+p))
  tr=Tracker(im(freq[0],0),spectrum(im(freq[0],0)));rows=np.array([tr.push(im(k,p)) for k,p in zip(freq,phase)])
  self.assertGreater(rows[:,-1].sum(),0);self.assertTrue(np.isfinite(rows[:,0]).all());self.assertAlmostEqual(rows[:,0].sum(),2.4,delta=.03)
 def test_direct_reference_rescues_observation_not_missing_data(self):
  m,a=fixture();a['reason'][100,:4]=8;a['delta'][100,:4]=np.nan;r=derive(m,a)
  self.assertTrue(r['track']['valid'][100]);self.assertAlmostEqual(r['track']['delta'][100],a['delta'][100,4]);self.assertEqual(r['audit']['direct_reference_steps'],1)
  c=default_config(m);c['direct_reference']=False;self.assertFalse(derive(m,a,c)['track']['valid'][100])
  a['reason'][100,4]=8;self.assertFalse(derive(m,a)['track']['valid'][100])
 def test_direct_reference_never_extrapolates(self):
  m,a=fixture();a['reason'][100,:4]=8;c=default_config(m);c['reference_point_px']=[100,98];self.assertFalse(derive(m,a,c)['track']['valid'][100])
 def test_reference_near_half_still_rejected(self):
  m,a=fixture();a['reason'][100,:4]=8;a['delta'][100,4]=.45;a['reason'][100,4]=16;self.assertFalse(derive(m,a)['track']['valid'][100])
 def test_qualified_partial_excludes_invalid_finite(self):
  from processing import summarize
  t=np.arange(5);d=np.array([0.,.1,.49,.2,-.1]);v=np.array([1,1,0,1,1],bool);r=summarize(t,d,v,0,4)
  self.assertAlmostEqual(r['conditional_net_cycles'],.69);self.assertAlmostEqual(r['qualified_net_cycles'],.2);self.assertIsNone(r['accepted_net_cycles']);self.assertEqual(r['excluded_finite_steps'],1)
 def test_diagnostics_match_summary_and_include_first_run_increment(self):
  m,a=fixture();a['reason'][100:110]=8;a['delta'][100:110]=np.nan;r=derive(m,a)
  self.assertEqual(sum(q['steps'] for q in r['audit']['unresolved_intervals']),r['summary']['unresolved_steps'])
  self.assertAlmostEqual(sum(q['net_cycles'] for q in r['audit']['continuous_intervals']),r['summary']['qualified_net_cycles'])
  with tempfile.TemporaryDirectory() as tmp:
   rev=save_revision(tmp,r);p=Path(tmp)/'revisions'/rev;self.assertTrue((p/'unresolved_intervals.csv').exists());self.assertEqual(json.loads((p/'diagnostics.json').read_text())['reason_counts'],r['audit']['reason_counts'])
 def test_sampling_ambiguity_is_not_solved_by_duplicate_frames(self):
  # +0.55 and -0.45 produce identical intensity images; neither may be
  # called an accepted 0.45-fringe measurement solely from duplicate frames.
  y,x=np.indices((96,128));im=lambda p:110+65*np.cos(2*np.pi*(x/12+y/31+p));np.testing.assert_allclose(im(.55),im(-.45),atol=1e-11)
  tr=Tracker(im(0),spectrum(im(0)));tr.push(im(0));tr.push(im(0));row=tr.push(im(.55));self.assertTrue(int(row[1])&16)
if __name__=='__main__':unittest.main()
