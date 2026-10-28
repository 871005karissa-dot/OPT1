"""Reproduce rounds40-43 and independently validate the quality extension."""
from contextlib import redirect_stdout
from datetime import datetime,timezone
from hashlib import sha256
from pathlib import Path
import io
import json
import runpy
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
MODULES=("backbone.round40_quality_recoverability","backbone.round41_selective_upgrade",
         "backbone.round42_one_sided_repair","backbone.round43_failed_return_fate")


def main():
    for number,module in zip(range(40,44),MODULES):
        with redirect_stdout(io.StringIO()):
            runpy.run_module(module,run_name="__main__")
        payload=json.loads((HERE/f"round{number}.json").read_text(encoding="utf-8"))
        for relative,expected in payload["provenance"]["sha256"].items():
            assert sha256((ROOT/relative).read_bytes()).hexdigest()==expected
        print(f"Round {number}: passed",flush=True)
    with redirect_stdout(io.StringIO()):
        runpy.run_path(str(HERE/"check_quality.py"),run_name="__main__")
    result=json.loads((HERE/"quality_check.json").read_text(encoding="utf-8"))
    manifest={"completed_at_utc":datetime.now(timezone.utc).isoformat(),"rounds":list(range(40,44)),
        "independent_check":result,"checker_sha256":sha256((HERE/"check_quality.py").read_bytes()).hexdigest(),
        "runner_sha256":sha256(Path(__file__).read_bytes()).hexdigest()}
    (HERE/"validation_quality_run.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(json.dumps(result),flush=True)


if __name__=="__main__":
    main()
