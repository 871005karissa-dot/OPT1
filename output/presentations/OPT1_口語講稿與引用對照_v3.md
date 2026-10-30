# 口語講稿與引用對照 v3

主報告可用第1–22頁。第23–24頁交代研究歷程與成稿，第25–30頁供追問時使用，第31–36頁為完整書目，第37頁為本研究結果索引。無須一次講完全部頁面。

分批報告建議：第一次用第1–8、22頁確認題目，第二次用第9–17頁解釋計算，第三次用第18–21、25頁報告結果。文獻追問開第27–28頁，數值核對開第29頁，資料定位開第30頁，時程用第23–24頁。

目前候選主問題：在高低品共同交足機率達標下，選事前整數投入與檢驗後重工規則，比較期望利潤。服務可行性與投入判斷是目前較明顯的發現；教授仍需核定題目與資料定位。

R編號是外部文獻，S編號是本研究模型與結果，E編號是教學示意。已取得PDF不等於逐頁讀完，文獻閱讀版本與範圍逐項標示。

## 第1頁 有限批次品質與選別重工

我的研究是接著原稿往下做。原稿比較不同交貨方式能不能交足，我多問一步：如果允許重工，該投多少、看到哪些品質狀況才要修。

引用：研究起點：[R1] Chen & Lin (2026)　　本研究模型：[S1]

完整書目見第31頁。

## 第2頁 這個研究問題從哪裡來

這個方向是從原稿長出來的。原稿已經在看交足訂單的機率，也把多等級重工列成後續方向。我把這件事做成能計算、能比較的決策問題。

引用：[R1] Chen & Lin (2026), §7, PDF p.17　　本案設定與結果：[S1–S3]

完整書目見第31頁。

## 第3頁 研究問題、限制與主要發現

我的問題還是怎麼投料、怎麼重工，讓期望利潤比較好。但有一個前提：高低品一起交足的機率，要先達到要求。教授還需要核定這個範圍。

引用：共同服務限制的前例：[R3] Jiang et al. (2017)　　本研究決策定義：[S1]

完整書目見第32頁。

## 第4頁 原稿的兩個交貨政策

原稿的兩個政策都在分配成品。第一個只交同等級；第二個可以把剩下的高品補給低品客戶。這個替代不用送回機器。

引用：[R1] Chen & Lin (2026), §3.3, PDF p.7　　本頁100/50算例為教學示意

完整書目見第31頁。

## 第5頁 向下替代與升級返修

向下替代是高品直接交給低品客戶。重工則是把符合條件的低品再加工，嘗試升成高品。後者會花錢、占產能，而且可能失敗。

引用：替代政策：[R1] §3.3　　品質後升級前例：[R2] Chen et al. (2018)　　本案：[S1]

完整書目見第31頁。

## 第6頁 原有內容與本專案新增內容

原稿已有分級、容量和替代。我加的是有限一批的件數變動、可修品限制，以及檢驗後才決定修不修。相對原稿有新增，還不等於學術首創。

引用：原有模型：[R1]　　另附案例：重工case.docx　　本專案延伸：[S1]

完整書目見第31頁。

## 第7頁 目前保留的產線流程

正常生產先照固定規則做，檢驗後才知道有哪些成品。低品裡只有一部分能修，還得留夠低品訂單，用剩下的產能處理。最後一站只是待確認的例子。

引用：共享產能前例：[R4]　　可修特性與方向：[R6]　　本案單向路徑設定：[S1]

完整書目見第32、33頁。

## 第8頁 決策與資訊揭露的時間順序

順序不能顛倒。先投料，再知道容量、做完正常生產，接著看品質決定修不修。修好幾件是最後才知道，程式不能先看答案再選。

引用：品質揭露後升級前例：[R2] 作者稿p.3–5　　本案資訊時點與未知成功數：[S1]

完整書目見第31頁。

## 第9頁 先算好一張規則表，現場再照表決定

