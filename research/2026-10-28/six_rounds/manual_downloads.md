# 建議手動補下載的全文

日期：2026-10-28。前兩篇與第四篇的出版社摘要已核對，但 PDF 下載回傳 Cookie 提示頁；第三篇的出版社 PDF 為 403，本機瀏覽器也停在人機驗證。均未標記為取得全文。現有實驗沒有冒用其完整定理或證明。

1. **Gerchak, Y., Tripathy, A., & Wang, K. (1996). Co-production models with random functionality yields. IIE Transactions, 28(5), 391–403.**
   - [DOI／出版社](https://doi.org/10.1080/07408179608966286)
   - 需要補讀：隨機總產出與等級比例的模型假設、向下替代與殘值計價、期望利潤及最適條件的證明。
   - 建議檔名：`Gerchak_Tripathy_Wang_1996_random_functionality_yields.pdf`。
2. **So, K. C., & Tang, C. S. (1995). Optimal Operating Policy for a Bottleneck with Random Rework. Management Science, 41(4), 620–636.**
   - [DOI／出版社](https://doi.org/10.1287/mnsc.41.4.620)
   - 需要補讀：正常加工與重工切換的資訊時點、切換時間與成本、門檻政策的最適性條件及證明。
   - 建議檔名：`So_Tang_1995_bottleneck_random_rework.pdf`。
3. **Tsai, S. C., Yeh, Y., Wang, H., & Chou, T. C. (2024). Efficient optimization in stochastic production planning problems with product substitution. Computers & Operations Research, 164, 106544.**
   - [DOI／出版社](https://doi.org/10.1016/j.cor.2024.106544)
   - 需要補讀：隨機產出與等級之間的機率模型、服務限制的精確定義、投入量／替代決策時點、PGF 與 SPLINE 方法及對照條件。這是檢查本案新穎性的直接近期對照。
   - 出版社全文連結已實際嘗試，HTTP 403。成大有同題碩論紀錄，但顯示 2027-07-07 才公開，不以未公開論文冒充可取得全文。
   - 建議檔名：`Tsai_Yeh_Wang_Chou_2024_product_substitution.pdf`。
4. **Hsu, A., & Bassok, Y. (1999). Random Yield and Random Demand in a Production System with Downward Substitution. Operations Research,47(2),277–290.**
   - [DOI／出版社](https://doi.org/10.1287/opre.47.2.277)
   - 需要補讀：一種原料產生多種隨機等級的模型、投入與品質揭露後配置的兩階段結構、network-flow分解與貪婪最適條件。是本案精確基準與貢獻邊界的重要經典。
   - 建議檔名：`Hsu_Bassok_1999_random_yield_downward_substitution.pdf`。

可以放入本專案 `OPT1/paper/`，並告知檔名；建議先補Tsai2024與Hsu1999，再補另兩篇。這四篇對政策結構與新穎性判斷的重要性高於繼續增加泛用演化演算法文獻。

Sereshti, Bodur & Luedtke (2026), EJOR，DOI [10.1016/j.ejor.2026.01.007](https://doi.org/10.1016/j.ejor.2026.01.007)，期刊 PDF 也回傳 403，但已取得並閱讀 2022 作者預印本 `research/2026-10-28/sereshti_bodur_luedtke_2022_preprint.pdf`。期刊版可補做版本核對，優先性低於上述完全缺全文的三篇。

另有 Carabelli et al. (2026), *An approximate analytical method for the performance evaluation of semiconductor front-end fabrication with model-based inspection and rework policies in process control*, DOI [10.1016/j.jmsy.2026.03.020](https://doi.org/10.1016/j.jmsy.2026.03.020)，作者典藏 PDF 目前 403。該篇列為檢驗／製程控制方向的次要候選，尚未用作本六輪的核心模型依據。

## 第二批新增：已取得與次要待補

**已取得，不需手動下載：** Boutarfa等2024，*Integration and substitution in hybrid manufacturing and refurbishing systems*，DOI [10.1016/j.ijpe.2024.109308](https://doi.org/10.1016/j.ijpe.2024.109308)。23頁開放正式版已存`research/2026-10-28/boutarfa_et_al_2024.pdf`；讀p1,5,7–10。它已整合升降級、替代、共享線，應列為貢獻邊界對照。

以下兩篇從原案例參考文獻找到，出版社PDF均403，僅讀摘要／可見片段，優先性低於Tsai與Hsu，無須為這兩篇延後主模型核定：

- Freeman, Narayanan & Keskin2021，*Optimal use of downward substitution in a manufacturing operation subject to uncertainty*，Omega103102372，DOI [10.1016/j.omega.2020.102372](https://doi.org/10.1016/j.omega.2020.102372)。待補：兩種替代用途、容量／供給風險、單期最適條件及多期資訊時點。建議檔名`Freeman_Narayanan_Keskin_2021_downward_substitution.pdf`。
- Kolus & Duffuaa2025，*Determining optimal process means in a multi-stage production system with inspection errors in 100% inspection*，QTQM22(1)105–130，DOI [10.1080/16843703.2024.2312016](https://doi.org/10.1080/16843703.2024.2312016)。待補：不同工序如何共同影響一個KQC、檢驗錯誤與返修／設定的模型；摘要不能直接證明本案例的連帶影響。建議檔名`Kolus_Duffuaa_2025_process_means_inspection.pdf`。
# 2026-10-28新增優先項目：平均近似的直接前例

在原優先Tsai2024、Hsu/Bassok1999之外，請同批補：

- **Bitran與Leong1992**，Deterministic Approximations to Co-Production Problems with Service Constraints and Random Yields，Management Science38(5)724–742，DOI [10.1287/mnsc.38.5.724](https://doi.org/10.1287/mnsc.38.5.724)。出版社摘要可讀、PDF403；建議存`bitran_leong_1992.pdf`。需要核對共同／個別服務、其確定性近似有無分位數或安全量、隨機類別產出分布、品質後替用及是否含共享返修。不能把本案直接代均值的方法說成這篇的實際方法。
- 次要 **Birge1982**，The Value of the Stochastic Solution in Stochastic Linear Programs with Fixed Recourse，DOI [10.1007/BF01585113](https://doi.org/10.1007/BF01585113)，建議`birge_1982.pdf`。典藏舊網址404；目前僅索引摘要／公式片段。用來釐清VSS評估，非本案直接製程先例。

取得後請放內層OPT1的`research/2026-10-28/`，補讀再更新reading depth；不要把403／Cookie HTML改名PDF。其餘既有清單保留如下。

補充下載路徑：Bitran/Leong的[SMU accepted version記錄](https://ink.library.smu.edu.sg/sis_research/155/)有download，但此環境回212 bytes HTML，已拒存；另有[MIT1989工作論文記錄](https://dspace.mit.edu/entities/publication/2445b1e8-dfc0-4075-afe0-4d98346de26b)，由頁面citation_pdf_url確認[PDF連結](https://dspace.mit.edu/bitstreams/6f069a98-3475-41ce-9bc3-165a4ecaa652/download)，首下載429，未再密集重試。1989是不同版本，若先取得請命名`bitran_leong_1989_working.pdf`，不能當作1992正式版逐頁已核。

