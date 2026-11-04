# SELFTEST.md：自测报告（P0/P1 逐项可复验）

> 所有命令在仓库根执行；数据集与 `.env`（两把 key）就绪后全部可复现。
> 生成模型：**deepseek-flash + 关思考**（openai 端点 `extra_body thinking disabled`）；embedding：智谱 embedding-3。

## 0. 一键复验入口

```bash
python -X utf8 -m pytest tests/ -v                                          # 26 个测试（含真实数据集成）
python -X utf8 run.py --input questions/selftest.jsonl --output results/answers.jsonl      # 8 道官方自测题
python -X utf8 evaluate.py --answers results/answers.jsonl --labels labels.jsonl           # 五组指标
python -X utf8 run.py --input questions/sample100.jsonl --output results/sample100_answers.jsonl   # 100题压测
```

## 1. P0 必做 · 逐项验证

### P0-1 入库：80 份 PDF 全部解析、表格结构化、跨页合并、三层页码

| 要求 | 复验命令 | 当前结果 |
|---|---|---|
| 80 份全部入库 | `python -X utf8 -c "from ingest import get_conn; print(get_conn().execute('SELECT COUNT(*) FROM docs').fetchone()[0])"` | **80/80**，空公司名 0 |
| 表格结构化保留（行列 JSON） | `python -X utf8 -m pytest tests/test_tables_real.py -v` | PASSED（随机 200 表块全为二维结构，≥2行2列 占比 >80%） |
| 跨页表格合并 | 同上 `test_cross_page_merge_on_real_pdf` | PASSED（真实 PDF 相邻页同表头对 → 合并 + 表头去重 + 数据行并集断言） |
| doc_id + PDF 物理页码 + 印刷页码（含 `1-1-xx`） | `python -X utf8 -m pytest tests/test_pipeline_pages.py -v` | PASSED（doc_id=哈希文件名、物理页码 1..N 连续、印刷页码识别率 ≥90% 且随物理页单调） |
| 印刷页码识别率 | `python -X utf8 -c "from ingest import get_conn; print(get_conn().execute('SELECT ROUND(100.0*SUM(printed_page IS NOT NULL)/COUNT(*),1) FROM pages').fetchone()[0])"` | **87.3%**（未识别集中在无页码扉页/封底，已有全文档一致性修复兜底） |

实据样例（东微 doc）：`pdf_page=3 → printed_page=1-1-2`；p29 募投表 8行×4列 JSON 含 `合计|93,869.10|100.00%`。

### P0-2 问答：单文档事实/数值/列表

复验：§0 第三条命令。当前：q4 事实（股数+比例双值）、q3 数值（93,869.10 万元）、q7 数值+计算（48,902.67 万元，增速 33.2181% vs 原文自披露 33.22%）、q6 列表（22 项带类别）。

### P0-3 引用溯源：doc_id + 页码 + 原文片段逐字可找到

复验（不依赖 run 自报，独立重验全部引用）：

```bash
python -X utf8 -c "
import json
from run import verify_quote
from ingest import get_conn
c = get_conn()
ok = tot = 0
for line in open('results/answers.jsonl', encoding='utf-8'):
    for ct in json.loads(line)['citations']:
        tot += 1
        ok += verify_quote(c, ct)
print(f'{ok}/{tot}')"
```

当前：**8 题非拒答题引用 100% 逐字通过**；quote 校验空间 = 页文本 ∪ 该页表格块（表格区域已从页文本剔除，必须并集）。

### P0-4 拒答：库外公司与未披露信息

复验：`grep 拒答 results/answers.jsonl`（或 evaluate 的拒答 P/R）。当前：q1/q2/q8 库外公司拒答（80 份未覆盖）、q5 未披露拒答（原文即「每股发行价格、人民币【】元」）——**拒答 P/R = 1.0/1.0**。

### P0-5 结构化输出：题目 §4 JSON Schema

复验：

```bash
python -X utf8 -c "
import json, schema
print(sum(1 for l in open('results/answers.jsonl', encoding='utf-8') if schema.AnswerRecord(**json.loads(l))), '/ 8')"
```

当前：**8/8** 全字段过 pydantic 严格校验；命令入口即题目要求的 `python run.py --input --output`。

## 2. P1 进阶 · 逐项验证

### P1-1 意图路由 + SQL 只读安全 + 实体链接

| 要求 | 复验命令 | 当前结果 |
|---|---|---|
| 路由 doc/sql/hybrid/none | 100 题压测：`python -X utf8 -c "import json;from collections import Counter;print(Counter(json.loads(l)['route'] for l in open('results/sample100_answers.jsonl',encoding='utf-8')))"` | sql=60 / doc=40 / none=0 |
| SQL 只读 + 安全校验 | `python -X utf8 -m pytest tests/test_sqlguard.py -v` | PASSED（DELETE/DROP/UPDATE/多语句/ATTACH/PRAGMA/INSERT 全拦截；SELECT 自动强制 LIMIT）+ `mode=ro` 只读连接双保险 |
| 实体链接（自建对照表） | `python -X utf8 -c "from ingest import get_conn; print(get_conn().execute('SELECT COUNT(*) FROM company_registry').fetchone()[0])"` | 236 别名（全称+简称），桥梁=招股书封面公司名 ↔ 行情表名称列（IPO 招股书无股票代码，实测封面全称在第 1~16 页） |
| Text-to-SQL 鲁棒性 | 100 题中 sql 路 60 题 | 执行错误自纠错重试 1 次 + 样例行提示（日期 `'YYYY-MM-DD 00:00:00'` 格式假零已修复：s483 → 2262）；带括号列名双引号包裹 |