程式先在規劃時算好投入量和一張啟動表。現場不用重算所有可能，只要檢驗後知道件數和剩餘產能，再照表決定要不要修。

引用：本研究規則與求解：[S1] stochastic_setup_frontier.py；命題稽核§3–4

## 第10頁 程式需要哪些資料

程式要先有訂單、達標要求、機台和成本，也要有品質和返修的機率。像成功率九成七，目前只是模型假設，不能當成工廠已量到的數據。

引用：原始機台與品質案例：[R1] §5.1、表2–3　　新增假設與成本口徑：[S1]

完整書目見第31頁。

## 第11頁 固定一個投入量，程式如何計算

先固定一個投入量。程式把可能的容量、品質和修復結果算進去，替每個決定算平均收益和交足率。再換另一個投入量做同樣的比較。

引用：本研究條件分解：[S1] 命題稽核§2–4；求解器（標準機率公式）

## 第12頁 合法返修量有三道上限

例如低品有七十件，要留五十件交貨，最多能動二十件。可修的有二十五件，但產能只夠修十五件，所以最後最多只能送十五件。

引用：方向與可修資格的文獻依據：[R6]　　本案上限及0/R推導：[S1] §1–2　　算例：[E1]

完整書目見第33頁。

## 第13頁 啟動返修之後，仍可能交不齊

這時高品有八十六件，還缺十四件。送十五件去修，成功十三件還是不夠，成功十四件才交得齊。所以送出十五件，不代表一定補得足。

引用：本頁為教學狀態：[E1]　　合法行動與決策時點：[S1]

## 第14頁 送15件返修，交足的機率怎麼算

假設每件有九成七的機會修好，十五件裡至少修好十四件的機率，大約是92.7%。程式把這些可能結果加起來，不會拿平均14.55件直接當成交貨數量。

引用：教學計算：[E1]，二項式尾機率　　模型與0/R條件：[S1] §1–3

## 第15頁 整體服務是把各種情況加權相加

接著要把不同情況合在一起。這個教學例裡，一半本來就能交足，三成靠重工，另外兩成仍缺貨。加權後約七成七八，才是整體交足率。

引用：教學權重與算例：[E1]；50%/30%/20%為說明用權重

## 第16頁 啟動表如何兼顧利潤與達標

修了可能比較容易交足，但不一定多賺。所以先納入有利潤的重工；如果整體交足率還不足，再找補足服務所需代價較小的情況。

引用：本研究推導：[S1] 命題稽核§4（標準覆蓋排序、LP上界及固定規則差距）

## 第17頁 達標後，以期望利潤挑投入

最後只比較達標的投入。這個示意表裡，兩百件已經達標，但兩百一十件的期望利潤更好，所以選兩百一十。最少投入和最賺的投入要分開看。

引用：選擇準則：[S1]　　200/210/220與收益數字為教學示意：[E1]

## 第18頁 公平比較後，利潤增益多半不大

回到真正的計算，每個基準也都重新選投入。公平比完，選擇重工通常只多賺一點，有的訂單甚至不重工最好。這是目前的結果。

引用：本研究結果：[S2] 第73輪 round73.json；每個基準均重選投入

## 第19頁 平均計數可能高估共同交足

圖裡的C把初次分級和成功件數都換成平均，M只平均未來成功件數，T兩層都保留隨機。這一點C算成九成六，T只有五成一左右，主要差在平均初次件數跨過了交貨門檻。

引用：本研究結果：[S3] 第79輪＋平均近似口徑勘誤；151點拆分 results.json

## 第20頁 服務估計會改變投入決策

這會改變決策。五百、三百這張訂單要九成五，平均算法會選一一五二件，完整模型要一一八四件。這裡是在找最少達標投入，和利潤最佳化分開報。

引用：本研究結果：[S4] 第83輪 round83.json；最大合法回流下的最少投入

## 第21頁 文獻如何影響模型與貢獻

這些文獻各有用途：有的幫我檢查可修條件，有的提醒我升級、共享產能和共同服務早已有前例。後面有逐篇對照與完整書目，三篇缺全文的會清楚列出。

