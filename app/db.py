from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

DATA_DIR = Path("data")
DB_PATH = DATA_DIR / "doc_rag.db"

engine = create_engine(f"sqlite:///{DB_PATH}")


def init_db():
    DATA_DIR.mkdir(exist_ok=True)
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
