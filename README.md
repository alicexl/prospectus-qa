# prospectus-qa：金融招股书 + 结构化数据的可溯源问答 Agent

基于 2023 博金大模型挑战赛数据集（80 份招股书 PDF + 1.46GB SQLite 结构化库）构建的可溯源问答系统：**每个答案附引用（doc_id / PDF 物理页码 / 印刷页码 / 逐字原文片段，程序化校验），知识库外与未披露信息明确拒答**。

## 运行环境

- Python 3.12（Anaconda base 即可）
- 依赖：`pip install -r requirements.txt`（pymupdf / pdfplumber / sqlglot / pydantic / openai）
- API key：写入仓库根 `.env`（已 gitignore）：

```
DEEPSEEK_API_KEY=sk-xxx          # platform.deepseek.com 生成，用于生成（deepseek-flash，关思考）
ZHIPU_API_KEY=id.secret          # open.bigmodel.cn 生成，用于向量（embedding-3）
```

## 数据集下载（~2GB，Apache-2.0）

```bash
# 放到仓库根 data/ 下（data/ 已 gitignore，不入库）
git clone --depth 1 https://www.modelscope.cn/datasets/BJQW14B/bs_challenge_financial_14b_dataset.git data
```

下载后目录结构：

```
data/
├── pdf/                  # 80 份招股书 PDF（哈希文件名，扩展名 .PDF）
├── pdf_txt_file/         # 主办方解析 txt（表格为占位符，本题仅辅助）
├── dataset/博金杯比赛数据.db  # SQLite 1.46GB，10 张表（字段名带单位）
└── question.json         # 原比赛 1000 题（无答案）
```

## 复现步骤

```bash
# ① 入库：解析 80 份 PDF → data/knowledge.db（多进程解析，幂等断点续跑，约 30-60 分钟）
python -X utf8 ingest.py

# ② 补 embedding：为全部 chunk 计算向量（智谱 embedding-3，约 20-40 分钟）
python -X utf8 ingest.py --embed-only

# ③ 问答：逐行输出题目 §4 Schema 的 JSON
python -X utf8 run.py --input questions/      # selftest.jsonl(8题) + sample30.jsonl(1000题抽样)
# questions/selftest.jsonl --output results/answers.jsonl

# ④ 评估：五组指标 → results/metrics.json
python -X utf8 evaluate.py --answers results/answers.jsonl --labels labels.jsonl
```

任意 jsonl 输入（每行 `{"question_id": ..., "question": ...}`）均可直接喂给 run.py。

## 所用模型

| 用途 | 模型 | 说明 |
|---|---|---|
| 生成（抽取/判断/Text-to-SQL） | deepseek-flash（关思考） | DeepSeek 官方 API，openai 端点 extra_body thinking disabled |
| 向量检索 | embedding-3 | 智谱 BigModel，2048 维 |

LLM 只在节点内做抽取/判断；**路由、引用逐字校验、单位换算、增长率/比例/合计计算、SQL 安全校验全部为确定性代码**，LLM 零心算。

## 输出格式（题目 §4 Schema）

每行一个 JSON：`question_id / answer / answer_type(number|text|list|refusal) / value{number,unit} / items / citations[{doc_id, pdf_page, printed_page, quote}] / sql / route(doc|sql|hybrid|none) / confidence / latency_ms / tokens{input,output}`，pydantic 严格校验。

## 测试

```bash
python -X utf8 -m pytest tests/ -v    # 26 个测试：纯函数单测 + 真实数据集成测试
```

逐项验证与 1000 题抽样压测报告见 **SELFTEST.md**。覆盖：印刷页码多格式识别（含 1-1-xx）、doc_id/PDF物理页码/印刷页码三层溯源链落库、表格结构化保留、跨页表格合并、SQL 注入拦截、单位换算/增长率、RRF 融合、quote 逐字校验、评估指标。

## 目录说明

```
ingest.py     # 入库管线：PyMuPDF文本 + pdfplumber表格(跨页合并) + FTS5(trigram) + 向量
run.py        # 问答管线：实体链接→路由→doc/sql/hybrid→quote程序化逐字校验→Schema输出
evaluate.py   # 评估：数值准确率/列表PRF1/引用独立重验/拒答PR/延迟成本
label.py      # 标注流水线：题型判定→确定性优先→证据分级→人工复核队列（1000题定标）
schema.py     # 题目§4输出Schema（pydantic）
llm.py        # DeepSeek/智谱 API 封装（key走环境变量/.env）
labels.jsonl  # 8道自测题人工标注（核对PDF原页）
results/      # 交付物：answers.jsonl + metrics.json
spec.md       # 需求与设计基线
design.md     # 设计说明（面向评审）
```

## 已知限制

- 无线框/复杂合并单元格表格的行列还原依赖 pdfplumber lattice 检测，个别表格可能缺列
- 路由为规则优先（关键词），极端措辞可能误路由（sql/hybrid 路会兜底拒答或按文档路处理）
- SQL 路覆盖比赛库 10 张表的只读查询；写操作在 AST 层与只读连接双重拒绝
