"""Reproduce rounds33-39 after the service kernel was extended; validate hashes."""
from contextlib import redirect_stdout
from datetime import datetime,timezone
from hashlib import sha256
from pathlib import Path
import io
import json
import runpy
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
MODULES=("backbone.round33_service_constraint","backbone.round34_service_capacity",
    "backbone.round35_release_service","backbone.round36_critical_release",
    "backbone.round37_material_commitment","backbone.round38_upstream_control",
    "backbone.round39_coordinated_commitment")


def main():
    records=[]
    for number,module in zip(range(33,40),MODULES):
        started=time.perf_counter()
        with redirect_stdout(io.StringIO()):
            runpy.run_module(module,run_name="__main__")
        payload=json.loads((HERE/f"round{number}.json").read_text(encoding="utf-8"))
        assert abs(payload["provenance"]["probability_mass"]-1)<1e-10
        for relative,expected in payload["provenance"]["sha256"].items():
            assert sha256((ROOT/relative).read_bytes()).hexdigest()==expected,relative
        elapsed=time.perf_counter()-started
        records.append({"round":number,"passed":True,"elapsed_seconds":elapsed,"module":module})
        print(f"Round {number}: passed ({elapsed:.2f}s)",flush=True)
    checks=[]
    for filename,resultfile in (("check_service.py","service_check.json"),("check_coordinated.py","coordinated_check.json")):
        with redirect_stdout(io.StringIO()):
            runpy.run_path(str(HERE/filename),run_name="__main__")
        checks.append({"checker":filename,"checker_sha256":sha256((HERE/filename).read_bytes()).hexdigest(),
                       "result":json.loads((HERE/resultfile).read_text(encoding="utf-8"))})
        print(f"Independent check {filename}: passed",flush=True)
    manifest={"completed_at_utc":datetime.now(timezone.utc).isoformat(),"rounds":records,
              "checks":checks,"run_all_sha256":sha256(Path(__file__).read_bytes()).hexdigest()}
    (HERE/"validation_run.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")


if __name__=="__main__":
    main()
