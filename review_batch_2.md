# 人工复核队列

| id | 题型 | 复核原因 | 系统答案 | 证据 |
|---|---|---|---|---|
| s2 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT a.股票代码)=0 | SELECT * FROM (SELECT COUNT(DISTINCT a.股票代码) FROM "A股公司行业划分表" a JOIN "A股票日行情表" b |
| s8 | sql | 多表JOIN/CASE：语义风险需人工核；多问句 | 股票代码=600028，成交金额(元)=488439709.0 | SELECT a.股票代码, b."成交金额(元)" FROM "A股公司行业划分表" a JOIN "A股票日行情表" b ON a.股票代码 = b.股票代 |
| s11 | sql | 多表JOIN/CASE：语义风险需人工核；多问句 | 净申购基金家数=445，净申购份额合计=95620586764.09 | SELECT * FROM (SELECT COUNT(*) AS 净申购基金家数, ROUND(SUM(净申购份额), 2) AS 净申购份额合计 FROM  |
| s17 | doc | 多问句 | 各报告期末，公司存货分别为4,924.58万元、6,647.27万元、8,576.59万元和9,832.60万元，占流动 | 各报告期末，公司存货分别为4,924.58 万元、6,647.27 万元、8,5；2007年末、2008年末、2009年末和2010年半年末余值分别为4,924 |
| s23 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(AVG(t2."市值"), 3)=2238220.0 | SELECT * FROM (SELECT ROUND(AVG(t2."市值"), 3) FROM 基金股票持仓明细 t2 JOIN A股公司行业划分表 t1  |
| s26 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(AVG(h."成交金额(元)"), 5)=456321251.1 | SELECT * FROM (SELECT ROUND(AVG(h."成交金额(元)"), 5) FROM "A股票日行情表" h JOIN "A股公司行业划分 |
| s29 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=10 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT s.股票代码, (MAX(q."收盘价(元)") - MIN(q."收盘 |
| s32 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=3 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT f."基金代码" FROM "基金基本信息" f JOIN "基金规模变 |
| s42 | sql | 多表JOIN/CASE：语义风险需人工核 | 涨跌幅(%)=52.97 | SELECT * FROM (SELECT ROUND((MAX(q."收盘价(元)") - MIN(q."收盘价(元)")) / MIN(q."收盘价(元)" |
| s55 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=91 | SELECT * FROM (SELECT COUNT(*) FROM "A股票日行情表" WHERE 股票代码 = '301005' AND 交易日 LIKE |
| s61 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(AVG(h."成交金额(元)"), 5)=75707757.0 | SELECT * FROM (SELECT ROUND(AVG(h."成交金额(元)"), 5) FROM "A股票日行情表" h JOIN "A股公司行业划分 |
| s67 | doc | 多问句 | 是。公司自2011年起被认定为“国家高新技术企业”，并先后建立了“省级高新技术企业研究开发中心”、“省级博士后工作站”、 | 公司注重技术创新和产品研发，自2011 年起被认定为“国家高新技术企业”，；先后建立了“省级高新技术企业研究开发中心”、“省级博士后工作站”、“省级企；业技术中 |
| s76 | sql | 多表JOIN/CASE：语义风险需人工核 | 债券类型=金融债券 | SELECT b."债券类型" FROM 基金债券持仓明细 b JOIN 基金基本信息 f ON b."基金代码" = f."基金代码" WHERE f."基金 |
| s79 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT b.基金代码)=3 | SELECT * FROM (SELECT COUNT(DISTINCT b.基金代码) FROM 基金基本信息 b JOIN 基金债券持仓明细 d ON b. |
| s82 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1.基金代码)=2 | SELECT * FROM (SELECT COUNT(DISTINCT t1.基金代码) FROM 基金份额持有人结构 t1 JOIN 基金基本信息 t2 O |
| s86 | sql | 多表JOIN/CASE：语义风险需人工核 | 股票代码=603833 | SELECT a.股票代码 FROM A股票日行情表 a JOIN A股公司行业划分表 b ON a.股票代码 = b.股票代码 AND b.交易日期 = '2 |
| s92 | sql | 多表JOIN/CASE：语义风险需人工核 | 股票代码=601186，股票名称=中国铁建，涨跌幅(%)=-3.15 | SELECT * FROM (SELECT T1."股票代码", T1."股票名称", ROUND((T2."收盘价(元)" - T2."昨收盘(元)") /  |
| s101 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1.基金代码)=0 | SELECT * FROM (SELECT COUNT(DISTINCT t1.基金代码) FROM 基金份额持有人结构 t1 JOIN 基金基本信息 t2 O |
| s104 | sql | 多表JOIN/CASE：语义风险需人工核 | 股票代码=601816 | SELECT * FROM (SELECT t1."股票代码" FROM 基金股票持仓明细 t1 JOIN 基金基本信息 t2 ON t1."基金代码" = t |
| s107 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1.基金代码)=0 | SELECT * FROM (SELECT COUNT(DISTINCT t1.基金代码) FROM 基金份额持有人结构 t1 JOIN 基金基本信息 t2 O |
| s119 | sql | 多表JOIN/CASE：语义风险需人工核 | 管理人=浦银安盛基金管理有限公司，累计单位净值=1.0549 | SELECT * FROM (SELECT f."管理人", d."累计单位净值" FROM 基金基本信息 f JOIN 基金日行情表 d ON f."基金代码 |
| s122 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=4 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT "所在证券市场" FROM "基金股票持仓明细" WHERE "基金简称 |
| s128 | sql | 多表JOIN/CASE：语义风险需人工核；多问句 | 股票代码=000655，涨跌幅=4.81 | SELECT a.股票代码, ROUND((b."收盘价(元)" - b."昨收盘(元)") / b."昨收盘(元)" * 100, 2) AS 涨跌幅 FRO |
| s152 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(AVG(t2."市值"), 3)=900322566.003 | SELECT * FROM (SELECT ROUND(AVG(t2."市值"), 3) FROM 基金股票持仓明细 t2 JOIN A股公司行业划分表 t1  |
| s167 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(100.0 * SUM(CASE WHEN "个人投资者持有的基金份额" > "机构投资者持有的基金份额"  | SELECT * FROM (SELECT ROUND(100.0 * SUM(CASE WHEN "个人投资者持有的基金份额" > "机构投资者持有的基金份额 |
| s176 | sql | 多表JOIN/CASE：语义风险需人工核 | 债券类型=金融债券 | SELECT b."债券类型" FROM 基金债券持仓明细 b JOIN 基金基本信息 f ON b."基金代码" = f."基金代码" WHERE f."基金 |
| s179 | doc | 库内公司但拒答：疑检索未命中或真未披露，须人工对PDF | 片段中未包含对湖南国科微电子股份有限公司主营业务的具体文字描述，仅出现'（一）主营业务和主要产品'等标题及产品分类表格， | （一）主营业务和主要产品；一、公司主营业务和主要产品 |
| s204 | sql | 多问句 | 股票代码=300178，涨跌幅=4.62 | SELECT a.股票代码, ROUND((b."收盘价(元)" - b."昨收盘(元)") / b."昨收盘(元)" * 100, 2) AS 涨跌幅
FRO |
| s225 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT a.股票代码)=0 | SELECT * FROM (SELECT COUNT(DISTINCT a.股票代码) FROM "A股公司行业划分表" a JOIN "A股票日行情表" b |
| s228 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=128 | SELECT * FROM (SELECT COUNT(*) FROM "A股票日行情表" AS t1 JOIN "A股票日行情表" AS t2 ON t1.股 |
| s249 | doc | 多问句 | 成立日期：2003年2月16日；注册资本：52,000万元 | 注册资本：52,000万元；成立日期：2003 年2 月16 日；5、有限公司成立日期： 2003年2月16日；4、注册资本： 52,000万元 |
| s252 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=0 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT t1."股票代码", t1."持仓日期", t1."第N大重仓股", t |
| s255 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=0 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT m.股票代码, (SELECT h."收盘价(元)" FROM A股票日 |
| s261 | doc | 库内公司但拒答：疑检索未命中或真未披露，须人工对PDF | 资料片段中未包含董事会成员名单，仅提及黄辉、卢信群简历详见'（一）董事会成员'，但该名单本身未在片段中给出。 | 1、黄辉：总经理，简历详见本节“（一）董事会成员”。；4、卢信群：财务总监，简历详见本节“（一）董事会成员”。 |
| s273 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=159 | SELECT * FROM (SELECT COUNT(*) FROM "A股票日行情表" WHERE 股票代码 = '603679' AND 交易日 LIKE |
| s285 | doc | 多问句 | 公司在高效电池正极材料领域具有多年的技术积累，技术水平处于业内领先，掌握了动力电池正极材料制备技术、三元前驱体共沉淀技术 | 公司在高效电池正极材料领域具有多年的技术积累，技术水平处于业内领先，掌握；了动力电池正极材料制备技术、三元前驱体共沉淀技术、三元前驱体晶面调控技术、三；元前驱体 |
| s294 | doc | 答案值未出现在已验证quote中；多问句 | 公司实际控制人为李银会先生，共1人。 | 公司实际控制人为李银会先生，李银会先生目前持有发行人控股股东华实投；公司的实际控制人为李银会先生，李银会先生目前持有青海华实科技投资管；公司实际控制人是李银会先 |
| s312 | doc | 多问句 | 公司已获得171项国内专利（其中发明专利17项） | 公司已获得171 项国内专利（其中发明
专利17 项）；公司已获得171 项国内专利（其中发明专利17 项）；公司已获得171 项国
内专利（其中发明专利17  |
| s315 | sql | 多问句 | 基金家数=1554，净赎回份额=506369181950.08 | SELECT * FROM (SELECT COUNT(*) AS 基金家数, ROUND(SUM(报告期基金总赎回份额 - 报告期基金总申购份额), 2) A |
| s321 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1.基金代码)=31 | SELECT * FROM (SELECT COUNT(DISTINCT t1.基金代码) FROM 基金份额持有人结构 t1 JOIN 基金基本信息 t2 O |
| s324 | doc | 多问句 | 截至2016年6月30日，公司及子公司共有技术研发人员118人，占员工总人数6.54%（其中母公司华达科技的技术研发人员 | 截至2016 年6 月30 日，公司及子公司共有技术研发人员118 人，占员工总；技术研发人员、、、118、、6.54%、 |
| s337 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=0 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT s.股票代码, (MAX(q."收盘价(元)") - MIN(q."收盘 |
| s349 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=0 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT "所在证券市场" FROM 基金股票持仓明细 WHERE "基金简称"  |
| s360 | sql | 多表JOIN/CASE：语义风险需人工核 | 股票代码=002027，股票名称=分众传媒 | SELECT t1."股票代码", t1."股票名称" FROM "基金股票持仓明细" t1 JOIN "基金基本信息" t2 ON t1."基金代码" = t |
| s388 | sql | 多表JOIN/CASE：语义风险需人工核 | CAST(SUM("成交量(股)") AS INTEGER)=4596648865 | SELECT * FROM (SELECT CAST(SUM("成交量(股)") AS INTEGER) FROM A股票日行情表 WHERE 交易日 = '2 |
| s391 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT a.股票代码)=0 | SELECT * FROM (SELECT COUNT(DISTINCT a.股票代码) FROM "A股公司行业划分表" a JOIN "A股票日行情表" b |
| s394 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=4 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT m.股票代码, (SELECT (h."收盘价(元)" - h2."收盘 |
| s397 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=53 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT m.基金代码, m.报告期期初基金总份额, m.报告期期末基金总份额 F |
| s403 | sql | 多问句 | 基金简称=汇添富理财14天债券型B，差额=7167766311.78 | SELECT 基金简称, ROUND(ABS(报告期基金总申购份额 - 报告期基金总赎回份额), 2) AS 差额 FROM 基金规模变动表 WHERE 截止日 |
| s406 | none | 无路由命中：需人工确认是否DB题措辞遗漏 | 知识库外且无DB关键词 |  |
| s412 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=516 | SELECT * FROM (SELECT COUNT(*) FROM "A股票日行情表" AS t1 JOIN "A股票日行情表" AS t2 ON t1.股 |
| s419 | sql | 多表JOIN/CASE：语义风险需人工核 | 债券名称=20国债15; 债券名称=20国债10; 债券名称=19国债03 | SELECT * FROM (SELECT b.债券名称 FROM 基金债券持仓明细 b JOIN 基金基本信息 f ON b.基金代码 = f.基金代码 WH |
| s425 | doc | 多问句 | 预计市值不低于人民币30亿元，且最近一年营业收入不低于人民币3亿元。 | 预计市值不低于人民币
30 亿元，且最近一年营业收入不低于人民币3 亿元。 |
| s434 | sql | 多问句 | 基金简称=华夏鼎略债券A，差额=4504188854.73 | SELECT "基金简称", ROUND(ABS("报告期基金总申购份额" - "报告期基金总赎回份额"), 2) AS 差额 FROM 基金规模变动表 WHE |
| s437 | doc | 多问句 | 《铁路产品认证证书》有效期5年；公司取得《铁路产品认证证书》后，每12个月至少接受一次监督。 | 公司取得《铁路产品认证证书》后，每12 个月至少接受一次监督，《铁路产品认证证书；公司取得《铁路产品认证证书》后，每12 个月至少接受一次监督，《铁路产品认证证 |
| s440 | sql | 多问句 | 净赎回基金家数=274，净赎回总份额=55689213867.09 | SELECT * FROM (SELECT COUNT(*) AS 净赎回基金家数, ROUND(SUM(报告期基金总赎回份额 - 报告期基金总申购份额), 2 |
| s446 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=71 | SELECT * FROM (SELECT COUNT(*) FROM "A股票日行情表" AS t1 JOIN "A股票日行情表" AS t2 ON t1.股 |
| s456 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=0 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT m.股票代码, (SELECT h."收盘价(元)" FROM A股票日 |
| s469 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1.基金代码)=0 | SELECT * FROM (SELECT COUNT(DISTINCT t1.基金代码) FROM 基金份额持有人结构 t1 JOIN 基金基本信息 t2 O |
| s472 | doc | 多问句 | 公司控股股东为国际工程公司，直接持有公司股份43.43%，间接通过控股子公司中机国际持有公司股份4.88%。 | 公司控股股东为国际工程公司，直接持有公司股份43.43%，间接通过控股子公司中机；本次发行前，国际工程公司持有公司43.43%的股份，为公司控股股东，国际工程公 |
| s475 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(AVG(t2."市值"), 3)=2963916.0 | SELECT * FROM (SELECT ROUND(AVG(t2."市值"), 3) FROM 基金股票持仓明细 t2 JOIN A股公司行业划分表 t1  |
| s479 | none | 无路由命中：需人工确认是否DB题措辞遗漏 | 知识库外且无DB关键词 |  |
| s482 | none | 无路由命中：需人工确认是否DB题措辞遗漏 | 知识库外且无DB关键词 |  |
| s495 | sql | 多表JOIN/CASE：语义风险需人工核 | 股票代码=603535 | SELECT a.股票代码 FROM "A股公司行业划分表" a JOIN "A股票日行情表" b ON a.股票代码 = b.股票代码 WHERE a.交易日 |
| s498 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1.基金代码)=0 | SELECT * FROM (SELECT COUNT(DISTINCT t1.基金代码) FROM 基金份额持有人结构 t1 JOIN 基金基本信息 t2 O |
| s505 | sql | 多表JOIN/CASE：语义风险需人工核；多问句 | 股票代码=002565，成交金额(元)=2418629627.0 | SELECT a.股票代码, b."成交金额(元)" FROM "A股公司行业划分表" a JOIN "A股票日行情表" b ON a.股票代码 = b.股票代 |
| s512 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=0 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT "所在证券市场" FROM "基金股票持仓明细" WHERE "基金简称 |
| s525 | sql | 多表JOIN/CASE：语义风险需人工核 | 股票名称=海康威视，涨跌幅(%)=45.65 | SELECT * FROM (SELECT a."股票名称", ROUND((MAX(b."收盘价(元)") - MIN(b."收盘价(元)")) / MIN( |
| s528 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=166 | SELECT * FROM (SELECT COUNT(*) FROM "A股票日行情表" WHERE "股票代码" = '300300' AND "交易日"  |
| s537 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=128 | SELECT * FROM (SELECT COUNT(*) FROM "A股票日行情表" AS t1 JOIN "A股票日行情表" AS t2 ON t1.股 |
| s549 | sql | 多表JOIN/CASE：语义风险需人工核 | 单位净值=1.3141，资产净值=223466099.94 | SELECT * FROM (SELECT f."单位净值", f."资产净值" FROM "基金日行情表" f JOIN "基金基本信息" b ON f."基 |
| s556 | doc | 多问句 | 海南双成药业股份有限公司的前身海南双成药业有限公司成立于2000年5月22日。 | 海南双成药业股份有限公司的前身海南双成药业有限公司成立于2000年5月22日。 |
| s574 | sql | 多表JOIN/CASE：语义风险需人工核 | 一级行业名称=银行 | SELECT t1."一级行业名称"
FROM "基金可转债持仓明细" AS t2
JOIN "基金基本信息" AS t3
  ON t3."基金代码" = t |
| s577 | doc | 多问句 | 报告期内，公司移动媒体平台服务业务收入分别为1,277.85万元、618.75万元及334.01万元，呈逐年下降趋势。 | 报告期内，公司移动媒体平台服务业务收入分别为1,277.85 万元、618.75；及334.01 万元。；报告期内发行人移动媒体平台服务业务收入分别为1,277 |
| s583 | sql | 多表JOIN/CASE：语义风险需人工核 | 管理人=融通基金管理有限公司，ROUND(q.单位净值, 2)=1.56 | SELECT * FROM (SELECT f.管理人, ROUND(q.单位净值, 2) FROM 基金基本信息 f JOIN 基金日行情表 q ON f.基 |
| s586 | doc | 多问句 | 货币资金增加5,363.69万元，主要系经营规模扩大所致 | 货币资金增加5,363.69 万元，主要系经营规模扩大所致 |
| s604 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=0 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT m.股票代码, (SELECT h."收盘价(元)" FROM A股票日 |
| s607 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1.基金代码)=0 | SELECT * FROM (SELECT COUNT(DISTINCT t1.基金代码) FROM 基金份额持有人结构 t1 JOIN 基金基本信息 t2 O |
| s613 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT h.基金代码)=1 | SELECT * FROM (SELECT COUNT(DISTINCT h.基金代码) FROM 基金份额持有人结构 h JOIN 基金基本信息 b ON h |
| s621 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=16 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT f."股票代码", (SELECT (SELECT "收盘价(元)" F |
| s631 | sql | 多表JOIN/CASE：语义风险需人工核 | 股票代码=002959 | SELECT a.股票代码 FROM A股公司行业划分表 a JOIN A股票日行情表 b ON a.股票代码 = b.股票代码 WHERE a.交易日期 =  |
| s643 | doc | 库内公司但拒答：疑检索未命中或真未披露，须人工对PDF | 未能在知识库中定位相关章节内容 |  |
| s652 | sql | 多表JOIN/CASE：语义风险需人工核；多问句 | 股票代码=601318，成交金额(元)=2723611890.0 | SELECT a.股票代码, b."成交金额(元)" FROM "A股公司行业划分表" a JOIN "A股票日行情表" b ON a.股票代码 = b.股票代 |
| s658 | sql | 多问句 | 基金简称=工银瑞信瑞丰半年定期开放纯债债券，差额=11389257171.66 | SELECT 基金简称, ROUND(ABS("报告期基金总申购份额" - "报告期基金总赎回份额"), 2) AS 差额 FROM 基金规模变动表 WHERE |
| s667 | doc | 多问句 | 最近三年及一期，公司汽车内饰面料产品的毛利率分别为39.27%、34.18%、35.27%和33.51%，呈现整体略微下 | 最近三年及一期，公司汽车内饰面料产品的毛利率分别为39.27%、34.18%、3；最近三年及一期，公司汽车内饰面料产品的毛利率分别为39.27%、34.18%、 |
| s673 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(100.0 * SUM(CASE WHEN "个人投资者持有的基金份额" > "机构投资者持有的基金份额"  | SELECT * FROM (SELECT ROUND(100.0 * SUM(CASE WHEN "个人投资者持有的基金份额" > "机构投资者持有的基金份额 |
| s683 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(AVG(t2."市值"), 3)=1673880.0 | SELECT * FROM (SELECT ROUND(AVG(t2."市值"), 3) FROM 基金股票持仓明细 t2 JOIN A股公司行业划分表 t1  |
| s689 | sql | 多问句 | 净赎回基金数=2262，净赎回总份额=534872293851.14 | SELECT * FROM (SELECT COUNT(*) AS 净赎回基金数, ROUND(SUM(报告期基金总赎回份额 - 报告期基金总申购份额), 2) |
| s704 | doc | 库内公司但拒答：疑检索未命中或真未披露，须人工对PDF | 招股意向书阶段尚未确定发行价格 |  |
| s707 | sql | 多表JOIN/CASE：语义风险需人工核 | CAST(SUM("成交金额(元)") AS INTEGER)=15900347965 | SELECT * FROM (SELECT CAST(SUM("成交金额(元)") AS INTEGER) FROM A股票日行情表 WHERE 交易日 = ' |
| s719 | hybrid | 多表JOIN/CASE：语义风险需人工核 | ROUND(AVG(h."市值"), 3)=41389392.0｜文档侧：资料片段为海尔施生物医药股份有限公司招股意向书 | SELECT * FROM (SELECT ROUND(AVG(h."市值"), 3) FROM "基金股票持仓明细" h JOIN "A股公司行业划分表" i |
| s722 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(100.0 * SUM(CASE WHEN h."个人投资者持有的基金份额" > h."机构投资者持有的基金 | SELECT * FROM (SELECT ROUND(100.0 * SUM(CASE WHEN h."个人投资者持有的基金份额" > h."机构投资者持有的 |
| s725 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=0 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT "所在证券市场" FROM "基金股票持仓明细" WHERE "基金简称 |
| s731 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1.基金代码)=0 | SELECT * FROM (SELECT COUNT(DISTINCT t1.基金代码) FROM 基金份额持有人结构 t1 JOIN 基金基本信息 t2 O |
| s738 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1.基金代码)=5 | SELECT * FROM (SELECT COUNT(DISTINCT t1.基金代码) FROM 基金基本信息 t1 JOIN 基金债券持仓明细 t2 ON |
| s761 | doc | 多问句 | 本次发行前，公司总股本为14,050.00万股。本次发行的股份约占发行后总股本的比例为25.00%。 | 本次发行前，公司总股本为14,050.00 万股。；本次发行的股份约占发行后总股本的比例为25.00%。；3、发行股数：4,683.50 万股，约占发行后总股本 |
| s778 | doc | 答案值未出现在已验证quote中 | 战略委员会成员由五名公司董事组成 | 战略委员会成员由五名公司董事组成，其中应至少包括一名独立董事。 |
| s787 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=14 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT f."基金代码", f."报告期期初基金总份额", f."报告期期末基金 |
| s794 | doc | 答案值未出现在已验证quote中 | 共 32 项 | （一）技术路线替代的风险；（二）新技术和新产品研发风险；（三）研发人员流失风险；（四）关键技术流失风险；（一）下游行业需求波动风险；（二）原材料价格波动风险；（ |
| s800 | doc | 多问句 | 吴佩芳直接持有发行人31.19%的股份，为发行人的控股股东；吴佩芳及其一致行动人共计持有发行人35.68%的股份。 | 吴佩芳直接持有发行人31.19%的股份，为发行；吴佩芳及其一致行动人共计持有发行人35.68%的股份 |
| s803 | doc | 库内公司但拒答：疑检索未命中或真未披露，须人工对PDF | 招股意向书片段中仅出现"(三)公司的竞争劣势"这一标题，其后具体内容未在所给片段中呈现，无法依据现有资料回答公司劣势的具 | (三)公司的竞争劣势 |
| s806 | sql | 多表JOIN/CASE：语义风险需人工核；多问句 | 净申购基金家数=1696，净申购份额合计=456868200841.76 | SELECT * FROM (SELECT COUNT(*) AS 净申购基金家数, ROUND(SUM(净申购份额), 2) AS 净申购份额合计 FROM  |
| s810 | none | 无路由命中：需人工确认是否DB题措辞遗漏 | 知识库外且无DB关键词 |  |
| s813 | doc | 答案值未出现在已验证quote中 | 2007年度，公司向欧盟出口的销售收入占公司工业业务收入的比重为3.84%。 | 占公司工业业务收入的比重分别为3.14%、5.23%和3.84%；分别为3.14%、5.23%和3.84%。公司出口欧盟的销售收入在工业业务中的比 |
| s822 | sql | 多表JOIN/CASE：语义风险需人工核 | 债券名称=20进出08; 债券名称=20国开06; 债券名称=国开1805 | SELECT * FROM (SELECT t1."债券名称" FROM 基金债券持仓明细 t1 JOIN 基金基本信息 t2 ON t1.基金代码 = t2. |
| s840 | sql | 多表JOIN/CASE：语义风险需人工核 | CAST(SUM("成交金额(元)") AS INTEGER)=None | SELECT * FROM (SELECT CAST(SUM("成交金额(元)") AS INTEGER) FROM A股票日行情表 WHERE 交易日 = ' |
| s849 | sql | 多表JOIN/CASE：语义风险需人工核 | 管理人=嘉合基金管理有限公司，累计单位净值=1.0165 | SELECT * FROM (SELECT f."管理人", d."累计单位净值" FROM 基金基本信息 f JOIN 基金日行情表 d ON f."基金代码 |
| s852 | sql | 多表JOIN/CASE：语义风险需人工核；多问句 | 股票代码=000002，成交金额(元)=2612104090.0 | SELECT a.股票代码, b."成交金额(元)" FROM "A股公司行业划分表" a JOIN "A股票日行情表" b ON a.股票代码 = b.股票代 |
| s861 | none | 无路由命中：需人工确认是否DB题措辞遗漏 | 知识库外且无DB关键词 |  |
| s864 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(AVG(h."成交金额(元)"), 5)=204115497.39535 | SELECT * FROM (SELECT ROUND(AVG(h."成交金额(元)"), 5) FROM "A股公司行业划分表" i JOIN "A股票日行情 |
| s873 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=0 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT "所在证券市场" FROM "基金股票持仓明细" WHERE "基金简称 |
| s891 | sql | 多表JOIN/CASE：语义风险需人工核 | 管理人=华宝基金管理有限公司，累计单位净值=1.9347 | SELECT * FROM (SELECT f."管理人", q."累计单位净值" FROM "基金基本信息" f JOIN "基金日行情表" q ON f." |
| s898 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=85 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT f."基金代码" FROM "基金基本信息" f JOIN "基金规模变 |
| s907 | doc | 答案值未出现在已验证quote中 | 2009年12月24日，公司创立大会暨第一次股东大会选举吉西平、彭长城、董有山、陈泽奎、黄强、雷志宏为公司董事，聘任高新 | 2009 年12 月24 日，公司创立大会暨第一次股东大会选举吉西平、彭长城、董；决定选举吉西平、彭长城、董有山、陈泽奎、马永强、陈海平等人为公司董事，同时聘任 |
| s910 | sql | 多表JOIN/CASE：语义风险需人工核 | 年化收益率=-11.74 | SELECT * FROM (SELECT ROUND((((SELECT "收盘价(元)" FROM A股票日行情表 WHERE 股票代码='603937'  |
| s913 | sql | 多表JOIN/CASE：语义风险需人工核 | ROUND(100.0 * SUM(CASE WHEN "个人投资者持有的基金份额" > "机构投资者持有的基金份额"  | SELECT * FROM (SELECT ROUND(100.0 * SUM(CASE WHEN "个人投资者持有的基金份额" > "机构投资者持有的基金份额 |
| s916 | doc | 答案值未出现在已验证quote中；多问句 | 共 2 项 | 六、管理风险；（一）公司快速发展引致的管理及经营风险；如果届时公司管理体系和经营模式不能进；行及时调整以适应上述变化，公司将存在一定的管理及经营风险。；（二）大 |
| s919 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT h.基金代码)=1 | SELECT * FROM (SELECT COUNT(DISTINCT h.基金代码) FROM 基金份额持有人结构 h JOIN 基金基本信息 b ON h |
| s926 | doc | 库内公司但拒答：疑检索未命中或真未披露，须人工对PDF | 资料片段中未提及烟台杰瑞石油服务集团股份有限公司获得过的荣誉称号。 |  |
| s929 | doc | 多问句 | 本次拟发行股份2,000万股，发行后总股本为8,000万股。 | 本次发行前公司总股本为6,000 万股，本次拟发行股份2,000 万股，发行后；总股本为8,000 万股，本次拟发行股份数量占发行后总股本的比例为25.00%。 |
| s935 | sql | 多问句 | 基金简称=建信现金增利货币B，差额=19400369672.31 | SELECT "基金简称", ROUND(ABS("报告期基金总申购份额" - "报告期基金总赎回份额"), 2) AS 差额 FROM 基金规模变动表 WHE |
| s938 | sql | 多表JOIN/CASE：语义风险需人工核 | 单位净值=1.1938，资产净值=68466391.45 | SELECT * FROM (SELECT f."单位净值", f."资产净值" FROM 基金日行情表 f JOIN 基金基本信息 b ON f.基金代码 = |
| s962 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(DISTINCT t1.基金代码)=0 | SELECT * FROM (SELECT COUNT(DISTINCT t1.基金代码) FROM 基金份额持有人结构 t1 JOIN 基金基本信息 t2 O |
| s965 | doc | 多问句 | 公司主要原材料为车用板材（包括冷板、铝板、镀铝板、管件、不锈钢板等），报告期内主要原材料占主营业务成本的比例维持在80% | 公司主要原材料为车用板材，报告期内，车用板材成本占公司主营业务成本的比例平均为8；报告期内公司产品的主要原材料占主营业务成本的比例稳定，维持在80%左右。；其中 |
| s974 | doc | 多问句 | 应收账款净额2008年末、2009年末、2010年末和2011年6月30日分别为13,351万元、18,920万元、20 | 公司应收账款净额2008 年末、2009 年末、2010 年末和2011
年6 ；账款净额占资产总额的比重分别为18%、24%、17%和14%。；公司应收账款净 |
| s977 | sql | 多表JOIN/CASE：语义风险需人工核 | 单位净值=1.0013，资产净值=1752890148.18 | SELECT * FROM (SELECT f."单位净值", f."资产净值" FROM "基金日行情表" f JOIN "基金基本信息" b ON f."基 |
| s989 | sql | 多表JOIN/CASE：语义风险需人工核 | COUNT(*)=0 | SELECT * FROM (SELECT COUNT(*) FROM (SELECT s.股票代码, (MAX(q."收盘价(元)") - MIN(q."收盘 |
| s992 | doc | 多问句 | 报告期内，公司实际持有的罗德精密、鲲彤智能、西安巴比特股权由自然人代为持股，2020年该部分股份代持予以解除。 | 报告期内，公司实际持有的罗德精密、鲲彤智能、西安巴比特股权由自然人代为持股，20 |
| s998 | sql | 多表JOIN/CASE：语义风险需人工核 | 股票代码=002555，股票名称=三七互娱 | SELECT t1."股票代码", t1."股票名称" FROM "基金股票持仓明细" t1 JOIN "基金基本信息" t2 ON t1."基金代码" = t |
