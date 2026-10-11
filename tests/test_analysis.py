import unittest
import numpy as np
import pandas as pd
from analysis import generate,estimate,TRUTH
class CausalChecks(unittest.TestCase):
 def test_reproducible_and_binary(self):
  d=generate();pd.testing.assert_frame_equal(d,generate());self.assertTrue(d.person_id.is_unique)
  self.assertTrue(d[['severe','treated','adverse_event']].isin([0,1]).all().all())
 def test_population_algebra(self):
  rows=[]
  for s,a,n,events in [(0,0,5600,560),(0,1,1400,70),(1,0,600,240),(1,1,2400,600)]:
   rows.extend({'severe':s,'treated':a,'adverse_event':int(i<events)} for i in range(n))
  crude,adj=estimate(pd.DataFrame(rows));self.assertAlmostEqual(adj,TRUTH);self.assertAlmostEqual(crude,.04728353140916808)
 def test_empty_cells_not_zero(self):
  d=generate();self.assertTrue(np.isnan(estimate(d[d.severe==0])[1]))
 def test_large_randomised_control(self):
  a,b=estimate(generate(100000,222,True));self.assertLess(abs(a-TRUTH),.01);self.assertLess(abs(b-TRUTH),.01)
if __name__=='__main__':unittest.main()
