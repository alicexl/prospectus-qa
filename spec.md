# 题目 2 项目 Spec：金融招股书 + 结构化数据的可溯源问答 Agent

- 立项日期：2026-11-04
- 交付 deadline：2026-11-05
- 状态：已交付（2026-11-05）
- 题目源：`../question1/question.txt` 题目二
- 仓库：GitHub 公开仓 `alicexl/prospectus-qa`

## 1. 目标与交付物

实现题目二要求的招股书可溯源问答 Agent：P0 五项全做，P1 五项全做；时间落后时按 §9 砍单顺序收缩。

| 交付物 | 说明 |
|---|---|
| 代码仓库 | 入库 + 问答代码，入口 `python run.py --input questions.jsonl --output answers.jsonl` |
| README.md | 运行环境、所用模型、复现命令、**数据集下载方法（modelscope）** |
| results/ | 8 道自测题按题目 §4 Schema 输出的答案 |
| design.md | 简要设计说明（交付物，从本 spec 提炼） |
| spec.md | 本文件（需求与设计基线） |
| labels.jsonl + evaluate.py | 自测题人工标注 + 评估程序（P1.5，入口命令写在 README） |

## 2. 数据与外部依赖

- 数据集：`modelscope.cn/datasets/BJQW14Bbs_challenge_financial_14b_dataset`（Apache-2.0）
  - `pdf/` 80 份招股书 PDF（约 527 MB，文件名为哈希值）；**主信息源**
  - `pdf_txt_file/` 80 份 txt，表格被替换为 `<|TABLE_xxxx_xxxx.xlsx|>` 占位符（仅辅助：用于表格位置交叉验证）
  - `dataset/博金杯比赛数据.db` SQLite 约 1.46 GB，10 张表（基金/持仓/行情/行业/规模/持有人，2019–2021），字段名带单位如 `收盘价(元)`
  - `question.json` 原比赛 1000 题（无答案），用于抽样自测
- 数据放 `data/`，**不进 git**（.gitignore 排除），README 写下载命令
- 模型：DeepSeek 官方 API（生成）+ 智谱 BigModel embedding-3（向量化）；两个 key 走环境变量 `DEEPSEEK_API_KEY` / `ZHIPU_API_KEY`
- 存储：自包含 SQLite（知识库 `knowledge.db` 自建；比赛库只读挂载），零外部服务，pip install 即跑

## 3. 架构总览

```
80份PDF ──ingest.py──> knowledge.db（SQLite 自包含）
                          ├─ docs / pages / blocks / chunks(+FTS5) / tables
                          └─ company_registry（实体链接表）

questions.jsonl ──run.py──> ①实体链接 → ②路由(doc/sql/hybrid/none)
                              ├─ doc路: BM25+向量 RRF检索 → DeepSeek抽取 → quote程序化逐字校验
                              ├─ sql路: schema卡片 → DeepSeek生成SQL → AST安全校验 → 只读执行
                              └─ ③拒答判定(三层)
                            → pydantic校验 → answers.jsonl（题目§4 Schema）

answers.jsonl + labels.jsonl ──evaluate.py──> 全指标报告
```

核心原则：**控制流全部确定性代码，LLM 只在节点内做抽取/判断**。quote 逐字匹配、页码、单位换算、增长率、SQL 安全全部由程序保证，不依赖 LLM 自觉。

## 4. 存储 schema（knowledge.db）

| 表 | 关键字段 | 说明 |
|---|---|---|
| `docs` | doc_id(PK, =PDF哈希文件名), company_name, stock_code, doc_type, page_count | 封面抽取公司全称+股票代码 |
| `pages` | doc_id, pdf_page, printed_page, text | 印刷页码页眉页脚正则识别，支持 `1-1-xx` 格式，识别不到为 null |
| `blocks` | doc_id, pdf_page, block_id, type(heading/paragraph/table), text, table_json | 版面块级结构，表格存行列 JSON |
| `chunks` | chunk_id, doc_id, pdf_page, text, emb(blob) + FTS5 虚表(trigram) | 检索单元：标题感知切分约 500 字；表格整表一个 chunk |
| `company_registry` | alias, doc_id, stock_code | 实体链接：招股书封面自带公司全称+股票代码，与比赛库行情表代码↔名称互为桥梁（题目明说库中无现成对照表，此为自建方案） |

## 5. 入库管线（ingest.py）

