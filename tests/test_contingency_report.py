"""Contingency margins and percentages are presentation data, not test inputs."""
import json
import unittest
from test_advanced_statistics import evaluate, tree
from calc_engine import dispatch
from calc_statistics_report import statistics_report


class ContingencyReportTests(unittest.TestCase):
    def section(self, report, title):
        return next(section for section in report['sections'] if section['title'] == title)

    def numbers(self, section):
        return [[float(cell['decimal']) if isinstance(cell, dict) else cell for cell in row[1:]]
                for row in section.get('copyRows', section['rows'])]

    def test_public_chi_square_and_fisher_preserve_labels_and_exact_answers(self):
        xs = [0]*30+[1]*70
        ys = [0]*10+[1]*20+[0]*30+[1]*40
        labels = {'table:row':'Treatment (x)', 'table:column':'Outcome (y)',
                  'table:row:1':'Control', 'table:row:2':'Drug',
                  'table:column:1':'No', 'table:column:2':'Yes'}
        for name in ('chi2independence', 'fisherexact'):
            source = f'{name}({xs},{ys})'
            result = evaluate(source)
            labeled = json.loads(dispatch(json.dumps({'tree':tree(source), 'precision':20,
                'statisticsTermLabels':labels})))
            self.assertTrue(labeled['ok'], labeled.get('error'))
            self.assertEqual(result['exact'], labeled['exact'])
            report = labeled['statisticsReport']
            observed = self.section(report, 'observed')
            self.assertEqual(observed['columns'], ['Treatment (x)', 'Outcome (y): No', 'Outcome (y): Yes', 'Total'])
            self.assertEqual([row[0] for row in observed['rows']], ['Control','Drug','Total'])
            self.assertEqual(observed['totalRow'], 2)
            self.assertEqual(self.numbers(observed), [[10,20,30],[30,40,70],[40,60,100]])
            row = self.numbers(self.section(report, 'Row percentages (%)'))
            column = self.numbers(self.section(report, 'Column percentages (%)'))
            self.assertAlmostEqual(row[0][0], 100/3)
            self.assertAlmostEqual(row[1][1], 400/7)
            self.assertEqual(row[-1], [40,60,100])
            self.assertEqual(column[0], [25,100/3,30])
            self.assertEqual(column[-1], [100,100,100])
            for values in row[:-1]: self.assertAlmostEqual(sum(values[:-1]),100)
            for at in range(2): self.assertAlmostEqual(sum(values[at] for values in column[:-1]),100)

    def test_count_input_analyses_display_observed_counts_without_changing_ans(self):
        counts = [[20,8],[2,15]]
        for name in ('mcnemar','cramerv','phi','cohenkappa'):
            result = evaluate(f'{name}({counts})')
            self.assertNotIn('observed:', result['exact'])
            self.assertEqual(self.numbers(self.section(result['statisticsReport'], 'observed')),
                             [[20,8,28],[2,15,17],[22,23,45]])
            self.assertEqual(self.numbers(self.section(result['statisticsReport'], 'Row percentages (%)'))[-1][-1],100)

    def test_rectangular_expected_table_gets_margins_and_only_observed_gets_percentages(self):
        counts = [[1,2,3],[4,5,6]]
        report = statistics_report('chi2independence', {'observed':counts, 'expected':counts},20)
        for title in ('observed','expected'):
            self.assertEqual(self.numbers(self.section(report,title)),[[1,2,3,6],[4,5,6,15],[5,7,9,21]])
        self.assertEqual(sum(section['title']=='Row percentages (%)' for section in report['sections']),1)
        self.assertEqual(counts, [[1,2,3],[4,5,6]])

    def test_zero_margins_show_unavailable_and_large_copy_keeps_total(self):
        report = statistics_report('mcnemar', {'observed':[[0,0],[0,5]]},20)
        self.assertEqual(self.numbers(self.section(report,'Row percentages (%)'))[0],['unavailable']*3)
        self.assertEqual([row[0] for row in self.numbers(self.section(report,'Column percentages (%)'))],['unavailable']*3)
        report = statistics_report('chi2independence', {'observed':[[1,2]]*101},20)
        observed = self.section(report,'observed')
        self.assertEqual(len(observed['rows']),100)
        self.assertEqual(observed['totalRow'],101)
        self.assertEqual(observed['copyRows'][-1][0],'Total')
        self.assertEqual(self.numbers(observed)[-1],[101,202,303])


if __name__ == '__main__': unittest.main()
