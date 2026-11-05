# design.md：招股书可溯源问答 Agent 设计说明

## 1. 目标与交付物

实现题目二的招股书可溯源问答 Agent：对 80 份招股书与比赛数据库的任意提问，输出题目 §4 Schema 的答案，每个答案附可逐字回溯的引用（doc_id / PDF 物理页码 / 印刷页码 / 原文片段），知识库外与未披露信息明确拒答。

| 交付物 | 说明 |
|---|---|
| 代码仓库 | 入库 + 问答代码，入口 `python run.py --input questions.jsonl --output answers.jsonl` |
| README.md | 运行环境、所用模型、复现命令、数据集下载方法 |
| results/ | 自测题按题目 §4 Schema 输出的答案 |
| design.md | 本文件（简要设计说明） |
| labels.jsonl + evaluate.py | 自测题人工标注 + 评估程序（P1.5） |

## 2. 数据与外部依赖

- 数据集：modelscope `BJQW14B/bs_challenge_financial_14b_dataset`（Apache-2.0）
  - `pdf/` 80 份招股书 PDF（哈希文件名）；**主信息源**
  - `pdf_txt_file/` 80 份 txt，表格为占位符（仅辅助：表格位置交叉验证）
  - `dataset/博金杯比赛数据.db` SQLite 1.46GB，10 张表（基金/持仓/行情/行业/规模/持有人，2019–2021），字段名带单位如 `收盘价(元)`
  - `question.json` 原比赛 1000 题（无答案）
- 模型：DeepSeek deepseek-flash（生成，关思考）+ 智谱 embedding-3（2048 维向量）；key 走 `.env`
- 存储：自包含 SQLite（knowledge.db 自建；比赛库只读挂载），零外部服务

## 3. 总体架构

```
80份PDF ──ingest.py──> knowledge.db（SQLite 自包含）
                          ├─ docs / pages / blocks(表格JSON) / chunks(向量blob；BM25为doc内内存打分)
                          └─ company_registry（实体链接表 + jieba别名词典源）

questions.jsonl ──run.py──> ①实体链接 → ②路由(doc/sql/hybrid/none)
                              ├─ doc路: 实体锁定doc→内存BM25(jieba)+向量RRF(同页表格联动) → DeepSeek抽取 → quote程序化逐字校验
                              ├─ sql路: schema卡片 → DeepSeek生成SQL → sqlglot AST校验 → 只读执行
                              └─ 长列表路: 章节定位 → 整章全量召回 → 结构化 items+条目数
                            → 确定性数值后处理 → pydantic校验 → answers.jsonl

answers.jsonl + labels.jsonl ──evaluate.py──> 五组指标（引用独立重验）
```

核心原则：**控制流全部确定性代码，LLM 只在节点内做抽取/判断**。引用逐字性、页码、单位换算、增长率、SQL 安全全部由程序保证，不依赖 LLM 自觉。

### 3.1 PDF 入库管线（ingest.py）

```
80份 PDF（哈希文件名，.PDF）
  │  6 进程并行 parse_pdf
  ▼
单 PDF 解析
  ├─ PyMuPDF      页文本（表格 bbox 区域剔除，防重复入库）
  ├─ pdfplumber   lattice 表格检测 → 行列矩阵
  └─ 印刷页码     页首/页尾各 2 行 × 多 pattern 正则（含 1-1-xx）
  ▼
印刷页码全文档一致性修复（主流格式族 + 组内单调，孤值噪声置 None）
  ▼
封面元数据抽取（公司全称 + 股票代码，前 20 页）
  ▼
跨页表格合并（相邻页：表头 ≥60% 相似 / 无头续表同列数相接）
  ▼
_write_doc 落库（单事务，doc 级幂等断点续跑）
  ├─ pages           doc_id + pdf_page + printed_page + text
  ├─ blocks          表格结构化 JSON（溯源页 = 起始页）
  ├─ chunks          标题感知切分 ≤500 字文本片
  │                  表格片：≤1200 字整表一块；超长表 50 行/片（重复表头 + 章节引导句）
  ├─ chunks_fts      FTS5 trigram 全文索引
  └─ company_registry 全称 + 去后缀别名注册（实体链接数据源）
  ▼
--embed-only：chunks 调智谱 embedding-3（批量 64 × 8 线程，单条 1800 字截断）
  → 2048 维 float32 → emb blob（幂等：只补 emb IS NULL 的 chunk）
```

### 3.2 问答管线（run.py，逐题）

