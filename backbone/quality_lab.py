"""Independent extension: inspect quality subtypes before choosing eligible returns.

Grade shares and eligible-pool fraction must come from the same probability
source. Deterministic fluid subtype proportions, not random item counts.
No station-to-quality-characteristic correspondence is claimed.
"""
from backbone.service_frontier import *


@dataclass
class QualityFlow(Flow):
    q1: float
    q2: float

    @property
    def g1(self):
        return self.finished*self.q1

    @property
    def g2(self):
        return self.finished*self.q2


def quality_forward(raw,x,q1,q2):
    upper=forward(raw).loads[:,1]
    fraction=np.where(np.abs(x-upper)<1e-10,0.,fraction_for_work(x))
    flow=forward(raw,fraction)
    return QualityFlow(flow.loads,flow.finished,q1,q2)


@dataclass
class GradeStockFlow(Flow):
    stock1: np.ndarray
    stock2: np.ndarray

    @property
    def g1(self):
        return self.stock1

    @property
    def g2(self):
        return self.stock2


def evaluate_quality(flow,d,r,eta,retention=0.):
    if retention==0.:
        return evaluate(flow,d,r,eta)
    stock=GradeStockFlow(flow.loads,flow.finished,flow.g1+eta*r,
                        flow.g2-r+retention*(1-eta)*r)
    action=evaluate(stock,d)
    action["profit"]-=r*MANUFACTURING_COSTS[1]
    action["sent"]=r.copy()
    return action


def quality_candidates(raw,d,eta,q1,q2,eligible,setup):
    rates=[s.yield_rate for s in STATIONS]
    t=float(np.prod(rates[1:]))
    upper=forward(raw).loads[:,1]
    limit=np.minimum.reduce((CAPS[:,2]*np.prod(rates[2:]),CAPS[:,3]*np.prod(rates[3:]),CAPS[:,4]*rates[4]))
    points=[upper,np.zeros(len(PROB))]
    factor=rates[1]
    for j in (2,3,4):
        points.append(CAPS[:,j]/factor)
        factor*=rates[j]
    for value in (d[0]/(q1*t),d[1]/(q2*t),sum(d)/((q1+q2)*t)):
        points.append(np.full(len(PROB),value))
    for slope,intercept in ((t,np.zeros(len(PROB))),(0.,limit)):
        lines=[(0.,np.zeros(len(PROB))),(q2*slope,q2*intercept-d[1]),
               (-1.,CAPS[:,1]-setup),(eligible*q2*slope,eligible*q2*intercept),
               (-q1*slope/eta,(d[0]-q1*intercept)/eta)]
        for i,(m1,b1) in enumerate(lines):
            for m2,b2 in lines[i+1:]:
                if abs(m1-m2)>1e-12:
                    points.append((b2-b1)/(m1-m2))
    return [np.clip(point,0.,upper) for point in points]


def quality_action_pair(raw,d,eta,q1,q2,eligible=1.,setup=350.,retention=0.):
    if not (0<eta<=1 and 0<=eligible<=1 and 0<=retention<=1 and q1>0 and q2>0 and q1+q2<=1+1e-10):
        raise ValueError("invalid quality or rework parameter")
    best=serve=None
    found=np.zeros(len(PROB),dtype=bool)
    best_x=np.zeros(len(PROB))
    count=0
    for x in quality_candidates(raw,d,eta,q1,q2,eligible,setup):
        flow=quality_forward(raw,x,q1,q2)
        cap=np.minimum(available_returns(flow,d,setup),eligible*flow.g2)
        gap=np.maximum(d[0]-flow.g1,0.)
        for r in np.sort(np.stack((np.zeros(len(PROB)),cap,np.minimum(cap,gap/eta))),axis=0):
            candidate=evaluate_quality(flow,d,r,eta,retention)
            count+=1
            if best is None:
                best={key:value.copy() for key,value in candidate.items()}
                serve={key:value.copy() for key,value in candidate.items()}
                best_x=x.copy()
            else:
                best,improve=pick(best,candidate)
                best_x=np.where(improve,x,best_x)
            choose=candidate["met"]&(~found|(candidate["profit"]>serve["profit"]+1e-8))
            serve={key:np.where(choose,candidate[key],value) for key,value in serve.items()}
            found|=candidate["met"]
    flow=quality_forward(raw,best_x,q1,q2)
    assert np.all(best["sent"]<=eligible*flow.g2+EPS)
    assert np.all(best["sent"]<=available_returns(flow,d,setup)+EPS)
    return best,serve,found,count
