"""Frozen round79 false-80 points: separate initial-count and future-success means.

No new model, input grid, distribution, route, or policy optimization. C is
the comparator averaging initial classes AND future successes; M retains random
initial counts but uses eta*r; T is saved full finite-batch/binomial service.
C-T=(C-M)+(M-T) is an ordered, signed decomposition, not a causal/Shapley split.
The return RULE is shared; realized return quantities need not be identical.
"""
import csv
import gc
import json
import time
from datetime import datetime, timezone, timedelta
from hashlib import sha256
from pathlib import Path

from backbone.round76_certainty_equivalent_audit import mean_success_service
from backbone.stochastic_setup_frontier import StochasticSetupFrontier
from backbone.integer_rework import release_integer_caches

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "research/2026-10-28/service_rounds"
OUT = ROOT / "research/2026-10-30/mean_error_151"


def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def main():
    start = time.perf_counter()
    OUT.mkdir(parents=True, exist_ok=True)
    frozen = {str(p.relative_to(ROOT)): digest(p) for p in sorted(OLD.glob("round*.json"))}
    previous = json.loads((OLD / "round79.json").read_text(encoding="utf-8"))
    params = json.loads((OLD / "round63.json").read_text(encoding="utf-8"))
    selection = [{"demands": list(map(int, case["demands"])), "input": p["input"],
                  "C": p["matched_CE"], "T": p["finite_batch"]}
                 for case in previous["cases"] for p in case["points"]
                 if p["matched_CE"] >= .8 and p["finite_batch"] < .8]
    assert len(selection) == 151
    # Persist the entire selected set before evaluating the new middle profile.
    (OUT / "frozen_selection.json").write_text(json.dumps({"criterion": "C>=.8 and T<.8 in saved round79 grid",
        "round79_sha256": digest(OLD / "round79.json"), "points": selection}, ensure_ascii=False, indent=2), encoding="utf-8")
    rows = []
    summaries = []
    for d in sorted({tuple(p["demands"]) for p in selection}):
        solver = StochasticSetupFrontier(*params["grade_shares"], params["eligible_fraction"], d)
        selected = [p for p in selection if tuple(p["demands"]) == d]
        for p in selected:
            middle = mean_success_service(solver, float(p["input"]))
            initial = p["C"] - middle
            future = middle - p["T"]
            total = p["C"] - p["T"]
            assert abs(initial + future - total) < 1e-13
            row = {**p, "M": middle, "C_minus_T": total, "C_minus_M": initial,
                   "M_minus_T": future, "initial_signed_fraction": initial / total,
                   "future_signed_fraction": future / total,
                   "middle_says80": middle >= .8}
            rows.append(row)
        group = rows[-len(selected):]
        summaries.append({"demands": list(d), "points": len(group),
            "inputs": [min(x["input"] for x in group), max(x["input"] for x in group)],
            "initial_signed_fraction_range": [min(x["initial_signed_fraction"] for x in group), max(x["initial_signed_fraction"] for x in group)],
            "future_component_pp_range": [100*min(x["M_minus_T"] for x in group), 100*max(x["M_minus_T"] for x in group)],
            "middle_false80_count": sum(x["middle_says80"] for x in group)})
        (OUT / "checkpoint.json").write_text(json.dumps({"complete": False, "completed": len(rows), "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(summaries[-1], ensure_ascii=False), flush=True)
        release_integer_caches(solver)
        StochasticSetupFrontier.unbounded_return_law.cache_clear()
        del solver
        gc.collect()
    # Existing independently simulated round80 witness is an overlap check;
    # it is not fresh independent validation of every one of the 151 points.
    r80 = json.loads((OLD / "round80.json").read_text(encoding="utf-8"))
    overlap = []
    for row in rows:
        witness = next((x for x in r80["rows"] if list(map(int, x["demands"])) == row["demands"] and x["input"] == row["input"]), None)
        if witness:
            error = abs(row["M"] - witness["exact_mean_success"])
            assert error < 1e-11
            overlap.append({"demands": row["demands"], "input": row["input"], "middle_absolute_error": error})
    assert all(digest(ROOT / name) == value for name, value in frozen.items())
    result = {"created_at": datetime.now(timezone(timedelta(hours=8))).isoformat(), "scope": __doc__,
        "selection_size": len(rows), "summaries": summaries,
        "headline": {"initial_signed_fraction_range": [min(x["initial_signed_fraction"] for x in rows), max(x["initial_signed_fraction"] for x in rows)],
                     "largest_abs_future_component_pp": max(100*abs(x["M_minus_T"]) for x in rows),
                     "middle_false80_count": sum(x["middle_says80"] for x in rows),
                     "opposite_signed_components": sum(x["C_minus_M"]*x["M_minus_T"] < 0 for x in rows)},
        "validation": {"historical_json_unchanged": len(frozen), "round80_overlap": overlap,
                       "limitations": "New M uses existing conditional tail evaluator; only overlapping witnesses had prior independent simulation. No new factory data."},
        "source_hashes": {**{name: digest(ROOT / name) for name in frozen if name.endswith(("round63.json", "round79.json", "round80.json"))},
            "backbone/mean_error_151_decomposition.py": digest(Path(__file__)),
            "backbone/round76_certainty_equivalent_audit.py": digest(ROOT / "backbone/round76_certainty_equivalent_audit.py"),
            "backbone/exact_quality_service.py": digest(ROOT / "backbone/exact_quality_service.py")},
        "elapsed_seconds": time.perf_counter()-start, "rows": rows}
    (OUT / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    with (OUT / "results.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (OUT / "checkpoint.json").write_text(json.dumps({"complete": True, "completed": len(rows), "results_sha256": digest(OUT / "results.json")}, indent=2), encoding="utf-8")
    print(json.dumps(result["headline"], ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
