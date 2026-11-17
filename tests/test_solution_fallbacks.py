"""Complete versus partial Lambert W solutions and runtime-bounded factorization."""
import pathlib
import subprocess
import sys
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"app/src/main/python"))
import sympy as s
from calc_solutions import affine_exponential_solutions

class SolutionFallbackTests(unittest.TestCase):
    def test_complete_lambert_families_satisfy_equations_across_branches(self):
        x=s.Symbol("x")
        for expression in [s.exp(x)-x,s.exp(2*x+1)+3*x-1,s.exp(x)-4*x,
                           x*s.exp(x)-1,(2*x+3)*s.exp(4*x+1)-5]:
            result,note=affine_exponential_solutions(expression,x,s.S.Complexes)
            self.assertIsInstance(result,s.ImageSet)
            self.assertEqual(s.S.Integers,result.base_set)
            self.assertIn("All complex solutions",note)
            for k in range(-3,4):
                root=result.lamda(k)
                residual=s.N(expression.subs(x,root),50)
                self.assertLess(abs(residual),s.Rational(1,10)**40)

class NumberTheoryLimitTests(unittest.TestCase):


    def test_hard_factorization_stops_at_runtime_deadline(self):
        python_source=str(pathlib.Path(__file__).resolve().parents[1]/"app/src/main/python")
        program=f"""
import sys,json,time
sys.path.insert(0,{python_source!r})
import calc_engine
number=(2**127-1)*(2**61-1)
tree={{'kind':'call','value':'factorint','args':[{{'kind':'number','value':str(number)}}]}}
result=json.loads(calc_engine.dispatch(json.dumps({{'tree':tree,'budget':.01}})))
assert not result['ok'] and 'Computation limit reached' in result['error'],result
"""
        completed=subprocess.run([sys.executable,"-c",program],capture_output=True,text=True,timeout=5)
        self.assertEqual(0,completed.returncode,completed.stdout+completed.stderr)

if __name__=="__main__":
    unittest.main()
