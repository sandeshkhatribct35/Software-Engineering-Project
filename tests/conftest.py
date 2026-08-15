"""Test configuration shared by the whole suite.

The application database URL is redirected to the test database *before* any
application module is imported, because the engine is built at import time.
Tests must never touch the development database: the integration fixtures
truncate every table between tests (GUIDE §13.2).

This module deliberately opens no connection, so the unit tests under
``tests/unit`` run with no database available at all.
"""

import os

DEFAULT_TEST_DATABASE_URL = "postgresql+psycopg://fairshare:fairshare@localhost:5432/fairshare_test"

os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL)
