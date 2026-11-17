"""SVM reference parity, degenerate inputs and production entry points."""
import json
import math
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"app/src/main/python"))
from calc_evaluator import Engine
from calc_shared import MathError
from calc_statistics import fit_regression
import symvacas_catalog as calc


def fit(rows, mode="svm", options=None):
    engine = Engine({"precision": 30})
    fit_regression(engine, calc._sympify(rows), mode, calc._sympify(options) if options else None)
    return engine


def node(value):
    if isinstance(value, list):
        return {"kind": "list", "args": [node(v) for v in value]}
    return {"kind": "symbol" if isinstance(value, str) else "number", "value": str(value)}


class SvmTests(unittest.TestCase):
    def test_predictions_match_independent_sklearn_references(self):
        fixture = json.loads((ROOT/"tests/fixtures/svm_reference.json").read_text())
        for case in fixture["cases"]:
            with self.subTest(mode=case["mode"], kernel=case["options"][0]):
                engine = fit(case["rows"], case["mode"], case["options"])
                report = engine.regression_report
                key = "decisionScore" if case["mode"] == "svc" else "fitted"
                actual = [float(row[key]) for row in report["residuals"]]
                for a, b in zip(actual, case["training"]):
                    self.assertAlmostEqual(a, b, delta=fixture["tolerance"])
                for row, expected in zip(case["test"], case["predictions"]):
                    self.assertAlmostEqual(engine.regression_predict(row),
                        int(expected >= 0) if case["mode"] == "svc" else expected,
                        delta=fixture["tolerance"])
                self.assertLessEqual(report["kktViolation"], 1e-6)
                if case['mode'] == 'svr':
                    errors = [row[-1]-expected for row, expected in zip(case['rows'], case['training'])]
                    self.assertAlmostEqual(float(report['mae']), sum(map(abs,errors))/len(errors), delta=fixture['tolerance'])
                    self.assertAlmostEqual(float(report['rmse']), math.sqrt(sum(e*e for e in errors)/len(errors)), delta=fixture['tolerance'])
                    cv = report['crossValidation']
                    reference = case['crossValidation']
                    self.assertEqual(cv['folds'],5)
                    self.assertEqual([row['fold'] for row in cv['predictions']],reference['folds'])
                    for row, expected in zip(cv['predictions'],reference['predictions']):
                        self.assertAlmostEqual(row['predicted'],expected,delta=fixture['tolerance'])
                    for key in ('rSquared','rmse','mae'):
                        self.assertAlmostEqual(float(cv[key]),reference[key],delta=fixture['tolerance'])
                if case['mode'] == 'svc':
                    cv = report['crossValidation']
                    self.assertEqual([row['predicted'] for row in cv['predictions']], case['crossValidation']['predictions'])
                    self.assertEqual([row['fold'] for row in cv['predictions']], case['crossValidation']['folds'])
                    self.assertAlmostEqual(cv['accuracy'], sum(row['observed'] == row['predicted'] for row in cv['predictions'])/len(case['rows']))
                if case["options"][0] == "linear":
                    coefficients = [float(c["estimate"]) for c in report["coefficients"]]
                    self.assertEqual(coefficients[-1], 0)  # constant predictor
                    for row, expected in zip(case["test"], case["predictions"]):
                        self.assertAlmostEqual(coefficients[0]+sum(a*b for a, b in zip(coefficients[1:], row)),
                                               expected, delta=fixture["tolerance"])

    def test_input_validation(self):
        for options in (["bad",1,"auto",.1], ["rbf",0,"auto",.1], ["rbf",1,0,.1],
                        ["rbf",1,"auto",-1], ["rbf",1,"auto"], ["rbf",float('inf'),"auto",.1]):
            with self.subTest(options=options), self.assertRaises((MathError, ValueError)):
                fit([[0,0],[1,1]], "svc", options)
        for rows in ([[0,1],[1,1]], [[0,1],[1,2]], [[0,0],[1,float('nan')]]):
            with self.assertRaises((MathError, ValueError)):
                fit(rows, "svc")
        with self.assertRaises(MathError):
            fit([[x,x] for x in range(501)], "svr")

    def test_decision_equations_and_boundary_levels_match_fitted_scores(self):
        import sympy as s
        rows = [[-2,-1,0],[-1,-2,0],[1,2,1],[2,1,1]]
        for kernel in ('linear','rbf'):
            model = fit(rows, 'svc', [kernel, 10, .4, .1])
            report = model.regression_report
            eq = report['decisionEquation']
            expression = s.sympify(eq['expression'].replace('^','**'))
            fn = s.lambdify(eq['variables'], expression, 'math')
            for row, observed in zip(rows, report['residuals']):
                self.assertAlmostEqual(fn(*row[:-1]), float(observed['decisionScore']), places=12)
            plot = report['decisionPlot']
            self.assertEqual(len(plot['points']), len(rows))
            self.assertEqual(sum(point['support'] for point in plot['points']), report['supportVectors'])
            for contour in plot['contours']:
                self.assertTrue(contour['segments'])
                for segment in contour['segments'][:20]:
                    for point in segment:
                        self.assertAlmostEqual(fn(*point), contour['level'], delta=.012)
            if kernel=='rbf':
                self.assertFalse(any('linear coefficients' in warning for warning in report['warnings']))
                from calc_statistics_report import statistics_copy_report
                copied = statistics_copy_report('regression', 'SVC', report, 15)
                terms = next(section for section in copied['sections'] if section['title'] == 'Support vector terms')
                self.assertIn('Signed coefficient (αᵢyᵢ)', terms['columns'])
                self.assertNotIn('aᵢ', terms['columns'])
                # The displayed values remain signed alpha*y, not alpha.
                self.assertTrue(any(term['coefficient'] < 0 for term in eq['supportTerms']))
                self.assertTrue(any(term['coefficient'] > 0 for term in eq['supportTerms']))
        one = fit([[-2,0],[-1,0],[1,1],[2,1]], 'svc').regression_report['decisionPlot']
        self.assertEqual(one['kind'], 'score')
        self.assertEqual([c['level'] for c in one['contours']], [-1,0,1])
        multi = fit([[a,b,7,y] for a,b,y in rows], 'svc').regression_report['decisionPlot']
        self.assertEqual(multi['fixedFeatures'], [{'index':2,'value':7}])

    def test_public_svm_svc_svr_modes_all_support_linear_and_rbf_cross_validation(self):
        from calc_statistics_report import statistics_copy_report
        for kernel in ('linear','rbf'):
            options = [kernel,2,.4,.1]
            for binary in (False,True):
                rows = [[i, int(i>=6) if binary else math.sin(i)+.2*i] for i in range(12)]
                explicit = calc.regression_report(rows,'svc' if binary else 'svr',options)
                automatic = calc.regression_report(rows,'svm',options)
                self.assertEqual(explicit,automatic)
                cv = explicit['crossValidation']
                self.assertTrue(cv['available'])
                self.assertEqual(cv['folds'],5)
                self.assertEqual(sorted(row['row'] for row in cv['predictions']),list(range(1,13)))
                sizes = [sum(row['fold']==fold for row in cv['predictions']) for fold in range(1,6)]
                self.assertLessEqual(max(sizes)-min(sizes),1)
                if binary:
                    self.assertIn('accuracy',cv)
                    self.assertNotIn('rmse',cv)
                else:
                    errors = [row['observed']-row['predicted'] for row in cv['predictions']]
                    mean = sum(row['observed'] for row in cv['predictions'])/12
                    sst = sum((row['observed']-mean)**2 for row in cv['predictions'])
                    self.assertAlmostEqual(float(cv['rSquared']),1-sum(e*e for e in errors)/sst,places=12)
                    self.assertAlmostEqual(float(cv['rmse']),math.sqrt(sum(e*e for e in errors)/12),places=12)
                    self.assertAlmostEqual(float(cv['mae']),sum(map(abs,errors))/12,places=12)
                    copied = statistics_copy_report('regression','SVR',explicit,15)
                    section = next(s for s in copied['sections'] if s['title']=='Cross-validation')
                    self.assertTrue({'Cross-validated R²','Cross-validated RMSE','Cross-validated MAE'}.issubset({r[0] for r in section['rows']}))
            # Explicit SVR retains regression semantics even for a binary response.
            self.assertIn('rmse',calc.regression_report(rows,'svr',options)['crossValidation'])
        short = fit([[0,2],[1,3],[2,4],[3,5]],'svr').regression_report
        self.assertFalse(short['crossValidation']['available'])
        self.assertIn('at least 5',short['crossValidation']['reason'])
        constant = fit([[i,7] for i in range(5)],'svr').regression_report['crossValidation']
        self.assertIsNone(constant['rSquared'])
        self.assertEqual(float(constant['rmse']),0)
        self.assertEqual(float(constant['mae']),0)


if __name__ == "__main__":
    unittest.main()
