from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class Document(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    filename: str
    content_type: str
    size: int
    path: str
    status: str = "uploaded"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # Silinen belge veritabanında kalır; listede ve aramada görünmez.
    is_deleted: bool = False


def not_deleted():
    # Sütun sonradan eklendiği için eski satırlarda NULL olabilir.
    return Document.is_deleted.is_not(True)


class Page(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="document.id", index=True)
    number: int
    text: str


class Chunk(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="document.id", index=True)
    page: int
    position: int
    text: str
    kind: str  # text | table
    source: str  # text (metin katmanı) | ocr
    section: str | None = None  # parçanın başladığı yerdeki son başlık


class Embedding(SQLModel, table=True):
    chunk_id: int = Field(foreign_key="chunk.id", primary_key=True)
    document_id: int = Field(foreign_key="document.id", index=True)
    model: str
    vector: bytes  # float32, birim uzunlukta
