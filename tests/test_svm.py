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
import calc_engine
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

    def test_nonlinear_classification_uses_decision_scores_and_zero_threshold(self):
        rows = [[-1,-1,0], [-1,1,1], [1,-1,1], [1,1,0]]
        report = fit(rows, "svc", ["rbf", 10, "auto", .1]).regression_report
        self.assertEqual(report["confusionMatrix"], [[2, 0], [0, 2]])
        self.assertEqual(float(report["auc"]), 1)
        self.assertEqual(report["threshold"], 0)
        self.assertTrue(any(float(r["decisionScore"]) < 0 for r in report["residuals"]))
        self.assertNotIn("logLoss", report)
        self.assertNotIn("rSquared", report)
        self.assertTrue(all(float(r["fitted"]) in (0, 1) for r in report["residuals"]))
        self.assertEqual(report, fit(rows, "svc", ["rbf", 10, "auto", .1]).regression_report)

    def test_auto_task_constants_duplicate_points_and_response_translation(self):
        self.assertEqual(fit([[0,0],[1,1]]).regression_report["task"], "classification")
        self.assertEqual(fit([[0,0],[1,1]], "svr").regression_report["task"], "regression")
        for kernel in ("linear", "rbf"):
            report = fit([[7,0],[7,1],[7,1]], "svc", [kernel,1,"auto",0]).regression_report
            self.assertEqual(report["accuracy"], 2/3)
            constant = fit([[7,8],[7,8]], "svr", [kernel,1,"auto",0])
            self.assertEqual(constant.regression_predict([7]), 8)
            rows = [[x, math.sin(x)] for x in range(-3,4)]
            original = fit(rows, "svr", [kernel,2,.5,.1])
            shifted = fit([[100*x+1e5,y+1e6] for x,y in rows], "svr", [kernel,2,.5,.1])
            self.assertAlmostEqual(original.regression_predict([.5]), shifted.regression_predict([100*.5+1e5])-1e6, places=5)

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

    def test_engine_catalog_curve_copy_and_cancellation_contracts(self):
        rows = [[-2,0],[-1,0],[1,1],[2,1]]
        options = ["linear",1,"auto",.1]
        request = {"tree": {"kind":"call", "value":"regression", "args":[node(rows),node("svc"),node(options)]}}
        result = json.loads(calc_engine.dispatch(json.dumps(request)))
        self.assertTrue(result["ok"], result.get("error"))
        self.assertFalse(result["reusable"])
        self.assertNotIn("resultAst", result)
        self.assertGreater(len(result["curve"]), 100)
        self.assertEqual(result["regression"], calc.regression_report(rows, "svc", options))
        copied = result['statisticsCopyReport']
        self.assertEqual(copied['title'], 'SVM classification')
        summary = next(section for section in copied['sections'] if section['title'] == 'Summary')
        metrics = [row[0] for row in summary['rows']]
        self.assertNotIn('df', metrics)
        self.assertNotIn('Gamma', metrics)
        self.assertNotIn('Epsilon (SVR)', metrics)
        prediction = next(section for section in copied['sections'] if section['title'] == 'Classification predictions')
        self.assertNotIn('Residual', prediction['columns'])
        self.assertIn('Decision score', prediction['columns'])
        class Control:
            calls = 0
            def isCancelled(self):
                self.calls += 1
                return self.calls > 5
        cancelled = json.loads(calc_engine.dispatch(json.dumps(request), Control()))
        self.assertFalse(cancelled["ok"])
        self.assertIn("cancel", cancelled["error"].lower())

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

    def test_small_samples_report_cross_validation_unavailable(self):
        cv = fit([[0,0],[1,1]], 'svc').regression_report['crossValidation']
        self.assertFalse(cv['available'])
        self.assertIn('two observations', cv['reason'])

    def test_cross_validation_balances_total_and_per_class_fold_sizes(self):
        for zeros, ones in ((12,12), (7,23), (2,9), (5,5), (11,13), (23,7)):
            with self.subTest(zeros=zeros, ones=ones):
                rows = [[i,0] for i in range(zeros)]+[[zeros+i,1] for i in range(ones)]
                cv = fit(rows, 'svc', ['linear',1,'auto',.1]).regression_report['crossValidation']
                folds = cv['folds']
                self.assertEqual(sorted(row['row'] for row in cv['predictions']), list(range(1,len(rows)+1)))
                totals = [sum(row['fold']==f for row in cv['predictions']) for f in range(1,folds+1)]
                self.assertLessEqual(max(totals)-min(totals), 1)
                for label in (0,1):
                    counts = [sum(row['fold']==f and row['observed']==label for row in cv['predictions']) for f in range(1,folds+1)]
                    self.assertGreaterEqual(min(counts), 1)
                    self.assertLessEqual(max(counts)-min(counts), 1)
                if zeros==ones==12:
                    self.assertEqual(totals, [5,5,5,5,4])
                repeated = fit(rows, 'svc', ['linear',1,'auto',.1]).regression_report['crossValidation']
                self.assertEqual(cv, repeated)


if __name__ == "__main__":
    unittest.main()
