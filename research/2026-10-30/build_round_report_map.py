"""Map the existing84 research records to six talks; never run experiments."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent


def classification(i):
    if i<=4:
        return "重現基礎", "第二章／案例來源"
    if i in (7,8,9,10,17,18):
        return "跳線分支，正文略述", "附錄"
    if i<=26:
        return "早期探索；不移用舊路徑數值", "背景／附錄"
    if i in (31,34,38,39):
        return "正常控流分支，未升主軸", "假設界線／附錄"
    if i<=39:
        return "指標、帳務與時點基礎", "第三章；舊數值另列"
    if i in (40,41,42,57,59,60):
        return "可修性／辨識基礎", "第三章／限制"
    if i==43:
        return "失敗去向敏感度，未升主軸", "附錄／假設"
    if i in (50,51,74,75,78,82):
        return "可選替代分支，未升主軸", "附錄／合約界線"
    if i<=56:
        return "有限批次與方法探索；舊口徑", "方法背景／附錄"
    if i in (58,61,62,63,64):
        return "主模型與核對", "第三／四／五章"
    if i==65:
        return "保留負結果，不泛化反例", "限制／附錄"
    if i in (66,67,68,69,71,72,73):
        return "主要條件實驗／強基準", "第四／五章"
    if i==70:
        return "正常量控制，未升主軸", "附錄"
    if i in (76,79,80,83):
        return "主要近似偏差與決策後果", "第五章；依勘誤解讀"
    if i==77:
        return "部分返修反例，停在界線", "假設／附錄"
    if i==81:
        return "解釋均值邊界的基本例", "說明／附錄，非新定理"
    if i==84:
        return "資料識別診斷，尚未校準", "第三／六章或附錄"
    raise ValueError(i)


def main():
    sections=re.split(r'(?=^## 第)',(ROOT/'進度.md').read_text(encoding='utf-8'),flags=re.M)[1:]
    assert len(sections)==84
    text=["# 1–84輪：教授報告與論文章節對照", "",
          "2026-10-30整理。完整涵蓋既有84輪；不是新增實驗，也不要求84張主投影片。先讀總覽，再依需要查表。",
          "", "| 輪次 | 報告批次 | 當輪在問什麼／做什麼 | 現在用途 | 論文位置 |",
          "| --- | --- | --- | --- | --- |"]
    for i,section in enumerate(sections,1):
        first=next(line[3:] for line in section.splitlines() if line.startswith('1. '))
        purpose=first.split('。')[0]
        if len(purpose)>115:
            purpose=purpose[:112]+"…"
        purpose=purpose.replace('|',r'\|')
        batch=1 if i<=26 else 2 if i<=43 else 3 if i<=57 else 4 if i<=64 else 5 if i<=73 else 6
        use,chapter=classification(i)
        text.append(f"| {i} | 第{batch}批 | {purpose} | {use} | {chapter} |")
    text.extend(["", "原始數字、假設與留／丟判讀以[進度紀錄](C:/Users/uuuwk/karissa/OPT1/OPT1/進度.md)為準。表內只做導航，不能代替閱讀與答辯理解。",
        "", "各場正文只挑重要轉折，其餘是備查。第44–56輪等早期結果所用路徑、品質與成本帳不同，不能與第63/68/73輪直接相減。第79的歷史JSON假設文字依[勘誤](C:/Users/uuuwk/karissa/OPT1/OPT1/research/2026-10-28/平均近似口徑勘誤.md)解讀。",
        "", "本次不開第85輪。三篇全文與151點拆分列為後續有限工作，沒有標為已完成。", ""])
    target=HERE/'1至84輪_報告與章節對照.md'
    target.write_text('\n'.join(text),encoding='utf-8')
    print('Mapped84 existing rounds; no experiments executed.')


if __name__=='__main__':
    main()
