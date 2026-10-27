import collections
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Names, conventional abbreviations, and formula labels deliberately kept in Latin script.
LATIN_LABELS = {
    'McDonald ω', 'log BF10', 'LRT χ²', 'Ljung–Box Q', 'ML χ²', 'Cohen κ',
    'Cronbach α', 'Mauchly W', 'Mauchly chi2', 'GG epsilon', 'HF epsilon',
    'Welch ANOVA', 'MCSE', 'Pearson (p)', 'Spearman (s)', 'Kendall (k)',
    'Ward', 'Wilcoxon', 'Mann–Whitney', 'Kruskal–Wallis', 'Mann–Whitney U',
    'Pearson chi2', 'OOB C-statistic (AUC)', 'ridge', 'elasticnet', 'lasso',
    'MAE', 'Lasso α',
}


class LocalizationTests(unittest.TestCase):
    def test_korean_dictionary_has_unique_keys_and_translated_values(self):
        source = (ROOT / 'app/src/main/java/com/kirinonakar/symvacas/ui/Localization.kt').read_text(encoding='utf-8')
        pairs = re.findall(r'"([^"\n]+)" to "([^"\n]+)"', source)
        self.assertGreater(len(pairs), 2000, 'the dictionary must actually be inspected')
        counts = collections.Counter(key for key, _ in pairs)
        self.assertEqual([], [key for key, count in counts.items() if count > 1])
        untranslated = [key for key, value in pairs if not re.search('[가-힣]', value) and key not in LATIN_LABELS]
        self.assertEqual([], untranslated, 'translate prose; explicitly list intentional Latin labels')
        korean = dict(pairs)
        self.assertEqual('베이지안 구간', korean['Credible interval'])
        self.assertEqual('베이지안 구간', korean['credible interval'])
        self.assertEqual('상관계수', korean['Correlation'])
        self.assertEqual('이탈도 잔차', korean['Deviance residual'])
