"""Conventional reliability/agreement ratings and contingency effect sizes."""
import math

ICC_GUIDE = [{'Range': 'ICC < 0.50', 'Rating': 'Poor reliability'},
             {'Range': '0.50 ≤ ICC < 0.75', 'Rating': 'Moderate reliability'},
             {'Range': '0.75 ≤ ICC ≤ 0.90', 'Rating': 'Good reliability'},
             {'Range': 'ICC > 0.90', 'Rating': 'Excellent reliability'}]
KAPPA_GUIDE = [{'Range': 'κ < 0', 'Rating': 'Poor agreement'},
               {'Range': '0 ≤ κ ≤ 0.20', 'Rating': 'Slight agreement'},
               {'Range': '0.20 < κ ≤ 0.40', 'Rating': 'Fair agreement'},
               {'Range': '0.40 < κ ≤ 0.60', 'Rating': 'Moderate agreement'},
               {'Range': '0.60 < κ ≤ 0.80', 'Rating': 'Substantial agreement'},
               {'Range': '0.80 < κ ≤ 1', 'Rating': 'Almost perfect agreement'}]


def icc_rating(value):
    return 'Poor reliability' if value < .5 else 'Moderate reliability' if value < .75 else 'Good reliability' if value <= .9 else 'Excellent reliability'


def kappa_rating(value):
    if value < 0: return 'Poor agreement'
    for cutoff, rating in [(.2,'Slight agreement'),(.4,'Fair agreement'),(.6,'Moderate agreement'),(.8,'Substantial agreement')]:
        if value <= cutoff: return rating
    return 'Almost perfect agreement'


def effect_rating(value, dimension=1):
    magnitude = abs(value)*math.sqrt(dimension)
    return 'Negligible effect' if magnitude < .1 else 'Small effect' if magnitude < .3 else 'Medium effect' if magnitude < .5 else 'Large effect'


def contingency_effects(rows):
    rows = [list(map(float,row)) for row in rows]
    nr, nc = len(rows), len(rows[0]); n = sum(map(sum,rows))
    r = list(map(sum,rows)); c = list(map(sum,zip(*rows)))
    # Zero-margin count levels contain no information about association.
    dimension = min(sum(v>0 for v in r)-1,sum(v>0 for v in c)-1)
    if n <= 0 or dimension < 1: return {'phi':'unavailable', 'Cramér’s V':'unavailable'}
    chi = sum((rows[i][j]-r[i]*c[j]/n)**2/(r[i]*c[j]/n) for i in range(nr) for j in range(nc) if r[i]*c[j]>0)
    v = math.sqrt(max(0,chi/(n*dimension)))
    phi = (rows[0][0]*rows[1][1]-rows[0][1]*rows[1][0])/math.sqrt(math.prod(r)*math.prod(c)) if nr==nc==2 and all(r+c) else None
    small,medium,large = [cut/math.sqrt(dimension) for cut in (.1,.3,.5)]
    return {'phi':phi if phi is not None else 'Not applicable (requires 2×2)', 'Cramér’s V':v,
            'Phi effect rating':effect_rating(phi) if phi is not None else 'Not applicable (requires 2×2)',
            'V effect rating':effect_rating(v,dimension), 'Effect-size dimension':dimension,
            'Cohen effect-size guide':[{'Lower threshold':0,'Upper threshold (exclusive)':small,'Rating':'Negligible effect'},
                                      {'Lower threshold':small,'Upper threshold (exclusive)':medium,'Rating':'Small effect'},
                                      {'Lower threshold':medium,'Upper threshold (exclusive)':large,'Rating':'Medium effect'},
                                      {'Lower threshold':large,'Upper threshold (exclusive)':'No upper cutoff','Rating':'Large effect'}],
            'Note':'Effect sizes use uncorrected Pearson χ² even when the test uses Yates correction or Fisher exact. Signed phi is for 2×2 only; its magnitude equals Cramér’s V. Cohen benchmarks for V are .10/.30/.50 divided by sqrt(min(rows−1,columns−1)); phi uses absolute magnitude and dimension 1. Benchmarks describe association, not clinical importance or causation.'}
