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
  │  6 进程并行 parse_pdf（worker 进程）
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
_write_doc 落库（主进程，单事务，doc 级幂等断点续跑）
  ├─ 跨页表格合并   相邻页：表头 ≥60% 相似 / 无头续表同列数相接
  ├─ pages          doc_id + pdf_page + printed_page + text
  ├─ blocks         表格结构化 JSON（溯源页 = 起始页）
  ├─ chunks         标题感知切分 ≤500 字文本片
  │                 表格片：≤1200 字整表一块；超长表 50 行/片（重复表头 + 章节引导句）
  ├─ chunks_fts     FTS5 trigram 全文索引
  └─ company_registry 全称 + 去后缀别名 + MANUAL_ALIASES 手动别名（实体链接数据源）
  ▼
--embed-only：chunks 调智谱 embedding-3（批量 64 × 8 线程，单条 1800 字截断）
  → 2048 维 float32 → emb blob（幂等：只补 emb IS NULL 的 chunk）
```

### 3.2 问答管线（run.py，逐题）

```
question
  ▼
① 实体链接（精确匹配：全称 / 核心名 / 手动别名 ⊆ 题面，最长匹配）
  ├─ 未命中：DB 领域词表命中 → sql 路（schema 卡片 → 生成 SQL → sqlglot 守卫
  │          → 只读执行 → 报错/空结果自纠错 → 列名清洗）——终态
  │          否则 → 拒答（知识库外）——终态
  └─ 命中 doc_id ↓
② 长列表题（题面点名节标题 / 兜底章节表）→ 长列表路：行首锚定定位章节
    → 整章全量召回（非 top-k）→ items + 条目数校验——终态
  │ 否 ↓
③ 规则路由（DB/文档领域词表，doc_id 已锁定时只判 doc/hybrid）
  ├─ doc 路   剥公司名 query → doc 内 BM25(jieba) + 向量余弦 RRF top10
  │           （文本 chunk 入选 → 同页表格 chunk 联动带上）
  │           → DeepSeek 抽取答案 + quote → 页文本 ∪ 表格块逐字校验
  │           （校验不过的引用丢弃；非拒答但引用全灭 → 降级拒答）
  │           → 数值题：计算意图(convert/growth/ratio/sum) Python 确定性重算
  └─ hybrid   doc 路为主 + sql 路结果拼接
  ▼
④ 拒答三层：实体链接失败（无 DB 词）/ 检索置信不足 / LLM 判定未披露
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

**① 实体先行 + 精确链接**。问题：80 份招股书高度同质，全库检索必混入别家公司同类内容；query 里的公司名还会在向量侧匹配到每一页页眉，把真正含答案的 chunk 挤出 top-k。方案：检索前先实体链接锁定 doc，BM25 与向量只在 doc 内打分（全库 trigram 扫描慢一个数量级）。链接只做精确匹配（全称/核心名/手动别名 ⊆ 题面，最长匹配），简称与变体写法靠 `MANUAL_ALIASES` 注册，不做模糊猜测；冷僻公司名是 jieba 未登录词（中海达→中海/达），启动时全部别名 `add_word` 注入词典，链接与 BM25 词级匹配同时受益。附带收益：链接失败=库外，第一层零成本拒答。

**② 表格拆片与双轨召回**。问题：a) 跨页合并后的长表（最长 3866 字）整表一个 chunk 超 embedding 单条上限，且单一向量把具体数值行稀释到检索不到；b) 表格区域从页文本剔除后正文只剩「见下表」引导文，LLM 看不到数值。方案：小表（≤1200 字）整表一片，超长表 50 行/片（每片重复表头 + 章节引导句）；文本 chunk 入选后同页表格 chunk 自动带上——表格是文本的数值补充，页为召回单元。

