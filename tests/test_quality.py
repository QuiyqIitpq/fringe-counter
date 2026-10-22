import unittest,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import Tracker,spectrum
from processing import derive,default_config,conservative_repair
from test_v12 import fixture
class QualityTests(unittest.TestCase):
 def test_near_half_cycle_is_flagged(self):
  y,x=np.indices((96,128));im=lambda p:110+70*np.cos(2*np.pi*(x/12+y/31+p));tr=Tracker(im(0),spectrum(im(0)));tr.push(im(0));row=tr.push(im(.45));self.assertTrue(int(row[1])&16)
 def test_redundancy_supported_repair(self):
  m,a=fixture();a['reason'][150,0]=8;a['delta'][150,0]=np.nan;fixed,ok,records=conservative_repair(m,a,a['delta'],a['reason']==0,list(range(5)));self.assertTrue(ok[150,0]);self.assertTrue(records);self.assertAlmostEqual(fixed[150,0],a['delta'][150,1]);self.assertTrue(np.isnan(a['delta'][150,0]))
 def test_applied_exclusion_is_not_overridden_by_cleaning(self):
  m,a=fixture();a['reason'][150,0]=8;a['delta'][150,0]=np.nan;r=derive(m,a);c=r['config'];c.update(cleaning=True,applied=[s['id'] for s in r['suggestions'] if s['roi_id']=='r0']);r=derive(m,a,c);self.assertFalse(r['rois'][0]['valid'][150]);self.assertFalse(r['rois'][0]['estimated'][150]);self.assertTrue(r['rois'][0]['valid'][149])
 def test_slow_true_drift_survives_cleaning(self):
  m,a=fixture();a['delta'][:]=.0003;a['delta'][0]=0;c=default_config(m);c['cleaning']=True;r=derive(m,a,c);self.assertAlmostEqual(r['summary']['accepted_net_cycles'],.0003*299,places=10)
 def test_mean_missing_keeps_fixed_denominator(self):
  m,a=fixture();a['delta'][120,0]=np.nan;a['reason'][120,0]=8;r=derive(m,a);self.assertFalse(r['track']['mean_valid'][120]);self.assertIsNone(r['track']['mean'][120]);self.assertIsNone(r['mean_summary']['accepted_net_cycles'])
if __name__=='__main__':unittest.main()
