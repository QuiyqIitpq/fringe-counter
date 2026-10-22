import sys,unittest,copy,json,tempfile
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from spatial_recovery import measure,field,qualify,eligible,fingerprint
from core import clean_json

class SpatialTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.y,cls.x=np.indices((480,576));cls.carrier=cls.x/11-cls.y/15
 def trial(self,delta,black=False):
  left=110+65*np.cos(2*np.pi*self.carrier);right=110+65*np.cos(2*np.pi*(self.carrier+delta));orient=np.array([1/11,-1/15])
  if black:left[210:300]=0;right[210:300]=0
  variants=[]
  for size in [64,80,96,112,128]:
   q=measure(left,right,(288-size//2,348-size//2,size,size),orient)
   if q:variants.append(q)
  if len(variants)<2:return dict(qualified=False)
  ref=variants[-1];record=dict(reference_variants=variants,original_reference_delta=ref['phase'],field96=field(left,right,orient,ref,48,96),field80=field(left,right,orient,ref,40,80))
  return qualify(record)
 def test_known_positive_and_negative(self):
  for sign in [1,-1]:
   delta=sign*(.02+.00165*self.y);r=self.trial(delta)
   self.assertTrue(r['qualified'],r)
   self.assertLess(abs(r['estimate']-sign*(.02+.00165*347.5)),.01)
 def test_common_half_branch_remains_unresolved(self):
  self.assertFalse(self.trial(np.zeros_like(self.x)+.48)['qualified'])
 def test_disconnected_anchors_reject(self):
  self.assertFalse(self.trial(.10+.0016*self.y,black=True)['qualified'])
 def test_global_alias_is_not_claimed_observed(self):
  # A common whole fringe leaves the same two images. No pair-only algorithm
  # can determine it; even a passing spatial model remains conditional.
  r1=self.trial(np.zeros_like(self.x)+.10);r2=self.trial(np.zeros_like(self.x)+1.10)
  self.assertEqual(r1['qualified'],r2['qualified']);self.assertAlmostEqual(r1['estimate'],r2['estimate'],places=8)
 def test_proof_invalidated_by_participation_and_reference(self):
  m=dict(identity='a',engine_revision='b',reference_point_px=[50,50],rois=[dict(id='one',x=0,y=0,w=100,h=100)])
  m['spatial_evidence']=dict(method='1.6-spatial-graph-1',fingerprint=fingerprint(m),records=[dict(frame=1,qualified=True,held_out=False)])
  c=dict(reference_point_px=[50,50]);b=np.zeros((3,1),bool)
  self.assertEqual(len(eligible(m,c,[0],b)),1)
  self.assertEqual(eligible(m,c,[],b),[])
  self.assertEqual(eligible(m,dict(reference_point_px=[51,50]),[0],b),[])
  b[1]=True;self.assertEqual(eligible(m,c,[0],b),[])
if __name__=='__main__':unittest.main()

class PrimaryResultTests(unittest.TestCase):
 def test_cards_exports_and_raw_are_separate(self):
  import csv
  from test_v14 import data
  from processing import derive,save_revision
  m,a,c=data();a['reason'][120]=16;a['delta'][120]=.43;c.update(start=3.01,end=5.01,sign=-1)
  r=derive(m,a,c);self.assertEqual(r['primary']['mode'],'conditional_model');self.assertIsNone(r['summary']['accepted_net_cycles'])
  self.assertAlmostEqual(r['primary']['net_cycles'],r['primary']['positive_cycles']+r['primary']['negative_cycles'])
  hidden=copy.deepcopy(c);hidden['visible']=[];self.assertEqual(derive(m,a,hidden)['primary'],r['primary'])
  off=copy.deepcopy(c);off['joint_recovery']=False;ro=derive(m,a,off)
  self.assertEqual(ro['summary'],r['summary']);self.assertEqual(ro['track'],r['track']);self.assertEqual(ro['primary']['mode'],'unavailable')
  with tempfile.TemporaryDirectory() as tmp:
   rid=save_revision(tmp,r);folder=Path(tmp)/'revisions'/rid
   self.assertEqual(json.loads((folder/'primary_summary.json').read_text()),r['primary'])
   with (folder/'fringe_counts.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
   total=sum(float(q['primary_delta']) for q in rows if q['in_selected_interval']=='True')
   self.assertAlmostEqual(total,r['primary']['net_cycles'])
