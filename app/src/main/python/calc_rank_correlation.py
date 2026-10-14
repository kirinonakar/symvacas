"""Paired Pearson and rank correlations with portable significance tests."""
from collections import Counter
from itertools import permutations
import math
import mpmath as mp
import sympy as s
from calc_shared import require
from calc_inference import _numbers, _ranks


def calculate(engine, name, args):
    from calc_statistics import _normal_sf, _t_sf, _mp_result, _mpf, pearson_correlation
    require(len(args) in (2,3) and all(isinstance(v,(list,tuple)) for v in args[:2]),
            name+" expects two paired data lists and optional both / left / right")
    x,y=map(_numbers,args[:2]); n=len(x)
    require(n==len(y) and n>=2,"Correlation requires at least two pairs with equal lengths")
    require(len(set(x))>1 and len(set(y))>1,"Correlation is undefined for a constant sample")
    tail=str(args[2]) if len(args)==3 else "both"
    require(tail in ("both","left","right"),"Use both, left or right")
    with mp.workdps(engine.precision+15):
        def probability(stat,sf):
            p=sf(abs(stat)); right=p if stat>=0 else 1-p
            return 2*p if tail=="both" else right if tail=="right" else 1-right
        if name=="pearson":
            require(n>=3,"Pearson significance testing requires at least three pairs")
            r=min(mp.mpf(1),max(mp.mpf(-1),_mpf(pearson_correlation(x,y),engine.precision+10)))
            statistic=r*mp.sqrt((n-2)/(1-r*r)) if abs(r)<1 else mp.sign(r)*mp.inf
            p=_mp_result(probability(statistic,lambda z:_t_sf(z,n-2)),engine)
            result={"n":n,"r":_mp_result(r,engine),"p":p,"df":n-2,"method":"Pearson t test","alternative":tail}
            note="Independent paired observations; the Pearson p value assumes a bivariate normal population under the null hypothesis of zero correlation."
        elif name=="spearman":
            rx,tx=_ranks(x); ry,ty=_ranks(y)
            rx=[int(2*v)-(n+1) for v in rx]; ry=[int(2*v)-(n+1) for v in ry]
            score=sum(a*b for a,b in zip(rx,ry))
            rho=mp.mpf(score)/mp.sqrt(sum(v*v for v in rx)*sum(v*v for v in ry))
            if n<=8:
                extreme=0
                for perm in permutations(ry):
                    trial=sum(a*b for a,b in zip(rx,perm))
                    extreme+=abs(trial)>=abs(score) if tail=="both" else trial>=score if tail=="right" else trial<=score
                p=s.Rational(extreme,math.factorial(n)); method="Exact permutation"
            else:
                stat=rho*mp.sqrt((n-2)/max(mp.mpf(0),1-rho*rho)) if abs(rho)<1 else mp.sign(rho)*mp.inf
                p=_mp_result(probability(stat,lambda z:_t_sf(z,n-2)),engine)
                method="Asymptotic t approximation"
            note="Average ranks for ties; independent paired observations."
            if n>8 and n<=500: note+=" The p value is approximate; small samples may need a permutation test."
            result={"n":n,"rho":_mp_result(rho,engine),"p":p,"method":method,"alternative":tail}
        else:
            cx,cy=Counter(x),Counter(y)
            xtie=sum(t*(t-1)//2 for t in cx.values()); ytie=sum(t*(t-1)//2 for t in cy.values())
            joint=sum(t*(t-1)//2 for t in Counter(zip(x,y)).values())
            ordered=sorted(zip(x,y)); levels={v:i+1 for i,v in enumerate(sorted(cy))}
            fenwick=[0]*(len(levels)+1); discord=seen=0; start=0
            while start<n:
                end=start+1
                while end<n and ordered[end][0]==ordered[start][0]: end+=1
                for _,value in ordered[start:end]:
                    at=levels[value]; prefix=0
                    while at: prefix+=fenwick[at]; at-=at&-at
                    discord+=seen-prefix
                for _,value in ordered[start:end]:
                    at=levels[value]
                    while at<len(fenwick): fenwick[at]+=1; at+=at&-at
                seen+=end-start; start=end
            total=n*(n-1)//2; comparable=total-xtie-ytie+joint
            score=comparable-2*discord
            tau=mp.mpf(score)/mp.sqrt((total-xtie)*(total-ytie))
            if not xtie and not ytie and n<=33:
                counts=[1]
                for size in range(2,n+1):
                    updated=[]; running=0
                    for k in range(size*(size-1)//2+1):
                        if k<len(counts): running+=counts[k]
                        if k>=size and k-size<len(counts): running-=counts[k-size]
                        updated.append(running)
                    counts=updated
                denominator=math.factorial(n)
                if tail=="both": p=min(s.Integer(1),s.Rational(2*sum(counts[:min(discord,total-discord)+1]),denominator))
                elif tail=="right": p=s.Rational(sum(counts[:discord+1]),denominator)
                else: p=s.Rational(sum(counts[discord:]),denominator)
                method="Exact no-tie permutation"
            else:
                m=n*(n-1)
                x0=sum(t*(t-1)*(t-2) for t in cx.values()); y0=sum(t*(t-1)*(t-2) for t in cy.values())
                x1=sum(t*(t-1)*(2*t+5) for t in cx.values()); y1=sum(t*(t-1)*(2*t+5) for t in cy.values())
                variance=mp.mpf(m*(2*n+5)-x1-y1)/18+mp.mpf(2*xtie*ytie)/m
                if n>2: variance+=mp.mpf(x0*y0)/(9*m*(n-2))
                require(variance>0,"Kendall test variance is zero")
                p=_mp_result(probability(mp.mpf(score)/mp.sqrt(variance),_normal_sf),engine)
                method="Tie-corrected asymptotic normal"
            result={"n":n,"tau-b":_mp_result(tau,engine),"p":p,"method":method,"alternative":tail,
                    "concordant pairs":comparable-discord,"discordant pairs":discord,"tied x pairs":xtie,"tied y pairs":ytie}
            note="Kendall tau-b adjusts for ties; independent paired observations."
        engine.note=note
        return result
