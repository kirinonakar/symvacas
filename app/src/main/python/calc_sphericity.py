"""Within-subject contrast covariance: Mauchly and GG/HF corrections."""
import math
import mpmath as mp
from calc_statistics import _chisq_sf, _f_sf
from calc_shared import require


def helmert(levels):
    return [[1/math.sqrt(u*(u+1)) if j<u else -u/math.sqrt(u*(u+1)) if j==u else 0.
             for j in range(levels)] for u in range(1,levels)]


def corrections(rows, f, contrast=False):
    n=len(rows)
    if not contrast:
        basis=helmert(len(rows[0]))
        rows=[[math.fsum(a*b for a,b in zip(row,c)) for c in basis] for row in rows]
    d=len(rows[0]); centers=[math.fsum(c)/n for c in zip(*rows)]
    covariance=mp.matrix([[math.fsum((r[i]-centers[i])*(r[j]-centers[j]) for r in rows)/(n-1)
                           for j in range(d)] for i in range(d)])
    trace=float(sum(covariance[i,i] for i in range(d))); squares=float(sum(v*v for v in covariance))
    require(squares>0,'Sphericity corrections require within-subject contrast variation')
    gg=min(1.,max(1/d,trace*trace/(d*squares)))
    denominator=d*(n-1-d*gg)
    hf=min(1.,max(gg,(n*d*gg-2)/denominator)) if denominator>0 else None
    result={'GG epsilon':gg,'HF epsilon':hf}
    for name,epsilon in [('GG',gg),('HF',hf)]:
        result.update({name+' df1':d*epsilon if epsilon is not None else None,
                       name+' df2':(n-1)*d*epsilon if epsilon is not None else None,
                       name+' p':float(_f_sf(f,d*epsilon,(n-1)*d*epsilon)) if epsilon is not None else None})
    result.update({'Mauchly W':None,'Mauchly chi2':None,'Mauchly df':d*(d+1)//2-1,'Mauchly p':None})
    if d==1:
        result.update({'HF epsilon':1.,'HF df1':1,'HF df2':n-1,'HF p':float(_f_sf(f,1,n-1)),
                       'Sphericity note':'Automatic with two levels (one contrast); Mauchly test not applicable.'})
    elif n<=d or min(mp.eigsy(covariance,eigvals_only=True))<=trace*1e-12:
        result['Sphericity note']='Mauchly unavailable: singular contrast covariance or insufficient subjects; GG remains available.'
    else:
        logw=min(0.,float(mp.log(mp.det(covariance)))-d*math.log(trace/d))
        factor=1-(2*d*d+d+2)/(6*d*(n-1)); chi2=-(n-1)*factor*logw
        result.update({'Mauchly W':math.exp(logw),'Mauchly chi2':chi2,
                       'Mauchly p':float(_chisq_sf(chi2,result['Mauchly df'])),
                       'Sphericity note':'Mauchly chi-square approximation; independent multivariate-normal subject vectors assumed.'})
    if hf is None and d>1:
        result['HF note']='Unavailable: insufficient subjects for the Huynh–Feldt denominator.'
    return result
