import fs from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
const ROOT='C:/Users/uuuwk/karissa/OPT1/OPT1';
const SKILL='C:/Users/uuuwk/.codex/plugins/cache/openai-primary-runtime/presentations/26.1025.11240/skills/presentations';
const {applyPresentationChartFont}=await import(pathToFileURL(SKILL+'/container_tools/artifact_tool_utils.mjs').href);
const FONT='Microsoft JhengHei';
const C={bg:'#FAFBFA',ink:'#153447',muted:'#506573',old:'#244B6A',oldBg:'#EAF0F5',new:'#007F78',newBg:'#E6F2EF',amber:'#986411',amberBg:'#FBF1DB',red:'#B1493F',line:'#B9C7CC',white:'#FFFFFF'};
const SOURCE={origin:ROOT+'/research/2026-10-30/原文兩政策_重工來源與84輪程式說明.md', beginner:ROOT+'/research/2026-10-30/從零理解_研究目標與現況.md', latest:ROOT+'/research/2026-10-30/收斂推進_本次成果與教授決策.md', plan:ROOT+'/research/2026-10-30/教授報告與三月成稿計畫.md',r73:ROOT+'/research/2026-10-28/service_rounds/round73.json',r79:ROOT+'/research/2026-10-28/service_rounds/round79.json',r83:ROOT+'/research/2026-10-28/service_rounds/round83.json',split:ROOT+'/research/2026-10-30/mean_error_151/results.json',cross:ROOT+'/research/2026-10-30/mean_error_151/crosscheck.json',lit:ROOT+'/research/2026-10-30/literature/全文閱讀與差異核對.md'};
const pages=[];
const read=async p=>JSON.parse(await fs.readFile(p,'utf8'));
function text(s,t,x,y,w,h,size=28,color=C.ink,bold=false,align='left'){
 const a=s.shapes.add({geometry:'textbox',name:t.slice(0,45),position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 a.text=t;a.text.style={typeface:FONT,fontSize:size,color,bold,alignment:align,verticalAlignment:'middle',wrap:'square',autoFit:'none',insets:0};return a;
}
function node(s,t,x,y,w=230,h=108,kind='new',size=27,geometry='rect'){
 const col=kind==='old'?C.old:kind==='hyp'?C.amber:C.new;
 const bg=kind==='old'?C.oldBg:kind==='hyp'?C.amberBg:C.newBg;
 const a=s.shapes.add({geometry,name:t.replaceAll('\n',' / '),position:{left:x,top:y,width:w,height:h},fill:bg,line:{fill:col,width:1.5}});
 a.text=t;a.text.style={typeface:FONT,fontSize:size,color:col,bold:true,alignment:'center',verticalAlignment:'middle',insets:13,autoFit:'none',wrap:'square'};return a;
}
function conn(s,a,b,from='right',to='left',color=C.muted,kind='straight'){
 return s.shapes.connect(a,b,{kind,fromSide:from,toSide:to,line:{fill:color,width:2.2,style:'solid'},tail:{type:'triangle',width:'med',length:'med'}});
}
function note(s,t){text(s,t,60,646,1130,42,20,C.muted);}
function slide(p,title,notes,sources=[]){
 const s=p.slides.add({width:1280,height:720});s.background.fill=C.bg;
 text(s,title,60,42,1160,82,44,C.ink,true);
 text(s,String(p.slides.items.length).padStart(2,'0'),1210,660,40,30,17,C.muted,false,'right');
 s.speakerNotes.text=notes+'\n\n來源與閱讀界線\n'+sources.join('\n');
 pages.push({page:p.slides.items.length,title,notes,sources});return s;
}
function table(s,values,x=60,y=170,w=1160,h=400,widths=null,size=26){
 const a=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,values,...(widths?{columnWidths:widths}:{})});
 a.borders.assign({fill:'#D3DDE0',width:1,style:'solid'});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
  const cell=a.getCell(r,c);cell.fill=r===0?C.old:(r%2===0?'#F0F4F3':C.white);
  cell.text.style={typeface:FONT,fontSize:size,color:r===0?C.white:C.ink,bold:r===0,verticalAlignment:'middle',insets:12,autoFit:'none',wrap:'square'};
 }
 return a;
}
function list(s,items,x=70,y=175,w=1130,gap=108,size=30){items.forEach((t,i)=>{text(s,String(i+1).padStart(2,'0'),x,y+i*gap,65,65,35,C.new,true);text(s,t,x+90,y+i*gap,w-90,75,size,C.ink);});}

