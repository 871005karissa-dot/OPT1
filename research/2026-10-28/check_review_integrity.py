"""Check review links, source manifests, PDF pages and bibliography keys."""
from datetime import datetime,timezone
from hashlib import sha256
from pathlib import Path
import json,re
from pypdf import PdfReader

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def main():
    documents=[HERE/name for name in ("明晚審閱入口.md","最小模型規格_v0.1.md","論文主軸與章節草稿.md",
        "資料需求與識別.md","平均品質近似文獻定位.md","文獻差異與候選貢獻矩陣.md","命題條件與證明稽核.md")]
    local=[]
    for document in documents:
        body=document.read_text(encoding="utf-8")
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',body):
            if target.startswith(("http:","https:","#")):
                continue
            target=target.strip("<>").split("#",1)[0]
            path=Path(re.sub(r':\d+$','',target))
            if not path.is_absolute():
                path=document.parent/path
            local.append({"document":document.name,"target":target,"exists":path.exists()})
    assert all(x["exists"] for x in local),[x for x in local if not x["exists"]]
    manifest=json.loads((HERE/"service_figure_manifest.json").read_text(encoding="utf-8"))
    for name,digest in manifest["source_sha256"].items():
        assert sha256((ROOT/name).read_bytes()).hexdigest()==digest,("stale figure source",name)
    pdf=ROOT/manifest["output"]
    reader=PdfReader(pdf)
    assert len(reader.pages)==manifest["pages"]==3
    assert all(page.extract_text().strip() for page in reader.pages)
    keys=re.findall(r'@\w+\s*\{\s*([^,]+),',(HERE/"references.bib").read_text(encoding="utf-8"))
    assert len(keys)==len(set(keys)),"Duplicate bibliography keys"
    report={"checked_at_utc":datetime.now(timezone.utc).isoformat(),"passed":True,
        "local_links":local,"source_manifest_inputs":len(manifest["source_sha256"]),
        "pdf_pages":len(reader.pages),"pdf_sha256":sha256(pdf.read_bytes()).hexdigest(),
        "bibliography_keys":len(keys),
        "scope":"Local existence, recorded figure-source hashes, page text and unique keys only. Visual PDF review was performed separately; external URLs, citation semantics and novelty are not certified."}
    (HERE/"review_integrity.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"passed":True,"local_links":len(local),"pdf_pages":len(reader.pages),"bibliography_keys":len(keys)}))


if __name__=="__main__":
    main()
