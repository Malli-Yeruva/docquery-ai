"""
Query Log Model
===============

SQLAlchemy model to store history of user queries, generated answers,
model metadata, and RAG retrieval latency/metrics.
"""

from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, Float, JSON, String

from app.db.database import Base


class QueryLog(Base):
    """
    Saves an audit trail of questions asked, LLM answers generated,
    citations/sources used, and system performance metrics.
    """

    __tablename__ = "query_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    sources = Column(JSON, nullable=True)  # List of source chunk dicts
    model = Column(String, nullable=False)
    query_time_ms = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
