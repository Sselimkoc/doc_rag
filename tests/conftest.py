import os
import tempfile

# Testler gerçek data/ klasörüne dokunmasın; app modülleri içe aktarılmadan önce ayarlanmalı.
os.environ["DOC_RAG_DATA"] = tempfile.mkdtemp(prefix="doc_rag_test_")

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine


@pytest.fixture
def session():
    import app.models  # noqa: F401  (tabloları metadata'ya kaydeder)

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
