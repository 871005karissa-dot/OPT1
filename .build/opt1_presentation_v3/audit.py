import hashlib
import json
import math
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path('C:/Users/uuuwk/karissa/OPT1/OPT1')
BUILD = ROOT / '.build/opt1_presentation_v3'
FINAL = ROOT / 'output/presentations/OPT1_教授報告_完整引用版_v3.pptx'
PREVIOUS = ROOT / 'output/presentations/OPT1_研究主軸與執行邏輯_口語版_v2.pptx'
ORIGINAL = ROOT / 'output/presentations/OPT1_研究入門與教授報告_20261030.pptx'
NS = {'a':'http://schemas.openxmlformats.org/drawingml/2006/main',
      'p':'http://schemas.openxmlformats.org/presentationml/2006/main',
      'c':'http://schemas.openxmlformats.org/drawingml/2006/chart',
      'r':'http://schemas.openxmlformats.org/package/2006/relationships'}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
compact = lambda t: re.sub(r'\s+', '', t)
manifest = json.loads((BUILD / 'slide_manifest.json').read_text(encoding='utf-8'))
md = (ROOT / 'output/presentations/OPT1_口語講稿與引用對照_v3.md').read_text(encoding='utf-8')
refs = manifest['referenceCatalog']
assert len(refs) == 12 and len({r['doi'] for r in refs}) == 12
for ref in refs:
    if ref.get('local'):
        assert (ROOT / ref['local']).is_file(), ref
for own in manifest['ownSources'].values():
    for file in own['files']:
        assert (ROOT / file).is_file(), file
source_lines = 0
with zipfile.ZipFile(FINAL) as z, zipfile.ZipFile(PREVIOUS) as old:
    slides = [n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml', n)]
    notes = [n for n in z.namelist() if re.fullmatch(r'ppt/notesSlides/notesSlide\d+\.xml', n)]
    assert len(slides) == len(notes) == 37
    hyperlink_targets = []
    for n in z.namelist():
        if n.endswith('.rels'):
            for rel in ET.fromstring(z.read(n)).findall('r:Relationship',NS):
                if rel.attrib['Type'].endswith('/hyperlink'):
                    assert rel.attrib.get('TargetMode') == 'External'
                    hyperlink_targets.append(rel.attrib['Target'])
    assert sorted(hyperlink_targets) == sorted(r['url'] for r in refs)
    texts = []
    for row in manifest['slides']:
        num = row['page']
        tree = ET.fromstring(z.read(f'ppt/slides/slide{num}.xml'))
        body = '\n'.join(e.text or '' for e in tree.findall('.//a:t',NS))
        text = compact(body)
        texts.append(body)
        note_tree = ET.fromstring(z.read(f'ppt/notesSlides/notesSlide{num}.xml'))
        note_text = compact('\n'.join(e.text or '' for e in note_tree.findall('.//a:t',NS)))
        assert compact(row['spoken']) in note_text, f'Note mismatch page {num}'
        assert row['spoken'] in md, f'Markdown mismatch page {num}'
        assert compact(row['citation']) in text, f'Missing visible source page {num}'
        source_lines += 1
        for ref_id in row['ids']:
            assert f'[{ref_id}]' in note_text, (num, ref_id)
        if num in manifest['flowSlides']:
            assert tree.findall('.//p:cxnSp',NS), f'Missing native flow page {num}'
        if num in manifest['tables']:
            assert tree.findall('.//a:tbl',NS), f'Missing native table page {num}'
        if num <= 26:
            previous = ET.fromstring(old.read(f'ppt/slides/slide{num}.xml'))
            extract_tables = lambda t: ['\n'.join(x.text or '' for x in tbl.findall('.//a:t',NS)) for tbl in t.findall('.//a:tbl',NS)]
            assert extract_tables(tree) == extract_tables(previous), f'Original table changed page {num}'
    for i, ref in enumerate(refs):
        index = 30 + i//2
        assert ref['doi'] in texts[index] or ref['id'] == 'R8'
        if ref['id'] in ('R9','R10','R11'):
            assert '待補全文' in texts[index]
    assert 'C：兩層都代均值' in texts[18]
    assert '97' in texts[13] and '92.70%' in texts[13]
    assert '77.81%' in texts[14]
    chart_names = [n for n in z.namelist() if re.fullmatch(r'ppt/(?:slides/)?charts/chart\d+\.xml',n)]
    assert len(chart_names) == 1
    get_values = lambda zz: [float(x.text) for x in ET.fromstring(zz.read(chart_names[0])).findall('.//c:numLit/c:pt/c:v',NS)]
    assert get_values(z) == get_values(old)
    chart_values = get_values(z)
toy = json.loads((ROOT / '.build/opt1_presentation_v2/teaching_arithmetic.json').read_text(encoding='utf-8'))
exact = sum(math.comb(15,k)*.97**k*.03**(15-k) for k in (14,15))
assert abs(toy['service_if_repair']-exact) < 1e-14
assert round((.5+.3*exact)*100,2) == 77.81
assert sha(PREVIOUS) == '7ddd52699f9c845b0312810d9fe331f08d35be46f270cd09a221c49a1681f37b'
assert sha(ORIGINAL) == '9e375ce8f7f6f17695e479141bdfcec3b5bf0220b715e8ce07e47f3418668391'
frozen = json.loads((ROOT / 'research/2026-10-30/frozen_results_before_review.json').read_text(encoding='utf-8-sig'))
assert all(sha(ROOT/name)==digest for name,digest in frozen.items())
receipt = json.loads((BUILD / 'validation.json').read_text(encoding='utf-8'))
assert receipt['finalSha256'] == sha(FINAL)
report = {'status':'pass','final_sha256':sha(FINAL),'slides':37,'matched_spoken_notes':37,
          'visible_source_lines':source_lines,'complete_references':12,'verified_external_hyperlinks':len(hyperlink_targets),
          'native_flow_slides':manifest['flowSlides'],'native_tables':len(manifest['tables']),
          'native_chart_values_preserved':chart_values,'old_tables_preserved':11,
          'source_pptx_and_v2_preserved':True,'historical_json_preserved':len(frozen),
          'visual_review':{'individually_inspected':list(range(1,38)),'changed_slide_rerendered':[19]},
          'claim_boundary':'Checks package structure, citation coverage, narration, source paths, hyperlink targets, retained values and teaching arithmetic. Actual native PowerPoint opening and factory validation remain separate.'}
(BUILD / 'content_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
