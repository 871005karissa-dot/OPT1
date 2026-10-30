import fs from 'node:fs/promises';
const ROOT='C:/Users/uuuwk/karissa/OPT1/OPT1';
const DIR=ROOT+'/.build/opt1_presentation_v3';
const FONT='Microsoft JhengHei';
const C={bg:'#FAFBFA',ink:'#153447',muted:'#506573',old:'#244B6A',new:'#007F78',amber:'#986411',white:'#FFFFFF'};
const refs=JSON.parse(await fs.readFile(DIR+'/references.json','utf8'));
const refBy=Object.fromEntries(refs.map(r=>[r.id,r]));
const own={
 S1:{label:'模型、推導與求解',files:['research/2026-10-28/教授討論用問題定義.md','research/2026-10-28/命題條件與證明稽核.md','backbone/stochastic_setup_frontier.py','JORS_manuscript_anonymous_R5.docx','重工case.docx']},
 S2:{label:'公平經濟比較',files:['research/2026-10-28/service_rounds/round73.json','backbone/round73_fair_economic_baselines.py']},
 S3:{label:'平均比較器與151點拆分',files:['research/2026-10-28/service_rounds/round79.json','research/2026-10-28/平均近似口徑勘誤.md','research/2026-10-30/mean_error_151/results.json','research/2026-10-30/mean_error_151/crosscheck.json']},
 S4:{label:'最大合法回流的最少投入',files:['research/2026-10-28/service_rounds/round83.json']},
 S5:{label:'枚舉、替代積分及抽樣核對',files:['research/2026-10-28/service_rounds/round58.json','research/2026-10-28/service_rounds/round69.json','research/2026-10-28/service_rounds/round72.json','research/2026-10-28/service_rounds/round80.json','research/2026-10-30/mean_error_151/crosscheck.json']},
 S6:{label:'0/R條件失效的部分返修反例',files:['research/2026-10-28/service_rounds/round77.json']},
 E1:{label:'簡報教學算例',files:['.build/opt1_presentation_v2/teaching_arithmetic.json'],note:'三類權重及200/210/220投入表為教學示意；非工廠觀測或新增研究結果。'}
};
const cites=[
 {ids:['R1','S1'],line:'研究起點：[R1] Chen & Lin (2026)　　本研究模型：[S1]'},
 {ids:['R1','S1','S2','S3'],line:'[R1] Chen & Lin (2026), §7, PDF p.17　　本案設定與結果：[S1–S3]'},
 {ids:['R3','S1'],line:'共同服務限制的前例：[R3] Jiang et al. (2017)　　本研究決策定義：[S1]'},
 {ids:['R1','E1'],line:'[R1] Chen & Lin (2026), §3.3, PDF p.7　　本頁100/50算例為教學示意'},
 {ids:['R1','R2','S1'],line:'替代政策：[R1] §3.3　　品質後升級前例：[R2] Chen et al. (2018)　　本案：[S1]'},
 {ids:['R1','S1'],line:'原有模型：[R1]　　另附案例：重工case.docx　　本專案延伸：[S1]'},
 {ids:['R4','R6','S1'],line:'共享產能前例：[R4]　　可修特性與方向：[R6]　　本案單向路徑設定：[S1]'},
 {ids:['R2','S1'],line:'品質揭露後升級前例：[R2] 作者稿p.3–5　　本案資訊時點與未知成功數：[S1]'},
 {ids:['S1'],line:'本研究規則與求解：[S1] stochastic_setup_frontier.py；命題稽核§3–4'},
 {ids:['R1','S1'],line:'原始機台與品質案例：[R1] §5.1、表2–3　　新增假設與成本口徑：[S1]'},
 {ids:['S1'],line:'本研究條件分解：[S1] 命題稽核§2–4；求解器（標準機率公式）'},
 {ids:['R6','S1','E1'],line:'方向與可修資格的文獻依據：[R6]　　本案上限及0/R推導：[S1] §1–2　　算例：[E1]'},
 {ids:['S1','E1'],line:'本頁為教學狀態：[E1]　　合法行動與決策時點：[S1]'},
 {ids:['S1','E1'],line:'教學計算：[E1]，二項式尾機率　　模型與0/R條件：[S1] §1–3'},
 {ids:['E1'],line:'教學權重與算例：[E1]；50%/30%/20%為說明用權重'},
 {ids:['S1'],line:'本研究推導：[S1] 命題稽核§4（標準覆蓋排序、LP上界及固定規則差距）'},
 {ids:['S1','E1'],line:'選擇準則：[S1]　　200/210/220與收益數字為教學示意：[E1]'},
 {ids:['S2'],line:'本研究結果：[S2] 第73輪 round73.json；每個基準均重選投入'},
 {ids:['S3'],line:'本研究結果：[S3] 第79輪＋平均近似口徑勘誤；151點拆分 results.json'},
 {ids:['S4'],line:'本研究結果：[S4] 第83輪 round83.json；最大合法回流下的最少投入'},
 {ids:['R2','R3','R4','R5','R6','R7','R9','R10','R11'],line:'模型前例：[R2–R7]　　直接對照待全文：[R9–R11]　　版本及閱讀範圍見文末'},
 {ids:['S1'],line:'本研究候選規格：[S1]；本頁為待教授核定事項'},
 {ids:['S1','S2','S3','S4','S5','S6'],line:'本研究歷程與保存結果：[S1–S6]；輪次代表不同檢查工作'},
 {ids:[],line:'研究與成稿建議時程，規劃日2026/10/30；目標2027年3月完稿'},
 {ids:['S3'],line:'本研究結果：[S3] mean_error_151/results.json、crosscheck.json（151個既有點）'},
 {ids:['S1','S6'],line:'充分條件：[S1] 命題稽核§1　　條件改變的部分返修反例：[S6] 第77輪'}
];
function text(s,t,x,y,w,h,size=28,color=C.ink,bold=false){
 const a=s.shapes.add({geometry:'textbox',name:t.slice(0,70),position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 a.text=t;a.text.style={typeface:FONT,fontSize:size,color,bold,verticalAlignment:'middle',insets:0,autoFit:'none',wrap:'square'};return a;
}
function sourceLine(s,t){return text(s,t,60,689,1135,24,18,C.muted);}
function slide(p,title){const s=p.slides.add({width:1280,height:720});s.background.fill=C.bg;text(s,title,60,42,1160,82,44,C.ink,true);return s;}
function table(s,values,x=60,y=165,w=1160,h=405,widths=[260,430,470],size=25){
 const a=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,values,columnWidths:widths});
 a.borders.assign({fill:'#D3DDE0',width:1,style:'solid'});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){const q=a.getCell(r,c);q.fill=r===0?C.old:(r%2===0?'#F0F4F3':C.white);q.text.style={typeface:FONT,fontSize:size,color:r===0?C.white:C.ink,bold:r===0,verticalAlignment:'middle',insets:12,autoFit:'none',wrap:'square'};}
 return a;
}
function notes(row){
 const paper=(row.ids??[]).filter(id=>refBy[id]).map(id=>{const r=refBy[id];return `[${id}] ${r.authors} (${r.year}). ${r.title}. ${r.publication}\n${r.url}\n閱讀狀態：${r.status}\n本次可核位置：${r.locator}`+(r.author_url?'\n作者稿：'+r.author_url:'')+(r.local?'\n本地全文：'+ROOT+'/'+r.local:'');}).join('\n\n');
 const internal=(row.ids??[]).filter(id=>own[id]).map(id=>`[${id}] ${own[id].label}\n`+own[id].files.map(f=>ROOT+'/'+f).join('\n')+(own[id].note?'\n'+own[id].note:'')).join('\n\n');
 return row.spoken+(row.reserve?'\n\n被問到再補充（不用照念）\n'+row.reserve:'')+'\n\n引用與適用範圍（不用念）\n'+(row.citation??'')+(paper?'\n\n原始文獻\n'+paper:'')+(internal?'\n\n本研究結果與程式\n'+internal:'')+(row.sources?.length?'\n\n其他原始紀錄\n'+row.sources.join('\n'):'');
}
function referenceEntry(s,r,y){
 text(s,`[${r.id}] ${r.authors} (${r.year})`,60,y,1160,40,26,C.old,true);
 text(s,r.title,60,y+42,1160,65,25);
 text(s,r.publication,60,y+109,1160,48,23,C.muted);
 const a=text(s,r.url,60,y+162,1160,30,21,C.new);
 a.text=[[{run:r.url,style:{typeface:FONT,fontSize:'21px',color:C.new,underline:'sng'},link:{uri:r.url,isExternal:true}}]];
 text(s,r.reading,60,y+197,1160,42,21,r.id==='R9'||r.id==='R10'||r.id==='R11'?C.amber:C.muted);
}
export async function complete(p){
 if(p.slides.items.length!==26)throw new Error('Expected unmodified 26-slide v2 source');
 const old=JSON.parse(await fs.readFile(ROOT+'/.build/opt1_presentation_v2/slide_manifest.json','utf8'));
 const snap=await p.inspect({select:'$.slides[*]',include:['id','index','title','elements.id','elements.kind','elements.text','elements.position']});
 const pages=[];
 for(let i=0;i<26;i++){
  const rec=snap.records[i],s=p.resolve(rec.id),base=old.slides[i];
  if(i===0){for(const e of rec.elements??[])if(typeof e.text==='string'&&e.text.includes('研究主軸與執行邏輯，口語版'))p.resolve(e.id).text=e.text.replace('研究主軸與執行邏輯，口語版','研究主軸、執行邏輯與文獻引用');}
  const row={...base,ids:cites[i].ids,citation:cites[i].line};
  if(i===18){row.spoken='圖裡的C把初次分級和成功件數都換成平均，M只平均未來成功件數，T兩層都保留隨機。這一點C算成九成六，T只有五成一左右，主要差在平均初次件數跨過了交貨門檻。';row.reserve='C同時代入平均初次分類及ηr。M保留初次(A,B,E)隨機，只以ηr取代決策後成功數。T保留初次與未來成功的隨機性。三者沿用相同容量來源與最大合法回流規則，各自的R不保證是同一實現。本例M與T差約2.35×10⁻⁹機率單位。';for(const e of rec.elements??[])if(typeof e.text==='string'&&e.text.startsWith('C同時平均初次分類及成功數'))p.resolve(e.id).text='C：兩層都代均值；M：只平均未來成功數；T：兩層都保留隨機';}
  if(i===20)row.spoken='這些文獻各有用途：有的幫我檢查可修條件，有的提醒我升級、共享產能和共同服務早已有前例。後面有逐篇對照與完整書目，三篇缺全文的會清楚列出。';
  if(i===23)row.spoken='接下來以寫成完整文章為主。十一月先核範圍和資料，一月底交完整初稿，再留二月到三月修訂和準備口試。這是建議時程，後面的文獻與方法附錄可以依老師提問再開。';
  sourceLine(s,row.citation);s.speakerNotes.text=notes(row);pages.push(row);
 }
 let s=slide(p,'附錄B：文獻怎麼用進模型');
 table(s,[['文獻','已讀到的內容','本案怎麼用'],['[R2] Chen et al.\n2018','品質揭露後可升級\n兩品模型有單門檻','檢查資訊時點與前例\n本案另列未來未知成功數'],['[R4] Kohlmann / Sahling\n2024','正常與重工共用產能\n有分開的啟動成本','核對資源與啟動假設\n服務定義仍須分開'],['[R5] Berling / Sonntag\n2022','逐件／批次良率\n非完美重工','明列所用品質法則\n本案未採unit-tracking'],['[R6] Dodd et al.\n2015','不同失敗特性\n有不同加工方向','限定可修池與方向\n比例及η仍需資料']],60,155,1160,420,[320,410,430],25);
 text(s,'本案使用標準機率與覆蓋排序，另對這個單期問題推導與實作',60,595,1160,50,27,C.new,true);
 pages.push({page:27,title:'附錄B：文獻怎麼用進模型',spoken:'這幾篇有實際影響模型設定。共享產能、可修方向和品質波動都有文獻依據；本案再把自己的資訊順序和限制寫清楚，用標準機率工具計算。',reserve:'Chen作者稿式(2)/(8)中的升級採確定性轉換。Kohlmann的加權期望欠交服務與本案共同交足機率不同。Dodd支持物理方向的檢查，沒有提供本案已驗證的η或可修比例。',ids:['R2','R4','R5','R6','S1'],citation:'[R2] 作者稿p.3–8　[R4] PDF p.5–10　[R5] HTML §6.1/6.3/7.2　[R6] 作者稿p.6–8'});
 s=slide(p,'附錄C：已有前例與待核對的差異');
 table(s,[['要討論的內容','文獻已知／目前能報告的範圍'],['共同服務限制','[R1、R3、R8] 已有相關事件與限制，需交代本案是同批跨等級'],['升級、替代與共享線','[R2、R7] 已有前例，單靠這些機制不足以定位貢獻'],['本研究工作','限定可修池與資訊時點，推導0/R條件、服務界及可核對計算'],['仍待全文核對','[R9–R11] 共同或分別服務、均值與安全量、選別返修及成敗時點']],60,155,1160,400,[330,830],26);
 text(s,'平均比較器C由本研究明確定義，不能套稱為上述文獻的方法',60,578,1160,60,29,C.new,true);
 pages.push({page:28,title:'附錄C：已有前例與待核對的差異',spoken:'升級和共同服務都有前例，所以我會把重點放在這個限定問題怎麼定義、怎麼算、哪些情況可行。三篇最接近的全文還沒補齊，現在先保留差異定位。',reserve:'Jiang的共同事件跨期間，且無追索；Sereshti實讀2022v1。Boutarfa已讀多等級模型為確定性、隨機擴充採單等級。Bitran/Tsai不能由摘要推定採用本案C。',ids:['R1','R2','R3','R7','R8','R9','R10','R11','S1','S3'],citation:'共同服務：[R1、R3、R8]　升級與共享線：[R2、R7]　直接全文待補：[R9–R11]'});
 s=slide(p,'附錄D：計算如何核對');
 table(s,[['核對方式','核對到什麼','仍然不能推論什麼'],['小批全枚舉\n第58、72輪','把品質、合法行動及未來成功逐項算出，再比對快速公式','不能由小批核對證明工廠假設正確'],['另一種機率加總\n151點拆分','改用回流尾分布積分\n與原式相差最多約1.62×10⁻¹⁴','共享部分機率元件\n並非完全獨立軟體'],['凍結規則後重抽\n第69、80輪','先固定行動，再抽品質與成功\n以抽樣區間核對精算值','新亂數不是現場新資料\n下界未跨75%不構成達標證明']],60,170,1160,390,[260,500,400],25);
 text(s,'這些工作支持程式與指定模型相符，現場適用性還需要資料',60,586,1160,55,29,C.new,true);
 pages.push({page:29,title:'附錄D：計算如何核對',spoken:'我用了小批全算、另一種機率加總，以及先固定規則再抽樣這幾種檢查。它們幫我找程式和公式的錯誤；真正能不能用在現場，還要確認資料和製程假設。',reserve:'第69輪三個模擬下界均未跨75%，精算值落在區間內核對的是模型實作。加權Bernoulli Hoeffding與聯集界推導見[S1] §8；原文[R12]僅核摘要與書目。151點另一積分最大差1.6209256159527285e-14，亦共享binomial primitives。',ids:['S1','S3','S5','R12'],citation:'本研究核對：[S5] 第58/69/72/80輪與151點crosscheck　　標準界來源：[R12]'});
 s=slide(p,'附錄E：參數來源與待補資料');
 table(s,[['資料／設定','目前來源或身分','下一步要確認'],['機台容量、正常良率\n公差與原案例價格','[R1] 原始案例資料\n本案沿用指定版本','可否代表欲研究的產線與批次'],['可修資格、方向與比例','方向有[R6]概念支持\n本案可修池為條件假設','哪些缺陷可修，其他尺寸是否受損'],['η=.97、啟動費2000\n終端價值90/30','[S1] 情境假設\n尚無批次實證支持','返修成功數、實際費用及剩餘品價值'],['品質獨立與批次波動','主模型指定獨立法則\nκ為壓力測試，尚未估計','批次品質計數與取樣方式']],60,160,1160,410,[350,420,390],25);
 text(s,'資料不足時，可先用明確標示的合成案例；由教授核定研究定位',60,590,1160,55,28,C.new,true);
 pages.push({page:30,title:'附錄E：參數來源與待補資料',spoken:'原案例有機台和品質資料，但新增重工的成功率、可修比例和成本，仍是我們的假設。接下來要請老師決定採現場批次資料，還是把研究明確定位成合成案例。',reserve:'正常工序良率不能直接當升級成功率。κ沒有估計值；固定p、外生批量的動差診斷不等於現場識別。0/R充分條件仍須依終端價值和成功率核定。',ids:['R1','R6','S1'],citation:'原案例：[R1] §5　　可修特性前例：[R6]　　本案假設與條件：[S1]'});
 const titles=['參考文獻①：原始問題與升級前例','參考文獻②：共同服務與共享產能','參考文獻③：品質法則與可修方向','參考文獻④：整合機制與替代服務','參考文獻⑤：待補全文的直接對照','參考文獻⑥：待補對照與標準工具'];
 for(let j=0;j<6;j++){
  s=slide(p,titles[j]);const pair=refs.slice(j*2,j*2+2);pair.forEach((r,k)=>referenceEntry(s,r,145+k*247));
  text(s,'頁碼以實際讀取版本計，作者稿、期刊PDF與HTML各自標示',60,650,1135,30,20,C.muted);
  pages.push({page:31+j,title:titles[j],spoken:j===4?'這兩篇直接對照還需要全文，現在只根據已見摘要列出待核問題。':'這頁是完整書目與閱讀版本，報告時可以先跳過，老師需要來源再回來看。',reserve:pair.map(r=>`[${r.id}] ${r.locator}`).join('\n'),ids:pair.map(r=>r.id),citation:'文獻編號與各頁一致，DOI／預印本連結可點擊開啟'});
 }
 s=slide(p,'本研究結果、程式與教學資料索引');
 table(s,[['編號','用途','可追溯紀錄'],['[S1]','模型、條件與求解','stochastic_setup_frontier.py\n教授討論用問題定義／命題稽核'],['[S2]','公平經濟基準','第73輪 round73.json'],['[S3]','平均化誤差與151點拆分','round79.json＋口徑勘誤\nmean_error_151/results.json'],['[S4]','最大回流的最少投入','第83輪 round83.json'],['[S5]','公式與抽樣核對','第58/69/72/80輪\nmean_error_151/crosscheck.json'],['[S6]','0/R條件失效反例','第77輪 round77.json'],['[E1]','教學狀態與說明用權重','teaching_arithmetic.json\n200/210/220表為教學示意']],60,145,1160,492,[110,350,700],23);
 pages.push({page:37,title:'本研究結果、程式與教學資料索引',spoken:'文獻用R編號，我們自己的模型和結果用S編號，教學例用E編號。這樣老師看到一個數字，就能知道它是論文前例、我們算的結果，還是用來解釋的例子。',reserve:'本頁備註列完整本機路徑。歷史JSON保留原檔；round79引用時以平均近似口徑勘誤為準。',ids:['S1','S2','S3','S4','S5','S6','E1'],citation:'R＝外部文獻　S＝本研究模型／結果　E＝教學示意；完整路徑見備註'});
 const all=await p.inspect({select:'$.slides[*]',include:['id','index','title','elements.id','elements.kind','elements.text','elements.position']});
 if(all.records.length!==37)throw new Error('Expected 37 slides after reference completion');
 for(let i=26;i<37;i++){
  const row=pages[i],sl=p.resolve(all.records[i].id);text(sl,String(i+1).padStart(2,'0'),1210,660,40,30,17,C.muted);sourceLine(sl,row.citation);sl.speakerNotes.text=notes(row);
 }
 for(const row of pages)row.referenceSlides=(row.ids??[]).filter(id=>refBy[id]).map(id=>31+Math.floor(refs.findIndex(r=>r.id===id)/2));
 await fs.writeFile(DIR+'/slide_manifest.json',JSON.stringify({slides:pages,referenceCatalog:refs,ownSources:own,flowSlides:old.flowSlides,tables:[...old.tables,27,28,29,30,37],charts:old.charts},null,2));
 const sourceMap=pages.map(r=>`## 第${r.page}頁 ${r.title}\n\n${r.spoken}\n\n引用：${r.citation}\n`+(r.referenceSlides.length?'\n完整書目見第'+[...new Set(r.referenceSlides)].join('、')+'頁。\n':''));
 const intro='# 口語講稿與引用對照 v3\n\n主報告可用第1–22頁。第23–24頁交代研究歷程與成稿，第25–30頁供追問時使用，第31–36頁為完整書目，第37頁為本研究結果索引。無須一次講完全部頁面。\n\n分批報告建議：第一次用第1–8、22頁確認題目，第二次用第9–17頁解釋計算，第三次用第18–21、25頁報告結果。文獻追問開第27–28頁，數值核對開第29頁，資料定位開第30頁，時程用第23–24頁。\n\n目前候選主問題：在高低品共同交足機率達標下，選事前整數投入與檢驗後重工規則，比較期望利潤。服務可行性與投入判斷是目前較明顯的發現；教授仍需核定題目與資料定位。\n\nR編號是外部文獻，S編號是本研究模型與結果，E編號是教學示意。已取得PDF不等於逐頁讀完，文獻閱讀版本與範圍逐項標示。\n\n';
 const bibliography='\n# 完整參考文獻與閱讀深度\n\n'+refs.map(r=>`## [${r.id}] ${r.short}\n\n${r.authors} (${r.year}). ${r.title}. ${r.publication}\n\n[DOI／版本連結](${r.url})`+(r.author_url?`， [作者稿](${r.author_url})`:'')+`\n\n閱讀狀態：${r.status}。\n\n定位：${r.locator}\n`).join('\n');
 const internals='\n# 本研究來源索引\n\n'+Object.entries(own).map(([id,o])=>`## [${id}] ${o.label}\n\n`+o.files.map(f=>`- [${f}](${ROOT+'/'+f})`).join('\n')+(o.note?'\n\n'+o.note:'')+'\n').join('\n');
 await fs.writeFile(ROOT+'/output/presentations/OPT1_口語講稿與引用對照_v3.md',intro+sourceMap.join('\n')+bibliography+internals,'utf8');
 return {slideCount:37,referenceCount:12,visibleSourceLines:37,clickableReferenceLinks:12,spokenNotes:37};
}

