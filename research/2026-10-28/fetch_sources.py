"""Fetch explicitly selected scholarly sources; do not execute downloaded content."""

from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path
import json
import sys
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parent
SOURCES = (
    ("bitran_leong_1989_working.pdf", "https://dspace.mit.edu/bitstreams/6f069a98-3475-41ce-9bc3-165a4ecaa652/download"),
    ("bitran_leong_1992_accepted.pdf", "https://ink.library.smu.edu.sg/cgi/viewcontent.cgi?article=1154&context=sis_research"),
    ("bitran_leong_1992.pdf", "https://pubsonline.informs.org/doi/pdf/10.1287/mnsc.38.5.724"),
    ("birge_1982.pdf", "https://deepblue.lib.umich.edu/bitstream/handle/2027.42/47912/10107_2005_Article_BF01585113.pdf?sequence=1"),
    ("freeman_et_al_2021.pdf", "https://www.sciencedirect.com/science/article/pii/S030504832030726X/pdfft?isDTMRedir=true&download=true"),
    ("kolus_duffuaa_2025.pdf", "https://www.tandfonline.com/doi/pdf/10.1080/16843703.2024.2312016?download=true"),
    ("boutarfa_et_al_2024.pdf", "https://backoffice.biblio.ugent.be/download/01K5RM17B3QF2GDJ5PVJMFZHX7/01K5V8CZVN6HFDZYHTXYBR2VT5"),
    ("hoeffding_1963_scan.pdf", "https://www.cs.rpi.edu/academics/courses/spring06/random/hoefding.pdf"),
    ("hsu_bassok_1999.pdf", "https://pubsonline.informs.org/doi/pdf/10.1287/opre.47.2.277"),
    ("dodd_et_al_multiple_quality_means_author.pdf", "https://eprints.soton.ac.uk/375226/1/MultipleOptimalMeans_Manuscript.pdf"),
    ("tsai_et_al_2024.pdf", "https://www.sciencedirect.com/science/article/pii/S0305054824000169/pdfft?isDTMRedir=true&download=true"),
    ("sereshti_et_al_2026_journal.pdf", "https://www.sciencedirect.com/science/article/pii/S0377221726000056/pdfft?isDTMRedir=true&download=true"),
    ("sereshti_bodur_luedtke_2022_preprint.pdf", "https://arxiv.org/pdf/2301.00258v1"),
    ("carabelli_et_al_2026.pdf", "https://re.public.polimi.it/retrieve/66b1648a-296d-4b57-bfc6-41db79b48506/1-s2.0-S0278612526000816-main.pdf"),
    ("kohlmann_sahling_2024_full.html", "https://www.tandfonline.com/doi/full/10.1080/00207543.2024.2314717"),
    ("kohlmann_sahling_2024.pdf", "https://www.tandfonline.com/doi/pdf/10.1080/00207543.2024.2314717?download=true"),
    ("so_tang_1995.pdf", "https://pubsonline.informs.org/doi/pdf/10.1287/mnsc.41.4.620"),
    ("shen_et_al_2024_preprint.pdf", "https://arxiv.org/pdf/2411.01772"),
    ("yeh_et_al_2024.pdf", "https://link.springer.com/content/pdf/10.1007/s10479-023-05813-5.pdf"),
    ("berling_sonntag_2022.pdf", "https://madoc.bib.uni-mannheim.de/61900/1/Production%20Oper%20Manag%20-%202022%20-%20Berling%20-%20Inventory%20control%20in%20production%20inventory%20systems%20with%20random%20yield%20and%20rework%20.pdf"),
    ("gerchak_et_al_1996.pdf", "https://www.tandfonline.com/doi/pdf/10.1080/07408179608966286?download=true"),
)


def fetch(source):
    name, url = source
    record = {"filename": name, "requested_url": url}
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/pdf,text/html;q=0.9,*/*;q=0.8"})
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read(20_000_001)
            record.update(status=response.status, final_url=response.url, content_type=response.headers.get("Content-Type", ""))
        if len(data) > 20_000_000:
            raise ValueError("Source exceeds 20 MB limit")
        if name.endswith(".pdf") and not data.startswith(b"%PDF-"):
            record.update(saved=False, reason="Response was not a PDF; not saved as a paper", bytes=len(data))
        else:
            target = ROOT / name
            target.write_bytes(data)
            record.update(saved=True, bytes=len(data), sha256=sha256(data).hexdigest())
    except Exception as error:
        record.update(saved=False, error=f"{type(error).__name__}: {error}")
    print(json.dumps(record, ensure_ascii=True), flush=True)
    return record


if __name__ == "__main__":
    selected = tuple(source for source in SOURCES if not sys.argv[1:] or source[0] in sys.argv[1:])
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(fetch, selected))
    manifest = ROOT / "access_manifest.json"
    previous = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else []
    combined = {record["filename"]: record for record in previous}
    combined.update({record["filename"]: record for record in records})
    manifest.write_text(json.dumps(list(combined.values()), ensure_ascii=False, indent=2), encoding="utf-8")
