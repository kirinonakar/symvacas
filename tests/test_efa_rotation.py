"""Regression for the supplied study-habits CSV and truthful loading reports."""
import csv
import json
import unittest
from test_advanced_statistics import ROOT, run


class EFARotationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT/'tests/fixtures/efa_study_habits_sample.csv').open(encoding='utf-8-sig',newline='') as stream:
            rows=list(csv.reader(stream))
        cls.labels=rows[0]; cls.rows=[[float(v) for v in row] for row in rows[1:]]
        cls.references=json.loads((ROOT/'tests/fixtures/efa_rotation_reference.json').read_text())['cases']

    def test_supplied_data_matches_independent_varimax_and_variance_references(self):
        self.assertEqual(len(self.rows),180)
        for case in self.references:
            with self.subTest(extraction=case['extraction']):
                result=run('efa',self.rows,2,'varimax',case['extraction'])
                for actual,expected in zip(result['loadings'],case['loadings']):
                    for a,b in zip(actual,expected): self.assertAlmostEqual(float(a),b,places=6)
                for row,percentage,rotated in zip(result['Explained variance'],case['percentages'],case['rotatedPercentages']):
                    self.assertAlmostEqual(float(row['Explained variance (%)']),percentage,places=6)
                    self.assertAlmostEqual(float(row['Rotated explained variance (%)']),rotated,places=6)
                variance=result['Explained variance'][-1]
                self.assertAlmostEqual(float(variance['Cumulative explained variance (%)']),sum(case['percentages']),places=6)
                self.assertAlmostEqual(float(variance['Rotated cumulative explained variance (%)']),sum(case['percentages']),places=6)


if __name__=='__main__': unittest.main()
