"""Executor for a frozen setup table plus optional-substitution prefix.

Setup sees only initial A and available R. Substitution is limited to B<D2,
where surplus-only rework is impossible, so no repair outcome is needed to plan
it. A fine boundary may use the recorded capacity priority and initial A/B.
"""
from backbone.frozen_policy import FrozenPolicy
import numpy as np


class JointDecisionPolicy(FrozenPolicy):
    def __init__(self,path,key,expected_sha256,specification):
        super().__init__(path,key,expected_sha256)
        with np.load(path,allow_pickle=False) as archive:
            self.capacity_rank=archive["capacity_rank"].copy()
        self.spec=specification
        self.d1,self.d2=map(int,specification["demands"])
        self.boundary=specification["boundary"]

    def priority_for_indices(self,indices):
        indices=np.asarray(indices,dtype=int)
        if np.any(indices<0) or np.any(indices>=len(self.capacity_rank)):
            raise ValueError("Capacity index outside the frozen discrete source model")
        boundary=self.boundary
        if boundary is None or boundary["kind"]!="substitution":
            return np.zeros(indices.shape,dtype=int)
        fine=boundary["fine_prefix"]["boundary"]
        if fine is None:
            return np.zeros(indices.shape,dtype=int)
        return np.sign(fine["capacity_position"]-self.capacity_rank[indices])

    def substitute(self,initial_high,initial_low,priority_side):
        a,b,side=np.broadcast_arrays(np.asarray(initial_high,dtype=int),np.asarray(initial_low,dtype=int),np.asarray(priority_side,dtype=int))
        gap=self.d2-b
        eligible=(gap>0)&(a>=self.d1+gap)
        boundary=self.boundary
        if boundary is None:
            return np.zeros(a.shape,dtype=int)
        if boundary["kind"]=="setup":
            selected=30*gap<boundary["ratio"]
        else:
            k=boundary["gap"]
            fine=boundary["fine_prefix"]["boundary"]
            if fine is None:
                edge=np.full(a.shape,boundary["deterministic_fraction"]>=1-1e-10)
            else:
                edge=(side>0)|((side==0)&(a<=fine["grade1_count"]))
            selected=(gap<k)|((gap==k)&edge)
        return np.where(eligible&selected,gap,0)