export async function build(p){
 if(p.slides.items.length)throw new Error('Expected new empty deck');
 const r73=await read(SOURCE.r73), split=await read(SOURCE.split);
 // 01
 let s=slide(p,'有限批次品質與選別重工',
 '開場可以說：我們接續一份多等級產線研究，想知道有限一批產品的品質不確定時，該先投入多少、看到品質後要不要返修，才能同時交足高低品訂單。84輪是探索、計算和核對的紀錄，不是84個全新模型。今天先把工廠故事、來源、方法與結果講清楚。',[SOURCE.beginner,SOURCE.latest]);
 text(s,'我們在研究什麼？',60,205,1160,95,61,C.ink,true);
 text(s,'先投入多少，檢驗後何時值得返修，\n才能把高低品訂單一起交足',60,335,1130,150,40,C.new,true);
 text(s,'研究入門與教授報告版\n依第1–84輪及2026年10月30日補充整理',60,550,1120,78,25,C.muted);
 // 02
 s=slide(p,'工廠面對一張高低品訂單',
 '先用高品100、低品50的教學訂單說明。同一批經正常加工後會出現不同品質等級，不能事先保證各有幾件。原稿已有KQC品質規格及品質分級。此頁是問題示意，數字不是工廠實測。高低品必須在同一批交足，才算一次完整履約。',[SOURCE.origin,SOURCE.beginner]);
 const o=node(s,'訂單\n高品100\n低品50',60,210,240,120,'old');
 const pr=node(s,'決定原料投入\n正常加工',370,210,230,120,'old');
 const in1=node(s,'檢驗分級\n高品／低品／報廢',670,210,250,120,'old');
 const de=node(s,'分配交貨\n兩級都要交足',990,210,230,120,'old');
 conn(s,o,pr);conn(s,pr,in1);conn(s,in1,de);
 text(s,'研究要面對的落差',60,420,1100,60,34,C.new,true);
 text(s,'平均看起來夠，實際這一批仍可能高品不足或低品不足',60,495,1140,95,34);
 note(s,'本頁100／50是教學例，不是新增實驗情境或現場資料');
 // 03
 s=slide(p,'原稿的兩個交貨政策',
 '原稿Policy I讓各等級只供自己的需求。Policy II允許剩餘高品直接補低品缺口，產品不回機器。教學例中，高品120低品30，需求100及50，Policy I低品缺20；Policy II把20件剩餘高品交給低品客戶即可全數交足。不能把這個直接替代說成把高品重作成低品。',[SOURCE.origin,'原始多等級論文PDF第7頁§3.3；原稿JORS_manuscript_anonymous_R5.docx']);
 text(s,'例：需求高品100、低品50；成品高品120、低品30',60,132,1150,55,29,C.muted);
 table(s,[['政策','分配方式','是否交足'],['Policy I\n同等級供貨','高品交100\n低品交30','低品缺20'],['Policy II\n向下替代','高品交100\n剩餘高品20加低品30供低品單','兩級都交足']],60,220,1160,330,[240,670,250],29);
 note(s,'Policy II的替代只改交貨用途與售價，不需要再加工');
 // 04
 s=slide(p,'向下替代與升級返修',
 '這是最重要的區別。上半是原稿Policy II，高品本來符合低品較寬規格，直接交貨。下半是本案探索的升級返修，要把部分低品送回加工，耗產能及成本，成功才成高品。低品不能直接冒充高品，返修也不能保證成功。',[SOURCE.origin]);
 text(s,'原稿已有的向下替代',60,155,1140,50,31,C.old,true);
 let a=node(s,'剩餘高品',60,225,280,100,'old'),b=node(s,'直接供低品訂單',480,225,320,100,'old'),c=node(s,'不再加工',940,225,280,100,'old');conn(s,a,b);conn(s,b,c);
 text(s,'後來研究的升級返修',60,390,1140,50,31,C.new,true);
 a=node(s,'符合可修條件的低品',60,460,300,110);b=node(s,'再加工\n耗成本與產能',480,460,320,110);c=node(s,'成功成高品\n失敗報廢',940,460,280,110,'hyp');conn(s,a,b);conn(s,b,c);
 note(s,'升級路徑、成功率及失敗報廢目前均需製程資料確認');
 // 05
 s=slide(p,'原有內容與本專案新增內容',
 '左欄是來源，右欄是相對來源新增的處理，不等於學術首創。原稿本來已有隨機KQC推分級比例及共同交足可靠度。新增的是有限批次件數隨機、合法可修子類、品質後啟動與未來成功的資訊順序。原稿結尾也已點名多等級返修與KQC相依的未來方向。',[SOURCE.origin]);
 table(s,[['項目','原有內容','本專案後來處理'],['品質與交貨','品質規格、分級、Policy I／II','有限批次的等級件數隨機'],['機台容量','多狀態可用容量與正常良率','同批剩餘容量供合法返修'],['重工來源','另一份光纖案例已有P1–P3回流','篩選候選單向路徑與可修池'],['決策','原政策計算所需投入與可靠度','整數投入與品質後啟動一起比較'],['研究證據','原文模型與案例資料','程式、條件推導、獨立核對與界線']],60,165,1160,435,[180,450,530],25);
 note(s,'相對起點新增，與學術界首創，是兩個不同的判斷');
 // 06
 s=slide(p,'目前保留的產線流程',
 '先投入並執行固定正常加工，檢驗後才有高品、低品及不合格品。只允許符合指定條件的一部分低品返修，而且要保留低品訂單並受最後站剩餘工作量限制。圖上的返修回到最後一站是候選示例，並未確認真實螺桿能照此加工。正常加工耗過的工作量不能重複當成返修容量。',[SOURCE.latest,ROOT+'/research/2026-10-28/最小模型規格_v0.1.md']);
 a=node(s,'整數投入 I',60,205,190,95,'old');b=node(s,'五站正常加工\n容量已揭露',320,205,240,95,'old');c=node(s,'檢驗分級',630,205,210,95,'old');const alloc=node(s,'向下替代與交貨\n檢查共同交足',940,205,280,95,'old');conn(s,a,b);conn(s,b,c);conn(s,c,alloc);
 const pool=node(s,'低品中的可修子集合\n先保留低品訂單',520,425,310,120);
 const repair=node(s,'最後站單次返修\n只用剩餘工作量',940,425,280,120);
 conn(s,c,pool,'bottom','top',C.new,'elbow');conn(s,pool,repair,'right','left',C.new);conn(s,repair,alloc,'top','bottom',C.new);
 text(s,'返修成功數仍未知',60,435,370,55,32,C.amber,true);text(s,'成功成高品，失敗報廢\n單向路徑是待確認的示例',60,500,390,92,27,C.muted);
 note(s,'主軸維持單期、固定正常流；其餘回流路徑及正常量控制留作界線');
 // 07
 s=slide(p,'決策與資訊揭露的時間順序',
 '逐步解釋每個時點：t0只有法則與參數，先選確定性整數投入。t1看見容量後執行固定正常流，不在這版重新最佳化正常量。t2看見初次品質和可修件數後決定是否啟動。t3才知道成功多少並計算交貨。即使程式能枚舉所有未來結果，也不能讓t2的政策偷看t3。',[SOURCE.latest,ROOT+'/research/2026-10-28/最小模型規格_v0.1.md']);
 const ts=[['t0 事前','選投入 I\n尚不知道本批容量'],['t1 容量揭露','執行固定正常流\n得到完成量 N'],['t2 品質揭露','觀察品質與可修量\n決定是否啟動'],['t3 成敗揭露','知道返修成功件數\n計算交貨與收益']];
 const ns=ts.map((t,i)=>node(s,t[0]+'\n\n'+t[1],60+i*300,220,260,230,i<2?'old':i===2?'new':'hyp',27));ns.slice(1).forEach((x,i)=>conn(s,ns[i],x));
 text(s,'啟動時知道可送幾件，還不知道會成功幾件',60,510,1160,82,37,C.new,true);
 note(s,'精算會加總未來結果；實際決策必須遵守當時已知的資訊');
 // 08
 s=slide(p,'合法返修量有三道上限',
 '例子是教學用的單一觀察狀態。低品70，訂單低品50，所以最多動用20；可修低品25；剩餘容量可加工15。三個上限取最小，最多送15件。可修池是可辨識子集合，先保留低品需求是這版固定行動規則，不宣稱這是所有契約下的最優配置。',[SOURCE.origin,ROOT+'/research/2026-10-28/最小模型規格_v0.1.md']);
 const caps=[['可修品資格','可修低品25件'],['保留低品訂單','70件低品減需求50\n可動用20件'],['剩餘工作量','最後站還能加工15件']];
 const capnodes=caps.map((t,i)=>node(s,t[0]+'\n\n'+t[1],60+i*410,185,340,180,i===0?'hyp':'new',28));
 const min=node(s,'最多返修 R = min(25, 20, 15) = 15件',310,465,660,100,'new',34);
 capnodes.forEach((x,i)=>conn(s,x,min,'bottom','top',C.new,'elbow'));
 note(s,'教學例。可修比例、路徑與可用時段均需資料支持；不是所有低品都能升級');
 // 09
 s=slide(p,'啟動返修之後，仍可能交不齊',
 '沿用教學狀態：高品92低品70，需求100及50，可送15。若不修，高品不足。若送15，低品剩55，但未來成功若只有7件，高品99仍失敗；若成功14件，高品106則兩級交足。例子說明合法與可能有幫助不等於保證成功。真實政策比較所有未知結果的條件期望和共同服務機率。',[SOURCE.origin,SOURCE.latest]);
 const st=node(s,'已觀察\n高品92／低品70',60,285,240,110,'old');
 const zero=node(s,'不啟動\n返修0件',400,175,220,105);
 const yes=node(s,'啟動\n返修15件',400,395,220,105);
 const zresult=node(s,'高品92／低品70\n高品不足',860,175,350,105,'hyp');
 const fail=node(s,'若成功7件\n高品99／低品55，未交足',860,340,350,105,'hyp',26);
 const ok=node(s,'若成功14件\n高品106／低品55，交足',860,510,350,105,'new',26);
 conn(s,st,zero,'right','left',C.muted,'elbow');conn(s,st,yes,'right','left',C.muted,'elbow');conn(s,zero,zresult);conn(s,yes,fail,'right','left',C.amber,'elbow');conn(s,yes,ok,'right','left',C.new,'elbow');
 text(s,'送出後\n才知成敗',650,260,180,70,26,C.amber,true,'center');
 note(s,'本頁是教學狀態與可能結果，未表示這兩種成功件數等機率');
 // 10
 s=slide(p,'共同交足機率的意思',
 '四個等機率的假想交貨結果，已按交貨政策完成分配，數字是實際供給各訂單的件數。高品達標3次、低品達標3次，各75%，但同時達標只有2次，所以共同交足50%。不能把兩個邊際服務水準平均，也不能未證明獨立就相乘。這個概念原稿已有，本案對新增品質與返修再正確計算。',[SOURCE.origin,SOURCE.beginner]);
 table(s,[['四個等機率教學結果','交高品／需求100','交低品／需求50','兩級共同交足'],['情況1','100','50','是'],['情況2','100','45','否'],['情況3','95','50','否'],['情況4','100','50','是']],60,160,1160,350,[330,280,280,270],27);
 text(s,'高品達標 75%      低品達標 75%      共同交足 50%',60,540,1160,80,34,C.new,true);
 note(s,'教學分布，非現場資料。共同交足與平均產量、填補率不同');
 // 11
 s=slide(p,'84輪研究的形成順序',
 '不需要報84次。把研究分成六段，讓教授看見為什麼留下主模型。第一段重現與早期重工，第二段修規格與經濟口徑，第三段有限批次及工序核對，第四段正式時點與精算，第五段批次壓力和公平基準，第六段界線與平均化後果。10月30日151點拆分是第84輪後的限定補充，不混進原輪數。',[SOURCE.plan,SOURCE.origin]);
 const stage=[['1–26輪','重現原稿\n試早期重工'],['27–43輪','修服務與成本\n核合法動作'],['44–57輪','有限批次品質\n重查工序'],['58–64輪','未知返修成功\n投入與啟動'],['65–73輪','批次壓力測試\n強基準比較'],['74–84輪','界線與反例\n投入決策後果']];
 const sx=[60,460,860,860,460,60],sy=[175,175,175,415,415,415];const ss=stage.map((t,i)=>node(s,t[0]+'\n\n'+t[1],sx[i],sy[i],350,160,i<2?'old':'new',28));
 conn(s,ss[0],ss[1]);conn(s,ss[1],ss[2]);conn(s,ss[2],ss[3],'bottom','top');conn(s,ss[3],ss[4],'left','right');conn(s,ss[4],ss[5],'left','right');
 note(s,'84輪含實作、文獻核對及條件稽核；不等於84個新模型或84批工廠資料');
 // 12
 s=slide(p,'每一輪如何產生可檢查的研究進展',
 '研究想法來自文獻、推導與結果的落差，程式幫忙檢驗，不會自動判定新穎性。每輪先有問題，再限定一項改動或假設，算完用另一方法或小批枚舉核對，最後留下或丟棄。失敗或增益很小也是結果，不能為了漂亮數字重抽或堆機制。',[SOURCE.origin,SOURCE.latest]);
 const r1=node(s,'文獻或既有落差\n提出一個問題',60,180,320,145,'old'),r2=node(s,'明確假設\n一次只改一項',480,180,320,145,'hyp'),r3=node(s,'程式計算\n保留同口徑基準',900,180,320,145);
 const r4=node(s,'獨立核對\n枚舉或另一種積分',900,415,320,145),r5=node(s,'判讀留或丟\n記錄適用條件',480,415,320,145),r6=node(s,'保存程式與結果\n才提出下一問',60,415,320,145,'old');
 conn(s,r1,r2);conn(s,r2,r3);conn(s,r3,r4,'bottom','top');conn(s,r4,r5,'left','right');conn(s,r5,r6,'left','right');conn(s,r6,r1,'top','bottom',C.muted,'elbow');
 note(s,'計算是模型內數值實驗。沒有訓練AI，也沒有因此取得新的現場樣本');
 // 13
 s=slide(p,'程式實際在算什麼',
 '五站各有不同可用機台數，合計28224種容量組合，這是模型狀態而非資料筆數。對每個投入與容量算正常產出，再用分布計算品質及返修成功，先按可觀察資訊選行動，最後加總機率與收益。主模型用條件機率與尾機率，經濟服務前緣用標準覆蓋排序和LP界，不是從新文獻直接搬來一個神奇AI算法。',[SOURCE.origin,ROOT+'/research/2026-10-28/命題條件與證明稽核.md']);
 const labels=['投入 I\n與容量狀態','正常產出\n與返修餘裕','隨機分級\n與合法動作','未知成功\n的機率加總','服務與收益\n再比較投入'];
 const ns2=labels.map((t,i)=>node(s,t,60+i*238,245,208,140,i<2?'old':'new',27));ns2.slice(1).forEach((x,i)=>conn(s,ns2[i],x));
 text(s,'28,224 種容量狀態',60,440,520,65,38,C.old,true);text(s,'15 組訂單 × 2,101 個投入',650,440,570,65,34,C.new,true);
 text(s,'枚舉可能機台組合',60,520,520,58,27,C.muted);text(s,'形成31,515個模型評估點',650,520,570,58,27,C.muted);
 note(s,'標準分布、尾機率與覆蓋排序已有理論；本案用途與條件仍須逐項交代');
 // 14
 s=slide(p,'公平比較後，利潤增益多半不大',
 '此表來自第73輪主模型自動替代，每種政策都在整數投入0到2100重新選投入，並達相同服務目標才比較。增益對最強可行基準，不能只挑弱的一律返修。550/350最好的政策是不重工。700/200與750/150的無重工基準在該目標不可行，比較對象為最佳一律重工。這些是指定假設下的模型利潤單位，不直接等於工廠貨幣收益。',[SOURCE.r73,SOURCE.latest]);
 const profits=r73.cases.map(x=>{const bas=[x.always_return_best.expected_profit,...(x.no_repair_best?[x.no_repair_best.expected_profit]:[])];const gain=x.proposed_feasible.expected_profit-Math.max(...bas);return [x.demands.map(Number).join('／'),(x.target*100).toFixed(0)+'%',gain.toFixed(2),x.no_repair_best?(gain<.01?'不重工即可':'最強基準為無重工'):'無重工在此目標不可行'];});
 table(s,[['高品／低品需求','共同服務目標','相對強基準多','結果意義'],...profits],60,175,1160,355,[270,240,240,410],27);
 text(s,'論文主要結果放在服務可行性與投入判斷',60,565,1160,62,34,C.new,true);
 note(s,'同一自動替代、原料全承諾及成本口徑，各政策都重選投入');
 // 15
 s=slide(p,'平均計數可能高估共同交足',
 '500/300投入1152是79輪全網格的最大高估見證。C同時平均初次分類和未來成功，M保留初次隨機只平均成功，T全隨機。C96.56%，M和T均約50.97%，相差約45.59百分點。這是指定平均化比較器，並非宣稱原文或Tsai、Bitran採這個算法，也不是說原稿在自己的比例假設內算錯。',[SOURCE.r79,SOURCE.split]);
 text(s,'需求高品500、低品300；投入1152；一律最大合法回流',60,130,1150,60,27,C.muted);
 const w=split.rows.find(x=>x.demands[0]===500&&x.demands[1]===300&&x.input===1152);
 const ch=s.charts.add('bar',{position:{left:65,top:220,width:770,height:360},categories:['平均計數 C','初次隨機 M','完整隨機 T'],series:[{name:'共同交足機率',values:[w.C,w.M,w.T],fill:C.new,points:[{idx:0,fill:C.amber},{idx:1,fill:C.old},{idx:2,fill:C.new}]}],barOptions:{direction:'column',gapWidth:100},hasLegend:false,yAxis:{min:0,max:1,majorUnit:.25,numberFormatCode:'0%',textStyle:{fontSize:22,fill:C.muted},majorGridlines:{fill:'#DCE3E3',width:1}},xAxis:{textStyle:{fontSize:24,fill:C.ink}},dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.00%',textStyle:{fontSize:27,bold:true,fill:C.ink}},chartFill:'none',plotAreaFill:'none'});applyPresentationChartFont(ch,{fontFamily:FONT});
 text(s,'高估約\n45.59\n個百分點',900,265,310,250,45,C.amber,true,'center');
 note(s,'C同時平均初次分類及成功數。M與T約差2.35×10⁻⁹機率單位');
 // 16
 s=slide(p,'151個誤判點已全部拆分',
 '151點是原31515網格中，C至少80%而T不足80%的預選集合，共9組訂單，不是151個工廠觀察。補算中間M後151點全部M<80%，另一條回流尾機率積分逐點核對最大差1.6209e-14，共用二項表所以不稱完全獨立軟體。未來成功平均化在本子集影響最大1.59024百分點。兩個分量會抵銷，不能硬說解釋率限制0至100%。',[SOURCE.split,SOURCE.cross]);
 text(s,'保留初次隨機計數後，151點全部低於80%',60,140,1160,75,37,C.new,true);
 const selected=[[500,300,1152],[650,250,1298],[700,200,1347]].map(([a,b,i])=>{const z=split.rows.find(x=>x.demands[0]===a&&x.demands[1]===b&&x.input===i);return [a+'/'+b+'，I='+i,...['C','M','T'].map(k=>(100*z[k]).toFixed(4)+'%')];});
 table(s,[['原誤判點','平均計數 C','初次隨機 M','完整隨機 T'],...selected],60,260,1160,290,[350,270,270,270],26);
 text(s,'只平均未來成功，影響最大約1.59個百分點',60,570,1140,62,31,C.ink,true);
 note(s,'只對這組預選點成立。初次計數平均化是指定順序拆分的大分量');
 // 17
 s=slide(p,'服務估計會改變投入決策',
 '此結果沿用第83輪，最大回流的最小投入問題，不是利潤政策或經濟VSS。500/300目標95%，平均比較器選1152，完整模型服務僅50.97%；完整模型最小需1184，服務95.2644%。700/200目標90%時平均比較器有解，但完整模型全投入0到2100最高89.3867%，在指定行動及分布下不可行。這不是工廠90%目標被排除。',[SOURCE.r83,ROOT+'/research/2026-10-28/service_rounds/round71.json']);
 table(s,[['訂單與目標','平均比較器的判斷','完整模型的判斷'],['500／300，95%','選投入1152\n實際模型服務僅50.97%','最小投入1184\n模型服務約95.26%'],['700／200，90%','判為可行','所有投入最高約89.39%\n在此模型下不可行']],60,190,1160,350,[280,440,440],28);
 text(s,'投入量與可行性，必須用完整服務機率評估',60,570,1150,65,32,C.new,true);
 note(s,'指定獨立品質、候選單向路徑與固定正常流。這項比較沒有計算經濟VSS');
 // 18
 s=slide(p,'文獻如何影響模型與貢獻',
 '文獻並不是最後才補在參考書目。它會支持共享資源及良率結構，也會排除不該說的新穎性。Chen2018作者稿已有產出後升級與門檻；Jiang2017有共同服務SAA；Boutarfa2024有升降級替代共享線。相對起點有新增，不表示整合首創。三篇最接近全文還沒取得，表內不能以摘要判定沒有選別返修。',[SOURCE.lit,'Chen et al DOI10.1080/00207543.2017.1402138；作者18頁稿，非期刊逐頁核對','Jiang et al DOI10.1080/00207543.2016.1193245','Kohlmann/Sahling DOI10.1080/00207543.2024.2314717','Boutarfa et al DOI10.1016/j.ijpe.2024.109308']);
 table(s,[['文獻用途','已知前例','對本案的作用'],['機制與假設','共享正常／返修資源\n逐件與批次良率','決定怎樣建模、哪些參數要資料'],['貢獻界線','品質後升級與門檻\n共同服務與替代／共享線','縮小主張，避免把舊概念當首創'],['最接近全文','Tsai 2024、Hsu/Bassok 1999\nBitran/Leong 1992','服務事件、安全量與返修時點\n仍待逐頁核對']],60,185,1160,360,[230,460,470],26);
 note(s,'標準機率與排序已有理論。目前是限定問題的候選整合，尚未確認首創');
 // 19
 s=slide(p,'分批報告與2027年3月成稿',
 '這是建議進度，不是已約會議或學校行政期限。11月中就先核定主問題、合成或實際資料、終端價值，不把風險拖到1月。六次研究報告依1–26、27–43、44–57、58–64、65–73、74–84分組，每場約15分鐘6至8頁。已有結果照實說已完成，分批是為理解與審查，不是假裝以後才做。1月底完整初稿，2月修，3月定稿留緩衝。',[SOURCE.plan]);
 const plan=[['11月','核主題與資料\n月底凍結範圍'],['12月','審方法與證據\n同步寫章節'],['1月','收斂正文附錄\n月底完整初稿'],['2月至3月','依教授意見修訂\n留口試行政時間']];
 const pn=plan.map((t,i)=>node(s,t[0]+'\n\n'+t[1],60+i*300,220,260,220,i===0?'hyp':'new',26));pn.slice(1).forEach((x,i)=>conn(s,pn[i],x));
 text(s,'每次集中一個問題，沿用流程圖與既有結果',60,505,1160,70,35,C.new,true);
 note(s,'六批研究報告加稿件審閱。不必逐輪報84次，也不需為報告重跑數據');
 // 20
 s=slide(p,'教授需要核定的三件事',
 '用這三個具體問題結束。第一，接受單期固定正常流、選別返修與共同交足作主軸嗎？第二，有現場批次與返修數據，或能接受明確標示的合成方法案例嗎？第三，現場剩餘價值是否讓每多返修一件期望邊際仍正，支持0與最大量二元比較？若不支持，現求解器不能稱一般返修量最適。不要把這一頁寫成教授已核准，也不保證3月一定完成。',[SOURCE.latest,SOURCE.plan]);
 list(s,['主問題：單期選別返修與共同交足是否足夠？','資料定位：現場批次，或明確標示的合成案例？','經濟條件：終端價值是否支持「不修或滿量修」？'],70,180,1120,135,32);
 text(s,'已有可寫初稿的模型與計算，貢獻與資料仍需核定',60,585,1160,54,29,C.new,true);
 // 21 appendix
 s=slide(p,'附錄A：主要符號與假設',
 '這頁備查，不必在第一次報告逐項推導。可回流上限R取可修件E、低品盈餘及容量L的最小值。Y在決策後才抽Bin(r,eta)。0/R簡化需售價p1不低於終端高品價值v1，以及v1 eta>v2+cr。現在120>=90，90*.97=87.3>30+12.4，所以滿足這個模型內前提；終端值降低可能出現部分返修，第77輪是單一狀態反例。',[ROOT+'/research/2026-10-28/論文主軸與章節草稿.md',ROOT+'/research/2026-10-28/service_rounds/round77.json']);
 table(s,[['符號','白話意思','狀態'],['I，N','事前投入；正常加工完成的整件數','I為決策，N依容量決定'],['A，B，E','高品、低品、低品中可修件數','檢驗後才觀察'],['R = min(E, (B−D₂)⁺, L)','最多能合法送回的件數','保留低品並受可用容量L限制'],['Yᵣ ∼ Binomial(r, η)','送r件之後真正成功的件數','啟動時仍未知'],['η=.97，v₁/v₂=90/30','成功率與終端剩餘價值','本案假設，待資料核定']],60,160,1160,380,[390,430,340],24);
 text(s,'0／R前提：p₁ ≥ v₁ 且 v₁η > v₂ + cᵣ',60,560,1140,55,32,C.new,true);
 note(s,'成功率不能由正常工序良率直接冒充。若前提不成立，可能需要部分返修量');
 // 22 appendix
 s=slide(p,'附錄B：引用與閱讀深度',
 '來源以實際取得與閱讀深度標記。原稿兩政策在原多等級PDF第7頁，未來研究在第17頁。Chen作者稿已讀p1,3–8,11–14，Jiang正式PDF含封面已讀p2–7,10–12；不是兩篇每頁都讀過。Kohlmann與Boutarfa先前讀關鍵模型頁。三篇直接全文仍未取得，不把403或Cookie頁當全文。完整DOI及本地來源列於本頁備註。',[SOURCE.lit,ROOT+'/research/2026-10-28/文獻差異與候選貢獻矩陣.md','Chen et al 2018: https://doi.org/10.1080/00207543.2017.1402138 ; author PDF https://facultystaff.richmond.edu/~bchen/Research/OperFlexibility2018.pdf','Jiang et al 2017: https://doi.org/10.1080/00207543.2016.1193245','Kohlmann and Sahling2024: https://doi.org/10.1080/00207543.2024.2314717','Boutarfa et al2024: https://doi.org/10.1016/j.ijpe.2024.109308','Tsai et al2024: https://doi.org/10.1016/j.cor.2024.106544','Hsu and Bassok1999: https://doi.org/10.1287/opre.47.2.277','Bitran and Leong1992: https://doi.org/10.1287/mnsc.38.5.724']);
 table(s,[['來源','實際閱讀範圍／版本','角色'],['多等級原稿','原政策、案例及未來研究段落','研究起點'],['Chen等 2018','18頁作者稿，讀p1、3–8、11–14','品質後升級前例'],['Jiang等 2017','22頁期刊PDF，讀p2–7、10–12','共同服務前例'],['Kohlmann／Sahling 2024','已取得全文，讀相關模型頁','共享資源及啟動'],['Boutarfa等 2024','已取得全文，讀多等級相關頁','整合貢獻界線'],['Tsai 2024、Hsu／Bassok 1999\nBitran／Leong 1992','僅摘要或片段，全文待補','仍需優先核對']],60,160,1160,445,[415,500,245],23);
 note(s,'完整DOI與本地證據在各頁備註。文獻有前例，不等於本研究沒有可做的限定問題');
 if(p.slides.items.length!==22)throw new Error('Unexpected slide count');
 await fs.writeFile(ROOT+'/.build/opt1_presentation/slide_manifest.json',JSON.stringify({slides:pages,editableFlowSlides:[2,4,6,7,8,9,11,12,13,19],nativeTableSlides:[3,5,10,14,16,17,18,21,22],nativeChartSlides:[15],font:FONT},null,2));
 return {slideCount:22,flowSlides:10,font:FONT};
}
