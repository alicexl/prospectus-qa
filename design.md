# design.md：招股书可溯源问答 Agent 设计说明

## 1. 总体架构

```
80份PDF ──ingest.py──> knowledge.db（SQLite 自包含）
                          ├─ docs / pages / blocks(表格JSON) / chunks(+FTS5 trigram+向量blob)
                          └─ company_registry（实体链接表）

questions.jsonl ──run.py──> ①实体链接 → ②路由(doc/sql/hybrid/none)
                              ├─ doc路: BM25+向量RRF检索(同页表格联动) → DeepSeek抽取 → quote程序化逐字校验
                              ├─ sql路: schema卡片 → DeepSeek生成SQL → sqlglot AST校验 → 只读执行
                              └─ 长列表路: 章节定位 → 整章全量召回 → 结构化 items+条目数
                            → 确定性数值后处理 → pydantic校验 → answers.jsonl

answers.jsonl + labels.jsonl ──evaluate.py──> 五组指标（引用独立重验）
```

核心原则：**控制流全部确定性代码，LLM 只在节点内做抽取/判断**。引用逐字性、页码、单位换算、增长率、SQL 安全全部由程序保证，不依赖 LLM 自觉。

## 2. 关键设计决策

**溯源链（P0#3）**：解析时保留 doc_id（=PDF哈希文件名）+ PDF 物理页码 + 印刷页码（页尾独立行逐行识别 `1-1-xx` 格式，全文档一致性修复：主流格式族 + 组内单调性，封底孤行噪声置空）。quote 校验在「页文本 ∪ 该页表格块」并集上做规范化（全半角/去空白）逐字匹配——表格区域已从页文本剔除，不并表格则表格类引用永远验不过。校验不过的引用直接丢弃；非拒答但引用全灭 → 降级拒答。

**表格处理（P0#1）**：pdfplumber lattice 检测，bbox 从文本流剔除防重复入库；跨页表按「相邻页 + 表头相似（或页末/页首相接同列数无头续表）」合并，blocks 存合并后行列 JSON（结构化保留），chunk 侧：小表整表一片、超长表按行拆片（片内行列完整、每片重复表头行）并拼章节引导句——超长合并表的 embedding 不被全表平均稀释。

**检索（P0#2）**：FTS5 trigram BM25（jieba 分词后 ≥3 字 token；中文不分词则整句成巨型 token 必然落空）+ 智谱 embedding-3 向量余弦 → RRF(k=60) 融合。两个实测大坑及对策：① query 中的公司全称会在向量侧匹配到每页页眉（页页含公司名）挤掉真答案——doc 内检索前剥离公司别名；② 表格数值是文本 chunk 的补充——文本 chunk 入选时同页表格 chunk 自动带上（q3 募投合计即靠此召回）。

**拒答（P0#4）三层**：实体链接失败（公司不在 80 份内，q1/q2/q8）→ refusal；检索置信不足（RRF 阈值）→ refusal；LLM 判定未披露（q5 每股发行价：招股意向书原文即「人民币【】元」）→ refusal。统一 `answer_type=refusal`，区分只在 answer 文案。

**数值计算（P1#2）**：LLM 只输出结构化计算意图（convert/growth/ratio/sum），Python 确定性执行元/万元/亿元换算与增长率。q7 验证：系统计算 2016 营收增长 33.2181%，原文自披露 33.22%——一致。

**实体链接（P1.1）**：IPO 招股书封面无股票代码（未上市），桥梁 = 招股书封面公司全称（扩至前 20 页，个别创业板文档公司名在第 16 页）↔ 比赛库行情表名称列；知识库词典最长匹配（全称或 ≥4 字核心名）。

**长列表（P1.3）**：章节定位用行首锚定的节标题正则（防正文引用「第四节 风险因素」字样误触发），整章全量召回（非 top-k），items 带类别前缀 + 条目数程序校验。q6：22 项/22 引用覆盖风险因素章 p37-46。

**多口径（P1.4）**：prompt 层要求合并/母公司等不同口径分别给数值与引用并注明差异（q7 的营收即标注主营业务收入口径）。

**SQL 路（P1.1）**：10 表 schema 卡片自动生成（字段名自带单位）→ DeepSeek 生成 → sqlglot AST 白名单（单语句/纯 SELECT/无写/DDL/ATTACH/PRAGMA）+ 自动强制 LIMIT 200 + `mode=ro` 只读连接，三层防御。

## 3. 评估结果（8 道自测题，labels 均经 PDF 原页核对）

| 指标 | 结果 |
|---|---|
| 数值题准确率（相对误差≤0.5%） | 1.0 |
| 列表题条目级 P / R / F1 | 1.0 / 1.0 / 1.0 |
| 引用正确率（evaluate 独立重验，非 run 自报） | 1.0 |
| 拒答 Precision / Recall | 1.0 / 1.0 |
| 延迟 avg / P95 | 1572 ms / 3042 ms |
| 单题平均 tokens（in/out） | 1790 / 149 |

复现：`python -X utf8 run.py --input questions/selftest.jsonl --output results/answers.jsonl && python -X utf8 evaluate.py --answers results/answers.jsonl --labels labels.jsonl`

## 4. 测试

25 个测试 = 纯函数单测（页码多格式/跨页合并判定/SQL 注入拦截/单位换算/RRF/quote 校验/评估指标）+ 真实数据集成测试（doc_id/物理页码/印刷页码三层溯源链落库、表格结构化保留、跨页表合并对真实 PDF 验证）。`python -X utf8 -m pytest tests/ -v`

## 5. 已知限制

- 无线框表格的行列还原依赖 lattice 检测，个别复杂合并单元格可能缺列
- 路由为关键词规则（无 LLM 兜底），极端措辞可能误路由（sql/hybrid 有兜底拒答）
- 8 题全指标 1.0 是小样本（题目指定的自测集）；question.json 1000 题抽样评测未在本轮时间盒内执行