引用：模型前例：[R2–R7]　　直接對照待全文：[R9–R11]　　版本及閱讀範圍見文末

完整書目見第31、32、33、34、35、36頁。

## 第22頁 教授需要核定的三件事

現在最需要老師確認的是：這個單期問題能不能當主軸、用現場還是合成資料，以及剩餘品價值能不能支持目前的返修規則。

引用：本研究候選規格：[S1]；本頁為待教授核定事項

## 第23頁 84輪研究的形成順序

八十四輪不用逐輪講。我把它分成六段：先重現，再修假設，接著建立可核對的計算，最後留下有用結果、交代不適用的地方。

引用：本研究歷程與保存結果：[S1–S6]；輪次代表不同檢查工作

## 第24頁 分批報告與2027年3月成稿

接下來以寫成完整文章為主。十一月先核範圍和資料，一月底交完整初稿，再留二月到三月修訂和準備口試。這是建議時程，後面的文獻與方法附錄可以依老師提問再開。

引用：研究與成稿建議時程，規劃日2026/10/30；目標2027年3月完稿

## 第25頁 151個誤判點已全部拆分

這一百五十一點是既有模型網格裡選出的誤判點。保留初次品質的隨機件數後，這些點都不再被判成達到八成。它們不是工廠樣本。

引用：本研究結果：[S3] mean_error_151/results.json、crosscheck.json（151個既有點）

## 第26頁 附錄A：主要符號與假設

這頁是符號備查。現在只比不修和修滿，是因為假設下多修的期望邊際為正。資料若不支持這個條件，就不能說現在這個解法涵蓋所有返修量。

引用：充分條件：[S1] 命題稽核§1　　條件改變的部分返修反例：[S6] 第77輪

## 第27頁 附錄B：文獻怎麼用進模型

這幾篇有實際影響模型設定。共享產能、可修方向和品質波動都有文獻依據；本案再把自己的資訊順序和限制寫清楚，用標準機率工具計算。

引用：[R2] 作者稿p.3–8　[R4] PDF p.5–10　[R5] HTML §6.1/6.3/7.2　[R6] 作者稿p.6–8

完整書目見第31、32、33頁。

## 第28頁 附錄C：已有前例與待核對的差異

升級和共同服務都有前例，所以我會把重點放在這個限定問題怎麼定義、怎麼算、哪些情況可行。三篇最接近的全文還沒補齊，現在先保留差異定位。

引用：共同服務：[R1、R3、R8]　升級與共享線：[R2、R7]　直接全文待補：[R9–R11]

完整書目見第31、32、34、35、36頁。

## 第29頁 附錄D：計算如何核對

我用了小批全算、另一種機率加總，以及先固定規則再抽樣這幾種檢查。它們幫我找程式和公式的錯誤；真正能不能用在現場，還要確認資料和製程假設。

引用：本研究核對：[S5] 第58/69/72/80輪與151點crosscheck　　標準界來源：[R12]

完整書目見第36頁。

## 第30頁 附錄E：參數來源與待補資料

原案例有機台和品質資料，但新增重工的成功率、可修比例和成本，仍是我們的假設。接下來要請老師決定採現場批次資料，還是把研究明確定位成合成案例。

引用：原案例：[R1] §5　　可修特性前例：[R6]　　本案假設與條件：[S1]

完整書目見第31、33頁。

## 第31頁 參考文獻①：原始問題與升級前例

這頁是完整書目與閱讀版本，報告時可以先跳過，老師需要來源再回來看。

引用：文獻編號與各頁一致，DOI／預印本連結可點擊開啟

完整書目見第31頁。

## 第32頁 參考文獻②：共同服務與共享產能

這頁是完整書目與閱讀版本，報告時可以先跳過，老師需要來源再回來看。

引用：文獻編號與各頁一致，DOI／預印本連結可點擊開啟

完整書目見第32頁。

## 第33頁 參考文獻③：品質法則與可修方向

