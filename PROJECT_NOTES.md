# PROJECT_NOTES.md

**Factual record of how the FairShare API was built.**

This file is raw material for the written report — dates, numbers, commands and
verified results. It is **not** the report itself. Every figure here was measured
from the actual project; nothing is estimated.

- **Project:** FairShare API — group expense sharing and settlement service
- **Author:** Sandesh Khatri (solo)
- **Repository:** https://github.com/sandeshkhatribct35/Software-Engineering-Project
- **Built on:** 15–16 August 2026
- **Specification:** `GUIDE.md` in the repository root

---

## 1. Project introduction

FairShare is a REST API for groups of people who share expenses — flatmates,
friends on a trip, classmates buying equipment. It records who paid for what and
how the cost is divided, keeps a running net balance for every member, and
computes the smallest practical set of payments that clears all debts.

Three problems motivated it:

1. **Splitting is not clean division.** ₹1000 between three people is 333.333…
   Money must not be lost or invented, so the remainder has to go somewhere
   explicit. FairShare gives it to the lowest member id and guarantees the shares
   sum to the exact total.
2. **People track individual debts, not net position.** If A owes B, B owes C and
   C owes A, nothing actually needs to be paid. Net balances make that visible.
3. **Too many payments.** Settling each debt separately means many transfers.
   The planner reduces a group of *n* members to at most *n − 1* payments.

Scope was kept deliberately narrow (no authentication, no frontend, no currency
conversion) so the engineering practices — testing, containerisation, CI,
documentation — could be done properly rather than partially.

---

## 2. Technologies used

| Layer | Technology | Version | Why |
|---|---|---|---|
| Language | Python | 3.12 | Same version locally, in Docker and in CI |
| Web framework | FastAPI | 0.141.1 | Generates OpenAPI docs from the code itself |
| ASGI server | Uvicorn | 0.52.3 | Standard server for FastAPI |
| Validation | Pydantic | 2.13.4 | Declarative validation with `Decimal` support |
| Settings | pydantic-settings | 2.15.0 | Typed configuration from environment variables |
| ORM | SQLAlchemy | 2.0.52 | Explicit constraints, typed models |
| DB driver | psycopg | 3.3.4 | Current PostgreSQL adapter, native 3.12 wheels |
| Database | PostgreSQL | 16-alpine | `NUMERIC` fixed-point arithmetic, real constraints |
| Testing | pytest | 9.1.1 | Fixtures, parametrisation |
| Coverage | pytest-cov | 7.1.0 | Line and branch coverage |
| Test client | httpx via Starlette TestClient | 0.28.1 | Real HTTP requests in integration tests |
| Lint + format | Ruff | 0.16.3 | One tool for both, enforced in CI |
| Containers | Docker + Compose | 29.6.1 | Reproducible stack |
| CI | GitHub Actions | — | Lint, test, coverage gate, image build |

**Key technical decision:** money is a `Decimal` in Python, `NUMERIC(12,2)` in
PostgreSQL and a **string** in JSON. Binary floating point cannot represent
values like 0.10 exactly, and rounding errors in money are not acceptable.

---

## 3. Architecture

Five layers with a strict one-directional dependency rule:

```
routers/        HTTP: routing, status codes, response building
schemas/        Pydantic request and response contracts
services/       Business logic — PURE: no FastAPI, no SQLAlchemy
repositories/   Every SQL statement
models/         Tables and constraints
```

`services/` importing neither the web framework nor the database is the decision
the whole test strategy rests on: the splitting rules, balance arithmetic and
settlement planner are ordinary Python functions, so they are tested exhaustively
without HTTP or a database.

**Database:** 5 tables — `groups`, `members`, `expenses`, `expense_shares`,
`settlements`. Foreign keys use `ON DELETE CASCADE` from a group to its contents,
and `ON DELETE RESTRICT` from financial records to members, so a member who has
paid for something cannot be deleted out from under everyone else's balance.
Named constraints: `uq_member_group_name`, `uq_share_expense_member`,
`ck_settlement_distinct_members`, `ck_expense_amount_positive`,
`ck_share_amount_non_negative`, `ck_settlement_amount_positive`,
`ck_expense_split_type`.

**Balance formula:** `paid − owed + settlements paid − settlements received`.
Invariant: the balances of a group always sum to exactly `0.00`.

**Settlement algorithm:** greedy matching of the largest debtor with the largest
creditor. Each transfer zeroes at least one member, so a group of *n* members
needs at most *n − 1* transfers. Ties break by member id, so the plan is
deterministic. The greedy method is not guaranteed to find the theoretical
minimum (that problem is NP-hard) but is optimal in common cases, runs in
O(n log n) and is easy to explain — a deliberate trade-off.

