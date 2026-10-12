"""CFA/SEM routing and optional nonparametric bootstrap inference."""
from calc_shared import require
from calc_advanced_common import option
from calc_advanced_sem_extras import options, bootstrap


def fit(engine,name,args,fast=False):
    offset=3 if name=='sem' else 2
    estimator=option(args,offset+4,'ml')
    require(estimator in ('ml','wlsmv'),'Choose ml or wlsmv estimation')
    if estimator=='wlsmv':
        from calc_advanced_sem_ordinal import calculate
    else:
        from calc_advanced_sem_extended import calculate
    return calculate(engine,name,args,fast=fast)


def calculate(engine,name,args):
    residual,mi,samples,seed=options(name,args,len(args[0][0]))
    require(not samples or name=='sem','Bootstrap effects are available for SEM with latent paths')
    result=fit(engine,name,args)
    if samples: bootstrap(engine,name,args,result,fit,samples,seed)
    return result