**③ 引用程序化逐字校验**。问题：LLM 自报引用会幻觉（页码错/引文不在原文），不能靠 prompt 自觉。方案：quote 在「页文本 ∪ 该页表格块」并集上规范化（全半角/去空白）逐字匹配，**校验不过的引用直接丢弃；非拒答但引用全灭 → 降级拒答**。三层页码（doc_id=哈希文件名 / PDF 物理页 / 印刷页含 `1-1-xx`）在解析期固化进每一行。

**④ LLM 零心算**。问题：数值换算/增长率交给 LLM 心算必错且不可复现。方案：LLM 只输出结构化计算意图（convert/growth/ratio/sum），Python 确定性执行；输入数字须来自已验证 quote（q7：系统算 33.2181% vs 原文自披露 33.22%）。同哲学延伸到 SQL 路三层防御（见下）。

**⑤ 拒答三层**。实体链接失败且无 DB 领域词（库外，q1/q2/q8）/ 检索置信不足（RRF 阈值）/ LLM 判定未披露（q5 原文即「人民币【】元」）→ refusal，统一 `answer_type=refusal`，区分只在 answer 文案。

**⑥ 规则路由（领域词表优先）**。问题：题库两类题——文档题与纯 DB 题（基金/持仓/行情/行业，题面无招股书公司名，链接必然落空但不能当库外拒答）。方案：显式词表 `_SQL_WORDS`（24 词）/`_DOC_WORDS`（9 词）；链接落空时命中 DB 词 → sql 优先，双词表齐中 → hybrid。领域词几乎不出现在文档事实题里，误判率很低；词表改动机会少，直接常量 + 增补注释。规则不决的极端措辞可用 LLM 分类兜底，当前未做——误判率已低，每题多一次请求的成本与延迟不划算。

**⑦ 长列表整章召回**。问题：「列出全部 X」类 top-k 检索天然不完整。方案：目标章节名优先题面点名（遍历文档节标题 ⊆ 题面取最长），兜底 `_LIST_FALLBACK` 常量（招股书两大列表章节：风险因素/募投项目）；行首锚定节标题定位（防正文引用误触发）→ 整章全量召回 → items + 条目数程序校验（q6：22 项/22 引用）。实测 101 道 list 题仅 6 题走此路（点名 1 + 兜底 5），其余 95 题由 doc 路覆盖。

**⑧ API 可靠性自管**。问题：openai SDK 默认超时 600s + 静默重试，连接悬挂吊死整题 10 分钟；限流窗约 1 分钟，短退避 5 连败全部撞窗。方案：timeout=60s + max_retries=0 关掉 SDK 隐式重试，自管重试——429 退避 10-60s 并读 Retry-After 头，其他异常 1-16s 快恢复，单题最坏约 3 分钟后优雅拒答。

**SQL 路（P1.1）**：10 表 schema 卡片自动生成（字段名自带单位 + 样例行，日期格式各表不统一须照样例）→ DeepSeek 生成 → sqlglot AST 白名单（单语句/纯 SELECT/无写/DDL/ATTACH/PRAGMA）+ 自动强制 LIMIT 200 + `mode=ro` 只读连接，三层防御。鲁棒性三修：实体链接失败≠拒答（纯 DB 题无文档实体仍走 sql 路）；多语句取首条 + 执行报错/空结果喂回自纠错重试（枚举不完整值、日期格式假零——`'2021-03-31 00:00:00'` 等值匹配曾静默 COUNT=0）；带括号字段名双引号包裹。

## 5. 已知限制

- 无线框表格的行列还原依赖 lattice 检测，个别复杂合并单元格可能缺列
- 路由为领域词表规则（无 LLM 兜底），极端措辞可能误路由（sql/hybrid 有兜底拒答）
- embedding 单条截断 1800 字，超长文本尾部语义不进向量；该上限随 API 而异，换 embedding 服务须重核
- 8 题全指标 1.0 是小样本（题目指定自测集）；100 题压测（s0~s99）Schema 100/100、引用逐字 104/104、误拒 0，与全量标注对照 answer_type 98/100 一致（2 处差异：s75 SQL路恒text类型（列名污染已修）/ s92 口径错误，详见 SELFTEST.md §3）