這頁是完整書目與閱讀版本，報告時可以先跳過，老師需要來源再回來看。

引用：文獻編號與各頁一致，DOI／預印本連結可點擊開啟

完整書目見第33頁。

## 第34頁 參考文獻④：整合機制與替代服務

這頁是完整書目與閱讀版本，報告時可以先跳過，老師需要來源再回來看。

引用：文獻編號與各頁一致，DOI／預印本連結可點擊開啟

完整書目見第34頁。

## 第35頁 參考文獻⑤：待補全文的直接對照

這兩篇直接對照還需要全文，現在只根據已見摘要列出待核問題。

引用：文獻編號與各頁一致，DOI／預印本連結可點擊開啟

完整書目見第35頁。

## 第36頁 參考文獻⑥：待補對照與標準工具

這頁是完整書目與閱讀版本，報告時可以先跳過，老師需要來源再回來看。

引用：文獻編號與各頁一致，DOI／預印本連結可點擊開啟

完整書目見第36頁。

## 第37頁 本研究結果、程式與教學資料索引

文獻用R編號，我們自己的模型和結果用S編號，教學例用E編號。這樣老師看到一個數字，就能知道它是論文前例、我們算的結果，還是用來解釋的例子。

引用：R＝外部文獻　S＝本研究模型／結果　E＝教學示意；完整路徑見備註

# 完整參考文獻與閱讀深度

## [R1] Chen & Lin (2026)

Chen, H.-Y., & Lin, Y.-K. (2026). Assessing system reliability in multi-grade production under different demand fulfilment policies via a multistate flow network. Journal of the Operational Research Society. Advance online publication.

