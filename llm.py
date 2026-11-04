"""DeepSeek 生成 + 智谱 embedding-3，均走 openai 兼容 SDK。key 从环境变量取，
缺省回落到仓库根 .env（已 gitignore）。"""
import os
import time
from pathlib import Path

from openai import OpenAI

DEEPSEEK_BASE = "https://api.deepseek.com"
ZHIPU_BASE = "https://open.bigmodel.cn/api/paas/v4/"


def _load_dotenv() -> None:
    p = Path(__file__).parent / ".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_dotenv()


def _deepseek() -> OpenAI:
    return OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url=DEEPSEEK_BASE)


def _zhipu() -> OpenAI:
    return OpenAI(api_key=os.environ["ZHIPU_API_KEY"], base_url=ZHIPU_BASE)


def chat(system: str, user: str, model: str = "deepseek-flash",
         temperature: float = 0.0, retries: int = 3) -> tuple[str, dict]:
    """返回 (content, usage{input,output})。指数退避重试。
    flash 默认带思考（completion 里灌 ~100 tok 思考内容），openai 端点用
    extra_body thinking disabled 关闭（ragbot anthropic 端点同款语义）。"""
    last_err = None
    extra = {"extra_body": {"thinking": {"type": "disabled"}}} if "flash" in model else {}
    for i in range(retries):
        try:
            resp = _deepseek().chat.completions.create(
                model=model, temperature=temperature,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}], **extra)
            u = resp.usage
            return resp.choices[0].message.content, {"input": u.prompt_tokens, "output": u.completion_tokens}
        except Exception as e:  # noqa: BLE001 限流/网络退避重试
            last_err = e
            time.sleep(2 ** i)
    raise RuntimeError(f"chat failed after {retries} retries") from last_err


def embed(texts: list[str]) -> list[list[float]]:
    """智谱 embedding-3，分批 64，返回与输入等长向量列表。
    单条截断 1800 字（超长合并表 chunk 会 400），空串以占位符替代。"""
    out: list[list[float]] = []
    for i in range(0, len(texts), 64):
        batch = [(t or "空")[:1800] for t in texts[i:i + 64]]
        for attempt in range(3):
            try:
                resp = _zhipu().embeddings.create(model="embedding-3", input=batch)
                out.extend(d.embedding for d in resp.data)
                break
            except Exception:  # noqa: BLE001
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
    return out


def embed_parallel(texts: list[str], workers: int = 8) -> list[list[float]]:
    """并发版 embed：HTTP 密集型，线程池提速（134k chunks 串行要数小时）。"""
    from concurrent.futures import ThreadPoolExecutor

    batches = [(i, texts[i:i + 64]) for i in range(0, len(texts), 64)]
    out: dict[int, list[float]] = {}

    def _run(b):
        return b[0], embed(b[1])

    with ThreadPoolExecutor(workers) as ex:
        for start, vecs in ex.map(_run, batches):
            for j, v in enumerate(vecs):
                out[start + j] = v
    return [out[k] for k in range(len(texts))]
