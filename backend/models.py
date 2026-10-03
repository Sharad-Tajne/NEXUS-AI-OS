from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    JSON,
    ForeignKey
)

from sqlalchemy.orm import relationship

from datetime import datetime

from database import Base


# ============================================================
# KNOWLEDGE
# ============================================================

class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    title = Column(
        String(200),
        nullable=False
    )

    content = Column(
        Text,
        nullable=False
    )

    category = Column(
        String(100),
        default="general"
    )

    source = Column(
        String(200),
        nullable=True
    )

    embedding = Column(
        JSON,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


# ============================================================
# PROJECT
# ============================================================

class Project(Base):
    __tablename__ = "projects"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(200),
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    technology = Column(
        String(500),
        nullable=True
    )

    status = Column(
        String(50),
        default="active"
    )

    progress = Column(
        Integer,
        default=0
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    tasks = relationship(
        "Task",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    notes = relationship(
        "Note",
        back_populates="project",
        cascade="all, delete-orphan"
    )


# ============================================================
# TASK
# ============================================================

class Task(Base):
    __tablename__ = "tasks"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    title = Column(
        String(300),
        nullable=False
    )

    completed = Column(
        Integer,
        default=0
    )

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=True,
        index=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    project = relationship(
        "Project",
        back_populates="tasks"
    )


# ============================================================
# NOTES
# ============================================================

class Note(Base):
    __tablename__ = "notes"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    title = Column(
        String(200),
        nullable=False
    )

    content = Column(
        Text,
        nullable=False
    )

    category = Column(
        String(100),
        default="General"
    )

    tags = Column(
        String(500),
        nullable=True
    )

    pinned = Column(
        Integer,
        default=0
    )

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=True,
        index=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    project = relationship(
        "Project",
        back_populates="notes"
    )