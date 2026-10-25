"""
DB engine/session.

Local dev (no DATABASE_URL set): SQLite file, zero setup.
Production (Render + Supabase): set the DATABASE_URL env var to the
Supabase connection string from Part 3.3 of DEPLOYMENT_GUIDE.md, e.g.

    postgresql://postgres.xxxx:PASSWORD@aws-0-ap-south-1.pooler.supabase.com:6543/postgres

No application code needs to change to switch between the two — only
this environment variable.
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fieldly_dev.db")
if DATABASE_URL.startswith("postgres://"):   # some providers still hand out the old scheme
    DATABASE_URL = "postgresql://" + DATABASE_URL[len("postgres://"):]

# Supabase's pooled connection string uses "postgresql://"; SQLAlchemy's
# psycopg2 driver understands that scheme directly, so no rewrite needed.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

pool_args = {} if DATABASE_URL.startswith("sqlite") else {"pool_size": 5, "max_overflow": 2, "pool_recycle": 300}  # small: free-tier DB connection limits
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True, **pool_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