export async function repair(p){
 const file=DIR+'/slide_manifest.json';const m=JSON.parse(await fs.readFile(file,'utf8'));
 const prev=m.slides[18].spoken;
 m.slides[18].spoken='圖裡的C把初次分級和成功件數都換成平均，M只平均未來成功件數，T兩層都保留隨機。這一點C算成九成六，T只有五成一左右，主要差在平均初次件數跨過了交貨門檻。';
 m.slides[18].reserve='C同時代入平均初次分類及ηr。M保留初次(A,B,E)隨機，只以ηr取代決策後成功數。T保留初次與未來成功的隨機性。三者沿用相同容量來源與最大合法回流規則，各自的R不保證是同一實現。本例M與T差約2.35×10⁻⁹機率單位。';
 m.slides[20].ids=cites[20].ids;m.ownSources=own;
 const snap=await p.inspect({select:'$.slides[*]',include:['id','index','elements.id','elements.kind','elements.text']});
 for(const e of snap.records[18].elements??[])if(typeof e.text==='string'&&e.text.startsWith('C同時平均初次分類及成功數'))p.resolve(e.id).text='C：兩層都代均值；M：只平均未來成功數；T：兩層都保留隨機';
 for(const [i,row]of m.slides.entries())p.resolve(snap.records[i].id).speakerNotes.text=notes(row);
 await fs.writeFile(file,JSON.stringify(m,null,2));
 const mdpath=ROOT+'/output/presentations/OPT1_口語講稿與引用對照_v3.md';let md=await fs.readFile(mdpath,'utf8');
 md=md.replace(prev,m.slides[18].spoken).replace('無須一次講完全部頁面。\n\n目前候選','無須一次講完全部頁面。\n\n分批報告建議：第一次用第1–8、22頁確認題目，第二次用第9–17頁解釋計算，第三次用第18–21、25頁報告結果。文獻追問開第27–28頁，數值核對開第29頁，資料定位開第30頁，時程用第23–24頁。\n\n目前候選');
 md=md.replace('- [backbone/stochastic_setup_frontier.py]('+ROOT+'/backbone/stochastic_setup_frontier.py)','- [backbone/stochastic_setup_frontier.py]('+ROOT+'/backbone/stochastic_setup_frontier.py)\n- [原始匿名稿]('+ROOT+'/JORS_manuscript_anonymous_R5.docx)\n- [另附重工案例]('+ROOT+'/重工case.docx)');
 await fs.writeFile(mdpath,md,'utf8');return {notesRefreshed:37,chartDefinitionsClarified:true};
}
