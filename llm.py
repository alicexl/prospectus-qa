"""DeepSeek 生成 + 智谱 embedding-3，均走 openai 兼容 SDK。key 只从环境变量取。"""
import os
import time

from openai import OpenAI

DEEPSEEK_BASE = "https://api.deepseek.com"
ZHIPU_BASE = "https://open.bigmodel.cn/api/paas/v4/"


def _deepseek() -> OpenAI:
    return OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url=DEEPSEEK_BASE)


def _zhipu() -> OpenAI:
    return OpenAI(api_key=os.environ["ZHIPU_API_KEY"], base_url=ZHIPU_BASE)


def chat(system: str, user: str, model: str = "deepseek-chat",
         temperature: float = 0.0, retries: int = 3) -> tuple[str, dict]:
    """返回 (content, usage{input,output})。指数退避重试。"""
    last_err = None
    for i in range(retries):
        try:
            resp = _deepseek().chat.completions.create(
                model=model, temperature=temperature,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}])
            u = resp.usage
            return resp.choices[0].message.content, {"input": u.prompt_tokens, "output": u.completion_tokens}
        except Exception as e:  # noqa: BLE001 限流/网络退避重试
            last_err = e
            time.sleep(2 ** i)
    raise RuntimeError(f"chat failed after {retries} retries") from last_err


def embed(texts: list[str]) -> list[list[float]]:
    """智谱 embedding-3，分批 64，返回与输入等长向量列表。"""
    out: list[list[float]] = []
    for i in range(0, len(texts), 64):
        batch = texts[i:i + 64]
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
