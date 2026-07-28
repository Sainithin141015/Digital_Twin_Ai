from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    profile = relationship("Profile", back_populates="user", uselist=False,
                            cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="user",
                                  cascade="all, delete-orphan")


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    age = Column(Integer, nullable=True)
    occupation = Column(String(120), nullable=True)
    goals = Column(JSON, default=dict)        # e.g. {"save_target": 50000, "gpa_target": 8.5}
    preferences = Column(JSON, default=dict)  # e.g. {"currency": "INR", "study_hours_target": 4}

    user = relationship("User", back_populates="profile")


class ActivityLog(Base):
    """
    Unified event feed. Every module (finance, study, habits, simulation, chat)
    writes a row here whenever something meaningful happens. This becomes the
    single source of 'historical behavioral data' the later modules read from.
    """
    __tablename__ = "activity_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    module = Column(String(50), nullable=False)   # "finance" | "study" | "habit" | "simulation" | "chat"
    action = Column(String(100), nullable=False)  # e.g. "transaction_created", "study_session_logged"
    payload = Column(JSON, default=dict)          # arbitrary details about the event
    timestamp = Column(DateTime(timezone=True), default=utcnow, index=True)

    user = relationship("User", back_populates="activity_logs")
