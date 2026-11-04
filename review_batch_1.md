# 人工复核队列

| id | 题型 | 复核原因 | 系统答案 | 证据 |
|---|---|---|---|---|
| s4 | sql | 多表JOIN/CASE：语义风险需人工核 | CAST(SUM(b."成交量(股)") AS INTEGER)=2627492624 | SELECT * FROM (SELECT CAST(SUM(b."成交量(股)") AS INTEGER) FROM A股公司行业划分表 a JOIN A股票 |
| s7 | sql | 多问句 | 基金家数=2085，净赎回总份额=317373703552.49 | SELECT * FROM (SELECT COUNT(*) AS 基金家数, ROUND(SUM(报告期基金总赎回份额 - 报告期基金总申购份额), 2) A |
| s10 | doc | 多问句 | 本次发行前，派思投资持有公司的股份数量为5,950万股，占公司总股份的65.89%。 | 本次发行前，派思投资持有公司的股份数量为5,950 万股，占公司总股份的65.8；派思投资、59,500,000、65.89%、59,500,000 |
| s22 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=10 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT s.股票代码, (MAX(h."收盘价(元)") - MIN(h."收盘 |
| s25 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT a.股票代码)=1 | SELECT * FROM (SELECT COUNT(DISTINCT a.股票代码) FROM "A股公司行业划分表" a JOIN "A股票日行情表" b |
| s28 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1.基金代码)=10 | SELECT * FROM (SELECT COUNT(DISTINCT t1.基金代码) FROM 基金份额持有人结构 t1 JOIN 基金基本信息 t2 O |
| s54 | sql | 多表JOIN/CASE：语义风险需人工核 | 单位净值=1.1144，资产净值=668176233.23 | SELECT * FROM (SELECT f."单位净值", f."资产净值" FROM 基金日行情表 f JOIN 基金基本信息 b ON f.基金代码 = |
| s57 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1.基金代码)=0 | SELECT * FROM (SELECT COUNT(DISTINCT t1.基金代码) FROM 基金份额持有人结构 t1 JOIN 基金基本信息 t2 O |
| s75 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(((MAX(CASE WHEN 交易日 = (SELECT MAX(交易日) FROM A股票日行情表 WH | SELECT * FROM (SELECT ROUND(((MAX(CASE WHEN 交易日 = (SELECT MAX(交易日) FROM A股票日行情表  |
| s91 | doc | 多问句 | 中海达测绘全称为“广州市中海达测绘仪器有限公司”；截至该次股权收购前，中海达测绘注册资本为800万元。 | 中海达测绘全称为“广州市中海达测绘仪器有限公司”，公司成立于1999年12月；截至该次股权收购前，中海达测绘注册资本为800万元 |
| s100 | sql | 多表JOIN/CASE：语义风险需人工核 | CAST(SUM(b."成交金额(元)") AS INTEGER)=15621610479 | SELECT * FROM (SELECT CAST(SUM(b."成交金额(元)") AS INTEGER) FROM "A股公司行业划分表" a JOIN  |
| s103 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=7 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT f."基金代码", f."报告期期初基金总份额", f."报告期期末基金 |
| s106 | doc | 答案值未出现在已验证quote中 | 2015年度净利润同比增长4.15%，2016年度净利润同比增长10.83% | 公司净利润分
别同比增长4.15%、10.83%，净利润呈持续增长态势。 |
| s118 | sql | 多表JOIN/CASE：语义风险需人工核 | 股票代码=688169 | SELECT a.股票代码 FROM A股公司行业划分表 a JOIN A股票日行情表 b ON a.股票代码 = b.股票代码 WHERE a.交易日期 =  |
| s127 | sql | 多表JOIN/CASE：语义风险需人工核；多问句 | 股票代码=002946，涨跌幅=10.06 | SELECT a.股票代码, ROUND((b."收盘价(元)" - b."昨收盘(元)") / b."昨收盘(元)" * 100, 2) AS 涨跌幅 FRO |
| s139 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(100.0 * SUM(CASE WHEN "个人投资者持有的基金份额" > "机构投资者持有的基金份额"  | SELECT * FROM (SELECT ROUND(100.0 * SUM(CASE WHEN "个人投资者持有的基金份额" > "机构投资者持有的基金份额 |
| s151 | sql | 多表JOIN/CASE：语义风险需人工核 | 股票代码=601155 | SELECT a.股票代码 FROM A股票日行情表 a JOIN A股公司行业划分表 b ON a.股票代码 = b.股票代码 AND b.交易日期 = '2 |
| s154 | sql | 多表JOIN/CASE：语义风险需人工核 | 单位净值=1.0381，资产净值=505830430.42 | SELECT * FROM (SELECT f."单位净值", f."资产净值" FROM "基金日行情表" f JOIN "基金基本信息" b ON f."基 |
| s157 | doc | 多问句 | 本公司自主研发、拥有自主知识产权的第一个疫苗Hib及第二个疫苗冻干A、C脑膜炎球菌多糖结合疫苗分别已于2007年9月、2 | 本公司自主研发、拥有自主知识产权的第一个疫苗Hib及第二个疫苗冻干A、C脑膜炎球；本公司自主研发、拥有自主知识产权的第一个疫苗Hib及第二个疫苗冻干A、C脑膜炎 |
| s160 | doc | 多问句 | 中心现有研发人员38人，其中具有高级职称人员6人，中级职称18人。 | 中心现有研发人员38 人，其中具有高级职称人员6 人，中级职
称18 人。 |
| s163 | doc | 多问句 | 公司主营业务为输电线路铁塔的研发、设计、生产和销售以及变电构支架和通讯铁塔的生产和销售。此外，公司还研发了复合材料绝缘杆 | 公司主营业务为输电线路铁塔的研发、设计、生产和销售以及变电构支架和通讯铁塔的生产；报告期内，公司的主营业务未发生重大变化。 |
| s178 | hybrid | 多表JOIN/CASE：语义风险需人工核 | CAST(SUM("成交量(股)") AS INTEGER)=899465961｜文档侧：招股意向书阶段尚未确定发行价格 | SELECT * FROM (SELECT CAST(SUM("成交量(股)") AS INTEGER) FROM A股票日行情表 WHERE 交易日 = '2 |
| s194 | doc | 多问句 | 公司主要产品为三片易拉罐；马口铁是公司生产三片易拉罐的主要原材料。 | 公司主要产品为三片易拉罐；马口铁是公司生产三片易拉罐的主要原材料 |
| s203 | sql | 多表JOIN/CASE：语义风险需人工核 | 管理人=汇安基金管理有限责任公司，累计单位净值=1.5558 | SELECT * FROM (SELECT f."管理人", d."累计单位净值" FROM 基金基本信息 f JOIN 基金日行情表 d ON f."基金代码 |
| s212 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=173 | SELECT * FROM (SELECT COUNT(*) FROM "A股票日行情表" WHERE "股票代码" = '002164' AND "交易日"  |
| s221 | sql | 多表JOIN/CASE：语义风险需人工核 | 年化收益率=11.8 | SELECT * FROM (SELECT ROUND(((SELECT "收盘价(元)" FROM A股票日行情表 WHERE 股票代码='603108' A |
| s236 | sql | 多表JOIN/CASE：语义风险需人工核 | 涨跌幅百分比=17.42 | SELECT * FROM (SELECT ROUND((MAX(q."收盘价(元)") - MIN(q."收盘价(元)")) / MIN(q."收盘价(元)" |
| s248 | sql | 多表JOIN/CASE：语义风险需人工核 | CAST(SUM(h."成交量(股)") AS INTEGER)=2776473053 | SELECT * FROM (SELECT CAST(SUM(h."成交量(股)") AS INTEGER) FROM "A股票日行情表" h JOIN "A股 |
| s254 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=309 | SELECT * FROM (SELECT COUNT(*) FROM "A股票日行情表" AS t1 JOIN "A股票日行情表" AS t2 ON t1.股 |
| s260 | doc | 库内公司但拒答：疑检索未命中或真未披露，须人工对PDF | 招股意向书仅披露了报告期内公司来自军用领域的收入占比分别为82.10%、97.31%、94.84%和94.34%，未直接 | 报告期内，公司来自军用领域的收入占比分别为82.10%、97.31%、94.84；2016年、2017年、2018年、2019年1-6月销售金额分别占公司主营业 |
| s263 | sql | 多表JOIN/CASE：语义风险需人工核；多问句 | 股票代码=300012，成交金额(元)=596786513.0 | SELECT a.股票代码, b."成交金额(元)" FROM "A股公司行业划分表" a JOIN "A股票日行情表" b ON a.股票代码 = b.股票代 |
| s275 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1.基金代码)=0 | SELECT * FROM (SELECT COUNT(DISTINCT t1.基金代码) FROM 基金基本信息 t1 JOIN 基金可转债持仓明细 t2 O |
| s278 | sql | 多表JOIN/CASE：语义风险需人工核 | 一级行业名称=电子; 一级行业名称=计算机; 一级行业名称=通信; 一级行业名称=传媒 | SELECT * FROM (SELECT DISTINCT a."一级行业名称" FROM 基金股票持仓明细 f JOIN A股公司行业划分表 a ON f. |
| s281 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(AVG(h."成交金额(元)"), 5)=57539317.55 | SELECT * FROM (SELECT ROUND(AVG(h."成交金额(元)"), 5) FROM "A股票日行情表" h JOIN "A股公司行业划分 |
| s284 | sql | 多表JOIN/CASE：语义风险需人工核 | 债券名称=19CHNE02; 债券名称=20附息国债04; 债券名称=18首开MTN001 | SELECT * FROM (SELECT t2."债券名称" FROM 基金基本信息 AS t1 JOIN 基金债券持仓明细 AS t2 ON t1."基金代 |
| s287 | doc | 库内公司但拒答：疑检索未命中或真未披露，须人工对PDF | 处理失败：1 validation error for Value
unit
  Input should be '元' |  |
| s290 | doc | 答案值未出现在已验证quote中 | 2016年度营业收入34,392.49万元，2015年度营业收入33,575.96万元；资料片段中未直接给出营业收入同比 | 营业收入、34,392.49、33,575.96、35,240.25；合计、33,605.08、2.19%、32,884.06、-4.21%、34,3 |
| s296 | sql | 多表JOIN/CASE：语义风险需人工核 | 单位净值=1.0304，资产净值=100788.34 | SELECT * FROM (SELECT f."单位净值", f."资产净值" FROM "基金日行情表" f JOIN "基金基本信息" b ON f."基 |
| s302 | doc | 多问句 | 现有遍布全国主要城市的7个大区、24个办事处和两家分公司，以及20多家签约代理商，营销服务人员240多人。 | 现有遍布全国主要城市的7 个大区、24 个办事处和两家分公司，以及20 多；家签约代理商，营销服务人员240 多人，80%以上具有测绘工程、信息工程、地 |
| s305 | doc | 多问句 | 2018年4月，索特传动设备有限公司认为因公司衬套磨损导致轮子故障率提高，向公司发出索赔通知；截至本招股意向书签署日，公 | 2018 年4 月，索特传动认为因公司衬套磨损导致轮子故障率提高；截至本招股意向书签署日，公司与索特传动该争议事项已解决 |
| s308 | sql | 多表JOIN/CASE：语义风险需人工核 | 股票代码=002594 | SELECT a.股票代码 FROM A股票日行情表 a JOIN A股公司行业划分表 b ON a.股票代码 = b.股票代码 AND b.交易日期 = '2 |
| s311 | none | 无路由命中：需人工确认是否DB题措辞遗漏 | 知识库外且无DB关键词 |  |
| s314 | doc | 库内公司但拒答：疑检索未命中或真未披露，须人工对PDF | 片段中未提供江苏爱康太阳能科技股份有限公司注册资本的信息；片段仅涉及子公司注册资本（如苏州爱康新材料注册资本10,000 | 注册资本10,000.00 万元；注册资本10,000 万元；注册资本8,000 万元；、15,000.00、100.00、20,000.00 |
| s329 | none | 无路由命中：需人工确认是否DB题措辞遗漏 | 知识库外且无DB关键词 |  |
| s339 | sql | 多表JOIN/CASE：语义风险需人工核 | 股票代码=601318，股票名称=中国平安，涨跌幅(%)=5.04 | SELECT * FROM (SELECT a."股票代码", a."股票名称", ROUND((b."收盘价(元)" - b."昨收盘(元)") / b."昨 |
| s345 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=0 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT "所在证券市场" FROM "基金股票持仓明细" WHERE "基金简称 |
| s352 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=161 | SELECT * FROM (SELECT COUNT(*) FROM "A股票日行情表" WHERE 股票代码 = '002158' AND 交易日 LIKE |
| s359 | sql | 多表JOIN/CASE：语义风险需人工核 | 股票代码=002142，股票名称=宁波银行; 股票代码=002142，股票名称=宁波银行 | SELECT * FROM (SELECT T1."股票代码", T1."股票名称" FROM "基金股票持仓明细" T1 JOIN "基金基本信息" T2 O |
| s362 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=148 | SELECT * FROM (SELECT COUNT(*) FROM "A股票日行情表" WHERE "股票代码" = '002771' AND "交易日"  |
| s366 | sql | 多表JOIN/CASE：语义风险需人工核 | 股票代码=002475，股票名称=立讯精密 | SELECT t1."股票代码", t1."股票名称" FROM "基金股票持仓明细" t1 JOIN "基金基本信息" t2 ON t1."基金代码" = t |
| s369 | sql | 多问句 | 股票代码=000524，涨跌幅=3.87 | SELECT t1.股票代码, ROUND((t2."收盘价(元)" - t2."昨收盘(元)") / t2."昨收盘(元)" * 100, 2) AS 涨跌幅 |
| s405 | sql | 多表JOIN/CASE：语义风险需人工核；多问句 | 股票代码=002192，涨跌幅=6.08 | SELECT a.股票代码, ROUND((b."收盘价(元)" - b."昨收盘(元)") / b."昨收盘(元)" * 100, 2) AS 涨跌幅 FRO |
| s408 | sql | 多表JOIN/CASE：语义风险需人工核 | CAST(SUM("成交金额(元)") AS INTEGER)=None | SELECT * FROM (SELECT CAST(SUM("成交金额(元)") AS INTEGER) FROM A股票日行情表 WHERE 交易日 = ' |
| s411 | sql | 多表JOIN/CASE：语义风险需人工核 | 管理人=工银瑞信基金管理有限公司，累计单位净值=1.493 | SELECT * FROM (SELECT f."管理人", d."累计单位净值" FROM 基金基本信息 f JOIN 基金日行情表 d ON f."基金代码 |
| s414 | sql | 多表JOIN/CASE：语义风险需人工核；多问句 | 股票代码=000829，成交金额(元)=1027041215.0 | SELECT a.股票代码, b."成交金额(元)" FROM "A股公司行业划分表" a JOIN "A股票日行情表" b ON a.股票代码 = b.股票代 |
| s427 | sql | 多表JOIN/CASE：语义风险需人工核 | 股票代码=600519，股票名称=贵州茅台 | SELECT t1."股票代码", t1."股票名称" FROM "基金股票持仓明细" t1 JOIN "基金基本信息" t2 ON t1."基金代码" = t |
| s448 | sql | 多表JOIN/CASE：语义风险需人工核 | 一级行业名称=非银金融; 一级行业名称=银行; 一级行业名称=家用电器; 一级行业名称=电子; 一级行业名称=电气设备 | SELECT * FROM (SELECT DISTINCT a."一级行业名称" FROM 基金股票持仓明细 f JOIN A股公司行业划分表 a ON f. |
| s452 | sql | 多表JOIN/CASE：语义风险需人工核 | 债券名称=20国开07; 债券名称=20国开12; 债券名称=20国债10 | SELECT * FROM (SELECT t1."债券名称" FROM 基金债券持仓明细 t1 JOIN 基金基本信息 t2 ON t1.基金代码 = t2. |
| s455 | sql | 多表JOIN/CASE：语义风险需人工核；多问句 | 股票代码=003035，成交金额(元)=2387414241.0 | SELECT a.股票代码, b."成交金额(元)" FROM "A股公司行业划分表" a JOIN "A股票日行情表" b ON a.股票代码 = b.股票代 |
| s468 | sql | 多表JOIN/CASE：语义风险需人工核；多问句 | 股票代码=600585，成交金额(元)=654587772.0 | SELECT a.股票代码, b."成交金额(元)" FROM "A股公司行业划分表" a JOIN "A股票日行情表" b ON a.股票代码 = b.股票代 |
| s471 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=0 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT s.股票代码, (MAX(q."收盘价(元)") - MIN(q."收盘 |
| s478 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(100.0 * SUM(CASE WHEN "个人投资者持有的基金份额" > "机构投资者持有的基金份额"  | SELECT * FROM (SELECT ROUND(100.0 * SUM(CASE WHEN "个人投资者持有的基金份额" > "机构投资者持有的基金份额 |
| s481 | sql | 多表JOIN/CASE：语义风险需人工核 | 管理人=民生加银基金管理有限公司，累计单位净值=1.0124 | SELECT * FROM (SELECT f."管理人", q."累计单位净值" FROM 基金基本信息 f JOIN 基金日行情表 q ON f."基金代码 |
| s485 | sql | 多表JOIN/CASE：语义风险需人工核 | 股票代码=600519 | SELECT a.股票代码 FROM A股公司行业划分表 a JOIN A股票日行情表 b ON a.股票代码 = b.股票代码 WHERE a.交易日期 =  |
| s488 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=115 | SELECT * FROM (SELECT COUNT(*) FROM "A股票日行情表" AS t1 JOIN "A股票日行情表" AS t2 ON t1.股 |
| s500 | doc | 库内公司但拒答：疑检索未命中或真未披露，须人工对PDF | 招股意向书提供的资料片段中未披露世界已探明天然气储量主要集中的地区，也未说明天然气消费以哪些地区为主。 |  |
| s508 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1.基金代码)=2 | SELECT * FROM (SELECT COUNT(DISTINCT t1.基金代码) FROM 基金基本信息 t1 JOIN 基金债券持仓明细 t2 ON |
| s511 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT h.基金代码)=10 | SELECT * FROM (SELECT COUNT(DISTINCT h.基金代码) FROM 基金份额持有人结构 h JOIN 基金基本信息 b ON h |
| s514 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT a.股票代码)=2 | SELECT * FROM (SELECT COUNT(DISTINCT a.股票代码) FROM A股公司行业划分表 a JOIN A股票日行情表 b ON  |
| s517 | doc | 多问句 | 持有公司5%以上股份的股东及公司实际控制人为孙伟杰、王坤晓和刘贞峰，本次公开发行前上述三人分别持有公司股份3,032.4 | 持有公司5%以上股份的股东及公司实际控制人为孙伟杰、王坤晓和刘贞峰，本次；公开发行前上述三人分别持有公司股份3,032.40 万股、2,074.80 万股；分别 |
| s530 | hybrid | 多表JOIN/CASE：语义风险需人工核 | ROUND(AVG(t1."市值"), 3)=92440.0｜文档侧：资料片段为苏州东微半导体股份有限公司招股意向书，未 | SELECT * FROM (SELECT ROUND(AVG(t1."市值"), 3) FROM "基金股票持仓明细" t1 JOIN "A股公司行业划分表" |
| s533 | doc | 答案值未出现在已验证quote中 | 在营销模式方面，本公司充分发挥对国内流行病发展趋势、国际国内疫苗发展趋势以及疫苗研发生产的深刻理解，通过组织高水平学术推 | 通过组织高水平学术推广会议、与各级疾
控中心合作开展基础预防教育等方式，提高本公；通过组织高水平学术推广会议、与各级疾
控中心合作开展基础预防教育等方式，提高本 |
| s536 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=0 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT m.股票代码, (SELECT (h."收盘价(元)" - h2."收盘 |
| s539 | sql | 多问句 | 股票代码=600824，涨跌幅=10.07 | SELECT t1.股票代码, ROUND((t2."收盘价(元)" - t2."昨收盘(元)") / t2."昨收盘(元)" * 100, 2) AS 涨跌幅 |
| s551 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1.基金代码)=0 | SELECT * FROM (SELECT COUNT(DISTINCT t1.基金代码) FROM 基金基本信息 t1 JOIN 基金债券持仓明细 t2 ON |
| s555 | sql | 多表JOIN/CASE：语义风险需人工核 | 涨跌幅百分比=12.66 | SELECT * FROM (SELECT ROUND((MAX(q."收盘价(元)") - MIN(q."收盘价(元)")) / MIN(q."收盘价(元)" |
| s570 | sql | 多表JOIN/CASE：语义风险需人工核 | 一级行业名称=医药生物; 一级行业名称=食品饮料; 一级行业名称=休闲服务 | SELECT * FROM (SELECT DISTINCT a."一级行业名称" FROM 基金股票持仓明细 f JOIN A股公司行业划分表 a ON f. |
| s573 | sql | 多表JOIN/CASE：语义风险需人工核 | 年化收益率=144.45 | SELECT * FROM (SELECT ROUND(((b."收盘价(元)" - a."今开盘(元)") / a."今开盘(元)") * 100, 2) A |
| s576 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(100.0 * SUM(CASE WHEN "个人投资者持有的基金份额" > "机构投资者持有的基金份额"  | SELECT * FROM (SELECT ROUND(100.0 * SUM(CASE WHEN "个人投资者持有的基金份额" > "机构投资者持有的基金份额 |
| s591 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=198 | SELECT * FROM (SELECT COUNT(*) FROM "A股票日行情表" AS t1 JOIN "A股票日行情表" AS t2 ON t1.股 |
| s594 | sql | 多表JOIN/CASE：语义风险需人工核 | 年化收益率=32.48 | SELECT * FROM (SELECT ROUND(((SELECT "收盘价(元)" FROM A股票日行情表 WHERE 股票代码='600884' A |
| s600 | doc | 答案值未出现在已验证quote中 | 医药行业主要销售渠道为：药品从制药企业进入终端医院通常需经由代理商和配送商两个环节。代理商负责开发和维护医院渠道资源，并 | 在“招商代理下的专业化学术推广”的销售模式下，药品从制药企业进入终端医院通常需经 |
| s603 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=1 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT b."基金代码", b."报告期期初基金总份额", b."报告期期末基金 |
| s606 | sql | 多问句 | 股票代码=300328，涨跌幅=9.99 | SELECT t1.股票代码, ROUND((t2."收盘价(元)" - t2."昨收盘(元)") / t2."昨收盘(元)" * 100, 2) AS 涨跌幅 |
| s627 | doc | 库内公司但拒答：疑检索未命中或真未披露，须人工对PDF | 片段中未直接以'主要产品为……'的表述给出宁波立立电子股份有限公司自身的主要产品，仅在固定资产相关表格中出现'单晶生长和 | 主要是用于单晶生长和硅抛光片、硅外延片、肖特基功率芯片等产品 |
| s630 | doc | 多问句 | 截至2007年12月31日，公司存货账面价值为12,392.06万元，占流动资产的29.46%，占总资产的17.12%。 | 截至2007 年12 月31 日，公司存货账面价值为12,392.06 万元，占；的29.46%，占总资产的17.12%，公司存货金额较大。 |
| s636 | none | 无路由命中：需人工确认是否DB题措辞遗漏 | 知识库外且无DB关键词 |  |
| s639 | doc | 多问句 | 2017 年12 月，锂科有限收购金驰材料100%股权及7,000 吨项目，构成重大资产重组。 | 2017 年12 月，锂科有限收购金驰材料100%股权及7,000 吨项目，构成 |
| s645 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=65 | SELECT * FROM (SELECT COUNT(*) FROM "A股票日行情表" AS t1 JOIN "A股票日行情表" AS t2 ON t1.股 |
| s648 | none | 无路由命中：需人工确认是否DB题措辞遗漏 | 知识库外且无DB关键词 |  |
| s654 | sql | 多表JOIN/CASE：语义风险需人工核 | CAST(SUM("成交量(股)") AS INTEGER)=None | SELECT * FROM (SELECT CAST(SUM("成交量(股)") AS INTEGER) FROM A股票日行情表 WHERE 交易日 = '2 |
| s660 | none | 无路由命中：需人工确认是否DB题措辞遗漏 | 知识库外且无DB关键词 |  |
| s663 | sql | 多问句 | 股票代码=300877，涨跌幅=14.43 | SELECT t1.股票代码, ROUND((t2."收盘价(元)" - t2."昨收盘(元)") / t2."昨收盘(元)" * 100, 2) AS 涨跌幅 |
| s675 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(AVG(t2."市值"), 3)=79164.0 | SELECT * FROM (SELECT ROUND(AVG(t2."市值"), 3) FROM 基金股票持仓明细 t2 JOIN A股公司行业划分表 t1  |
| s685 | doc | 库内公司但拒答：疑检索未命中或真未披露，须人工对PDF | 处理失败：1 validation error for Value
unit
  Input should be '元' |  |
| s700 | doc | 答案值未出现在已验证quote中 | 公司处于石油及天然气设备制造与服务行业，上游行业为配套零部件制造业；下游行业为石油及天然气开采业。 | 公司处于石油及天然气设备制造与服务行业，上游行业为配套零部件制造业；下游行业为石 |
| s709 | sql | 多表JOIN/CASE：语义风险需人工核 | 年化收益率=0.59 | SELECT * FROM (SELECT ROUND((((SELECT "收盘价(元)" FROM A股票日行情表 WHERE 股票代码='600510'  |
| s727 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1.基金代码)=15 | SELECT * FROM (SELECT COUNT(DISTINCT t1.基金代码) FROM 基金份额持有人结构 t1 JOIN 基金基本信息 t2 O |
| s734 | none | 无路由命中：需人工确认是否DB题措辞遗漏 | 知识库外且无DB关键词 |  |
| s740 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1.基金代码)=2 | SELECT * FROM (SELECT COUNT(DISTINCT t1.基金代码) FROM 基金基本信息 t1 JOIN 基金债券持仓明细 t2 ON |
| s743 | sql | 多表JOIN/CASE：语义风险需人工核 | 股票代码=300782 | SELECT a.股票代码 FROM A股公司行业划分表 a JOIN A股票日行情表 b ON a.股票代码 = b.股票代码 AND b.交易日 = '20 |
| s753 | sql | 多表JOIN/CASE：语义风险需人工核 | 管理人=华安基金管理有限公司，累计单位净值=1.0448 | SELECT * FROM (SELECT f."管理人", q."累计单位净值" FROM "基金基本信息" f JOIN "基金日行情表" q ON f." |
| s756 | doc | 答案值未出现在已验证quote中 | 截至本招股意向书签署日，公司拥有六家控股子公司（含全资子公司），无其他控股子公司和参股子公司。 | 截至本招股意向书签署日，公司拥有六家控股子公司（含全资子公司），无其他控股子公司 |
| s769 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=148 | SELECT * FROM (SELECT COUNT(*) FROM "A股票日行情表" WHERE "股票代码" = '600578' AND "交易日"  |
| s773 | sql | 多问句 | 净赎回基金家数=996，净赎回总份额=196350640124.8 | SELECT * FROM (SELECT COUNT(*) AS 净赎回基金家数, ROUND(SUM(报告期基金总赎回份额 - 报告期基金总申购份额), 2 |
| s777 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT a.股票代码)=0 | SELECT * FROM (SELECT COUNT(DISTINCT a.股票代码) FROM "A股公司行业划分表" a JOIN "A股票日行情表" b |
| s802 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(100.0 * SUM(CASE WHEN "个人投资者持有的基金份额" > "机构投资者持有的基金份额"  | SELECT * FROM (SELECT ROUND(100.0 * SUM(CASE WHEN "个人投资者持有的基金份额" > "机构投资者持有的基金份额 |
| s805 | sql | 多表JOIN/CASE：语义风险需人工核 | 年化收益率=15.1 | SELECT * FROM (SELECT ROUND((b."收盘价(元)" - a."今开盘(元)") * 100.0 / a."今开盘(元)", 2) A |
| s808 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=537 | SELECT * FROM (SELECT COUNT(*) FROM "A股票日行情表" AS t1 WHERE t1."交易日" = '20190408'  |
| s824 | sql | 多问句 | 基金家数=598，净赎回份额=115607107036.04 | SELECT * FROM (SELECT COUNT(*) AS 基金家数, ROUND(SUM(报告期基金总赎回份额 - 报告期基金总申购份额), 2) A |
| s833 | sql | 多问句 | 净赎回基金家数=2038，净赎回总份额=387213188588.97 | SELECT * FROM (SELECT COUNT(*) AS 净赎回基金家数, ROUND(SUM(报告期基金总赎回份额 - 报告期基金总申购份额), 2 |
| s848 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1.基金代码)=0 | SELECT * FROM (SELECT COUNT(DISTINCT t1.基金代码) FROM 基金基本信息 t1 JOIN 基金可转债持仓明细 t2 O |
| s860 | sql | 多问句 | 基金简称=鹏华添利宝货币B，差额=46226592575.53 | SELECT "基金简称", ROUND(ABS("报告期基金总申购份额" - "报告期基金总赎回份额"), 2) AS 差额 FROM 基金规模变动表 WHE |
| s863 | sql | 多表JOIN/CASE：语义风险需人工核 | 管理人=博道基金管理有限公司，累计单位净值=1.2561 | SELECT * FROM (SELECT f.管理人, q.累计单位净值 FROM 基金基本信息 f JOIN 基金日行情表 q ON f.基金代码 = q. |
| s869 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=0 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT m.股票代码, (SELECT (h."收盘价(元)" - h2."收盘 |
| s893 | sql | 多表JOIN/CASE：语义风险需人工核 | 股票代码=002460，股票名称=赣锋锂业 | SELECT t1."股票代码", t1."股票名称" FROM "基金股票持仓明细" t1 JOIN "基金基本信息" t2 ON t1."基金代码" = t |
| s897 | sql | 多表JOIN/CASE：语义风险需人工核 | 管理人=上海光大证券资产管理有限公司，ROUND(q."单位净值", 2)=1.03 | SELECT * FROM (SELECT f."管理人", ROUND(q."单位净值", 2) FROM "基金基本信息" f JOIN "基金日行情表"  |
| s900 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=1 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT f.基金代码, f.报告期期初基金总份额, f.报告期期末基金总份额 F |
| s903 | sql | 多表JOIN/CASE：语义风险需人工核 | CAST(SUM(b."成交量(股)") AS INTEGER)=1549865529 | SELECT * FROM (SELECT CAST(SUM(b."成交量(股)") AS INTEGER) FROM "A股公司行业划分表" a JOIN " |
| s909 | doc | 答案值未出现在已验证quote中 | 上海住友商事有限公司（上海住友）为发行人报告期内第一大客户 | 因此上海住友成为发行人报告期内第一大客户，公司向上海住友销售金额占总销售额的比例；1、上海住友商事有限公司、44,225.12；1、上海住友商事有限公司、日本、 |
| s918 | doc | 库内公司但拒答：疑检索未命中或真未披露，须人工对PDF | 片段中未直接给出广东银禧科技股份有限公司（发行人）的注册资本金额；仅提及股改前注册资本5,023.35万元已经足额到位， | 截至股改基准日2008 年2 月29 日止，银禧公司历次注册资本5,023.35；总股本、75,000,000、100.00%、100,000,000、100. |
| s940 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1."基金代码")=27 | SELECT * FROM (SELECT COUNT(DISTINCT t1."基金代码") FROM "基金可转债持仓明细" t1 WHERE t1."持仓 |
| s952 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=10 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT s.股票代码, (MAX(q."收盘价(元)") - MIN(q."收盘 |
| s967 | doc | 答案值未出现在已验证quote中 | 与公司在行业内形成竞争的汽车内饰面料生产企业主要包括合资企业瑞安市李尔汽车面料有限公司、青岛福基纺织有限公司和上海申达川 | 与公司在行业内形成竞争的汽车内饰面料生产企业主要包括合资企业瑞安市李尔汽车面料有 |
| s970 | sql | 多表JOIN/CASE：语义风险需人工核；多问句 | 净申购基金家数=145，净申购份额合计=33285436103.32 | SELECT * FROM (SELECT COUNT(*) AS 净申购基金家数, ROUND(SUM(净申购份额), 2) AS 净申购份额合计 FROM  |
| s973 | sql | 多问句 | 净申购基金家数=543，净申购份额合计=210782379651.24 | SELECT * FROM (SELECT COUNT(*) AS 净申购基金家数, ROUND(SUM(报告期基金总申购份额 - 报告期基金总赎回份额), 2 |
| s988 | doc | 多问句 | 公司目前主要产品包括LED 照明散热组件及PC 散热配件，其中LED 照明散热组件是公司未来业务增长的重点产品。 | 公司目前主要产品包括LED 照明散热组件及PC 散热配件，其中LED 照明散；热组件是公司未来业务增长的重点产品。；LED 照明散热组件、PC 散热配件为公司主 |
| s997 | doc | 多问句 | 公司实际控制人为李旭亮先生和温琦女士。李旭亮先生和温琦女士通过勤上集团间接持有公司34.53%的股份，同时，温琦女士直接 | 公司实际控制人为李旭亮先生和温琦女士。截至本招股意向书签署日，李旭；亮先生和温琦女士通过勤上集团间接持有公司34.53%的股份，同时，温琦女士；直接持有公司1. |
