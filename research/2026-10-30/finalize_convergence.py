"""Save reading depth, connect current notes, and audit immutable results/links."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone, timedelta
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = HERE.parent / "2026-10-28"


def append_once(path, marker, body):
    text = path.read_text(encoding="utf-8")
    if marker not in text:
        path.write_text(text.rstrip()+"\n\n"+body.strip()+"\n", encoding="utf-8")


def main():
    now = datetime.now(timezone(timedelta(hours=8))).isoformat()
    lit = HERE / "literature"
    reading = []
    for name, pages, version, url in (
        ("chen_kouvelis_biazaran_2018_author.pdf", [1,3,4,5,6,7,8,11,12,13,14], "18-page author manuscript, journal citation 2018; not pagewise reconciled with journal", "https://facultystaff.richmond.edu/~bchen/Research/OperFlexibility2018.pdf"),
        ("jiang_et_al_2017.pdf", [2,3,4,5,6,7,10,11,12], "22-page journal PDF, includes cover; article pp38-58", "https://doi.org/10.1080/00207543.2016.1193245")):
        path = lit / name
        from pypdf import PdfReader
        assert path.read_bytes().startswith(b"%PDF-")
        reading.append({"file": name, "sha256": sha256(path.read_bytes()).hexdigest(),
            "pdf_pages": len(PdfReader(path).pages), "version": version, "read_pdf_pages": pages,
            "rendered_and_viewed_pages": [5], "source_url": url, "all_pages_read": False})
    (lit / "reading_log.json").write_text(json.dumps({"updated_at": now, "sources": reading,
        "priority_full_texts_still_missing": ["Tsai et al 2024", "Hsu and Bassok 1999", "Bitran and Leong 1992"],
        "search_scope": "Targeted DOI/title, author/repository searches plus upgrading/joint-service neighbors; not a systematic review",
        "access_note": "Web tool and local download are different contexts; VPN does not guarantee publisher entitlement in either. MIT web429 not repeatedly retried."}, ensure_ascii=False, indent=2), encoding="utf-8")
    beginner = HERE / "從零理解_研究目標與現況.md"
    text = beginner.read_text(encoding="utf-8")
    text = text.replace("只補必要缺口；151個誤判點拆分尚未完成", "10/30已完成151個誤判點拆分及交叉核對；只補影響主張的必要缺口")
    beginner.write_text(text, encoding="utf-8")
    append_once(beginner, "10/30下午新增進展", "10/30下午新增進展見[收斂推進：本次成果與教授決策](收斂推進_本次成果與教授決策.md)：補讀兩篇新全文關鍵模型，完成151點拆分；三篇直接全文仍待補。")
    append_once(OLD / "論文主軸與章節草稿.md", "10/30限定補充", """
## 10/30限定補充：第二與第五章

第二章補入Chen/Kouvelis/Biazaran品質後升級作者稿、Jiang等共同服務期刊PDF。品質後升級、單門檻與共同服務已有前例，不作各別首創。實際閱讀範圍、版本與式號見[新全文比較](../2026-10-30/literature/全文閱讀與差異核對.md)。三篇直接全文尚待補，整合差異維持候選。

第五章補入[151點順序拆分](../2026-10-30/mean_error_151/結果判讀.md)。固定原C≥.8、T<.8子集，新增初次計數隨機、成功取ηr的M；151點全部M<.8，原高估14.10–45.59百分點，|M−T|最大1.59024百分點。初次分量約100%–106.24%，超過100%表示帶符號抵銷，不是因果解釋率。替代積分151點最大差1.63e−14，但共用二項表，無新現場資料。C是本文指定比較器，不指稱Bitran或Tsai採同一算子。
""")
    append_once(OLD / "文獻差異與候選貢獻矩陣.md", "10/30新增兩篇全文", """
## 10/30新增兩篇全文

