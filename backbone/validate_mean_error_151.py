"""Cross-check all 151 middle profiles using return-law tails and saved flow cache.

Different integration from ExactQualityService.conditional: precompute the
unlimited return law conditional on A, accumulate mass by required integer return
k=ceil((D1-A-EPS)/eta), then integrate saved (N,L) groups. No Monte Carlo and no
new science assumptions. Shares binomial primitives; not a fully independent
software implementation or empirical validation.
"""
import gc
import json
import math
from hashlib import sha256
from pathlib import Path
import numpy as np
from backbone.stochastic_setup_frontier import StochasticSetupFrontier
from backbone.integer_rework import release_integer_caches

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "research/2026-10-28/service_rounds"
OUT = ROOT / "research/2026-10-30/mean_error_151"


def main():
    data = json.loads((OUT / "results.json").read_text(encoding="utf-8"))
    p = json.loads((OLD / "round63.json").read_text(encoding="utf-8"))
    with np.load(OLD / "round71_physical_cache.npz", allow_pickle=False) as stored:
        groups, weights, offsets = (stored[k] for k in ("groups", "weights", "offsets"))
    checks = []
    for d in sorted({tuple(r["demands"]) for r in data["rows"]}):
        s = StochasticSetupFrontier(*p["grade_shares"], p["eligible_fraction"], d)
        curves = {}
        for row in (r for r in data["rows"] if tuple(r["demands"]) == d):
            i = row["input"]
            part = slice(int(offsets[i]), int(offsets[i+1]))
            values = []
            for n, limit in groups[part]:
                n, limit = int(n), int(limit)
                if n not in curves:
                    curve = np.zeros(s.maximum+1)
                    if n >= sum(d):
                        aa = np.arange(d[0], n+1)
                        needs = np.maximum(sum(d)-aa, 0)
                        base = float(s.a.pmf[n, aa] @ s.b.tail[n-aa, needs])
                        increments = np.zeros(s.maximum+1)
                        for a in range(min(d[0], n+1)):
                            k = int(math.ceil((d[0]-a-1e-9)/s.eta))
                            law = s.unbounded_return_law(n-a)
                            if k < len(law):
                                increments[k] += s.a.pmf[n, a]*float(law[k:].sum())
                        curve = base + np.cumsum(increments)
                    curves[n] = curve
                values.append(curves[n][limit])
            middle = float(weights[part] @ np.array(values))
            error = abs(middle-row["M"])
            assert error < 2e-10, (d, i, error)
            checks.append({"demands": list(d), "input": i, "alternative_middle": middle, "absolute_error": error})
        release_integer_caches(s)
        StochasticSetupFrontier.unbounded_return_law.cache_clear()
        del s
        gc.collect()
    assert len(checks) == 151
    result = {"scope": __doc__, "checked": len(checks), "max_absolute_error": max(x["absolute_error"] for x in checks),
              "results_sha256": sha256((OUT / "results.json").read_bytes()).hexdigest(),
              "script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(), "rows": checks}
    (OUT / "crosscheck.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k != "rows"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
