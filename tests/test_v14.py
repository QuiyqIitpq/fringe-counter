import unittest, sys, tempfile, json, csv
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from processing import derive, default_config, save_revision, robust_fuse
from recovery import recover
from test_v12 import fixture

def data():
 m,a=fixture();a['phase_slope_x']=np.zeros_like(a['delta']);a['phase_slope_y']=np.zeros_like(a['delta'])
 a['delta'][:]=.1;a['delta'][0]=0
 c=default_config(m);c['joint_recovery']=True
 return m,a,c

class RecoveryTests(unittest.TestCase):
 def test_off_and_visibility_preserve_original(self):
  m,a,c=data();a['reason'][120]=16;a['delta'][120]=.43
  off=derive(m,a);on=derive(m,a,c)
  self.assertEqual(on['summary'],off['summary']);self.assertEqual(on['track'],off['track'])
  c['visible']=[];self.assertEqual(derive(m,a,c)['recovery'],on['recovery'])
  c['joint_recovery']=False;self.assertIsNone(derive(m,a,c)['recovery'])
 def test_all_off_and_legacy_fail_closed(self):
  m,a,c=data();c['enabled']=[];self.assertFalse(derive(m,a,c)['recovery']['available'])
  c['enabled']=[q['id'] for q in m['rois']];a.pop('phase_slope_x');self.assertFalse(derive(m,a,c)['recovery']['available'])
 def test_spatial_wrap_with_two_safe_anchors(self):
  for sign in [-1,1]:
   m,a,c=data();m['rois'][4]['y']=200;c['reference_point_px']=[98,248]
   xy=np.array([[q['x']+48,q['y']+48] for q in m['rois']]);actual=sign*(.55+.002*(xy[:,1]-248))
   a['delta'][120]=(actual+.5)%1-.5;a['phase_slope_y'][120]=sign*.002
   a['reason'][120]=np.where(abs(a['delta'][120])>.38,16,0)
   r=derive(m,a,c);q=r['recovery'];self.assertEqual(q['counts']['spatial'],1)
   self.assertAlmostEqual(q['delta'][120],sign*.55,places=10)
   self.assertIsNone(r['summary']['accepted_net_cycles']);self.assertIsNone(q['accepted_net_cycles'])
 def test_common_integer_still_requires_assumption(self):
  m,a,c=data();a['delta'][1:]=.3;a['delta'][120]=.43;a['reason'][120]=16
  r=derive(m,a,c);q=r['recovery'];self.assertEqual(q['counts']['temporal'],1)
  self.assertAlmostEqual(q['delta'][120],.43);self.assertIsNone(q['accepted_net_cycles'])
  # +.43 and +1.43 have identical phase: recovery must not claim observation.
  self.assertTrue(q['estimated'][120]);self.assertIn(1.43,q['records'][0]['candidates'])
 def test_real_forward_reverse_and_permanent_jump_unchanged(self):
  m,a,c=data();a['delta'][150:]=-.1;a['delta'][149]=.2;a['delta'][-1]=0
  r=derive(m,a,c);np.testing.assert_allclose(r['recovery']['delta'],r['track']['delta'])
  self.assertAlmostEqual(r['recovery']['estimated_net_cycles'],r['summary']['accepted_net_cycles'])
 def test_missing_phase_is_interpolation_not_recovery(self):
  m,a,c=data();a['reason'][120:130]=8;a['delta'][120:130]=np.nan
  q=derive(m,a,c)['recovery'];self.assertEqual(q['counts']['missing'],10)
  self.assertEqual(q['remaining_ambiguous_steps'],10);self.assertIsNotNone(q['estimated_net_cycles'])
  self.assertIsNone(q['accepted_net_cycles'])
 def test_long_gap_cannot_be_zero_filled(self):
  m,a,c=data();a['reason'][30:280]=8;a['delta'][30:280]=np.nan
  q=derive(m,a,c)['recovery'];self.assertIsNone(q['estimated_net_cycles'])
  self.assertGreater(q['sensitivity_models'][1]['missing_steps'],0)
 def test_user_exclusion_never_restored(self):
  m,a,c=data();a['reason'][120:123]=8;c['applied']=['local:r4:120:122']
  q=derive(m,a,c)['recovery'];self.assertEqual(q['counts']['blocked'],3);self.assertIsNone(q['estimated_net_cycles'])
 def test_cleaning_not_mixed(self):
  m,a,c=data();c['cleaning']=True;self.assertFalse(derive(m,a,c)['recovery']['available'])
 def test_reference_outside_support_not_extrapolated(self):
  m,a,c=data();c['reference_point_px']=[900,900];q=derive(m,a,c)['recovery']
  self.assertEqual(q['counts']['spatial'],0);self.assertIsNone(q['estimated_net_cycles'])
 def test_nonlinear_gradients_reject_spatial_lift(self):
  m,a,c=data();a['reason'][120]=16;a['delta'][120]=.43
  a['phase_slope_x'][120]=[.01,-.01,.02,-.02,0]
  self.assertEqual(derive(m,a,c)['recovery']['counts']['spatial'],0)
 def test_sign_interval_export_consistent(self):
  m,a,c=data();a['reason'][120]=16;a['delta'][120]=.43;c.update(sign=-1,start=3.,end=5.)
  r=derive(m,a,c);q=r['recovery'];ix=(a['time']>3)&(a['time']<=5)
  self.assertAlmostEqual(q['estimated_net_cycles'],-np.sum(np.array(q['delta'])[ix]))
  with tempfile.TemporaryDirectory() as tmp:
   rev=save_revision(tmp,r);p=Path(tmp)/'revisions'/rev
   self.assertEqual(json.loads((p/'recovery.json').read_text()),q)
   with (p/'recovery_steps.csv').open(encoding='utf-8-sig') as file:rows=list(csv.DictReader(file))
   self.assertEqual(len(rows),1);self.assertAlmostEqual(float(rows[0]['estimate_cycles']),q['records'][0]['estimate_cycles'])
 def test_endpoint_is_explicit_estimate(self):
  m,a,c=data();a['reason'][-2]=16;a['delta'][-2]=.43
  q=derive(m,a,c)['recovery'];row=q['records'][0]
  self.assertEqual(q['counts']['temporal'],0);self.assertTrue(row['windows'][0]['one_sided_endpoint'])
  self.assertIsNotNone(q['estimated_net_cycles'])

if __name__=='__main__':unittest.main()
