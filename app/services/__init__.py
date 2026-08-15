"""Business logic (service layer).

Everything in this package is plain Python: no FastAPI, no SQLAlchemy, no
network and no clock. That restriction is deliberate — it is what allows the
rules that actually matter (how money is split, what each member owes, who
should pay whom) to be tested exhaustively without any infrastructure
(GUIDE §10.2, NFR-7).
"""
