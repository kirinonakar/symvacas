"""ARIMA/SARIMA analytical and independent numerical regression checks."""
import json
import math
import unittest
from test_advanced_statistics import ROOT, run, tree
from calc_engine import dispatch
from calc_shared import MathError
from calc_limits import computation_limits


class TimeSeriesTests(unittest.TestCase):

    def test_calendar_intervals_handle_month_ends_leap_years_and_invalid_dates(self):
        from calc_timeseries_calendar import time_calendar
        monthly = time_calendar([[2024,1,31],[2024,2,29],[2024,3,31],[2024,4,30]],4,2)
        self.assertEqual(monthly['labels'][-2:],['2024-05-31','2024-06-30'])
        leap = time_calendar([[2020,2,29],[2021,2,28],[2022,2,28],[2023,2,28]],4,1)
        self.assertEqual(leap['labels'][-1],'2024-02-29')
        quarterly = time_calendar([[2023,3,31],[2023,6,30],[2023,9,30],[2023,12,31]],4,1)
        self.assertEqual((quarterly['frequency'],quarterly['labels'][-1]),('Quarterly','2024-03-31'))
        daily = time_calendar([[2024,2,27],[2024,2,28],[2024,2,29],[2024,3,1]],4,1)
        self.assertEqual((daily['frequency'],daily['labels'][-1]),('Daily','2024-03-02'))
        for dates in ([[2024,2,30],[2024,3,1],[2024,3,2],[2024,3,3]],
                      [[2014,1,1],[2015,1,1],[2017,1,1],[2018,1,1]],
                      [2014,2014,2015,2016],[2017,2016,2015,2014],[[2014,1,1]]):
            with self.subTest(dates=dates),self.assertRaises(MathError): time_calendar(dates,4,2)

    def test_arima_and_multiplicative_integrated_sarima_match_independent_filters(self):
        fixtures = json.loads((ROOT/'tests/fixtures/timeseries_reference.json').read_text())
        for case in fixtures:
            with self.subTest(model=case['name']):
                args = [case['data'], case['order']] + ([case['seasonal']] if case['seasonal'] else []) + [8, .95, case.get('trend','none')]
                value = run(case['name'], *args)
                for actual, expected in zip(value['Coefficients'], case['coefficients']):
                    self.assertAlmostEqual(float(actual['Estimate']), expected, delta=2e-5)
                self.assertAlmostEqual(float(value['Innovation variance']), case['variance'], delta=1e-7)
                self.assertAlmostEqual(float(value['Conditional AIC']), case['aic'], delta=1e-5)
                for row, estimate, se in zip(value['Forecasts'], case['forecast'], case['standardError']):
                    self.assertAlmostEqual(float(row['Forecast']), estimate, delta=2e-4)
                    self.assertAlmostEqual(float(row['Standard error']), se, delta=2e-4)
                if 'driftInference' in case:
                    row = next(row for row in value['Coefficients'] if row['Parameter']=='Drift')
                    for key, expected in case['driftInference'].items():
                        self.assertAlmostEqual(float(row[key]),expected,delta=2e-5)

    def test_auto_selects_intercept_or_drift_using_aicc_and_preserves_manual_choices(self):
        cases = [('arima',[math.sin(i*2)+.3*math.cos(i*3) for i in range(60)],[[1,0,0]],'None'),
                 ('arima',[100+3*i+math.sin(i*2) for i in range(40)],[[1,1,0]],'Drift'),
                 ('sarima',[100+i*.75+[0,2,-1,3][i%4]+.4*math.sin(2.1*i) for i in range(80)],[[0,0,0],[1,1,0,4]],'Drift')]
        for name, data, orders, expected in cases:
            with self.subTest(model=name,expected=expected):
                automatic = run(name,data,*orders,4,.95,'auto')
                none = run(name,data,*orders,4,.95,'none')
                constant = run(name,data,*orders,4,.95,'constant')
                self.assertEqual(automatic['Intercept / drift'],expected)
                self.assertEqual(none['Intercept / drift'],'None')
                self.assertNotEqual(constant['Intercept / drift'],'None')
                self.assertAlmostEqual(float(automatic['Conditional AICc']),min(float(v['Conditional AICc']) for v in (none,constant)),places=8)
                self.assertEqual(len(automatic['Automatic intercept / drift selection']),2)
                self.assertEqual(sum(int(row['Selected']) for row in automatic['Automatic intercept / drift selection']),1)
                for row in automatic['Automatic intercept / drift selection']:
                    candidate = none if row['Intercept / drift']=='None' else constant
                    self.assertAlmostEqual(float(row['Conditional AICc']),float(candidate['Conditional AICc']),places=8)
                if expected=='Drift':
                    drift = next(row for row in automatic['Coefficients'] if row['Parameter']=='Drift')
                    self.assertTrue(float(drift['SE'])>0)
                    self.assertTrue(float(drift['Lower 95% CI'])<float(drift['Estimate'])<float(drift['Upper 95% CI']))
                    if name=='sarima': self.assertAlmostEqual(float(drift['Estimate']),.75,places=3)


    def test_drift_wald_standard_error_interval_and_non_extreme_p_match_ols_delta_method(self):
        data = [100+.15*i+math.sin(2*i) for i in range(40)]
        changes = [b-a for a,b in zip(data,data[1:])]
        x,y = changes[:-1],changes[1:]
        n = len(y);mx,my = sum(x)/n,sum(y)/n
        sxx = sum((v-mx)**2 for v in x)
        phi = sum((a-mx)*(b-my) for a,b in zip(x,y))/sxx
        intercept = my-phi*mx
        variance = sum((b-intercept-phi*a)**2 for a,b in zip(x,y))/n
        estimate = intercept/(1-phi)
        gphi,gc = intercept/(1-phi)**2,1/(1-phi)
        drift_variance = gphi*gphi*variance/sxx+gc*gc*variance*(1/n+mx*mx/sxx)-2*gphi*gc*mx*variance/sxx
        se = math.sqrt(drift_variance)
        expected_p = math.erfc(abs(estimate)/(se*math.sqrt(2)))
        value = run('arima',data,[1,1,0],3,.9,'constant')
        drift = next(row for row in value['Coefficients'] if row['Parameter']=='Drift')
        for key,expected in [('Estimate',estimate),('SE',se),('Lower 95% CI',estimate-1.959963984540054*se),
                              ('Upper 95% CI',estimate+1.959963984540054*se),('p value',expected_p)]:
            self.assertAlmostEqual(float(drift[key]),expected,delta=1e-8)
        self.assertTrue(.1<expected_p<.9)

    def test_random_walk_seasonal_walk_and_drift_have_analytical_forecasts(self):
        data = [4, 5, 3, 6, 4, 7, 5, 8, 6, 7, 9, 8]
        for name, orders, drift in [('arima', [[0,1,0]], False), ('arima', [[0,1,0]], True),
                                     ('sarima', [[0,0,0],[0,1,0,4]], False)]:
            value = run(name, data, *orders, 9, .9, 'constant' if drift else 'none')
            differences = [data[i]-data[i-(4 if name=='sarima' else 1)] for i in range(4 if name=='sarima' else 1, len(data))]
            mean = sum(differences)/len(differences) if drift else 0.
            variance = sum((v-mean)**2 for v in differences)/len(differences)
            for h, row in enumerate(value['Forecasts'], 1):
                expected = data[-4+(h-1)%4] if name=='sarima' else data[-1]+mean*h
                self.assertAlmostEqual(float(row['Forecast']), expected, places=6)
                self.assertAlmostEqual(float(row['Standard error'])**2, variance*(math.ceil(h/4) if name=='sarima' else h), places=6)


    def test_invalid_orders_degenerate_series_and_cancellation_fail_honestly(self):
        for args in [([1,2,3,4],[1,2]), ([1,2,3,4],[1,-1,0]), ([1,2,3,4],[1,0,0],0),
                     ([1,2,3,4],[0,0,0],2,1), ([1,2,3,4],[0,2,0],2,.95,'constant'),
                     ([2]*12,[0,0,0]), ([1,2,3,4,5,6],[1,1,1])]:
            with self.subTest(args=args), self.assertRaises(MathError): run('arima', *args)
        with self.assertRaises(MathError): run('sarima',[1,3,2,4,3,5],[0,0,0],[0,1,0,4])
        data = [4,5,3,6,4,7,5,8]
        with self.assertRaises(MathError): run('arima',data,[0,1,0],501,.95,'none')
        with computation_limits(True): self.assertEqual(int(run('arima',data,[0,1,0],501,.95,'none')['Forecast horizon']),501)
        class Cancelled:
            calls = 0
            def isCancelled(self):
                self.calls += 1
                return self.calls >= 3
        cancelled = Cancelled()
        result = json.loads(dispatch(json.dumps({'tree':tree(f'arima({data},[1,1,1])')}), cancelled))
        self.assertFalse(result['ok'])
        self.assertIn('cancelled', result['error'])
        self.assertGreaterEqual(cancelled.calls,3)


if __name__ == '__main__': unittest.main()
