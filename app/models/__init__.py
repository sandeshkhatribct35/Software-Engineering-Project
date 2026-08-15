"""SQLAlchemy ORM models (persistence layer).

Importing this package registers every mapped class with ``Base.metadata``,
which is what allows ``init_db`` to create the full schema.
"""

from app.models.base import Base

__all__ = ["Base"]
