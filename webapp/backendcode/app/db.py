from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

DB_URL = os.getenv("DB_URL", "sqlite:///app/storage/skillbot.db")

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Freelancer(Base):
    __tablename__ = "freelancers"
    id = Column(String, primary_key=True)          # همان GUID
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    pdf_path = Column(String, nullable=False)
    md_path = Column(String, nullable=False)
    index_dir = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)
