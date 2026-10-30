import hashlib
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path('C:/Users/uuuwk/karissa/OPT1/OPT1')
BUILD = ROOT / '.build/opt1_presentation_v2'
FINAL = ROOT / 'output/presentations/OPT1_研究主軸與執行邏輯_口語版_v2.pptx'
ORIGINAL = ROOT / 'output/presentations/OPT1_研究入門與教授報告_20261030.pptx'
N = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
     'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
     'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart'}
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
compact = lambda text: re.sub(r'\s+', '', text)
manifest = json.loads((BUILD / 'slide_manifest.json').read_text(encoding='utf-8'))
spoken_md = (ROOT / 'output/presentations/OPT1_逐頁口語講稿_v2.md').read_text(encoding='utf-8')
with zipfile.ZipFile(FINAL) as z:
    slide_parts = [x for x in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml', x)]
    note_parts = [x for x in z.namelist() if re.fullmatch(r'ppt/notesSlides/notesSlide\d+\.xml', x)]
    assert len(slide_parts) == len(note_parts) == 26
    texts, flow_counts = [], {}
    for row in manifest['slides']:
        num = row['page']
        tree = ET.fromstring(z.read(f'ppt/slides/slide{num}.xml'))
        text = '\n'.join(e.text or '' for e in tree.findall('.//a:t', N))
        texts.append(text)
        notes = ET.fromstring(z.read(f'ppt/notesSlides/notesSlide{num}.xml'))
        note_text = '\n'.join(e.text or '' for e in notes.findall('.//a:t', N))
        assert compact(row['spoken']) in compact(note_text), f'Speaker mismatch page {num}'
        assert row['spoken'] in spoken_md, f'Markdown mismatch page {num}'
        assert '資料來源' in note_text
        if num in manifest['flowSlides']:
            count = len(tree.findall('.//p:cxnSp', N))
            flow_counts[num] = count
            assert count > 0, f'Missing editable connections page {num}'
    assert '論文主要結果放在服務可行性與投入判斷' not in '\n'.join(texts)
    assert '92.70%' in texts[13]
    assert '77.81%' in texts[14]
    assert '高品86' in compact(texts[12])
    assert '成功13件' in compact(texts[12])
    assert '高品100' in compact(texts[12])
    chart_names = [x for x in z.namelist() if re.fullmatch(r'ppt/(?:slides/)?charts/chart\d+\.xml', x)]
    assert len(chart_names) == 1
    chart = ET.fromstring(z.read(chart_names[0]))
    chart_values = [float(x.text) for x in chart.findall('.//c:numLit/c:pt/c:v', N)]
with zipfile.ZipFile(ORIGINAL) as z:
    original_chart_name = next(x for x in z.namelist() if re.fullmatch(r'ppt/(?:slides/)?charts/chart\d+\.xml', x))
    original_chart = ET.fromstring(z.read(original_chart_name))
    original_values = [float(x.text) for x in original_chart.findall('.//c:numLit/c:pt/c:v', N)]
assert chart_values == original_values
assert sha(ORIGINAL) == '9e375ce8f7f6f17695e479141bdfcec3b5bf0220b715e8ce07e47f3418668391'
frozen = json.loads((ROOT / 'research/2026-10-30/frozen_results_before_review.json').read_text(encoding='utf-8-sig'))
changed = [name for name, digest in frozen.items() if sha(ROOT / name) != digest]
assert not changed, changed
receipt = json.loads((BUILD / 'validation.json').read_text(encoding='utf-8'))
assert receipt['finalSha256'] == sha(FINAL)
report = {'status': 'pass', 'final_sha256': sha(FINAL), 'slides': 26, 'matched_spoken_notes': 26,
          'editable_flow_connector_counts': flow_counts, 'native_tables': len(manifest['tables']),
          'chart_values_preserved': chart_values, 'original_pptx_unchanged': True,
          'historical_json_unchanged': len(frozen), 'claim_boundary':
          'Package, narration consistency, arithmetic display and provenance-preservation checks. Visual QA was performed separately in the authoring renderer; native PowerPoint execution was not tested.'}
(BUILD / 'content_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
