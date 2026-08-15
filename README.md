# FairShare API

A REST service for tracking shared group expenses and working out the **minimum
set of payments** needed to settle everybody up.

When friends share costs — a trip, a flat, a group purchase — the awkward part is
not recording who paid, it is working out what to do about it. FairShare records
every shared expense with its exact split, keeps each member's net balance, and
turns those balances into the smallest practical list of payments.

Software Engineering lab project — solo. The specification this project is built
against is [`GUIDE.md`](GUIDE.md).

---

## What it does

- **Groups and members** — create a group, add the people in it.
- **Two ways to split** — divide an expense **equally**, or give an **exact**
  amount per person. Either way the shares add up to the expense to the last
  paisa: ₹1000 between three people becomes 333.34 + 333.33 + 333.33.
- **Net balances** — one number per person: positive if the group owes them,
  negative if they owe the group. The balances of a group always sum to zero.
- **Settlement plan** — the largest debtor pays the largest creditor until
  everyone is square. A group of *n* people never needs more than *n − 1*
  payments, so circular debts (A owes B owes C owes A) cost nothing to clear.
- **Settlements** — record a payment that actually happened; balances update.
- **Group summary** — total spend and per-member paid/owed totals.

Deliberately **not** included: authentication, a frontend, multi-currency
conversion. See §4.2 of [`GUIDE.md`](GUIDE.md) for why.

## Technology

Python 3.12 · FastAPI · SQLAlchemy 2 · Pydantic v2 · PostgreSQL 16 · pytest ·
Ruff · Docker Compose · GitHub Actions.

Money is a `Decimal` in Python, `NUMERIC(12,2)` in PostgreSQL and a **string** in
JSON. Floating point is never used for money anywhere in the project.

---

## Quick start with Docker

The only requirement is Docker.

```bash
docker compose up --build -d
curl http://localhost:8000/
```

```json
{ "status": "ok", "service": "fairshare-api", "version": "1.0.0" }
```

Then open the interactive documentation at **http://localhost:8000/docs**.

Stop and remove everything, including the database volume:

```bash
docker compose down -v
```

## Running locally without Docker

A PostgreSQL server is still needed; the easiest way is the database container
from the Compose file (`docker compose up -d db`).

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # Linux / macOS

pip install -r requirements-dev.txt
cp .env.example .env              # optional; defaults already point at localhost
uvicorn app.main:app --reload
```

## Running the tests

```bash
# Unit tests only — pure logic, no database needed
pytest tests/unit

# Everything, including the API tests against PostgreSQL
pytest

# With a coverage report
pytest --cov=app --cov-report=term-missing --cov-report=html
start htmlcov/index.html          # Windows
```

The integration tests need a database called `fairshare_test`:

```bash
docker compose exec db psql -U fairshare -d fairshare -c "CREATE DATABASE fairshare_test;"
```

Point them elsewhere with `TEST_DATABASE_URL` if you prefer.

## Linting

```bash
ruff check .
ruff format --check .
```

---

## API documentation

| Format | URL |
|---|---|
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| OpenAPI schema | http://localhost:8000/openapi.json |
| Written reference | [`docs/API.md`](docs/API.md) |

The documentation is generated from the source code, so it cannot drift out of
date. Regenerate the committed schema snapshot with:

```bash
python scripts/export_openapi.py
```

### Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Health check |
| POST | `/api/v1/groups` | Create a group |
| GET | `/api/v1/groups` | List groups |
| GET | `/api/v1/groups/{group_id}` | Group detail with members |
| PATCH | `/api/v1/groups/{group_id}` | Rename / redescribe a group |
| DELETE | `/api/v1/groups/{group_id}` | Delete a group and its data |
| POST | `/api/v1/groups/{group_id}/members` | Add a member |
| GET | `/api/v1/groups/{group_id}/members` | List members |
| DELETE | `/api/v1/groups/{group_id}/members/{member_id}` | Remove an uninvolved member |
| POST | `/api/v1/groups/{group_id}/expenses` | Record an expense |
| GET | `/api/v1/groups/{group_id}/expenses` | List expenses (paginated) |
| GET | `/api/v1/expenses/{expense_id}` | Expense detail with shares |
| DELETE | `/api/v1/expenses/{expense_id}` | Delete an expense |
| GET | `/api/v1/groups/{group_id}/balances` | Net balance per member |
| GET | `/api/v1/groups/{group_id}/settlement-plan` | Minimal payment plan |
| POST | `/api/v1/groups/{group_id}/settlements` | Record a payment |
| GET | `/api/v1/groups/{group_id}/settlements` | List payments |
| GET | `/api/v1/groups/{group_id}/summary` | Group totals |

Every failure returns the same shape:

```json
{ "detail": "Group 7 does not exist", "code": "GROUP_NOT_FOUND" }
```

---

## How the code is organised

```text
app/
├── routers/        HTTP only — routing, status codes, response building
├── schemas/        Pydantic request and response contracts
├── services/       Business logic: splitting, balances, settlement planning
├── repositories/   Every SQL statement in the project
├── models/         SQLAlchemy tables and constraints
├── errors.py       Domain exceptions, each carrying its status and code
├── config.py       Settings read from the environment
└── main.py         Application, error handlers, router registration
```

The rule that holds it together: **`services/` imports no framework and no
database.** All the logic worth testing hard — how an odd paisa is allocated,
what each member's balance is, who should pay whom — is plain Python, so it is
tested directly, without HTTP or a database in the way.

## Continuous integration

`.github/workflows/ci.yml` runs on every push and pull request:

- **test** — lint, formatting check, then the full suite against a PostgreSQL
  service container, failing the build if coverage falls below 90%. The coverage
  report is uploaded as a downloadable artifact.
- **docker** — builds the image, starts the Compose stack, calls the API and
  tears it down.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://fairshare:fairshare@localhost:5432/fairshare` | Application database |
| `TEST_DATABASE_URL` | same host, `fairshare_test` database | Database used by the tests |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `ECHO_SQL` | `false` | Echo generated SQL when debugging |

No credentials are committed; `.env` is git-ignored and `.env.example` documents
the variables with local development values only.

## Project documentation

- [`GUIDE.md`](GUIDE.md) — the specification this project is built against
- [`docs/API.md`](docs/API.md) — endpoint reference with examples
- [`PROJECT_NOTES.md`](PROJECT_NOTES.md) — factual record of how it was built
