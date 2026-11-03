"""题目§4输出Schema——pydantic严格校验。run 产出、evaluate 消费。"""
from typing import Literal

from pydantic import BaseModel, Field

UNIT = Literal["元", "万元", "亿元", "%", "股", None]


class Value(BaseModel):
    number: float | None = None
    unit: UNIT = None


class Citation(BaseModel):
    doc_id: str
    pdf_page: int
    printed_page: str | None = None
    quote: str


class AnswerRecord(BaseModel):
    question_id: str
    answer: str
    answer_type: Literal["number", "text", "list", "refusal"]
    value: Value = Field(default_factory=Value)
    items: list[str] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    sql: str | None = None
    route: Literal["doc", "sql", "hybrid", "none"] = "none"
    confidence: float = 0.0
    latency_ms: int = 0
    tokens: dict[str, int] = Field(default_factory=lambda: {"input": 0, "output": 0})
