"""Reproduce all six rounds and their independent LP cross-check in one process."""
from contextlib import redirect_stdout
from datetime import datetime,timezone
from hashlib import sha256
from pathlib import Path
import io
import json
import runpy
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0,str(ROOT))
MODULES = (
    "backbone.round27_service_audit", "backbone.round28_accounting_audit",
    "backbone.round29_upgrade_yield", "backbone.round30_setup_workload",
    "backbone.round31_capacity_allocation", "backbone.round32_nonanticipative_yield",
)


def main():
    records = []
    for number,module in zip(range(27,33),MODULES):
        started = time.perf_counter()
        output = io.StringIO()
        with redirect_stdout(output):
            runpy.run_module(module,run_name="__main__")
        payload = json.loads((HERE/f"round{number}.json").read_text(encoding="utf-8"))
        assert abs(payload["provenance"]["probability_mass"]-1)<1e-10
        for relative,expected in payload["provenance"]["sha256"].items():
            assert sha256((ROOT/relative).read_bytes()).hexdigest()==expected
        elapsed = time.perf_counter()-started
        records.append({"round":number,"module":module,"passed":True,"elapsed_seconds":elapsed})
        print(f"Round {number}: passed ({elapsed:.2f}s)",flush=True)
    output = io.StringIO()
    with redirect_stdout(output):
        runpy.run_path(str(HERE/"check_capacity_lp.py"),run_name="__main__")
    checks = json.loads((HERE/"capacity_lp_check.json").read_text(encoding="utf-8"))
    manifest = {"completed_at_utc":datetime.now(timezone.utc).isoformat(),"rounds":records,
                "independent_lp_checks":checks,"run_all_sha256":sha256(Path(__file__).read_bytes()).hexdigest(),
                "checker_sha256":sha256((HERE/"check_capacity_lp.py").read_bytes()).hexdigest()}
    (HERE/"validation_run.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(f"Independent checks: {checks}",flush=True)


if __name__=="__main__":
    main()
