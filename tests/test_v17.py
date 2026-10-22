import unittest,sys,tempfile,importlib.util,time,json
from pathlib import Path
from unittest.mock import patch
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import Tracker,spectrum,load_raw,dump
from app import finish_analysis

class TestV17(unittest.TestCase):
 def test_optimized_matches_predecessor_through_carrier_changes(self):
  old=Path(__file__).resolve().parent/'baselines/v1_6_core.py'
  spec=importlib.util.spec_from_file_location('baseline_v16',old);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  y,x=np.indices((96,128));rng=np.random.default_rng(17)
  ims=[110+60*np.cos(2*np.pi*(x/(14-i*.02)+y/29+(.03*i if i<60 else 3.6-.03*i)))+rng.normal(0,.5,x.shape) for i in range(120)]
  ims[51]=np.zeros(x.shape);ims[52]=np.full(x.shape,255.)
  rows=[]
  for module in [m,sys.modules['core']]:
   tr=module.Tracker(ims[0],module.spectrum(ims[0]));rows.append(np.array([tr.push(im) for im in ims]))
  np.testing.assert_array_equal(rows[0],rows[1])
 def test_balanced_never_calls_dense_or_retains_proof(self):
  with tempfile.TemporaryDirectory() as folder,patch('spatial_recovery.build') as build:
   meta={'analysis_mode':'balanced','spatial_evidence':{'stale':True}};finish_analysis(folder,meta,{},time.perf_counter(),lambda *x:None)
   build.assert_not_called();self.assertNotIn('spatial_evidence',meta);self.assertEqual(json.loads((Path(folder)/'performance.json').read_text())['mode'],'balanced')
 def test_full_uses_dense_and_records_timing(self):
  with tempfile.TemporaryDirectory() as folder,patch('spatial_recovery.build',return_value={'checked':True}) as build:
   meta={'analysis_mode':'full'};finish_analysis(folder,meta,{},time.perf_counter(),lambda *x:None)
   build.assert_called_once();self.assertEqual(meta['spatial_evidence'],{'checked':True});self.assertGreaterEqual(meta['performance']['analysis_seconds'],0)
 def test_balanced_reopen_ignores_proof_file(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder);dump(p/'raw.json',{'analysis_mode':'balanced'});dump(p/'spatial_evidence.json',{'cached':True});np.savez(p/'raw_tracks.npz',time=np.arange(3))
   m,a=load_raw(p);self.assertNotIn('spatial_evidence',m)
if __name__=='__main__':unittest.main()
