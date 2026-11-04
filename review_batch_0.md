# 人工复核队列

| id | 题型 | 复核原因 | 系统答案 | 证据 |
|---|---|---|---|---|
| s0 | sql | 多表JOIN/CASE：语义风险需人工核；多问句 | 股票代码=600120，涨跌幅=0.0 | SELECT a.股票代码, ROUND((b."收盘价(元)" - b."昨收盘(元)") / b."昨收盘(元)" * 100, 2) AS 涨跌幅 FRO |
| s12 | sql | 多表JOIN/CASE：语义风险需人工核 | 单位净值=1.0421，资产净值=56644199.77 | SELECT * FROM (SELECT f."单位净值", f."资产净值" FROM 基金日行情表 f JOIN 基金基本信息 b ON f.基金代码 = |
| s18 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1.基金代码)=7 | SELECT * FROM (SELECT COUNT(DISTINCT t1.基金代码) FROM 基金份额持有人结构 t1 JOIN 基金基本信息 t2 O |
| s21 | doc | 多问句 | 公司拥有国内专利58 项，其中13 项发明专利，45 项实用新型专利。 | 拥有公司拥有国内专利58 项，其中13 项发明专利，45 项实用新型专利。；公司拥有国内专利58 项，其中13 项发明专利，45 项实用新型专利。；公司拥有国内 |
| s30 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(100.0 * SUM(CASE WHEN "个人投资者持有的基金份额" > "机构投资者持有的基金份额"  | SELECT * FROM (SELECT ROUND(100.0 * SUM(CASE WHEN "个人投资者持有的基金份额" > "机构投资者持有的基金份额 |
| s77 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(AVG(h."成交金额(元)"), 5)=27319513.66667 | SELECT * FROM (SELECT ROUND(AVG(h."成交金额(元)"), 5) FROM "A股票日行情表" h JOIN "A股公司行业划分 |
| s80 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=0 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT "所在证券市场" FROM "基金股票持仓明细" WHERE "基金简称 |
| s83 | sql | 多表JOIN/CASE：语义风险需人工核 | CAST(SUM("成交量(股)") AS INTEGER)=1397850836 | SELECT * FROM (SELECT CAST(SUM("成交量(股)") AS INTEGER) FROM A股票日行情表 WHERE 交易日 = '2 |
| s90 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=2 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT f."基金代码", f."报告期期初基金总份额", f."报告期期末基金 |
| s99 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1.基金代码)=14 | SELECT * FROM (SELECT COUNT(DISTINCT t1.基金代码) FROM 基金份额持有人结构 t1 JOIN 基金基本信息 t2 O |
| s111 | sql | 多表JOIN/CASE：语义风险需人工核 | 债券名称=21宁波银行CD164; 债券名称=20浦发银行CD513; 债券名称=19国开02 | SELECT * FROM (SELECT t1."债券名称" FROM 基金债券持仓明细 t1 JOIN 基金基本信息 t2 ON t1.基金代码 = t2. |
| s129 | doc | 多问句 | 截至2020年12月31日，公司控股股东为五矿股份，五矿股份直接持有公司22.88%股权，并通过长沙矿冶院间接持有公司2 | 公司控股股东为五矿股份，五矿股份直接持有公司22.88%股权，并通过长沙矿冶；院间接持有公司22.88%股权，合计持有公司45.76%股权。；截至2020 年1 |
| s135 | doc | 库内公司但拒答：疑检索未命中或真未披露，须人工对PDF | 招股意向书片段仅说明公司董事共9人（其中3名独立董事），并称董事简历见相关章节，但未列出具体董事姓名，无法据此确定董事是 | 截至本招股意向书签署之日，本公司董事共9 人，其中3 名独立董事。 |
| s141 | sql | 多表JOIN/CASE：语义风险需人工核；多问句 | 股票代码=600010，成交金额(元)=8416441221.0 | SELECT a.股票代码, b."成交金额(元)" FROM "A股公司行业划分表" a JOIN "A股票日行情表" b ON a.股票代码 = b.股票代 |
| s147 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1.基金代码)=4 | SELECT * FROM (SELECT COUNT(DISTINCT t1.基金代码) FROM 基金基本信息 t1 JOIN 基金可转债持仓明细 t2 O |
| s162 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT a.股票代码)=7 | SELECT * FROM (SELECT COUNT(DISTINCT a.股票代码) FROM "A股公司行业划分表" a JOIN "A股票日行情表" b |
| s190 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=10 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT m.股票代码 FROM 基金股票持仓明细 m JOIN 基金基本信息 b |
| s193 | sql | 多表JOIN/CASE：语义风险需人工核 | 股票代码=600643，股票名称=爱建集团，涨跌幅(%)=5.41 | SELECT * FROM (SELECT a."股票代码", a."股票名称", ROUND((b."收盘价(元)" - b."昨收盘(元)") / b."昨 |
| s214 | hybrid | 多表JOIN/CASE：语义风险需人工核 | ROUND(AVG(t2."市值"), 3)=117079147.5｜文档侧：资料片段为海尔施生物医药股份有限公司招股意 | SELECT * FROM (SELECT ROUND(AVG(t2."市值"), 3) FROM 基金股票持仓明细 t2 JOIN A股公司行业划分表 t1  |
| s229 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1."基金代码")=7 | SELECT * FROM (SELECT COUNT(DISTINCT t1."基金代码") FROM "基金可转债持仓明细" t1 WHERE t1."持仓 |
| s232 | sql | 多表JOIN/CASE：语义风险需人工核 | CAST(SUM(h."成交金额(元)") AS INTEGER)=63639494351 | SELECT * FROM (SELECT CAST(SUM(h."成交金额(元)") AS INTEGER) FROM "A股票日行情表" h JOIN "A |
| s235 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=0 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT "所在证券市场" FROM "基金股票持仓明细" WHERE "基金简称 |
| s241 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=0 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT s.股票代码, (MAX(q."收盘价(元)") - MIN(q."收盘 |
| s247 | sql | 多表JOIN/CASE：语义风险需人工核 | CAST(SUM("成交金额(元)") AS INTEGER)=53934559056 | SELECT * FROM (SELECT CAST(SUM("成交金额(元)") AS INTEGER) FROM A股票日行情表 WHERE 交易日 = ' |
| s250 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=10 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT s.股票代码, (MAX(q."收盘价(元)") - MIN(q."收盘 |
| s259 | doc | 答案值未出现在已验证quote中 | 报告期内，人工成本占主营业务成本的比例分别为：2016年度19.49%、2015年度19.01%、2014年度16.74 | 人工成本、8,621.96、、、19.49、、、8,240.25、、、19.01；合 计、、25,480.72、8,621.96、10,137.96、44,24 |
| s265 | doc | 多问句 | 公司控股子公司为西安启源软件技术有限责任公司，公司持有其75.42%的股份。 | 公司控股子公司为西安启源软件技术有限责任公司，公司持有其75.42%的股份。 |
| s271 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=153 | SELECT * FROM (SELECT COUNT(*) FROM "A股票日行情表" WHERE "股票代码" = '002641' AND "交易日"  |
| s274 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(AVG(f."市值"), 3)=77907468.5 | SELECT * FROM (SELECT ROUND(AVG(f."市值"), 3) FROM 基金股票持仓明细 f JOIN A股公司行业划分表 a ON  |
| s280 | none | 无路由命中：需人工确认是否DB题措辞遗漏 | 知识库外且无DB关键词 |  |
| s289 | sql | 多问句 | 股票代码=300338，涨跌幅=8.73 | SELECT t1.股票代码, ROUND((t2."收盘价(元)" - t2."昨收盘(元)") / t2."昨收盘(元)" * 100, 2) AS 涨跌幅 |
| s292 | doc | 答案值未出现在已验证quote中 | 报告期内，IPTV 业务是公司主营业务收入的主要来源，公司主营业务收入构成包括IPTV业务和移动媒体平台服务业务；其他业 | 报告期内，IPTV 业务占公司主营业务收入的比例分别为98.60%、99.35%；IPTV 98.60% 业务 移动媒体平台服务 1.40% 业务 100.00 |
| s298 | sql | 多表JOIN/CASE：语义风险需人工核；多问句 | 净申购基金家数=250，净申购份额合计=40784212401.97 | SELECT * FROM (SELECT COUNT(*) AS 净申购基金家数, ROUND(SUM(净申购份额), 2) AS 净申购份额合计 FROM  |
| s301 | sql | 多问句 | 基金家数=2354，净赎回份额合计=361411252772.73 | SELECT * FROM (SELECT COUNT(*) AS 基金家数, ROUND(SUM(报告期基金总赎回份额 - 报告期基金总申购份额), 2) A |
| s304 | doc | 多问句 | 本次发行前总股本为878,981.90万股，按照本次发行上限180,000.00万股计算，本次发行后本公司总股本为1,0 | 本公司本次发行前总股本为878,981.90 万股，按照本次发行上限180,00；万股计算，本次发行后本公司总股本为1,058,981.90 万股 |
| s307 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=0 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT "股票代码" FROM "基金股票持仓明细" WHERE "基金简称"  |
| s319 | sql | 多表JOIN/CASE：语义风险需人工核 | 单位净值=0.9794，资产净值=3356847033.12 | SELECT * FROM (SELECT f."单位净值", f."资产净值" FROM 基金日行情表 f JOIN 基金基本信息 b ON f.基金代码 = |
| s325 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1.基金代码)=0 | SELECT * FROM (SELECT COUNT(DISTINCT t1.基金代码) FROM 基金基本信息 t1 JOIN 基金可转债持仓明细 t2 O |
| s331 | sql | 多表JOIN/CASE：语义风险需人工核 | 管理人=申万菱信基金管理有限公司，累计单位净值=1.0449 | SELECT f."管理人", q."累计单位净值" FROM "基金基本信息" f JOIN "基金日行情表" q ON f."基金代码" = q."基金代码 |
| s334 | doc | 多问句 | 沉淀法二氧化硅广泛应用于橡胶、轮胎、医药、农药、固体消防材料、农业、饲料、涂料、油墨、造纸等行业，其中，对橡胶行业的依赖 | 沉淀法二氧化硅广泛应用于橡胶、轮胎、医药、农药、固体消防材料、农；业、饲料、涂料、油墨、造纸等行业，其中，对橡胶行业的依赖程度较大。 |
| s351 | sql | 多问句 | 基金家数=1437，净赎回总份额=397325433314.6 | SELECT * FROM (SELECT COUNT(*) AS 基金家数, ROUND(SUM(报告期基金总赎回份额 - 报告期基金总申购份额), 2) A |
| s361 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(AVG(h."成交金额(元)"), 5)=57267641.71429 | SELECT * FROM (SELECT ROUND(AVG(h."成交金额(元)"), 5) FROM "A股票日行情表" h JOIN "A股公司行业划分 |
| s377 | sql | 多表JOIN/CASE：语义风险需人工核 | 涨跌幅百分比=13.83 | SELECT * FROM (SELECT ROUND((MAX(q."收盘价(元)") - MIN(q."收盘价(元)")) / MIN(q."收盘价(元)" |
| s392 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND((MAX(q."收盘价(元)") - MIN(q."收盘价(元)")) / MIN(q."收盘价(元)")  | SELECT * FROM (SELECT ROUND((MAX(q."收盘价(元)") - MIN(q."收盘价(元)")) / MIN(q."收盘价(元)" |
| s395 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=7 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT f."基金代码" FROM "基金基本信息" f JOIN "基金规模变 |
| s398 | doc | 多问句 | 在采购端，发行人下属朵越实业与中国科学院控股有限公司下属成都中科唯实仪器有限责任公司设立中科智成；朵越实业持有中科智成2 | 在采购端，发行人下属朵越实业与中国科学院控股有限公司下属成都中科唯实仪器有限责任；截至本招股意向书签署之日朵越实业、成都中科唯实仪器有限责任公司分别持有中科智成 |
| s426 | sql | 多表JOIN/CASE：语义风险需人工核 | 债券类型=金融债券 | SELECT b."债券类型" FROM 基金债券持仓明细 b JOIN 基金基本信息 f ON b."基金代码" = f."基金代码" WHERE f."基金 |
| s435 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(SUM("成交金额(元)"))=None | SELECT * FROM (SELECT ROUND(SUM("成交金额(元)")) FROM A股票日行情表 WHERE 交易日 = '20201116'  |
| s441 | none | 无路由命中：需人工确认是否DB题措辞遗漏 | 知识库外且无DB关键词 |  |
| s444 | sql | 多表JOIN/CASE：语义风险需人工核；多问句 | 股票代码=600282，成交金额(元)=1766049991.0 | SELECT a.股票代码, b."成交金额(元)" FROM "A股公司行业划分表" a JOIN "A股票日行情表" b ON a.股票代码 = b.股票代 |
| s447 | doc | 库内公司但拒答：疑检索未命中或真未披露，须人工对PDF | 招股意向书片段未披露现有核心技术人员的具体人数及姓名，仅提及公司拥有80余人的研发设计团队、4位国家一级工业设计师，并另 | 公司建立了一支80 余人的研发设计团队，专业涵盖工程、材料、传热、设；公司目前拥有4 位国家一级工业设计师，并聘请了“中国工业设；本公司另有李娟、王伟两名其他核 |
| s451 | none | 无路由命中：需人工确认是否DB题措辞遗漏 | 知识库外且无DB关键词 |  |
| s454 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT a.股票代码)=6 | SELECT * FROM (SELECT COUNT(DISTINCT a.股票代码) FROM A股公司行业划分表 a JOIN A股票日行情表 b ON  |
| s457 | sql | 多表JOIN/CASE：语义风险需人工核 | 管理人=西部利得基金管理有限公司，ROUND(q.单位净值, 2)=1.0 | SELECT * FROM (SELECT f.管理人, ROUND(q.单位净值, 2) FROM 基金基本信息 f JOIN 基金日行情表 q ON f.基 |
| s460 | doc | 答案值未出现在已验证quote中 | 公司主要无形资产包括商标、软件著作权、专利和软件。 | 序号、专利名称、专利号、专利类型、权利期限、专利来源 |
| s470 | sql | 多表JOIN/CASE：语义风险需人工核 | 一级行业名称=电子; 一级行业名称=电气设备; 一级行业名称=国防军工; 一级行业名称=银行; 一级行业名称=建筑材料; | SELECT * FROM (SELECT DISTINCT a."一级行业名称" FROM 基金股票持仓明细 f JOIN A股公司行业划分表 a ON f. |
| s473 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(AVG(h."成交金额(元)"), 5)=132516957.35294 | SELECT * FROM (SELECT ROUND(AVG(h."成交金额(元)"), 5) FROM "A股公司行业划分表" i JOIN "A股票日行情 |
| s477 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1.基金代码)=0 | SELECT * FROM (SELECT COUNT(DISTINCT t1.基金代码) FROM 基金份额持有人结构 t1 JOIN 基金基本信息 t2 O |
| s480 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(AVG(h."成交金额(元)"), 5)=31234914.8 | SELECT * FROM (SELECT ROUND(AVG(h."成交金额(元)"), 5) FROM "A股票日行情表" h JOIN "A股公司行业划分 |
| s484 | doc | 库内公司但拒答：疑检索未命中或真未披露，须人工对PDF | 资料片段中未提及珠海健帆生物科技股份有限公司的首席科学家信息。 |  |
| s487 | none | 无路由命中：需人工确认是否DB题措辞遗漏 | 知识库外且无DB关键词 |  |
| s490 | sql | 多表JOIN/CASE：语义风险需人工核 | 管理人=易方达基金管理有限公司，累计单位净值=1.0721 | SELECT * FROM (SELECT f."管理人", d."累计单位净值" FROM 基金基本信息 f JOIN 基金日行情表 d ON f."基金代码 |
| s493 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT a.股票代码)=21 | SELECT * FROM (SELECT COUNT(DISTINCT a.股票代码) FROM "A股公司行业划分表" a JOIN "A股票日行情表" b |
| s499 | sql | 多表JOIN/CASE：语义风险需人工核 | 债券名称=21农发清发02; 债券名称=21国开07; 债券名称=20国开02 | SELECT * FROM (SELECT t1."债券名称" FROM 基金债券持仓明细 t1 JOIN 基金基本信息 t2 ON t1.基金代码 = t2. |
| s503 | sql | 多表JOIN/CASE：语义风险需人工核 | 单位净值=1.1646，资产净值=1076709134.79 | SELECT * FROM (SELECT f."单位净值", f."资产净值" FROM "基金日行情表" f JOIN "基金基本信息" b ON f."基 |
| s513 | doc | 库内公司但拒答：疑检索未命中或真未披露，须人工对PDF | 处理失败：1 validation error for Value
unit
  Input should be '元' |  |
| s522 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(100.0 * SUM(CASE WHEN "个人投资者持有的基金份额" > "机构投资者持有的基金份额"  | SELECT * FROM (SELECT ROUND(100.0 * SUM(CASE WHEN "个人投资者持有的基金份额" > "机构投资者持有的基金份额 |
| s526 | doc | 库内公司但拒答：疑检索未命中或真未披露，须人工对PDF | 资料片段中未包含实际控制人直系亲属控股企业的具体名单，仅涉及控股股东、实际控制人周举东直接或间接控制的其他企业。 | 发行人控股股东、实际控制人周举东直接或间接控制的其他企业情况如下表所示 |
| s535 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=10 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT f."基金代码" FROM "基金基本信息" f JOIN "基金规模变 |
| s538 | sql | 多表JOIN/CASE：语义风险需人工核 | 一级行业名称=汽车; 一级行业名称=化工; 一级行业名称=家用电器; 一级行业名称=交通运输 | SELECT * FROM (SELECT DISTINCT a."一级行业名称" FROM 基金股票持仓明细 f JOIN A股公司行业划分表 a ON f. |
| s541 | doc | 库内公司但拒答：疑检索未命中或真未披露，须人工对PDF | 未能在知识库中定位相关章节内容 |  |
| s544 | doc | 多问句 | 存在。发行人成立以来的重大资产重组为对同一控制下关联企业——宁波胜克的换向器业务和资产进行整合。 | 发行人成立以来的重大资产重组为对同一控制下关联企业——宁波胜克的换向器业务和资产 |
| s547 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1.基金代码)=0 | SELECT * FROM (SELECT COUNT(DISTINCT t1.基金代码) FROM 基金份额持有人结构 t1 JOIN 基金基本信息 t2 O |
| s553 | doc | 多问句 | 本次发行初始战略配售发行数量为5.4 亿股，占发行数量的30.00%。 | 本次发行初始战略配售发行数量为5.4 亿股，占发行数量的30.00%。 |
| s557 | sql | 多表JOIN/CASE：语义风险需人工核 | 单位净值=1.0736，资产净值=104342645.46 | SELECT * FROM (SELECT f."单位净值", f."资产净值" FROM 基金日行情表 f JOIN 基金基本信息 b ON f.基金代码 = |
| s572 | sql | 多问句 | 基金家数=482，净赎回份额=121459985678.29 | SELECT * FROM (SELECT COUNT(*) AS 基金家数, ROUND(SUM(报告期基金总赎回份额 - 报告期基金总申购份额), 2) A |
| s575 | sql | 多表JOIN/CASE：语义风险需人工核 | CAST(SUM("成交金额(元)") AS INTEGER)=23806622438 | SELECT * FROM (SELECT CAST(SUM("成交金额(元)") AS INTEGER) FROM A股票日行情表 WHERE 交易日 = ' |
| s590 | sql | 多表JOIN/CASE：语义风险需人工核 | 年化收益率=15.63 | SELECT * FROM (SELECT ROUND(((MAX(CASE WHEN 交易日 = (SELECT MAX(交易日) FROM A股票日行情表  |
| s599 | sql | 多表JOIN/CASE：语义风险需人工核 | CAST(SUM(b."成交金额(元)") AS INTEGER)=None | SELECT * FROM (SELECT CAST(SUM(b."成交金额(元)") AS INTEGER) FROM A股公司行业划分表 a JOIN A股 |
| s605 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=149 | SELECT * FROM (SELECT COUNT(*) FROM "A股票日行情表" WHERE "股票代码" = '603359' AND "交易日"  |
| s608 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=0 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT s.股票代码, (MAX(q."收盘价(元)") - MIN(q."收盘 |
| s626 | none | 无路由命中：需人工确认是否DB题措辞遗漏 | 知识库外且无DB关键词 |  |
| s638 | sql | 多表JOIN/CASE：语义风险需人工核；多问句 | 基金家数=1352，净申购份额合计=332305208096.65 | SELECT * FROM (SELECT COUNT(*) AS 基金家数, ROUND(SUM(净申购份额), 2) AS 净申购份额合计 FROM (SE |
| s641 | doc | 多问句 | 在销售端，发行人与中国燃气下属中燃燃气实业（深圳）有限公司合资成立河北华通。河北华通主要客户为中国燃气。 | 在销售端，发行人与中国燃气下属中燃燃气实业（深圳）有限公司合资成立河北华通。；在销售端，公司与中国燃气合作设立河北华通；河北华通主要客户为中国燃气。 |
| s650 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=10 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT m."股票代码", m."持仓日期", m."第N大重仓股", (SEL |
| s656 | hybrid | SQL空结果（疑日期格式/条件过严）；多问句 | 查询无结果｜文档侧：根据《国民经济行业分类》（GB/T4754-2002），公司主营业务所属行业为工程勘察设计行业，分类 | SELECT "一级行业名称", "二级行业名称" FROM "A股公司行业划分表" WHERE "股票代码" = '300746' AND "行业划分标准"  |
| s659 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1.基金代码)=1 | SELECT * FROM (SELECT COUNT(DISTINCT t1.基金代码) FROM 基金份额持有人结构 t1 JOIN 基金基本信息 t2 O |
| s665 | sql | 多表JOIN/CASE：语义风险需人工核；多问句 | 净申购基金家数=1259，净申购份额合计=246417046941.57 | SELECT * FROM (SELECT COUNT(*) AS 净申购基金家数, ROUND(SUM(净申购份额), 2) AS 净申购份额合计
FROM  |
| s668 | hybrid | SQL生成/校验失败 | 生成的 SQL 未通过安全校验，拒答｜文档侧：2009年我国光伏新增装机容量为160MW，占全球市场需求份额为2.22% |  |
| s671 | sql | 多问句 | 基金简称=建信现金增利货币B，差额=21507087348.72 | SELECT 基金简称, ROUND(ABS(报告期基金总申购份额 - 报告期基金总赎回份额), 2) AS 差额 FROM 基金规模变动表 WHERE 截止日 |
| s674 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1.基金代码)=0 | SELECT * FROM (SELECT COUNT(DISTINCT t1.基金代码) FROM 基金份额持有人结构 t1 JOIN 基金基本信息 t2 O |
| s680 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1.基金代码)=7 | SELECT * FROM (SELECT COUNT(DISTINCT t1.基金代码) FROM 基金基本信息 t1 JOIN 基金债券持仓明细 t2 ON |
| s684 | doc | 多问句 | 出版业的波动性特征主要表现在教材教辅销售市场上。教材教辅的销售高峰主要出现在每年春、秋两季开学时，形成图书市场销售季节性 | 出版业的波动性特征主要表现在教材教辅销售市场上。教材教辅的销售高峰主要出现在每年 |
| s687 | doc | 答案值未出现在已验证quote中 | 招股意向书仅列示“四、行业特点”“（一）经营特点”等标题，未在给定片段中展开具体经营特点内容；片段中仅提及“发行人所处天 | 四、行业特点；（一）经营特点；鉴于发行人所处天然气行业普遍带有固定资产规模庞大、前期运营投入较高 |
| s708 | sql | 多表JOIN/CASE：语义风险需人工核 | 债券名称=20国开03; 债券名称=20国开02; 债券名称=20国开05 | SELECT * FROM (SELECT t1."债券名称" FROM 基金债券持仓明细 t1 JOIN 基金基本信息 t2 ON t1.基金代码 = t2. |
| s711 | doc | 多问句 | 截至2011年6月30日，公司拥有专利166项，其中发明专利24项。 | 截至2011 年6 月30 日，公司拥有专利166 项，其中发明专利24 项，实；截至2011 年6 月30 日，公司拥有专利166 项，其中发明专利24 项， |
| s720 | doc | 答案值未出现在已验证quote中 | 本公司上游行业属于竞争性行业，生产用钢材、铝材等基础性原材料、零部件及元器件等可以通过外购及外协加工从国内得到充足供应， | 本公司上游行业属于竞争性行业。本公司生产用钢材、铝材等基础性原材料、零部件及元器；本行业受上游的制约较小。 |
| s733 | doc | 答案值未出现在已验证quote中 | 报告期内，IPTV 业务是公司主营业务收入的主要来源 | 报告期内，IPTV 业务占公司主营业务收入的比例分别为98.60%、99.35%；报告期内，公司IPTV 业务收入分别为89,931.53 万元、94,559. |
| s748 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=0 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT s.股票代码, (MAX(q."收盘价(元)") - MIN(q."收盘 |
| s762 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=406 | SELECT * FROM (SELECT COUNT(*) FROM "A股票日行情表" AS t1 JOIN "A股票日行情表" AS t2 ON t1.股 |
| s765 | doc | 多问句 | 报告期内，发行人保护氨基酸的采购量逐年下降，其主要原因是公司主导产品“胸腺法新”的生产工艺不断优化使单位产品原材料耗用降 | 报告期内，发行人保护氨基酸的采购量逐年下降，其主要原因是公司主导产品“胸腺法新”；采购量(Kg)、539.60、714.35、1,094.75；使每生产100g |
| s785 | sql | 多表JOIN/CASE：语义风险需人工核 | CAST(SUM(h."成交量(股)") AS INTEGER)=2342532922 | SELECT * FROM (SELECT CAST(SUM(h."成交量(股)") AS INTEGER) FROM "A股票日行情表" h JOIN "A股 |
| s801 | doc | 多问句 | 2007年4月，本公司收购博信发展持有的银禧工塑75%的股权；目的为丰富公司产品结构、扩大产能、提高核心竞争能力以及解决 | 为丰富公司产品结构、扩大产能、提高核心竞争能力以及解决潜在的同业竞
争问题，20；本次收购扩大了公司生产及销售规模，调整了公司产品结构，增强了盈利能
力，同时解 |
| s804 | sql | 多表JOIN/CASE：语义风险需人工核；多问句 | 净申购基金家数=798，净申购份额合计=325062572784.25 | SELECT * FROM (SELECT COUNT(*) AS 净申购基金家数, ROUND(SUM(净申购份额), 2) AS 净申购份额合计
FROM  |
| s811 | doc | 多问句 | 截至2017年12月31日，公司无形资产原值为2,812.92万元，账面价值为802.50万元。 | 截至2017 年12 月31 日，公司无形资产原值为2,812.92 万元，累计；2,010.42 万元，账面价值为802.50 万元。；一、无形资产原价、2, |
| s814 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=178 | SELECT * FROM (SELECT COUNT(*) FROM "A股票日行情表" WHERE "股票代码" = '600601' AND "交易日"  |
| s820 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(AVG(h."成交金额(元)"), 5)=41964749.89474 | SELECT * FROM (SELECT ROUND(AVG(h."成交金额(元)"), 5) FROM "A股公司行业划分表" i JOIN "A股票日行情 |
| s823 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(AVG(h."成交金额(元)"), 5)=114525816.7 | SELECT * FROM (SELECT ROUND(AVG(h."成交金额(元)"), 5) FROM "A股票日行情表" h JOIN "A股公司行业划分 |
| s829 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND((((SELECT "收盘价(元)" FROM A股票日行情表 WHERE 股票代码='601117' AN | SELECT * FROM (SELECT ROUND((((SELECT "收盘价(元)" FROM A股票日行情表 WHERE 股票代码='601117'  |
| s838 | sql | 多表JOIN/CASE：语义风险需人工核 | CAST(SUM(b."成交量(股)") AS INTEGER)=896842437 | SELECT * FROM (SELECT CAST(SUM(b."成交量(股)") AS INTEGER) FROM "A股公司行业划分表" a JOIN " |
| s850 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(((MAX(CASE WHEN 交易日 = (SELECT MAX(交易日) FROM A股票日行情表 WH | SELECT * FROM (SELECT ROUND(((MAX(CASE WHEN 交易日 = (SELECT MAX(交易日) FROM A股票日行情表  |
| s856 | doc | 多问句 | 涉及。发行人生产经营中涉及环境污染的环节主要包括机械加工过程中产生的电镀污泥和有机溶剂、电子产品装联和电缆挤塑过程中产生 | 发行人生产经营中涉及环境污染的环节主要包括机械加工过程中产生的电镀污泥和有机溶剂 |
| s874 | sql | 多问句 | 基金简称=华夏中证5G通信主题ETF，差额=23288000000.0 | SELECT 基金简称, ROUND(ABS(报告期基金总申购份额 - 报告期基金总赎回份额), 2) AS 差额 FROM 基金规模变动表 WHERE 截止日 |
| s877 | sql | 多问句 | 净赎回基金数=852，净赎回总份额=119166317697.93 | SELECT * FROM (SELECT COUNT(*) AS 净赎回基金数, ROUND(SUM(报告期基金总赎回份额 - 报告期基金总申购份额), 2) |
| s880 | doc | 多问句 | 下游行业：汽车零部件行业的下游行业为整车制造业，再下游为汽车消费市场；具体到发行人的主要产品车身零部件领域，下游主要以整 | 汽车零部件行业的下游行业为整车制造业，再下游为汽车消费市场。；下游主要以整车制造业为主，极少涉及汽车维修业务。；主要客户为东风本田、一汽-大众、上汽大众、广汽本 |
| s883 | sql | SQL空结果（疑日期格式/条件过严） | 查询无结果 | SELECT b."债券类型" FROM 基金债券持仓明细 b JOIN 基金基本信息 f ON b.基金代码 = f.基金代码 WHERE f.基金简称 =  |
| s886 | doc | 答案值未出现在已验证quote中 | 为防止技术失密，公司采取了较为谨慎的专利申请原则，同时公司与高级管理人员、核心技术人员以及相关研发人员均签订了严格的保密 | 为防止技术失密，公司采取了较为谨慎的专利申请原则，同时公司 |
| s896 | sql | 多问句 | 净赎回基金家数=2143，净赎回总份额=285843272136.08 | SELECT * FROM (SELECT COUNT(*) AS 净赎回基金家数, ROUND(SUM(报告期基金总赎回份额 - 报告期基金总申购份额), 2 |
| s899 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(AVG(h."成交金额(元)"), 5)=352904414.68421 | SELECT * FROM (SELECT ROUND(AVG(h."成交金额(元)"), 5) FROM "A股票日行情表" h JOIN "A股公司行业划分 |
| s905 | sql | 多问句 | 净申购基金家数=870，净申购份额合计=212728204287.07 | SELECT * FROM (SELECT COUNT(*) AS 净申购基金家数, ROUND(SUM(报告期基金总申购份额 - 报告期基金总赎回份额), 2 |
| s908 | sql | 多问句 | 净申购基金家数=1516，净申购份额合计=384235026323.63 | SELECT * FROM (SELECT COUNT(*) AS 净申购基金家数, ROUND(SUM(报告期基金总申购份额 - 报告期基金总赎回份额), 2 |
| s914 | sql | 多表JOIN/CASE：语义风险需人工核 | CAST(SUM("成交量(股)") AS INTEGER)=116221778 | SELECT * FROM (SELECT CAST(SUM("成交量(股)") AS INTEGER) FROM A股票日行情表 WHERE 交易日 = '2 |
| s920 | none | 无路由命中：需人工确认是否DB题措辞遗漏 | 知识库外且无DB关键词 |  |
| s930 | doc | 多问句 | 2018年、2019年及2020年，公司境外销售收入分别为11,751.32万元、9,855.10万元和9,466.41 | 2018 年、2019 年及2020年，公司境外销售收入分别为11,751.32；国外、9,466.41、17.81、9,855.10、19.82、11,751 |
| s936 | sql | 多表JOIN/CASE：语义风险需人工核 | 一级行业名称=食品饮料; 一级行业名称=家用电器; 一级行业名称=农林牧渔; 一级行业名称=休闲服务 | SELECT * FROM (SELECT DISTINCT a."一级行业名称" FROM 基金股票持仓明细 f JOIN A股公司行业划分表 a ON f. |
| s939 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT a."股票代码")=12 | SELECT * FROM (SELECT COUNT(DISTINCT a."股票代码") FROM "A股公司行业划分表" a JOIN "A股票日行情表" |
| s942 | sql | 多表JOIN/CASE：语义风险需人工核 | 债券类型=中期票据 | SELECT b."债券类型" FROM 基金债券持仓明细 b JOIN 基金基本信息 f ON b."基金代码" = f."基金代码" WHERE f."基金 |
| s951 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(AVG("成交金额(元)"), 5)=136224024.91176 | SELECT * FROM (SELECT ROUND(AVG("成交金额(元)"), 5) FROM A股票日行情表 WHERE 交易日 = '2020062 |
| s966 | doc | 库内公司但拒答：疑检索未命中或真未披露，须人工对PDF | 处理失败：1 validation error for Value
unit
  Input should be '元' |  |
| s972 | doc | 多问句 | 公司2007年、2008年、2009年和2010年1-6月综合毛利率分别为15.44%、20.25%、28.46%和27 | 公司2007 年、2008 年、2009 年和2010 年1-6 月综合毛利率分 |
| s975 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(AVG(h."成交金额(元)"), 5)=177206307.31111 | SELECT * FROM (SELECT ROUND(AVG(h."成交金额(元)"), 5) FROM "A股票日行情表" h JOIN "A股公司行业划分 |
| s978 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1.基金代码)=1 | SELECT * FROM (SELECT COUNT(DISTINCT t1.基金代码) FROM 基金份额持有人结构 t1 JOIN 基金基本信息 t2 O |
