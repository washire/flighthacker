"""
db/base.py
----------
SQLAlchemy declarative base for all database models.

Why this exists:
    All ORM models (User, SavedSearch, PriceHistory, AlertRule) inherit from
    Base defined here. This gives them SQLAlchemy's mapping machinery and
    ensures Alembic can discover them all for migrations.

What it connects to:
    - Every model file in db/models/ imports Base from here.
    - db/session.py uses Base.metadata for table creation.
    - Alembic's env.py imports Base.metadata to generate migrations.

IMPORTANT: import all model modules in db/session.py's init_db() so that
    Alembic can see the tables when generating migrations. If a model isn't
    imported before metadata is inspected, its table won't be created.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Shared base class for all FlightHacker database models.

    Inheriting from this class registers a model with SQLAlchemy's mapping
    system. The table name, columns, and relationships are declared as class
    attributes using SQLAlchemy's mapped_column() API.

    Example:
        from db.base import Base
        from sqlalchemy.orm import mapped_column, Mapped
        from sqlalchemy import String

        class User(Base):
            __tablename__ = "users"
            id: Mapped[str] = mapped_column(String, primary_key=True)
    """
    pass