### P1-2 数值计算与单位换算（确定性工具，LLM 零心算）

复验：`python -X utf8 -m pytest tests/test_calc.py -v`（含 LLM 吐带逗号字符串数字的强转用例）。
案例：q7 增长率 33.2181%（程序算）vs 原文自披露 33.22%——一致。

### P1-3 长列表完整性

复验：q6（列出全部风险因素按类别）→ `items` 22 项（类别前缀「技术风险-…」）+ 22 条引用覆盖整章 p37-46；条目数=items 长度程序校验；章节定位=行首锚定节标题（防正文引用字样误触发）+ 整章全量召回（非 top-k）。

### P1-4 歧义与多口径

实现于生成约束（run.py `_DOC_SYSTEM` 末条规则）：不同口径须分别给出数值与引用并注明差异。案例：q7 答案明确标注「主营业务收入」口径及其在 p275 财务表的来源（vs 营业收入合计口径）。

### P1-5 自测评估程序

复验：§0 第四条命令。当前 8 题（labels 全部经 PDF 原页人工核对）：

| 指标 | 结果 |
|---|---|
| 数值题准确率（±0.5%） | 1.0 |
| 列表条目 P/R/F1 | 1.0 / 1.0 / 1.0 |
| 引用正确率（独立重验） | 1.0 |
| 拒答 P/R | 1.0 / 1.0 |
| 延迟 avg / P95 | ~1.6s / ~3.2s |
| 单题 tokens in/out | ~1790 / ~150 |

## 3. 100 题压测（question.json 前 100 题，s0~s99）

抽样与重跑：

```bash
python -X utf8 -c "import json;qs=[json.loads(l) for l in open('data/question.json',encoding='utf-8') if l.strip()];open('questions/sample100.jsonl','w',encoding='utf-8').write(''.join(json.dumps({'question_id':'s%d'%q['id'],'question':q['question']},ensure_ascii=False)+chr(10) for q in qs[:100]))"
python -X utf8 run.py --input questions/sample100.jsonl --output results/sample100_answers.jsonl
```

当前结果（100/100 零崩溃）：

| 指标 | 结果 |
|---|---|
| Schema 合规 | 100/100 |
| 引用逐字重验 | 106/106 |
| 答案类型分布 | text=83 / list=12 / number=5 / refusal=0 |
| 路由分布 | sql=60 / doc=40 / none=0（与标签 qtype 100% 一致） |
| 拒答 | 0 条（标签 expect_refusal 亦为 0） |
| 延迟 avg / P95 | 5441 / 4937 ms（中位数 2223；s19 大表 JOIN 慢查询 180s 拉高均值） |
| 平均 in_tokens | 2112 |

与全量标注对照（labels_full.jsonl，全部 auto/cross 验证）：answer_type 97/100 一致，3 处差异：

- s45 三年销售费用：标签 number 但 value.number=None（多值题标签局限），答案内容与标签一致
- s75 年化收益率：数值正确（86.57=人工裁决）但 SQL 列名污染显示 + SQL 路恒 text 类型
- s92 第 6 大重仓股季度涨跌幅：口径错误（MAX-MIN 29.13 vs 人工裁决 -3.06），标注期已知

### 抽样压测揪出并已修复的问题

1. **实体链接失败短路误杀 DB 题**：`answer_one` 里公司匹配不到直接拒答，纯 DB 题（基金/行情/行业）没机会走 sql 路 → 改为先探 SQL hint 再决
2. **路由关键词缺口**：行业分类/成交金额/振幅/港股/股票代码等不在 hint → 补充
3. **SQL 鲁棒性**：多语句/幻觉列名直接崩「处理失败」→ 拆分号取首条 + 执行错误带报错自纠错重试 1 次 + 失败优雅拒答
4. **日期格式假零**：库里日期是 `'2021-03-31 00:00:00'`，LLM 等值匹配静默得 COUNT=0 → schema 卡片附样例行 + prompt 明示前缀 LIKE
5. **flash 关思考**（openai 端点 extra_body）+ LLM 吐带逗号字符串数字强转（`_num`）
6. **检索未命中型误拒**（s922 海外项目金额 / s350 主营业务 / s770 推广阶段产品）：分词 token 低于 FTS5 trigram 3 字下限（海外/项目/金额全是 2 字词，query 退化成「人民币」）+ 年份 token 把财务表格片顶上来 → 最终方案＝**吸收 ragbot 的 scope-then-score**：doc 圈定后内存手写 Okapi BM25（jieba 词级、doc 内 IDF、token 进程缓存 2.2s→0.33s），弃全库 FTS 扫描（trigram OR 全库打分慢一个数量级）；k 8→10
7. **openai SDK 默认超时 600s + 静默重试**：连接悬挂吊死整题 10 分钟 → 显式 timeout=60s + max_retries=0，自管重试兜底（单题最坏 3 分钟后优雅拒答）

### 已知限制（如实披露）

- 100 题标签由确定性流水线 + 交叉验证 + 人工裁决产出，与管线同源——一致性对照反映稳定性而非独立正确性
- 引用正确率评估把 SQL 路零引用答案（s75/s92）按失败计（evaluate 公式要求非拒答须有 citations），实际引用 106/106 逐字全过
- sql 路复杂多表 join 题（如 s92 季度涨跌幅口径）依赖 LLM 生成质量，错误时由自纠错/拒答兜底
