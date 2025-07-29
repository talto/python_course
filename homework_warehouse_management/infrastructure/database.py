from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

DATABASE_URL = "sqlite:///warehouse.db"
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionFactory = scoped_session(sessionmaker(bind=engine, autoflush=False))