```
question
  ▼
① 实体链接（四级：全称 → 核心名 → 词组 n-gram → 标点界定短 run；
    题面含完整公司名形态时只信①级精确匹配）
  ├─ 命中 doc_id ─────────────────────────┐
  └─ 未命中 ── SQL 关键词？─ 有 → sql 路   │
              └─ 无 → 拒答（80 份未覆盖）  │
  ▼                                      │
② 规则路由（关键词，无 LLM 兜底）          │
  ├─ doc 路   剥公司名 query → doc 内 BM25(jieba) + 向量余弦 RRF top10
  │           （文本 chunk 入选 → 同页表格 chunk 联动带上）
  │           → DeepSeek 抽取答案 + quote → 页文本 ∪ 表格块逐字校验
  │           （校验不过的引用丢弃；非拒答但引用全灭 → 降级拒答）
  │           → 数值题：计算意图(convert/growth/ratio/sum) Python 确定性重算
  ├─ sql 路   schema 卡片（字段 + 样例行）→ DeepSeek 生成 SQL
  │           → sqlglot 白名单 + 强制 LIMIT 200 → mode=ro 只读执行
  │           → 报错/空结果喂回自纠错（≤2 轮）→ 列名 >20 字清洗展示
  ├─ hybrid   doc 路为主 + sql 路结果拼接
  └─ 长列表路 行首锚定节标题 → 整章全量召回（非 top-k）→ items + 条目数程序校验
  ▼
③ 拒答三层：实体链接失败 / 检索置信不足 / LLM 判定未披露
  ▼
pydantic §4 Schema 校验 → 逐行写 answers.jsonl（单题异常 → refusal，不中断整批）
```

### 3.3 存储 schema（knowledge.db）

| 表 | 关键字段 | 说明 |
|---|---|---|
| `docs` | doc_id(PK, =PDF哈希文件名), company_name, stock_code, doc_type, page_count | 封面抽取公司全称+股票代码 |
| `pages` | doc_id, pdf_page, printed_page, text | 印刷页码多 pattern 识别（含 `1-1-xx`），识别不到为 null |
| `blocks` | doc_id, pdf_page, block_id, type, text, table_json | 表格结构化落位（行列 JSON），跨页合并后以起始页溯源 |
| `chunks` | chunk_id, doc_id, pdf_page, text, emb(blob) + FTS5 虚表(trigram) | 检索单元：标题感知 ~500 字文本片；表格整表/超长拆片 |
| `company_registry` | alias, doc_id, stock_code | 实体链接：封面公司名 ↔ 比赛库行情表名称列互为桥梁（库中无现成对照表，自建方案） |

## 4. 关键设计决策（问题驱动：每条先说解决什么问题）

**① 实体先行（scope-then-score）**。问题：80 份招股书内容高度同质（每份都有募集资金/风险因素/财务报表），全库检索必然把别家公司的同类内容混进上下文，且 query 里的公司全称会在向量侧匹配到**每一页的页眉**（页页含公司名），把真正含答案的 chunk 挤出 top-k。方案：任何检索前先实体链接锁定 doc，检索只在 doc 内做（BM25 也在 doc 内打分，不做全库扫描——全库 trigram 打分还慢一个数量级）。附带收益：链接失败=库外，构成第一层**零成本拒答**。链接只做**精确匹配**（全称/核心名/手动别名 ⊆ 题面，最长匹配）；简称与变体写法靠 `MANUAL_ALIASES` 显式注册（海看网络科技（山东）↔山东海看网络科技、广州中海达↔中海达等 5 组）。曾试过 n-gram 猜测救济（四级链接）后移除——猜错比拒答更糟（「湖南长远锂业」曾误链「湖南长远锂科」，q8 复现教训）；全量标注验证精确匹配+别名版 100 题一致性 97/100 反超四级版 96/100，代码还少 40 行。

**② 公司别名词典注入 jieba**。问题：冷僻公司名是未登录词，jieba 按 HMM 切碎（中海达→中海/达、真兰仪表→真兰/仪表），实体链接与 BM25 的词级匹配双双失效。方案：启动时把 80 家公司全部别名 `add_word` 注入词典（高词频保证成词）。效果：全名在链接与检索中都成整词；非全名子串类简称由四级链接兜底。