---

## 4. Git workflow

Git was initialised **before the first line of code**, and every stage of
development produced its own commit at the time the work was done.

**Branching model** — one branch per development stage, merged into `main` with
`git merge --no-ff` so each stage is visible as a merge point in the graph:

| Branch | Stage | Merged |
|---|---|---|
| `feature/foundation` | config, dependencies, database bootstrap, health endpoint | yes |
| `feature/domain-model` | ORM models and Pydantic schemas | yes |
| `feature/core-logic` | money, splitting, balances, settlement planner | yes |
| `feature/api` | repositories and routers | yes |
| `feature/testing` | unit and integration suites | yes |
| `feature/docker` | Dockerfile, Compose stack | yes |
| `feature/ci` | GitHub Actions workflow | yes |
| `refactor/clean-code-review` | fixes from the self-review | yes |
| `feature/docs` | README, API reference, these notes | via pull request |
| `feature/ci-failure-demo` | proves CI blocks broken code | **never merged, by design** |

**Commit convention:** Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`,
`chore:`, `ci:`, `refactor:`), imperative mood, one logical change per commit.

**Counts (measured with `git rev-list`):** 31 non-merge commits and 8 merge
commits at the time of writing, plus the documentation commits on
`feature/docs`. No commit was backdated, no empty commits were created, and there
is a single author.

**Commit history in order:**

```
chore: initialize repository with Python gitignore
docs: add FairShare API project specification
chore: add tooling configuration and pinned dependencies
feat: add settings, constants and domain error hierarchy
feat: add database engine, session dependency and ORM base
feat: add FastAPI application with health endpoint
docs: record actual pinned versions in the specification
feat: add ORM models for groups, members, expenses and settlements
feat: add Pydantic schemas for every resource
feat: add fixed-point money helpers
feat: add equal and exact expense splitting
feat: add net balance computation
feat: add greedy minimal settlement planner
feat: add repository layer for all database access
feat: add group and member endpoints
feat: add expense endpoints with split resolution
feat: add balance, settlement plan and summary endpoints
feat: add settlement endpoints and register every router
chore: declare first-party packages for import sorting
test: add unit tests for money handling and expense splitting
test: add unit tests for balances and the settlement planner
test: add unit tests for request validation and error handlers
test: add integration fixtures and health and group API tests
test: add member and expense API integration tests
test: add balance and settlement API integration tests
feat: add Docker image and Compose stack
ci: add GitHub Actions pipeline with coverage gate
refactor: remove duplication and dead code found in review
docs: record the review and CI demonstration branches
docs: add API reference and generated OpenAPI snapshot
docs: write the project README
docs: add factual project notes
```

**Specification discipline:** when implementation showed a spec detail was wrong
or incomplete, `GUIDE.md` was updated first and the change explained in the
commit message. This happened for the pinned dependency versions, the
`NEGATIVE_SHARE` error code, `schemas/common.py`, `repositories/balances.py`, and
the rule about which layers may import which.

---

## 5. Automated testing

**Two layers:**

| Layer | Location | Database? | Purpose |
|---|---|---|---|
| Unit | `tests/unit/` | No | Splitting, balances, planner, validation, error handlers |
| Integration | `tests/integration/` | Yes | Real HTTP through FastAPI → SQLAlchemy → PostgreSQL |

`pytest tests/unit` runs with no database at all — a direct consequence of
keeping `services/` free of infrastructure.

**Isolation:** integration tests run against a separate `fairshare_test`
database. A session fixture creates the schema; a function-scoped autouse fixture
runs `TRUNCATE ... RESTART IDENTITY CASCADE` before every test, so no test can be
affected by another test's data or by execution order.

**Result: 184 tests, all passing, in about 7–10 seconds.**

Notable cases covered:

- ₹1000 split three ways produces 333.34 + 333.33 + 333.33 and sums exactly.
- ₹0.01 split three ways: one member owes the paisa, nobody owes a fraction.
- Exact shares over or under by ₹0.01 are rejected, not silently adjusted.
- Property-style checks over six balance scenarios: executing the plan settles
  everyone, no plan exceeds *n − 1* payments, all amounts are positive, and the
  same input always produces the same plan.
- Balances sum to zero — asserted both as a unit test and end to end through HTTP.
- Every documented error code has a test that provokes it.
- Deleting a group removes its members and expenses; deleting an expense changes
  the balances immediately.
- An unexpected server error returns a generic message and leaks no internals.

---

## 6. Test coverage

Measured with pytest-cov (line **and** branch coverage) over the `app/` package.

**Actual result: 99.88% (782 statements, 0 missed; 62 branches, 1 partial).**

Per-package: `app/services/` — the business logic — is at **100%**, as are
`models/`, `schemas/`, `repositories/` and `routers/`.

The single partial branch is in `repositories/groups.py`: the guard that ignores
non-updatable fields in a PATCH payload. It cannot be reached over HTTP because
the request schema only contains updatable fields, so it is defensive code kept
deliberately.

Reports produced: `term-missing` (terminal), `htmlcov/` (browsable) and
`coverage.xml` (uploaded by CI as an artifact).

Coverage was not padded. When the first full run showed 99.41% with four missed
lines in `main.py`, the gap was in the two error handlers; the fix was to test
them for real — including asserting that a crash never leaks internal detail —
rather than to write tests that merely execute the lines.

Command used:

```bash
pytest --cov=app --cov-report=term-missing --cov-report=html --cov-report=xml
```

---

## 7. Docker

**Image** (`Dockerfile`): `python:3.12-slim`; dependencies installed in a layer
before the source is copied so code edits do not rebuild them; only `app/` and
`requirements.txt` enter the image; runs as the non-root user `fairshare`;
declares a `HEALTHCHECK` that calls the health endpoint using the standard
library instead of installing curl.

**Stack** (`compose.yaml`): two services — `api` built locally and `db` running
`postgres:16-alpine` with a `pg_isready` healthcheck and a named volume
`pgdata`. The API waits for `condition: service_healthy` before starting. The
database URL is injected as an environment variable, never hard-coded.

`.dockerignore` excludes `.git`, `.venv`, caches, tests, docs and markdown so the
build context stays small.

**Verified locally:**

```
$ docker compose up --build -d
$ docker compose ps
NAME            STATUS
fairshare-api   Up (healthy)
fairshare-db    Up (healthy)

