"""One normal download attempt per priority publisher/repository URL; no bypass."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from hashlib import sha256
from pathlib import Path
import json
import sys
import urllib.request

ROOT = Path(__file__).resolve().parent / "literature"
SOURCES = (
    ("tsai_2024.pdf", "https://www.sciencedirect.com/science/article/pii/S0305054824000169/pdfft?isDTMRedir=true&download=true"),
    ("hsu_bassok_1999.pdf", "https://pubsonline.informs.org/doi/pdf/10.1287/opre.47.2.277"),
    ("bitran_leong_1992.pdf", "https://pubsonline.informs.org/doi/pdf/10.1287/mnsc.38.5.724"),
    ("bitran_leong_1992_accepted.pdf", "https://ink.library.smu.edu.sg/cgi/viewcontent.cgi?article=1154&context=sis_research"),
)
RELATED = (
    ("chen_kouvelis_biazaran_2018_author.pdf", "https://facultystaff.richmond.edu/~bchen/Research/OperFlexibility2018.pdf"),
    ("jiang_et_al_2017.pdf", "https://www.tandfonline.com/doi/pdf/10.1080/00207543.2016.1193245?download=true"),
)

def fetch(spec):
    name, url = spec
    row = {"filename": name, "requested_url": url, "attempted_at": datetime.now(timezone(timedelta(hours=8))).isoformat()}
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/pdf,text/html;q=0.9"})
        with urllib.request.urlopen(request, timeout=25) as response:
            data = response.read(20_000_001)
            row.update(status=response.status, final_url=response.url, content_type=response.headers.get("Content-Type"), bytes=len(data))
        if len(data) > 20_000_000:
            raise ValueError("Over 20 MB")
        row["saved"] = data.startswith(b"%PDF-")
        if row["saved"]:
            from pypdf import PdfReader
            import io
            row["pages"] = len(PdfReader(io.BytesIO(data)).pages)
            (ROOT / name).write_bytes(data)
            row["sha256"] = sha256(data).hexdigest()
        else:
            row["reason"] = "Non-PDF response rejected; not full text acquired"
    except Exception as error:
        row.update(saved=False, error=f"{type(error).__name__}: {error}")
    print(json.dumps(row), flush=True)
    return row

if __name__ == "__main__":
    ROOT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(fetch, RELATED if "--related" in sys.argv else SOURCES))
    target = ROOT / ("related_download_attempts.json" if "--related" in sys.argv else "download_attempts.json")
    target.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
