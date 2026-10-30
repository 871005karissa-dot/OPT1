import fs from 'node:fs/promises';
const ROOT='C:/Users/uuuwk/karissa/OPT1/OPT1';
const DIR=ROOT+'/.build/opt1_presentation_v2';
const FONT='Microsoft JhengHei';
const C={bg:'#FAFBFA',ink:'#153447',muted:'#506573',old:'#244B6A',oldBg:'#EAF0F5',new:'#007F78',newBg:'#E6F2EF',amber:'#986411',amberBg:'#FBF1DB',white:'#FFFFFF'};
const SPEC=ROOT+'/research/2026-10-28/教授討論用問題定義.md';
const CODE=ROOT+'/backbone/stochastic_setup_frontier.py';
const PROOF=ROOT+'/research/2026-10-28/命題條件與證明稽核.md';
const ORIGIN=ROOT+'/research/2026-10-30/原文兩政策_重工來源與84輪程式說明.md';
const VOICE=[
'我的研究是接著原稿往下做。原稿比較不同交貨方式能不能交足，我多問一步：如果允許重工，該投多少、看到哪些品質狀況才要修。',
'這個方向是從原稿長出來的。原稿已經在看交足訂單的機率，也把多等級重工列成後續方向。我把這件事做成能計算、能比較的決策問題。',
'我的問題還是怎麼投料、怎麼重工，讓期望利潤比較好。但有一個前提：高低品一起交足的機率，要先達到要求。教授還需要核定這個範圍。',
'原稿的兩個政策都在分配成品。第一個只交同等級；第二個可以把剩下的高品補給低品客戶。這個替代不用送回機器。',
'向下替代是高品直接交給低品客戶。重工則是把符合條件的低品再加工，嘗試升成高品。後者會花錢、占產能，而且可能失敗。',
'原稿已有分級、容量和替代。我加的是有限一批的件數變動、可修品限制，以及檢驗後才決定修不修。相對原稿有新增，還不等於學術首創。',
'正常生產先照固定規則做，檢驗後才知道有哪些成品。低品裡只有一部分能修，還得留夠低品訂單，用剩下的產能處理。最後一站只是待確認的例子。',
'順序不能顛倒。先投料，再知道容量、做完正常生產，接著看品質決定修不修。修好幾件是最後才知道，程式不能先看答案再選。',
'程式先在規劃時算好投入量和一張啟動表。現場不用重算所有可能，只要檢驗後知道件數和剩餘產能，再照表決定要不要修。',
'程式要先有訂單、達標要求、機台和成本，也要有品質和返修的機率。像成功率九成七，目前只是模型假設，不能當成工廠已量到的數據。',
'先固定一個投入量。程式把可能的容量、品質和修復結果算進去，替每個決定算平均收益和交足率。再換另一個投入量做同樣的比較。',
'例如低品有七十件，要留五十件交貨，最多能動二十件。可修的有二十五件，但產能只夠修十五件，所以最後最多只能送十五件。',
'這時高品有八十六件，還缺十四件。送十五件去修，成功十三件還是不夠，成功十四件才交得齊。所以送出十五件，不代表一定補得足。',
'假設每件有九成七的機會修好，十五件裡至少修好十四件的機率，大約是92.7%。程式把這些可能結果加起來，不會拿平均14.55件直接當成交貨數量。',
'接著要把不同情況合在一起。這個教學例裡，一半本來就能交足，三成靠重工，另外兩成仍缺貨。加權後約七成七八，才是整體交足率。',
'修了可能比較容易交足，但不一定多賺。所以先納入有利潤的重工；如果整體交足率還不足，再找補足服務所需代價較小的情況。',
'最後只比較達標的投入。這個示意表裡，兩百件已經達標，但兩百一十件的期望利潤更好，所以選兩百一十。最少投入和最賺的投入要分開看。',
'回到真正的計算，每個基準也都重新選投入。公平比完，選擇重工通常只多賺一點，有的訂單甚至不重工最好。這是目前的結果。',
'比較明顯的是服務估計。這一點用平均件數會算成九成六，完整隨機模型只有五成一左右。問題主要出在平均件數剛好跨過交貨門檻。',
'這會改變決策。五百、三百這張訂單要九成五，平均算法會選一一五二件，完整模型要一一八四件。這裡是在找最少達標投入，和利潤最佳化分開報。',
'文獻會幫我檢查哪些做法早就有了。品質後升級、門檻和共同服務都有前例。目前只能提出限定問題的差異，三篇最接近的全文還要補齊。',
'現在最需要老師確認的是：這個單期問題能不能當主軸、用現場還是合成資料，以及剩餘品價值能不能支持目前的返修規則。',
'八十四輪不用逐輪講。我把它分成六段：先重現，再修假設，接著建立可核對的計算，最後留下有用結果、交代不適用的地方。',
'接下來以寫成完整文章為主。十一月先核範圍和資料，十二月邊審邊寫，一月底交完整初稿，再留二月到三月修訂和準備口試。這是建議時程。',
'這一百五十一點是既有模型網格裡選出的誤判點。保留初次品質的隨機件數後，這些點都不再被判成達到八成。它們不是工廠樣本。',
'這頁是符號備查。現在只比不修和修滿，是因為假設下多修的期望邊際為正。資料若不支持這個條件，就不能說現在這個解法涵蓋所有返修量。'
];

