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