$ curl http://localhost:8000/
{"status":"ok","service":"fairshare-api","version":"1.0.0"}

$ curl -X POST http://localhost:8000/api/v1/groups -H 'Content-Type: application/json' -d '{"name":"Docker Trip"}'
{"id":1,"name":"Docker Trip","description":null,"currency":"NPR","created_at":"2026-08-15T18:48:20.793736Z"}

$ docker compose exec api whoami
fairshare
```

---

## 8. Continuous integration

`.github/workflows/ci.yml`, triggered on every push to `main` and `feature/**`
and on every pull request to `main`. Two jobs:

**`test`** — starts a PostgreSQL 16 service container with a health check, sets
up Python 3.12 with pip caching, installs pinned dependencies, runs `ruff check`
and `ruff format --check`, then runs the full suite with
`--cov-fail-under=90`, and uploads `coverage.xml` plus the HTML report as an
artifact.

**`docker`** — builds the image, starts the Compose stack, waits for the API to
answer, creates and reads a group through the containerised API, and tears the
stack down.

**Results:**

- First run on `feature/ci`: **success**, every step green in both jobs —
  run `31902241278`.
- Deliberate failure check: on the unmerged branch `feature/ci-failure-demo`, one
  assertion in `test_splitting.py` was changed to expect 333.33 instead of
  333.34. CI went **red** — run `31902315459` — proving the pipeline actually
  blocks broken code. The next commit on that branch restored the assertion.

Run history: https://github.com/sandeshkhatribct35/Software-Engineering-Project/actions

---

## 9. Clean coding practices

- **Meaningful names:** `suggest_settlements`, `split_equally`,
  `validate_exact_shares`, `MemberHasActivityError`, `balances_are_settled`.
- **Separation of responsibilities:** the five layers described above, with an
  explicit rule about which layer may import which.
- **Small functions:** each does one thing; the longest is the expense-creation
  route handler, which validates, delegates and stores.
- **Complete type hints** on every function signature.
- **No magic numbers:** limits, precision, defaults and page sizes live in
  `app/constants.py`.
- **Single source of truth:** rounding exists in exactly one function
  (`services/money.quantize`); the monetary column type is declared once in
  `models/base.py`.
- **Consistent error handling:** routers raise domain exceptions; four handlers
  in `main.py` turn them into one error envelope. No router builds an error by hand.
- **No secrets in source:** the database URL comes from the environment; `.env`
  is git-ignored and only `.env.example` is committed.
- **Enforced mechanically:** Ruff (`E`, `F`, `I`, `B`, `UP`, `SIM`, `C4`, `ARG`)
  plus `ruff format`, both run in CI, so style is not a matter of opinion.

**Self-review findings and fixes** (commit `refactor: remove duplication and dead
code found in review`):

1. `MONEY_TYPE` was declared identically in two model modules → moved to
   `models/base.py`.
2. The digit count `12` for money columns was a literal in the models and again
   in the schemas → became `MONEY_MAX_DIGITS` in `constants.py`.
3. `MIN_EXPENSE_AMOUNT` was declared but never used → removed.
4. `validate_exact_shares` called `total([amount])` where it meant `quantize()`.
5. The eager-loading helper was annotated as returning `object` → given the real
   SQLAlchemy type.

---

## 10. API documentation

FastAPI generates the OpenAPI schema from the type hints, Pydantic models and
route metadata, so the documentation cannot drift away from the code. Three live
forms are served by the application: Swagger UI at `/docs`, ReDoc at `/redoc` and
the raw schema at `/openapi.json` — all three verified returning HTTP 200 from
the containerised stack.

The auto-generated output was enriched rather than left bare: every route
declares `summary`, `description`, `tags`, `status_code`, `response_model` and a
`responses` entry per documented error status; every Pydantic field declares a
description and, where useful, an example.

In addition:

- `docs/API.md` — a written reference for all 18 endpoints with `curl` examples,
  request rules, sample responses, the error-code table and a complete worked
  example.
- `docs/openapi.json` — a snapshot exported from the running application by
  `python scripts/export_openapi.py`, which reported "18 operations".

---

## 11. Problems encountered and how they were solved

1. **Docker Desktop was not running**, so no database was available. Started it
   and waited for the daemon before any integration work.
2. **A manually started `fairshare-db` container clashed with the Compose
   container name.** Removed the ad-hoc container and let Compose own the
   database from then on.
3. **`scripts/export_openapi.py` failed with `ModuleNotFoundError: No module
   named 'app'`** when run directly, because Python puts `scripts/` on the path
   rather than the project root. Fixed by inserting the project root into
   `sys.path` in the script, with a comment explaining why.
4. **Ruff classified `app` as a third-party import inside `tests/`,** producing
   import-order errors that would have failed CI. Fixed by declaring
   `known-first-party = ["app", "tests"]` in `pyproject.toml` rather than by
   silencing the rule.
5. **Ruff flagged two dictionary comprehensions (`C416`)** that were really just
   `dict(...)` calls, in `services/splitting.py` and `repositories/balances.py`.
   Both simplified.
6. **Coverage stopped at 99.41%**, with the gap in the two error handlers in
   `main.py`. Rather than ignore them, they were tested directly — including an
   assertion that an unexpected exception never leaks internal detail.
7. **Balance arithmetic had to survive rounding.** Solved by doing equal splits
   in integer minor units (paisa) and distributing the remainder explicitly, then
   proving the property with parametrised tests over several group sizes.
8. **The self-review found duplication and dead code** (section 9), all fixed in
   one commit before submission.

---

## 12. Final verification performed

| Check | Command | Result |
|---|---|---|
| Lint | `ruff check .` | All checks passed |
| Formatting | `ruff format --check .` | All files formatted |
| Unit tests without a database | `pytest tests/unit` | passed |
| Full suite | `pytest` | 184 passed |
| Coverage | `pytest --cov=app` | 99.88% |
| Compose validity | `docker compose config` | valid |
| Stack starts | `docker compose up --build -d` | both services healthy |
| API in Docker | `curl localhost:8000/` + create/read a group | worked |
| Non-root container | `docker compose exec api whoami` | `fairshare` |
| Swagger UI | `GET /docs` | 200 |
| ReDoc | `GET /redoc` | 200 |
| OpenAPI schema | `GET /openapi.json` | 200, 18 operations |
| CI green | GitHub Actions | run 31902241278, both jobs success |
| CI catches failures | GitHub Actions | run 31902315459, failed as intended |

---

## 13. Notes for the viva

Questions worth being ready for, with where the answer lives:

- *Why is money a string in JSON?* Floating point cannot represent 0.10 exactly —
  `services/money.py`, `schemas/common.py`.
- *What happens to the odd paisa?* Integer minor units, remainder to the lowest
  member ids — `services/splitting.py`, proven by `tests/unit/test_splitting.py`.
- *Why can `services/` not import SQLAlchemy?* So the rules can be tested without
  infrastructure — `GUIDE.md` §10.2, demonstrated by `pytest tests/unit`.
- *Why no authentication?* A documented scope decision, not an oversight —
  `GUIDE.md` §4.2.
- *Is your settlement plan optimal?* It is minimal-ish: greedy, at most *n − 1*
  transfers, deterministic; the true minimum is NP-hard — `settlement_plan.py`.
- *How do you know your tests are worth anything?* They include property checks
  and the zero-sum invariant, and CI has been shown to go red on a broken
  assertion (run 31902315459).
