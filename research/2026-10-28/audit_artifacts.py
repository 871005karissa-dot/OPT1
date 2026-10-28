"""Read-only consistency audit of research result sources and saved sample traces."""
from datetime import datetime,timezone
from hashlib import sha256
from pathlib import Path
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def checked_path(relative):
    target=(ROOT/relative).resolve()
    target.relative_to(ROOT.resolve())
    return target


def main():
    records=[]
    for folder in (HERE/"six_rounds",HERE/"service_rounds"):
        for path in sorted(folder.glob("round*.json")):
            result=json.loads(path.read_text(encoding="utf-8"))
            provenance=result.get("provenance")
            if provenance is None:
                continue
            for relative,expected in provenance["sha256"].items():
                assert sha256(checked_path(relative).read_bytes()).hexdigest()==expected,(path.name,relative)
            for key in ("replica_trace","trace"):
                if key in result:
                    trace=result[key]
                    assert sha256(checked_path(trace["path"]).read_bytes()).hexdigest()==trace["sha256"]
            records.append({"path":str(path.relative_to(ROOT)),"sha256":sha256(path.read_bytes()).hexdigest(),
                            "source_count":len(provenance["sha256"]),"source_and_trace_hashes_match":True})
    report={"audited_at_utc":datetime.now(timezone.utc).isoformat(),"round_outputs":len(records),
            "records":records,"audit_script_sha256":sha256(Path(__file__).read_bytes()).hexdigest(),
            "scope":"Source and saved-trace consistency, not an extra mathematical or empirical validation."}
    (HERE/"artifact_audit.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({"round_outputs":len(records),"all_source_and_trace_hashes_match":True}))


if __name__=="__main__":
    main()
