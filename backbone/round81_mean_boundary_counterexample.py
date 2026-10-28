"""Round81: self-contained two-positive-grade example at a mean boundary.

N=2m independent items, probabilities(high,low,scrap)=(1/4,1/4,1/2), no
rework, free downward substitution. Demands(1,m-1), m>=2. Mean-count service
is1, but actual service tends to1/2. This is an elementary illustration of an
indicator discontinuity, not a claim of a novel probability theorem.
"""
import math
from backbone.service_frontier import save_service


def service(m):
    n=2*m
    center=math.exp(math.lgamma(n+1)-2*math.lgamma(m+1)-n*math.log(2))
    logs=[math.lgamma(n+1)-math.lgamma(b+1)-math.lgamma(n-b+1)+b*math.log(.25)+(n-b)*math.log(.5)
          for b in range(m,n+1)]
    largest=max(logs)
    bad=math.exp(largest)*sum(math.exp(x-largest) for x in logs)
    return .5+.5*center-bad,center,bad


def main():
    rows=[]
    for m in (2,5,10,50,500,5000):
        probability,center,bad=service(m)
        lower=.5-.75**(2*m)
        upper=.5+.5/math.sqrt(m+1)
        assert lower<=probability<=upper
        rows.append({"N":2*m,"demands":[1,m-1],"mean_count_service":1.,"actual_service":probability,
            "central_binomial_mass":center,"bad_high_zero_and_total_sufficient":bad,
            "proved_interval":[lower,upper]})
    errors=[]
    for n in (4,6,10):
        actual=0.
        for a in range(n+1):
            for b in range(n-a+1):
                mass=math.factorial(n)/(math.factorial(a)*math.factorial(b)*math.factorial(n-a-b))*.25**(a+b)*.5**(n-a-b)
                actual+=mass*(a>=1 and a+b>=n//2)
        errors.append(abs(actual-service(n//2)[0]))
        assert errors[-1]<1e-12
    save_service(81,{"question":"Does increasing batch size make a mean-boundary service indicator reliable?",
        "assumptions":__doc__,"headline":{"full_multinomial_checks":len(errors),"max_error":max(errors)},
        "proof":"Full service iff A>=1 and T=A+B>=m. T~Bin(2m,1/2), so service=1/2+P(T=m)/2-P(A=0,B>=m). The subtracted term is at most(3/4)^(2m). Central mass=product(k=1..m)(1-1/(2k))<=exp(-H_m/2)<=1/sqrt(m+1). Thus service tends to1/2 although the mean-count indicator is1.",
        "scope":"Special symmetric example, not a universal one-half limit for arbitrary multi-grade demand boundaries.","rows":rows},__file__)


if __name__=="__main__":
    main()