[DOI／版本連結](https://doi.org/10.1080/01605682.2026.2708981)

閱讀狀態：原始案例全文已取得，已核對政策、工序與未來工作。

定位：§3.3：PDF p.7；§5.1與表2–3：PDF p.11起；§7：PDF p.16–17。PDF含封面，與正文頁碼差一頁。

## [R2] Chen et al. (2018)

Chen, X., Kouvelis, P., & Biazaran, M. (2018). Value of operational flexibility in co-production systems with yield and demand uncertainty. International Journal of Production Research, 56(1–2), 491–507.

[DOI／版本連結](https://doi.org/10.1080/00207543.2017.1402138)， [作者稿](https://facultystaff.richmond.edu/~bchen/Research/OperFlexibility2018.pdf)

閱讀狀態：已取得18頁作者稿，實讀部分章節，未與期刊版逐頁對照。

定位：18頁作者稿PDF p.1,3–8,11–14；p.5式(2)、p.13均值上界、一般化式(8)。期刊頁碼不能套到作者稿。

## [R3] Jiang et al. (2017)

Jiang, Y., Xu, J., Shen, S., & Shi, C. (2017). Production planning problems with joint service-level guarantee: a computational study. International Journal of Production Research, 55(1), 38–58.

[DOI／版本連結](https://doi.org/10.1080/00207543.2016.1193245)

閱讀狀態：已取得22頁期刊PDF含封面，實讀部分章節。

定位：PDF p.2–7,10–12，即期刊正文p.38–43,46–48；PDF p.5式(3)。

## [R4] Kohlmann & Sahling (2024)

Kohlmann, P., & Sahling, F. (2024). A flexible planning approach for integrated lot sizing and rework planning with random proportion of defective products. International Journal of Production Research, 62(19), 6961–6978.

[DOI／版本連結](https://doi.org/10.1080/00207543.2024.2314717)

閱讀狀態：已取得期刊PDF，實讀模型與數值部分。

定位：PDF p.5–10,12,16；共享正常／重工產能與分開啟動；式(13)已渲染核對。服務定義是加權期望欠交。

## [R5] Berling & Sonntag (2022)

Berling, P., & Sonntag, D. R. (2022). Inventory control in production–inventory systems with random yield and rework: The unit-tracking approach. Production and Operations Management, 31(6), 2628–2645.

[DOI／版本連結](https://doi.org/10.1111/poms.13706)

閱讀狀態：已讀出版社HTML相關章節，沒有本地PDF。

定位：出版社HTML §6.1、§6.3與§7.2。逐件／批次良率及非完美重工；§7.2未區分合格品質等級。

## [R6] Dodd et al. (2015)

Dodd, C., Scanlan, J., Marsh, R., & Wiseall, S. (2015). Improving profitability of optimal mean setting with multiple feature means for dual quality characteristics. The International Journal of Advanced Manufacturing Technology, 81, 1767–1780.

[DOI／版本連結](https://doi.org/10.1007/s00170-015-7254-4)， [作者稿](https://eprints.soton.ac.uk/375226/1/MultipleOptimalMeans_Manuscript.pdf)

閱讀狀態：在線讀作者14頁稿的相關部分，本地PDF下載曾403。

定位：Southampton作者稿PDF p.1–2,6–8。失敗特性、加工方向及多特性製程設定；本案可修比例公式由本案另行推導。

## [R7] Boutarfa et al. (2024)

Boutarfa, Y., Senoussi, A., Brahimi, N., & Aouam, T. (2024). Integration and substitution in hybrid manufacturing and refurbishing systems. International Journal of Production Economics, 274, 109308.

[DOI／版本連結](https://doi.org/10.1016/j.ijpe.2024.109308)

閱讀狀態：已取得23頁開放期刊PDF，實讀相關部分。

定位：PDF p.1,5,7–10；式(50)共享產線已渲染核對。已讀多等級模型為確定性，隨機擴充採單等級。

## [R8] Sereshti et al. (2022, v1)

Sereshti, N., Bodur, M., & Luedtke, J. R. (2022). Stochastic dynamic lot-sizing with supplier-driven substitution and service level constraints. arXiv:2301.00258v1. Preprint dated 31 December 2022.

[DOI／版本連結](https://arxiv.org/abs/2301.00258v1)

閱讀狀態：實讀2022預印本v1 p.1–33，未逐頁核對2026期刊版。

定位：2022-12-31預印本v1 PDF p.1–33，p.25表6另作視覺核對。2026期刊版DOI 10.1016/j.ejor.2026.01.007僅核書目，不作本簡報的模型閱讀版本。

## [R9] Tsai et al. (2024)

Tsai, S.-C., Yeh, Y., Wang, H., & Chou, T.-C. (2024). Efficient optimization in stochastic production planning problems with product substitution. Computers & Operations Research, 164, 106544.

[DOI／版本連結](https://doi.org/10.1016/j.cor.2024.106544)

閱讀狀態：僅摘要、導言與可見片段，全文尚未取得。

定位：出版社摘要／導言／可見section片段，PDF曾403。服務事件、安全量與品質後返修需補全文核對。

## [R10] Hsu & Bassok (1999)

Hsu, A., & Bassok, Y. (1999). Random yield and random demand in a production system with downward substitution. Operations Research, 47(2), 277–290.

[DOI／版本連結](https://doi.org/10.1287/opre.47.2.277)

閱讀狀態：僅出版社摘要，全文尚未取得。

定位：出版社摘要與書目。PDF回傳Cookie HTML，不能以此判定全文沒有共同服務或選別返修。

## [R11] Bitran & Leong (1992)

Bitran, G. R., & Leong, T.-Y. (1992). Deterministic approximations to co-production problems with service constraints and random yields. Management Science, 38(5), 724–742.

[DOI／版本連結](https://doi.org/10.1287/mnsc.38.5.724)

閱讀狀態：僅出版社摘要，全文尚未取得。

定位：出版社摘要與書目。PDF曾403／Cookie頁。無法判定其近似是否含安全量，不能視為本案C比較器。

## [R12] Hoeffding (1963)

Hoeffding, W. (1963). Probability inequalities for sums of bounded random variables. Journal of the American Statistical Association, 58(301), 13–30.

[DOI／版本連結](https://doi.org/10.1080/01621459.1963.10500830)

閱讀狀態：標準工具來源，已核摘要與書目，未取得原文PDF。

定位：本案加權Bernoulli界及聯集界的自含推導見命題條件與證明稽核§8。只用作標準工具歸屬，未聲稱讀完原文證明。

# 本研究來源索引

## [S1] 模型、推導與求解

- [research/2026-10-28/教授討論用問題定義.md](C:/Users/uuuwk/karissa/OPT1/OPT1/research/2026-10-28/教授討論用問題定義.md)
- [research/2026-10-28/命題條件與證明稽核.md](C:/Users/uuuwk/karissa/OPT1/OPT1/research/2026-10-28/命題條件與證明稽核.md)
- [backbone/stochastic_setup_frontier.py](C:/Users/uuuwk/karissa/OPT1/OPT1/backbone/stochastic_setup_frontier.py)
- [原始匿名稿](C:/Users/uuuwk/karissa/OPT1/OPT1/JORS_manuscript_anonymous_R5.docx)
- [另附重工案例](C:/Users/uuuwk/karissa/OPT1/OPT1/重工case.docx)

## [S2] 公平經濟比較

- [research/2026-10-28/service_rounds/round73.json](C:/Users/uuuwk/karissa/OPT1/OPT1/research/2026-10-28/service_rounds/round73.json)
- [backbone/round73_fair_economic_baselines.py](C:/Users/uuuwk/karissa/OPT1/OPT1/backbone/round73_fair_economic_baselines.py)

## [S3] 平均比較器與151點拆分

- [research/2026-10-28/service_rounds/round79.json](C:/Users/uuuwk/karissa/OPT1/OPT1/research/2026-10-28/service_rounds/round79.json)
- [research/2026-10-28/平均近似口徑勘誤.md](C:/Users/uuuwk/karissa/OPT1/OPT1/research/2026-10-28/平均近似口徑勘誤.md)
- [research/2026-10-30/mean_error_151/results.json](C:/Users/uuuwk/karissa/OPT1/OPT1/research/2026-10-30/mean_error_151/results.json)
- [research/2026-10-30/mean_error_151/crosscheck.json](C:/Users/uuuwk/karissa/OPT1/OPT1/research/2026-10-30/mean_error_151/crosscheck.json)

## [S4] 最大合法回流的最少投入

- [research/2026-10-28/service_rounds/round83.json](C:/Users/uuuwk/karissa/OPT1/OPT1/research/2026-10-28/service_rounds/round83.json)

## [S5] 枚舉、替代積分及抽樣核對

- [research/2026-10-28/service_rounds/round58.json](C:/Users/uuuwk/karissa/OPT1/OPT1/research/2026-10-28/service_rounds/round58.json)
- [research/2026-10-28/service_rounds/round69.json](C:/Users/uuuwk/karissa/OPT1/OPT1/research/2026-10-28/service_rounds/round69.json)
- [research/2026-10-28/service_rounds/round72.json](C:/Users/uuuwk/karissa/OPT1/OPT1/research/2026-10-28/service_rounds/round72.json)
- [research/2026-10-28/service_rounds/round80.json](C:/Users/uuuwk/karissa/OPT1/OPT1/research/2026-10-28/service_rounds/round80.json)
- [research/2026-10-30/mean_error_151/crosscheck.json](C:/Users/uuuwk/karissa/OPT1/OPT1/research/2026-10-30/mean_error_151/crosscheck.json)

## [S6] 0/R條件失效的部分返修反例

- [research/2026-10-28/service_rounds/round77.json](C:/Users/uuuwk/karissa/OPT1/OPT1/research/2026-10-28/service_rounds/round77.json)

## [E1] 簡報教學算例

- [.build/opt1_presentation_v2/teaching_arithmetic.json](C:/Users/uuuwk/karissa/OPT1/OPT1/.build/opt1_presentation_v2/teaching_arithmetic.json)

三類權重及200/210/220投入表為教學示意；非工廠觀測或新增研究結果。