**③ 大表格拆片存储**。问题：跨页合并后的长表（实测最长 3866 字）整表一个 chunk 会：a) 超出 embedding 单条输入上限直接 400；b) 即使不超，整表平均出的单一向量把具体数值行的信号稀释到检索不到（募投合计行淹没在全表里）。方案：小表（≤1200 字）整表一片；超长表按行拆片（50 行/片），**每片重复表头行 + 拼章节引导句**，片内行列完整。效果：每片向量聚焦且自带表头语义，q3 募投合计行可被直接召回。

**④ 表格与正文双轨入库 + 同页联动**。问题：表格区域从页文本剔除后（防重复入库），页文本里只剩「见下表」类引导文，答案数值在表格 chunk 里而检索只召回文本 chunk 时 LLM 看不到数。方案：文本 chunk 入选后，同页的表格 chunk 自动带上——表格是文本的数值补充，页为召回单元。

**⑤ 引用溯源的程序化保证**。问题：LLM 自报的引用会幻觉（页码错/引文不在原文），不能靠 prompt 自觉。方案：quote 在「页文本 ∪ 该页表格块」并集上做规范化（全半角/去空白）逐字匹配，**校验不过的引用直接丢弃；非拒答但引用全灭 → 降级拒答**。「逐字可找到」由程序保证而非模型自觉。三层页码（doc_id=哈希文件名 + PDF 物理页码 + 印刷页码含 `1-1-xx`，全文档一致性修复剔除封底孤行噪声）在解析期就固化进每一行。

**⑥ LLM 零心算**。问题：数值换算/增长率交给 LLM 心算必错且不可复现。方案：LLM 只输出结构化计算意图（convert/growth/ratio/sum），Python 确定性执行；输入数字须来自已验证 quote（q7：系统算 33.2181% vs 原文自披露 33.22%）。同哲学延伸到 SQL 路：sqlglot AST 白名单 + 强制 LIMIT + 只读连接三层防御，LLM 只写查询不碰执行。

**⑦ 拒答三层**。实体链接失败（库外，q1/q2/q8）→ refusal；检索置信不足（RRF 阈值）→ refusal；LLM 判定未披露（q5 每股发行价原文即「人民币【】元」）→ refusal。统一 `answer_type=refusal`，区分只在 answer 文案。

**⑧ 长列表整章召回**。问题：「列出全部 X」类问题 top-k 检索天然不完整。方案：行首锚定的节标题正则定位章节（防正文引用「第四节 风险因素」字样误触发），整章全量召回（非 top-k），items 带类别前缀 + 条目数程序校验（q6：22 项/22 引用覆盖 p37-46 整章）。

**⑨ 多口径显式标注**。prompt 层要求合并报表/母公司报表等不同口径分别给数值与引用并注明差异（q7 答案标注「主营业务收入」口径及来源页）。

**⑩ API 可靠性自管**。问题：openai SDK 默认超时 600s + 静默重试，连接悬挂会吊死整题 10 分钟；DeepSeek 限流窗约 1 分钟，短退避 5 连败全部撞窗。方案：timeout=60s + max_retries=0 关掉 SDK 隐式重试，自管重试——429 限流退避 10-60s 并读 Retry-After 头，其他异常 1-16s 快恢复，单题最坏约 3 分钟后优雅拒答，不拖垮整批。

**SQL 路（P1.1）**：10 表 schema 卡片自动生成（字段名自带单位 + 样例行，日期格式各表不统一须照样例）→ DeepSeek 生成 → sqlglot AST 白名单（单语句/纯 SELECT/无写/DDL/ATTACH/PRAGMA）+ 自动强制 LIMIT 200 + `mode=ro` 只读连接，三层防御。鲁棒性三修：实体链接失败≠拒答（纯 DB 题无文档实体仍走 sql 路）；多语句取首条 + 执行报错/空结果喂回自纠错重试（枚举不完整值、日期格式假零——`'2021-03-31 00:00:00'` 等值匹配曾静默 COUNT=0）；带括号字段名双引号包裹。

## 5. 已知限制

- 无线框表格的行列还原依赖 lattice 检测，个别复杂合并单元格可能缺列
- 路由为关键词规则（无 LLM 兜底），极端措辞可能误路由（sql/hybrid 有兜底拒答）
- 8 题全指标 1.0 是小样本（题目指定自测集）；100 题压测（s0~s99）Schema 100/100、引用逐字 105/105、误拒 0，与全量标注对照 answer_type 97/100 一致（3 处差异：s97 类型口径波动 / s75 SQL路恒text类型（列名污染已修）/ s92 口径错误，详见 SELFTEST.md §3）
