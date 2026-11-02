"""Independent references; statsmodels/SciPy are only development dependencies."""
import json
from pathlib import Path
import numpy as np
import scipy
import statsmodels
from statsmodels.stats.contingency_tables import StratifiedTable

cases = []
for rows in ([[12,18,8,22],[20,15,10,25],[8,12,6,14]],
             [[1,9,11,3],[8,2,1,5],[0,15,4,10]],
             [[50,10,8,40],[5,40,30,10],[12,30,8,25]],
             [[16,2,144,36],[40,20,30,30],[60,120,4,16]]):
    reference = StratifiedTable(np.array(rows,dtype=float).reshape(-1,2,2).transpose(1,2,0),shift_zeros=False)
    for name in ('mantelhaenszel','breslowday'):
        for mode in ('uncorrected','corrected' if name=='mantelhaenszel' else 'tarone'):
            test = reference.test_null_odds(mode=='corrected') if name=='mantelhaenszel' else reference.test_equal_odds(mode=='tarone')
            ci = reference.oddsratio_pooled_confint()
            cases.append({'function':name,'arguments':[rows,mode,.95],
                          'expected':{'χ²':float(test.statistic),'p value':float(test.pvalue),
                                      'Pooled odds ratio':float(reference.oddsratio_pooled),
                                      'SE log(OR)':float(reference.logodds_pooled_se),
                                      'confidence interval':[float(v) for v in ci]}})
output = Path(__file__).resolve().parents[1]/'tests/fixtures/stratified_statistics_reference.json'
output.write_text(json.dumps({'source':f'statsmodels {statsmodels.__version__}; SciPy {scipy.__version__}',
                              'cases':cases},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
