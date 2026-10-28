"""Round57: process names do not support sending every grade-upgrade to station2.

The local source, PDFp11, names centre-hole grinding as e3, external-diameter fine
grinding as e4, screw-diameter fine grinding as e5. Explore matched single-station
retouch candidates with their own spare capacity and unit cost. Normal KQC source
only, since tail direction cannot be inferred from rounded pass probabilities.
Increasing/decreasing characteristic values is hypothetical; the source does not
establish actual rework feasibility, eta, no collateral quality damage, or whether
downstream operations must be repeated. Treat this as an optimistic route audit.
"""
from functools import lru_cache
import gc
from backbone.exact_quality_economics import *
from backbone.exact_batch_quality import clear_solver_caches
from backbone.round42_one_sided_repair import one_sided_bounds
from backbone.round48_exact_quality_profit import brute_net_revenue


class RouteEconomics(ExactQualityEconomics):
    def __init__(self,q1,q2,f,d,station_index):
        super().__init__(q1,q2,f,d)
        self.station_index=station_index
        self.return_cost=MANUFACTURING_COSTS[station_index]
        assert 90*self.eta>30+self.return_cost

    @lru_cache(maxsize=None)
    def net_revenue_and_return(self,n,spare):
        revenue=self.no_return_revenue(n)
        sent=gain=0.
        for a,prob in enumerate(self.a.pmf[n,:n+1]):
            if prob<1e-300:
                continue
            r=self.expected_return(n-a,spare)
            fill=self.expected_return(n-a,min(spare,max(self.d1-a,0.)/self.eta))
            sent+=prob*r
            gain+=prob*((90*self.eta-30-self.return_cost)*r+30*self.eta*fill)
        return revenue+gain,sent

    def evaluate_route(self,raw,setup):
        flow=forward(raw)
        n=np.floor(flow.finished+1e-9).astype(int)
        j=self.station_index
        spare=np.maximum(CAPS[:,j]-flow.loads[:,j]-setup,0.)
        groups,inverse=np.unique(np.stack((n,spare),axis=1),axis=0,return_inverse=True)
        weights=np.bincount(inverse,weights=PROB,minlength=len(groups))
        values=np.array([self.net_revenue_and_return(int(n),float(l)) for n,l in groups])
        service=np.array([self.conditional(int(n),float(l)) for n,l in groups])
        cost=mean(flow.loads[:,0]*MATERIAL_COST+np.sum(flow.loads*MANUFACTURING_COSTS,axis=1))
        return {"expected_profit":float(weights@values[:,0])-cost,
                "fulfilment_probability":float(weights@service),"expected_rework":float(weights@values[:,1]),
                "capacity_groups":len(groups)}


def main():
    quality,bounds=one_sided_bounds()
    q1,q2=quality["implied_grade1_share"],quality["implied_grade2_share"]
    d=(750.,150.)
    raw=required_input(d,(q1,q2),STATIONS,1)
    rows=[]
    checks=[]
    for j in (1,2,3,4):
        solver=RouteEconomics(.5,.3,.2,(8,2),j)
        for spare in (0.,1.5,12.):
            original,r=brute_net_revenue(18,.5,.3,.2,(8,2),spare)
            expected=original-(MANUFACTURING_COSTS[j]-5.5)*r
            exact,sent=solver.net_revenue_and_return(18,spare)
            checks.append(abs(exact-expected))
            assert checks[-1]<1e-8 and abs(sent-r)<1e-10
        clear_solver_caches(solver)
        RouteEconomics.net_revenue_and_return.cache_clear()
    candidates=((1,2,"increase_value_bound"),(2,3,"decrease_value_bound"),(3,4,"decrease_value_bound"))
    for feature_index,station_index,direction in candidates:
      feature=bounds[feature_index]
      for label,f in (("bidirectional_optimistic",feature["bidirectional_bound"]),
                      ("one_direction_optimistic",feature[direction])):
        solver=RouteEconomics(q1,q2,f,d,station_index)
        for setup in (0.,STATIONS[station_index].machine_capacity):
            rows.append({"KQC_name":feature["KQC_name"],"candidate_return_station":station_index+1,
                "direction":direction,"eligibility_model":label,"eligible_fraction":f,
                "return_unit_cost":MANUFACTURING_COSTS[station_index],"setup_workload":setup,
                "setup_interpretation":"zero or one machine-period capacity equivalent; not measured hours",
                **solver.evaluate_route(raw,setup)})
        clear_solver_caches(solver)
        RouteEconomics.net_revenue_and_return.cache_clear()
        del solver
        gc.collect()
    save_service(57,{"question":"Do the named source processes and one-direction repair eligibility support the original all-to-station2 upgrade interpretation?",
        "assumptions":__doc__,"grade_shares":[q1,q2],"input":raw,"demands":d,
        "source_process_names":{"e1":"left-end centre-hole fine drilling","e2":"bottom-diameter fine grinding",
            "e3":"centre-hole grinding","e4":"external-diameter fine grinding","e5":"screw-diameter fine grinding"},
        "caution":"Only process names are sourced. Matching a feature name to a retouch station, direction, eta=.97 and preservation of all other KQCs are exploratory assumptions; retest/routing data remain necessary.",
        "headline":{"route_cases":len(rows),"small_brute_cost_checks":len(checks),"max_revenue_error":max(checks)},"rows":rows},__file__,
        (ROOT/"backbone"/"exact_quality_economics.py",ROOT/"backbone"/"exact_quality_service.py",
         ROOT/"backbone"/"quality_lab.py",ROOT/"backbone"/"round42_one_sided_repair.py",
         ROOT/"backbone"/"round48_exact_quality_profit.py",
         ROOT/"paper"/"Assessing system reliability in multi-grade production under different demand fulfilment policies via a multistate flow network.pdf"))


if __name__=="__main__":
    main()
