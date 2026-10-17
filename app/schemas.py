from datetime import datetime

from pydantic import BaseModel, Field


class DocumentSummary(BaseModel):
    id: int
    filename: str
    content_type: str
    size: int
    status: str
    created_at: datetime
    page_count: int
    ocr_page_count: int  # en az bir parçası OCR'dan gelen sayfalar


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    k: int = Field(default=8, ge=1, le=50)
    document_ids: list[int] | None = None  # None: bütün belgeler


class AnswerRequest(BaseModel):
    question: str = Field(min_length=1)
    document_ids: list[int] | None = None


class Citation(BaseModel):
    chunk_id: int
    document_id: int
    filename: str
    page: int
    quote: str


class SearchResult(BaseModel):
    chunk_id: int
    document_id: int
    filename: str
    page: int
    section: str | None
    kind: str
    source: str
    score: float
    text: str


class AnswerResponse(BaseModel):
    answered: bool
    answer: str
    # no_sources: ilgili parça yok | not_in_sources: model kaynaklarda bulamadı | unverified: alıntı kaynakta yok
    refusal: str | None
    citations: list[Citation]
    unverified_quotes: int
    sources: list[SearchResult]
