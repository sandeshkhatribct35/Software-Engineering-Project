"""SQLAlchemy ORM models (persistence layer).

Importing this package registers every mapped class with ``Base.metadata``,
which is what allows ``init_db`` to create the full schema.
"""

from app.models.base import Base
from app.models.expense import Expense, ExpenseShare
from app.models.group import Group
from app.models.member import Member
from app.models.settlement import Settlement

__all__ = ["Base", "Expense", "ExpenseShare", "Group", "Member", "Settlement"]