function txt(s,t,x,y,w,h,size=28,color=C.ink,bold=false,align='left'){
 const a=s.shapes.add({geometry:'textbox',name:t.slice(0,48),position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 a.text=t;a.text.style={typeface:FONT,fontSize:size,color,bold,alignment:align,verticalAlignment:'middle',wrap:'square',insets:0,autoFit:'none'};return a;
}
function box(s,t,x,y,w,h,kind='new',size=28){
 const col=kind==='old'?C.old:kind==='hyp'?C.amber:C.new;
 const bg=kind==='old'?C.oldBg:kind==='hyp'?C.amberBg:C.newBg;
 const a=s.shapes.add({geometry:'rect',name:t.replaceAll('\n',' / '),position:{left:x,top:y,width:w,height:h},fill:bg,line:{fill:col,width:1.5}});
 a.text=t;a.text.style={typeface:FONT,fontSize:size,color:col,bold:true,alignment:'center',verticalAlignment:'middle',insets:12,wrap:'square',autoFit:'none'};return a;
}
function link(s,a,b,from='right',to='left',kind='straight',color=C.muted){s.shapes.connect(a,b,{kind,fromSide:from,toSide:to,line:{fill:color,width:2.2},tail:{type:'triangle',width:'med',length:'med'}});}
function foot(s,t){txt(s,t,60,647,1130,40,20,C.muted);}
function newSlide(p,title,sources=[SPEC,CODE,PROOF]){
 const s=p.slides.add({width:1280,height:720});s.background.fill=C.bg;
 txt(s,title,60,42,1160,82,44,C.ink,true);txt(s,'00',1210,660,40,30,17,C.muted,false,'right');
 s.speakerNotes.text='\n\n資料來源（不用念）\n'+sources.join('\n');return s;
}
function table(s,values,x,y,w,h,widths,size=27){
 const a=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,values,columnWidths:widths});
 a.borders.assign({fill:'#D3DDE0',width:1,style:'solid'});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
  const q=a.getCell(r,c);q.fill=r===0?C.old:(r%2===0?'#F0F4F3':C.white);
  q.text.style={typeface:FONT,fontSize:size,color:r===0?C.white:C.ink,bold:r===0,verticalAlignment:'middle',insets:12,autoFit:'none',wrap:'square'};
 }
 return a;
}
async function replaceOn(p,index,replacements){
 const snap=await p.inspect({select:`$.slides[${index}].elements[*]`,include:['id','kind','text']});
 for(const rec of snap.records){if(!['shape','textbox'].includes(rec.kind)||typeof rec.text!=='string')continue;let t=rec.text;for(const [a,b] of replacements)t=t.replaceAll(a,b);if(t!==rec.text)p.resolve(rec.id).text=t;}
}

