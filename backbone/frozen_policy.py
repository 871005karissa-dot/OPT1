"""Portable binary decisions, indexed only by observed initial A and available R.

Packed truth tables make the executed decision independent of floating-point
tail/ratio tie comparisons on a different runtime. They do not make a fitted
probability law transferable to another plant, order or repair route.
"""
from hashlib import sha256
from pathlib import Path
import numpy as np


class FrozenPolicy:
    def __init__(self,path,key,expected_sha256):
        path=Path(path)
        if sha256(path.read_bytes()).hexdigest()!=expected_sha256:
            raise ValueError("Policy archive hash does not match the recorded artifact")
        with np.load(path,allow_pickle=False) as archive:
            shape=tuple(map(int,archive["shape"]))
            self.decisions=np.unpackbits(archive[key],count=int(np.prod(shape)),bitorder="big").reshape(shape).astype(bool)

    def decide(self,a,available_return):
        a,r=np.broadcast_arrays(np.asarray(a),np.asarray(available_return))
        if np.any(a!=a.astype(int)) or np.any(r!=r.astype(int)):
            raise ValueError("Initial grade1 and available return counts must be integers")
        a,r=a.astype(int),r.astype(int)
        if np.any(a<0) or np.any(r<0) or np.any(a>=self.decisions.shape[0]) or np.any(r>=self.decisions.shape[1]):
            raise ValueError("Observed counts are outside this frozen policy domain")
        return self.decisions[a,r]