Chen/Kouvelis/Biazaran18頁作者稿、Jiang等22頁期刊PDF已取得並讀關鍵模型。品質後升級、門檻政策、共同服務均已有前例；本案只能就已限定問題和可核對計算提出候選差異。[閱讀深度與具體模型對照](../2026-10-30/literature/全文閱讀與差異核對.md)。新書目另存該literature資料夾references.bib；不以新增兩篇代替三篇未取得的直接全文。
""")
    builder = OLD / "build_review_entry.py"
    text = builder.read_text(encoding="utf-8")
    text = text.replace("本次10月30日只核對文稿與安排報告，沒有重跑58–84或新增機制。", "10月30日依新授權完成151點拆分、補讀兩篇新全文，沒有重跑58–84或新增機制。")
    marker = "最新收斂先看"
    if marker not in text:
        text = text.replace("初次閱讀先看{link", "最新收斂先看[本次成果與教授決策](C:/Users/uuuwk/karissa/OPT1/OPT1/research/2026-10-30/收斂推進_本次成果與教授決策.md)。\n\n初次閱讀先看{link", 1)
    builder.write_text(text, encoding="utf-8")
    append_once(ROOT / "進度.md", "10/30下午：限定收斂補充", """
## 10/30下午：限定收斂補充（不是新增製程機制）

依新授權完成原79輪151個誤判80%點的C/M/T拆分；所有M<.8，|M−T|最大1.59024百分點。另一路回流尾機率積分151點最大差1.63e−14，原63份round*.json SHA不變。結果JSON/CSV與判讀在research/2026-10-30/mean_error_151/。

新取得Chen等品質後升級18頁作者稿及Jiang等共同服務22頁期刊PDF，閱讀深度明列；品質後升級、單門檻、共同服務不是各別首創。三直接全文正常下載仍403／Cookie／HTML，沒有取得則不作排除判定。入口research/2026-10-30/收斂推進_本次成果與教授決策.md。沒有重跑58–84、沒有新分布／路徑／多期，沒有重建夜間排程。
""")
    append_once(HERE.parent / "overnight_handoff.md", "10/30下午新授權收斂工作", """
## 10/30下午新授權收斂工作

原夜間兩批已停止；本次是新的使用者授權。151點拆分與替代積分全部完成，勿重做。新取得Chen品質後升級作者稿與Jiang共同服務期刊PDF，只精讀reading_log所列頁；三優先全文仍未取得。最新入口research/2026-10-30/收斂推進_本次成果與教授決策.md。無背景程序、無排程；保留第58–84輪和63份歷史round JSON。
""")
    frozen = json.loads((HERE / "frozen_results_before_review.json").read_text(encoding="utf-8"))
    assert all(sha256((ROOT/name).read_bytes()).hexdigest() == expected for name,expected in frozen.items())
    local = []
    for doc in [HERE/"收斂推進_本次成果與教授決策.md", HERE/"mean_error_151/結果判讀.md", lit/"全文閱讀與差異核對.md", lit/"手動下載_三篇優先全文.md"]:
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', doc.read_text(encoding="utf-8")):
            if target.startswith(("http:", "https:", "#")):
                continue
            path = Path(target.split("#",1)[0])
            if not path.is_absolute():
                path = doc.parent / path
            assert path.exists(), str(path)
            local.append(str(path))
    cross = json.loads((HERE / "mean_error_151/crosscheck.json").read_text(encoding="utf-8"))
    assert cross["checked"] == 151
    assert cross["results_sha256"] == sha256((HERE/"mean_error_151/results.json").read_bytes()).hexdigest()
    report = {"checked_at": now, "historical_json_unchanged": len(frozen), "new_local_links_checked":len(local),
              "crosschecked_points":151, "max_absolute_error":cross["max_absolute_error"], "new_pdfs":reading,
              "new_mechanisms":False, "reran_58_to_84":False, "passed":True}
    (HERE / "convergence_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k != "new_pdfs"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