export async function revise(p){
 if(p.slides.items.length!==22)throw new Error('Expected original 22-slide deck');
 const original=await p.inspect({select:'$.slides[*]',include:['id','index','title']});
 const old=original.records.map(x=>x.id);
 const oldManifest=JSON.parse(await fs.readFile(ROOT+'/.build/opt1_presentation/slide_manifest.json','utf8'));
 const toy=JSON.parse(await fs.readFile(DIR+'/teaching_arithmetic.json','utf8'));
 await replaceOn(p,0,[['先投入多少，檢驗後何時值得返修，\n才能把高低品訂單一起交足','交足率達標時，怎麼投料、怎麼決定重工，\n才能讓期望利潤更好'],['研究入門與教授報告版','研究主軸與執行邏輯，口語版']]);
 await replaceOn(p,8,[['高品92','高品86'],['若成功7件','若成功13件'],['高品106','高品100']]);
 await replaceOn(p,13,[['論文主要結果放在服務可行性與投入判斷','利潤仍要比較，本案增益有限']]);
 await replaceOn(p,19,[['主問題：單期選別返修與共同交足是否足夠？','主問題：這個單期投入與重工問題，是否作為主軸？']]);
 // New slide 1: provenance of research question
 let s=newSlide(p,'這個研究問題從哪裡來',[ORIGIN,SPEC,ROOT+'/research/2026-10-30/收斂推進_本次成果與教授決策.md']);
 const arr=[['原稿','比較交貨政策\n計算交足機率'],['原稿後續方向','多等級返修\n及品質特性相依'],['本案延伸','把投入與修不修\n做成決策'],['比較結果','利潤增益有限\n投入判斷差異明顯']].map((v,i)=>box(s,v[0]+'\n\n'+v[1],60+i*300,210,260,230,i<2?'old':'new',27));
 arr.slice(1).forEach((n,i)=>link(s,arr[i],n));
 txt(s,'題目接續原稿，結果再決定論文要強調哪些發現',60,505,1160,82,34,C.new,true);
 foot(s,'目前為候選主軸，仍需教授核定與直接文獻全文對照');
 // New slide 2: objective vs constraint vs findings
 s=newSlide(p,'研究問題、限制與主要發現',[SPEC,ROOT+'/research/2026-10-28/論文主軸與章節草稿.md']);
 table(s,[['角色','本案的意思'],['決策','事前投多少？檢驗後哪些狀況要修？'],['服務限制','高低品一起交足的機率至少達到 α'],['選擇準則','在達標方案中，取得較高的期望利潤'],['目前主要發現','品質估計會改變可行性與投入；利潤增益有限']],60,165,1160,390,[250,910],29);
 foot(s,'交足率是限制，期望利潤仍是主模型的選擇準則；最少投入另作比較');
 // New slide 3: policy design versus execution
 s=newSlide(p,'先算好一張規則表，現場再照表決定');
 txt(s,'事前規劃',60,145,1140,50,31,C.old,true);
 const pp=[['嘗試投入 I','換一個量就重評估'],['算各狀況收益','品質與未來成敗加權'],['訂啟動規則','哪些狀況要修'],['選投入與規則','整體達標，收益較好']].map((v,i)=>box(s,v[0]+'\n'+v[1],60+i*300,215,260,105,'old',25));pp.slice(1).forEach((n,i)=>link(s,pp[i],n));
 txt(s,'產線執行',60,370,1140,50,31,C.new,true);
 const ex=[['投料與正常加工','照選定的 I 執行'],['檢驗與看餘裕','得到高低品及可修量'],['查規則表','這個狀況修或不修'],['修完才知成功數','替代、交貨、計帳']].map((v,i)=>box(s,v[0]+'\n'+v[1],60+i*300,440,260,110,i===3?'hyp':'new',25));ex.slice(1).forEach((n,i)=>link(s,ex[i],n));
 foot(s,'規則使用檢驗當下可知的資訊，不能先看到返修成功數');
 // New slide 4: data inputs
 s=newSlide(p,'程式需要哪些資料');
 table(s,[['輸入','用來算什麼','目前身分'],['訂單與服務要求','高低品需求 D₁、D₂，以及 α','先指定要求，再比較政策'],['機台與正常加工','各容量狀態、發生機率、正常良率','原案例與固定正流規則'],['品質與返修','分級機率、可修條件、成功率 η','返修機制與 η 仍需資料支持'],['收益與成本','售價、原料、加工、啟動費及剩餘價值','統一口徑，部分數值為假設']],60,165,1160,405,[220,520,420],26);
 foot(s,'假設能讓模型計算，不代表它已經符合工廠；κ也尚未由批次資料估計');
 // New slide 5: fixed input calculation
 s=newSlide(p,'固定一個投入量，程式如何計算');
 const stages=[['可能容量','正常產出 N\n返修餘裕 L'],['可能初次品質','高品 A、低品 B\n可修量 E'],['決定行動','算合法上限 R\n查表選 0 或 R'],['可能成功數','決定後的 Y\n判斷交貨與收入']].map((v,i)=>box(s,v[0]+'\n\n'+v[1],60+i*300,210,260,220,i<2?'old':i===2?'new':'hyp',27));stages.slice(1).forEach((n,i)=>link(s,stages[i],n));
 txt(s,'路徑權重：容量機率 × 品質條件機率 × 成功數條件機率\n交足機率加總成功路徑；收益按路徑權重取平均',60,475,1150,125,29,C.new,true);
 foot(s,'容量共有28,224種。程式用條件分解與尾機率加速，不是每種未來各挑最好行動');
 // New slide 6: exact conditional probability
 s=newSlide(p,'送15件返修，交足的機率怎麼算',[CODE,PROOF,DIR+'/teaching_arithmetic.json']);
 txt(s,'需求高品100、低品50；目前高品86、低品70；可送15件',60,135,1160,65,28,C.muted);
 const g=box(s,'高品還缺14件',60,255,285,120,'old',32);
 const bin=box(s,'送15件，成功數 Y\n每件獨立成功率 .97',440,255,365,120,'hyp',30);
 const pass=box(s,'Y至少14件\n高低品才一起交足',900,255,320,120,'new',30);link(s,g,bin);link(s,bin,pass);
 txt(s,'P(交足｜這個狀況、選擇返修) = P(Y ≥ 14) ≈ '+(toy.service_if_repair*100).toFixed(2)+'%',60,450,1150,70,35,C.new,true);
 txt(s,'平均成功15 × .97 = 14.55件，不能直接當已交足',60,540,1150,60,29);
 foot(s,'教學狀態。這裡低品修後仍剩55件；.97是本案假設，非實測成功率');
 // New slide 7: total probability
 s=newSlide(p,'整體服務是把各種情況加權相加',[CODE,DIR+'/teaching_arithmetic.json']);
 table(s,[['教學情境','發生機率','該情境的交足率','對整體的貢獻'],['本來就交足','50%','100%','50.00%'],['需修15件，成功至少14件','30%',(100*toy.service_if_repair).toFixed(2)+'%',(30*toy.service_if_repair).toFixed(2)+'%'],['高品不足，也無法再修','20%','0%','0%']],60,175,1160,300,[440,200,250,270],26);
 txt(s,'整體交足率約 50% + 27.81% = 77.81%',60,510,1140,70,35,C.new,true);
 txt(s,'這個投入可達75%；若要求80%，連全修也不夠',60,585,1140,45,28);
 foot(s,'三類及權重只為教學加權，並非本案品質分布、現場資料或新研究結果');
 // New slide 8: setup decisions
 s=newSlide(p,'啟動表如何兼顧利潤與達標');
 const best=box(s,'先納入期望多賺的重工',60,205,370,115,'old',29);
 const enough=box(s,'整體交足率是否達標',500,205,350,115,'new',29);link(s,best,enough);
 const ok=box(s,'已達標\n保留這份規則',940,170,280,115,'new',28);link(s,enough,ok,'right','left','elbow');
 const need=box(s,'尚未達標\n按補服務的代價排序',500,430,350,125,'hyp',28);link(s,enough,need,'bottom','top');
 const rule=box(s,'補到目標\n形成固定啟動規則',940,430,280,125,'new',28);link(s,need,rule);
 txt(s,'某個狀況可能不多賺，\n但整體達標會需要它',60,430,370,120,30,C.amber,true);
 txt(s,'排序依據：少賺多少 ÷ 多增加多少交足機率',60,585,1150,42,28,C.new,true);
 foot(s,'使用標準覆蓋排序與LP上界，固定規則附差距界；不宣稱一般確定性最適');
 // New slide 9: release choice
 s=newSlide(p,'達標後，以期望利潤挑投入',[SPEC,CODE]);
 txt(s,'假設要求共同交足率至少80%，以下僅示範選擇規則',60,135,1150,60,28,C.muted);
 table(s,[['投入量','共同交足率','期望利潤','怎麼判斷'],['200','82%','100','達標，但利潤較低'],['210','86%','130','達標且利潤較高，選這個'],['220','90%','120','投入較多，利潤沒有更好']],60,235,1160,300,[220,260,250,430],28);
 txt(s,'最少達標投入是200；這裡較賺的投入是210',60,565,1160,60,32,C.new,true);
 foot(s,'表中數字是教學示意，非模型計算結果。主模型比較政策並報可行解與差距');
 const added=await p.inspect({select:'$.slides[*]',include:['id','index']});
 const neu=added.records.slice(22).map(x=>x.id);
 const desired=[old[0],neu[0],neu[1],old[2],old[3],old[4],old[5],old[6],neu[2],neu[3],neu[4],old[7],old[8],neu[5],neu[6],neu[7],neu[8],old[13],old[14],old[16],old[17],old[19],old[10],old[18],old[15],old[20]];
 const keep=new Set(desired);p.slides.keep(added.records.filter(x=>keep.has(x.id)).map(x=>x.index));p.slides.reorder(desired);
 const final=await p.inspect({select:'$.slides[*]',include:['id','index','title','elements.id','elements.kind','elements.text','elements.position']});
 const reserve={
 13:'P(Y≥14)=.97^15+15×.03×.97^14。以售價120、終端值90/30、返修成本12.4及F2000計，此狀態的期望增益約−909。這只解釋服務與收益需分開，未求新的全域政策。',
 14:'三類情境為教學加總，並非從新多項式、DM或工廠資料擬合。以這張示意表的行動集合計，最大服務77.8108%。',
 15:'固定I下先開G≥F的正R狀態。未達α時，對b>0的其他狀態按(F−G)/b排序，以w×b累積服務。隨機化LP提供上界，邊界全開給固定可行規則與差距界。這不等於已求得所有確定性政策的最適。',
 16:'主模型為max E[profit] s.t. joint-service≥α。最少投入問題另以最大合法回流計算，兩者不能混用。示意表未宣稱經濟VSS或任何現場結果。',
 19:'第83輪為最大合法回流下的最小整數投入比較，不是第63/73輪的利潤受限政策最佳化。',
 24:'151點來源為第79輪C≥.8且T<.8的既有子集；帶符號拆分分量可抵銷，不稱因果解釋比例。'
 };
 const pages=[];
 for(const [i,row]of final.records.entries()){
  const sl=p.resolve(row.id);
  if(i===11)txt(sl,'目前價值條件下，送正量時送滿較有利（條件見第26頁）',60,585,1150,42,27,C.new,true);
  for(const el of row.elements??[]){if(el.kind==='textbox'&&el.position?.left>=1200&&el.position?.top>=640&&/^\d{2}$/.test(el.text??''))p.resolve(el.id).text=String(i+1).padStart(2,'0');}
  const originalIndex=old.indexOf(row.id);
  const sources=originalIndex>=0?oldManifest.slides[originalIndex].sources:[SPEC,CODE,PROOF,...([13,14].includes(i)?[DIR+'/teaching_arithmetic.json']:[])];
  sl.speakerNotes.text=VOICE[i]+(reserve[i]?'\n\n被問到再補充（不用照念）\n'+reserve[i]:'')+'\n\n資料來源（不用念）\n'+sources.join('\n');
  pages.push({page:i+1,title:row.title,spoken:VOICE[i],reserve:reserve[i]??'',sources});
 }
 if(p.slides.items.length!==26)throw new Error('Expected 26 slides');
 await fs.writeFile(DIR+'/slide_manifest.json',JSON.stringify({slides:pages,flowSlides:[2,5,7,8,9,11,12,13,14,16,23,24],tables:[3,4,6,10,15,17,18,20,21,25,26],charts:[19]},null,2));
 const intro='# 逐頁口語講稿 v2\n\n頁碼對應新版26頁簡報。每頁先講下面這一小段，公式與來源留在投影片備註，教授追問再開。\n\n## 先講清楚主軸\n\n目前候選主問題是：在高低品一起交足的機率達標下，選投入量與檢驗後的重工規則，使期望利潤較好。教授仍需核定。\n\n「服務可行性與投入判斷」是目前比較有力的結果，不代表已決定改成純粹最少投入或只求最高服務的論文。原稿已有交足可靠度，多等級返修也是原稿提出的後續方向；加入可修與共享產能限制後，才形成這個投入與重工決策問題。\n\n';
 const guide='\n## 分批使用\n\n第一次說明題目，可用第1–8、22頁。要講底層怎麼算，集中第9–17頁。研究結果用第18–21頁；第23–24頁談研究進展與成稿，第25–26頁備查。這是分批使用建議，不需要一口氣講完26頁。\n';
 await fs.mkdir(ROOT+'/output/presentations',{recursive:true});
 await fs.writeFile(ROOT+'/output/presentations/OPT1_逐頁口語講稿_v2.md',intro+pages.map(x=>'## 第'+x.page+'頁 '+x.title+'\n\n'+x.spoken+'\n').join('\n')+guide,'utf8');
 return {slideCount:26,newExplanationSlides:9,spokenParagraphs:26,sourceSlidesReused:17};
}
