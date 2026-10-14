"""Example datasets and expression-to-table conversion."""
import ast
from statistics_comparison_schema import examples as comparison_examples
from .common import literal

GROUPS = '[1,2,4,5],[2,3,5,8]'
COUNTS = '[[0,1],[0,0],[1,3],[1,1],[2,2],[2,5],[3,4],[3,8],[4,6],[4,10]]'
CATEGORIES = '[[-2,0],[-2,1],[-1,0],[-1,2],[0,0],[0,1],[0,2],[1,1],[1,2],[2,1],[2,2],[2,0]]'
CLUSTERS = '[[1,0,2],[1,1,4],[1,2,4],[2,0,3],[2,1,4],[2,2,6],[3,0,1],[3,1,3],[3,2,4],[4,0,4],[4,1,5],[4,2,8]]'
GLMM = '[[1,0,0],[1,1,0],[1,2,1],[2,0,0],[2,1,1],[2,2,1],[3,0,0],[3,1,0],[3,2,0],[4,0,1],[4,1,1],[4,2,1],[5,0,1],[5,1,0],[5,2,1],[6,0,0],[6,1,1],[6,2,0]]'
SURVIVAL = '[[1,1],[2,0],[3,1],[4,1],[5,0],[6,1]]'
SERIES = '[12,15,14,18,13,17,16,21,15,19,18,24,17,22,20,27,19,24,23,30,21,27,25,33,24,29,28,36,26,32,30,39]'
LOGISTIC_COMPARE_ROWS=[[-2,0,0],[-2,1,0],[-1,0,0],[-1,1,1],[0,0,0],[0,1,1],[1,0,1],[1,1,1],[2,0,1],[2,1,1],[-1,1,0],[1,0,0],[0,1,0],[0,0,1],[2,0,0],[-2,1,1]]*3


def add_example_rows(schema):
    for item in schema:
        if 'controls' not in item:
            continue
        arguments=ast.parse(item['example'],mode='eval').body.args
        first=literal(arguments[0])
        if item['id'] in ('tinterval','zinterval'): rows=[[v] for v in literal(arguments[-1])]
        elif item['id']=='propztest': rows=literal(arguments[1])
        elif item['id']=='propztest2': rows=[[60,100],[45,100]]
        elif item['input']=='none': rows=[]
        elif item['id'] in ('shapiro','padjust','bayesproportion','bayesmean','bayesrate','bayesbootstrap','bootstrapci','arima','sarima','tost'): rows=[[v] for v in first]
        elif item['id'] in ('tukey','gameshowell','levene','bartlett','kstest','bayescompare','cohend','eta2','tost2','tostpaired','spearman','kendall'):
            samples=[literal(arg) for arg in (arguments[:2] if item['id'] in ('bayescompare','cohend','tost2','tostpaired','spearman','kendall') else arguments)]; rows=[[sample[i] if i<len(sample) else '' for sample in samples] for i in range(max(map(len,samples)))]
        elif item['id']=='logrank': rows=[r+[i+1] for i,arg in enumerate(arguments) for r in literal(arg)]
        elif item['id']=='dunn': rows=[[sample[i] if i<len(sample) else '' for sample in first] for i in range(max(map(len,first)))]
        else: rows=first
        item['exampleRows']=[[str(v) for v in row] for row in rows]
        if item['id']=='logisticcompare': item['validationExampleRows']=[[str(v) for v in row] for row in LOGISTIC_COMPARE_ROWS[5:]+LOGISTIC_COMPARE_ROWS[:5]]
        if item['id'] in ('cfa','sem'):
            # Every multi-group preset has a dedicated group column followed by the
            # same six indicators, so factor IDs continue to refer to those six.
            item['ordinalExampleCuts']=[2,3,4]
            item['multiGroupExampleIds']=['1','2']
    comparison_examples(schema,LOGISTIC_COMPARE_ROWS)
    meta=next(item for item in schema if item['id']=='metaanalysis')
    meta['binaryExampleRows']=[[str(v) for v in row] for row in [[12,100,20,100],[8,80,15,90],[25,150,40,160],[4,60,10,65]]]
    meta['continuousExampleRows']=[[str(v) for v in row] for row in [[12,3,50,10,2.5,48],[15,4,60,12,3.5,55],[9,2,40,8,2.2,42],[11,3.2,65,9.5,3,62]]]
    kappa=next(item for item in schema if item['id']=='cohenkappa')
    kappa_counts=[[6,1,0],[1,5,1],[0,1,5]]
    kappa['example']='cohenkappa([[6,1,0],[1,5,1],[0,1,5]],unweighted)'
    kappa['exampleRows']=[[['Normal','Mild','Severe'][i],['Normal','Mild','Severe'][j]] for i,row in enumerate(kappa_counts) for j,count in enumerate(row) for _ in range(count)]
