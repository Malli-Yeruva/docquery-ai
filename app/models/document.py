"""
Document Metadata Model
=======================

SQLAlchemy database model mapping the metadata of uploaded documents.
"""

from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class Document(Base):
    """
    Metadata representation of an uploaded document in the SQLite DB.
    """

    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False, index=True)
    file_type = Column(String, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    chunk_count = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False, default="processed")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationship to log queries referencing this document
    # We will define this when QueryLog model is defined
    # query_logs = relationship("QueryLog", back_populates="document")
