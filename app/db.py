from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine

from app.config import DATA_DIR

DB_PATH = DATA_DIR / "doc_rag.db"

engine = create_engine(f"sqlite:///{DB_PATH}")


def init_db():
    DATA_DIR.mkdir(exist_ok=True)
    SQLModel.metadata.create_all(engine)
    add_missing_columns()


def add_missing_columns():
    """create_all var olan tabloya sütun eklemez; modele sonradan eklenen sütunlar boş olarak eklenir."""
    inspector = inspect(engine)
    with engine.begin() as conn:
        for table in SQLModel.metadata.sorted_tables:
            existing = {c["name"] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name not in existing:
                    column_type = column.type.compile(engine.dialect)
                    conn.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {column_type}'))


def get_session():
    with Session(engine) as session:
        yield session