1. PyMuPDF 逐页：文本 + 字体信息（字号/加粗 → 标题层级）
2. pdfplumber 表格：lattice 检测 → 行列矩阵；表格 bbox 区域从文本流剔除避免重复入库
3. 印刷页码：页眉/页脚多 pattern 正则（`第x页`、`1-1-xx`、纯数字等）；抽样 20 页人工核对
4. 跨页表格合并：相邻页 + 列数一致 + 表头相似（或「续表」标记）→ 合并逻辑表，记录起始页；citation 引起始页
5. chunk 切分：标题层级感知，段落聚合；表格序列化为 `行头: 值, 值 | ...` 参与检索，原表 JSON 保留在 blocks
6. embedding：智谱 embedding-3 批量算存 blob；中文全文检索用 FTS5 trigram tokenizer
7. 幂等：doc 级断点续跑，已入库 doc 跳过

## 6. 问答管线（run.py，逐题处理）

1. **实体链接**：知识库公司词典（全称+简称）最长匹配 → doc_id；匹配不到（知识库外公司）→ 直接拒答 `route=none, answer_type=refusal`
2. **路由**：规则优先（「基金/持仓/行情/份额/规模变动」且能链到比赛库 → sql/hybrid；「招股书/披露/募集/风险因素」→ doc），规则不决 → 按 doc 路处理（实现无 LLM 兜底，见 design.md 已知限制）
3. **doc 路**：BM25 + 向量余弦 → RRF 融合 top-k → DeepSeek 带 chunk 上下文抽取答案+quote → **quote 程序化逐字校验**（规范化去空白/全半角后 substring 匹配对应页文本；失败换 chunk 重试，仍失败降置信或拒答）
4. **sql 路**：10 张表 schema 卡片（含单位说明）→ DeepSeek 生成 SQL → sqlglot AST 校验（单语句/SELECT-only/强制 LIMIT）→ `file:...?mode=ro` 只读连接执行
5. **数值计算**：LLM 输出结构化计算意图（`{op:"growth",a,b}`、`{op:"sum",unit:"万元",values:[...]}` 等），Python 确定性执行元/万元/亿元换算、增长率、比例、合计；LLM 不做心算
6. **长列表**：「列出全部 X」类 → 标题树定位章节 → 整章全量召回（非 top-k）→ LLM 按小节层级结构化 → `items[]` + 条目数；程序校验计数=items 长度
7. **多口径**：合并报表 vs 母公司报表、不同报告类型/行业分类标准——检索层召回多口径 chunk，prompt 要求分别给出数值与引用并指出差异
8. **拒答三层**：实体链接失败 → refusal；检索置信不足（阈值可调）→ refusal；LLM 判定文中未披露（如招股意向书阶段未定的发行价）→ refusal，answer 字段写明「未披露」及依据；三层统一 `answer_type=refusal`，区分点只在 answer 文案
9. **输出**：pydantic 严格校验题目 §4 Schema（含 `value/unit/items/citations/sql/route/confidence/latency_ms/tokens`）；单题失败重试 3 次后输出 refusal+confidence=0，不中断整批；全程 utf-8 显式 encoding

## 7. 评估（evaluate.py）

- `labels.jsonl`：8 道自测题人工标注；配套标注辅助工具（跑管线输出候选答案+页码原文，人工核对 PDF 原页定稿）
- 指标（入口命令写 README）：
  - 数值题准确率（相对误差 ≤0.5% 记正确）
  - 列表题条目级 Precision / Recall / F1
  - 引用正确率（doc_id + pdf_page + quote 逐字三项全对）
  - 拒答 Precision / Recall
  - 平均与 P95 延迟、单题平均成本（tokens × 单价表）
- `question.json` 1000 题抽样 100 题跑稳定性（防过拟合 8 道自测题），时间不够则砍（见 §9）

## 8. 测试

- 单测：印刷页码多格式正则、跨页表格合并判定、SQL 安全校验（注入样例）、单位换算/增长率、RRF 融合
- E2E：8 道自测题 = 黄金集，用于验收与回归
- 入库质量抽检：随机 20 页人工比对 PDF 原文

## 9. 风险

| 风险 | 对策 |
|---|---|
| 表格解析质量不达标（自测 Q3 直考） | 自测题验证 + 主办方 txt 占位符交叉定位表格；问题文档局部改用 MinerU 单跑 |
| 公开仓含自测标注答案，出题方可搜到 | 用户已确认公开；随时可转私有 |
| 印刷页码怪格式（`1-1-xx` 等） | 多 pattern + 20 页抽检；quote 匹配规范化兜底 |
| 一天半工期，API/解析环节不可控 | 里程碑内置 8 题差距检查点；砍单顺序明确 |
