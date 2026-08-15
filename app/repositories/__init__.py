"""Database access (repository layer).

Every SQL statement in the application lives in this package. Routers never
build queries themselves, which keeps persistence details out of the HTTP layer
and makes the queries easy to find when they need tuning (GUIDE §10.2).
"""
