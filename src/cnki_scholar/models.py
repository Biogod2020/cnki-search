from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Status = Literal["ok", "blocked", "error"]


class Record(BaseModel):
    title: str
    url: str
    authors: str | None = None
    year: str | None = None
    venue: str | None = None
    kind: str | None = None
    snippet: str | None = None


class SearchResponse(BaseModel):
    status: Status
    provider: Literal["cnki"] = "cnki"
    query: str
    field: str = "theme"
    page: int = 1
    returned_count: int = 0
    records: list[Record] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    elapsed_ms: int | None = None
    error: str | None = None


class RecordDetail(BaseModel):
    status: Status
    provider: Literal["cnki"] = "cnki"
    url: str
    title: str | None = None
    abstract: str | None = None
    institution: str | None = None
    degree: str | None = None
    year: str | None = None
    error: str | None = None
