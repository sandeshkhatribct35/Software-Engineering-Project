# GUIDE.md — FairShare API

**Group Expense Sharing & Settlement Service**

The authoritative specification for this Software Engineering lab project.
This document defines *what* must be built, *how* it must be built, and *how completion is proven*.
Any change to the project must be reflected here first.

| Field | Value |
|---|---|
| Project name | FairShare API |
| Repository | `Software-Engineering-Project` (local folder: `fairshare-api`) |
| Remote | https://github.com/sandeshkhatribct35/Software-Engineering-Project |
| Author | Sandesh Khatri (solo project) |
| Type | Backend REST API service |
| Course | Software Engineering — Lab Project |
| Status | Specification approved — implementation pending |

---

## TABLE OF CONTENTS

1. [Project Title](#1-project-title)
2. [Problem Statement](#2-problem-statement)
3. [Project Objective](#3-project-objective)
4. [Scope](#4-scope)
5. [Main Features](#5-main-features)
6. [User Roles](#6-user-roles)
7. [Functional Requirements](#7-functional-requirements)
8. [Non-Functional Requirements](#8-non-functional-requirements)
9. [Technology Stack](#9-technology-stack)
10. [System Architecture](#10-system-architecture)
11. [Database Design](#11-database-design)
12. [API Requirements](#12-api-requirements)
13. [Testing Requirements](#13-testing-requirements)
14. [Docker Requirements](#14-docker-requirements)
15. [CI Requirements](#15-ci-requirements)
16. [Clean Coding Requirements](#16-clean-coding-requirements)
17. [API Documentation Requirements](#17-api-documentation-requirements)
18. [Test Coverage Requirements](#18-test-coverage-requirements)
19. [Git / Version Control Workflow](#19-git--version-control-workflow)
20. [Expected Project Structure](#20-expected-project-structure)
21. [Definition of Done](#21-definition-of-done)
22. [Final Verification Checklist](#22-final-verification-checklist)

---

# 1. Project Title

**FairShare API — a REST service for tracking shared group expenses and computing the minimum set of payments required to settle all debts.**

---

# 2. Problem Statement

When a group of people share costs — flatmates paying rent and utilities, friends on a trip, classmates buying lab equipment — money is rarely paid in equal amounts by equal people. One person pays for dinner, another pays for fuel, a third pays for the hotel. Some expenses are split evenly; others are not (one person had the expensive meal).

Tracking this by hand fails for three reasons:

1. **Arithmetic errors.** Splitting ₹1000 among 3 people does not divide evenly. Manual splitting either loses money or invents it.
2. **No net view.** People remember individual debts ("you owe me for fuel") but not their *net position*. A owes B, B owes C, and C owes A — in reality almost nothing needs to change hands.
3. **Too many payments.** Settling every individual debt separately means many small transfers. A group of 6 people with 15 shared expenses might need 15 payments when 4 would suffice.

The result is disputes, forgotten debts, and unnecessary transactions.

**FairShare solves this** by recording every shared expense with its exact split, maintaining each member's *net balance*, and computing a minimal settlement plan — the smallest practical set of payments that clears every debt in the group.

---

# 3. Project Objective

The objective is twofold.

**Primary (academic):** demonstrate professional Software Engineering practice — version control with a real branching workflow, layered architecture, automated unit and integration testing with measured coverage, containerisation, continuous integration, and living API documentation.

**Secondary (functional):** deliver a working, correct backend service that:

- records groups, members, expenses, and payments with full referential integrity,
- splits expenses without losing or inventing money (to the last paisa/cent),
- computes net balances that always sum to exactly zero,
- produces a settlement plan with at most `n − 1` transfers for a group of `n` members,
- rejects every form of invalid input with a clear, documented error.

---

# 4. Scope

## 4.1 In scope

- A JSON REST API over HTTP, served by an application server.
- Persistent storage in a relational database with foreign-key constraints.
- Full lifecycle management of groups, members, expenses, expense shares, and settlements.
- Two expense split strategies: **EQUAL** and **EXACT**.
- Balance computation and settlement-plan generation as pure, independently testable logic.
- Request validation, domain error handling, and documented HTTP status codes.
- Automated test suite (unit + integration) with a coverage report.
- Containerisation of the application and its database.
- A CI pipeline that lints, tests, measures coverage, and builds the container image.
- Auto-generated interactive API documentation plus a written API reference.

## 4.2 Explicitly out of scope

These are deliberately excluded to keep the project completable and focused on engineering practice, not feature count:

- Authentication, authorisation, users, passwords, JWT, sessions.
- Any frontend, UI, or template rendering.
- Multi-currency conversion (a group has one currency; no exchange rates).
- Email, SMS, or push notifications.
- File uploads, receipt images, OCR.
- Recurring or scheduled expenses.
- Caching layers, message queues, background workers, microservices, Kubernetes.
- Database migration tooling (schema is created from the ORM metadata at startup).
- Soft deletes, audit logs, or per-record version history.

## 4.3 Assumptions

- All members of a group are trusted; there is no per-user access control.
- A group operates in a single currency, recorded for display purposes only.
- Monetary amounts have exactly two decimal places.
- The API is consumed by a developer or another program, not by an end user directly.

---

# 5. Main Features

| # | Feature | Description |
|---|---|---|
| F1 | Group management | Create, list, view, rename, and delete an expense-sharing group. |
| F2 | Member management | Add members to a group, list them, and remove a member who has no financial involvement. |
| F3 | Expense recording | Record who paid, how much, for what, and which members share the cost. |
| F4 | Equal split | Divide an expense evenly among the selected participants, distributing any indivisible remainder deterministically so the shares sum to the exact total. |
| F5 | Exact split | Accept a caller-supplied amount per participant, rejected unless the shares sum exactly to the expense total. |
| F6 | Net balance calculation | For every member, compute `paid − owed`, adjusted by settlements already made. Positive means the group owes them; negative means they owe the group. |
| F7 | Settlement plan | Compute a minimal set of member-to-member transfers that clears all balances, using greedy largest-debtor / largest-creditor matching. |
| F8 | Settlement recording | Record an actual payment between two members, which updates the balances. |
| F9 | Group summary | Report total spend, expense count, member count, and per-member paid/owed totals. |
| F10 | Validation & error reporting | Reject malformed and semantically invalid requests with documented status codes and machine-readable error codes. |

---

# 6. User Roles

The API has **no authentication and therefore no enforced roles.** The following are *conceptual* actors, useful for understanding the domain:

| Actor | Description | Interaction |
|---|---|---|
| Group organiser | The person who sets up the group and adds members. | Calls the group and member endpoints. |
| Group member | A person who pays for, or shares in, expenses. | Represented as data (a `member` row); does not authenticate. |
| API consumer | A developer or client application. | Calls all endpoints; is the only real "user" of the system. |

**Design note for viva:** the absence of authentication is a deliberate, documented scope decision (§4.2), not an oversight. Adding it would consume project time without demonstrating any Software Engineering practice not already covered.

---

# 7. Functional Requirements

Each requirement is testable and is referenced by the test suite.

## 7.1 Groups

| ID | Requirement |
|---|---|
| FR-1 | The system shall create a group with a name (1–100 characters, not blank), an optional description (max 500 characters), and a currency code (exactly 3 uppercase letters, default `NPR`). |
| FR-2 | The system shall reject a group whose name is empty or whitespace-only with HTTP 422. |
| FR-3 | The system shall list all groups, most recently created first. |
| FR-4 | The system shall return a single group including its member list, or HTTP 404 if the group does not exist. |
| FR-5 | The system shall allow updating a group's name and description; unspecified fields remain unchanged. |
| FR-6 | The system shall delete a group and, by cascade, all its members, expenses, expense shares, and settlements. |

## 7.2 Members

| ID | Requirement |
|---|---|
| FR-7 | The system shall add a member to an existing group with a name of 1–80 characters, not blank. |
| FR-8 | The system shall reject a member whose name already exists in that group, compared case-insensitively, with HTTP 409 and code `DUPLICATE_MEMBER_NAME`. |
| FR-9 | The system shall allow the same member name to exist in two different groups. |
| FR-10 | The system shall list all members of a group, ordered by creation time. |
| FR-11 | The system shall delete a member only if that member has paid no expense, shares no expense, and is party to no settlement; otherwise HTTP 409 with code `MEMBER_HAS_ACTIVITY`. |
| FR-12 | The system shall return HTTP 404 when adding a member to a non-existent group. |

## 7.3 Expenses

| ID | Requirement |
|---|---|
| FR-13 | The system shall record an expense with a description (1–200 characters, not blank), an amount, the paying member, a split type, and a list of participants. |
| FR-14 | The system shall require the amount to be strictly greater than 0, at most 1,000,000.00, and expressed with at most 2 decimal places; otherwise HTTP 422. |
| FR-15 | The system shall reject an expense whose paying member does not belong to the group, with HTTP 422 and code `PAYER_NOT_IN_GROUP`. |
| FR-16 | The system shall reject an expense with an empty participant list, with duplicate participants, or with any participant not belonging to the group, with HTTP 422 and codes `NO_PARTICIPANTS`, `DUPLICATE_PARTICIPANT`, `PARTICIPANT_NOT_IN_GROUP` respectively. |
| FR-17 | For `split_type = EQUAL`, the system shall divide the amount evenly among participants and allocate any indivisible remainder one minor unit at a time, in ascending participant-id order, so that the shares sum exactly to the expense amount. |
| FR-18 | For `split_type = EXACT`, the system shall require an explicit non-negative share for every participant, and shall reject the expense if the shares do not sum exactly to the amount, with HTTP 422 and code `SHARES_DO_NOT_SUM`. |
| FR-19 | The system shall list a group's expenses, newest first, with `limit` (1–100, default 50) and `offset` (≥ 0, default 0) pagination. |
| FR-20 | The system shall return a single expense including every participant's share, or HTTP 404. |
| FR-21 | The system shall delete an expense along with its shares, and the group's balances shall reflect the deletion immediately. |

## 7.4 Balances, settlement plan, and settlements

| ID | Requirement |
|---|---|
| FR-22 | The system shall compute each member's net balance as `(total paid) − (total owed) + (settlements paid) − (settlements received)`. |
| FR-23 | The sum of all member balances in a group shall always equal exactly `0.00`. |
| FR-24 | The system shall report balances for every member of the group, including members with a zero balance. |
| FR-25 | The system shall produce a settlement plan: a list of `{from, to, amount}` transfers whose execution brings every balance to zero. |
| FR-26 | The settlement plan shall contain at most `n − 1` transfers for a group of `n` members, and shall be empty when the group is already settled. |
| FR-27 | The settlement plan shall be deterministic — identical input always produces an identical plan — with ties broken by ascending member id. |
| FR-28 | The system shall record a settlement between two distinct members of the group with an amount strictly greater than 0 and an optional note (max 200 characters). |
| FR-29 | The system shall reject a settlement where payer and payee are the same member (`SAME_MEMBER_SETTLEMENT`) or where either member is not in the group (`MEMBER_NOT_IN_GROUP`), with HTTP 422. |
| FR-30 | The system shall list all recorded settlements of a group, newest first. |
| FR-31 | The system shall provide a group summary containing member count, expense count, total spend, and per-member paid and owed totals. |

## 7.5 Cross-cutting

| ID | Requirement |
|---|---|
| FR-32 | The system shall expose a health endpoint returning service status, name, and version. |
| FR-33 | Every error response shall be JSON containing a human-readable `detail` and a stable machine-readable `code`. |
| FR-34 | The system shall return `201 Created` for creations, `204 No Content` for deletions, and `200 OK` for reads and updates. |
| FR-35 | All monetary values shall be serialised as JSON strings with exactly two decimal places (e.g. `"333.34"`) to avoid floating-point representation errors. |

---

# 8. Non-Functional Requirements

| ID | Category | Requirement |
|---|---|---|
| NFR-1 | Correctness | All monetary arithmetic uses fixed-point decimals. Floating-point types are forbidden for money, in code and in the database. |
| NFR-2 | Correctness | Rounding uses ROUND_HALF_UP at two decimal places, applied in exactly one place in the codebase. |
| NFR-3 | Reliability | The database enforces its own invariants (foreign keys, uniqueness, positive-amount checks); the application never relies solely on in-code validation. |
| NFR-4 | Maintainability | Layered architecture (§10). Business logic must not import the web framework; the web layer must not contain arithmetic. |
| NFR-5 | Maintainability | Every function and method carries complete type hints. |
| NFR-6 | Maintainability | No function exceeds ~40 lines; no module exceeds ~250 lines. |
| NFR-7 | Testability | Balance and settlement logic must be executable without a database, a web server, or network access. |
| NFR-8 | Portability | The application and its database run identically via a single `docker compose up` on any machine with Docker. |
| NFR-9 | Configurability | All environment-specific values (database URL, log level) come from environment variables with safe local defaults. No credentials appear in source code. |
| NFR-10 | Security | No secrets, `.env` files, credentials, or tokens are committed to version control. |
| NFR-11 | Performance | A request against a group with ≤ 50 members and ≤ 500 expenses responds in under 200 ms locally. Balance queries use aggregate SQL, not per-member queries (no N+1). |
| NFR-12 | Observability | Unhandled exceptions return HTTP 500 with a generic message; internal details are logged, never returned to the client. |
| NFR-13 | Documentation | The API documentation is generated from the source code, so it cannot drift out of date. |
| NFR-14 | Reproducibility | All dependencies are pinned to exact versions. |
| NFR-15 | Consistency | Python version 3.12 is used identically in local development, the Docker image, and CI. |

---

# 9. Technology Stack

| Layer | Technology | Version | Justification |
|---|---|---|---|
| Language | Python | 3.12 | Available locally; strong typing support; matches Docker and CI exactly. |
| Web framework | FastAPI | 0.141.1 | Generates OpenAPI documentation from the code itself, satisfying NFR-13. |
| ASGI server | Uvicorn | 0.52.3 | Standard production server for FastAPI. |
| Validation | Pydantic | 2.13.4 | Declarative request/response validation with decimal support. |
| Settings | pydantic-settings | 2.15.0 | Typed configuration loaded from environment variables (NFR-9). |
| ORM | SQLAlchemy | 2.0.52 | Mature relational mapping with explicit constraint definitions. |
| Database driver | psycopg (v3) | 3.3.4 | Current PostgreSQL adapter with native Python 3.12 wheels. |
| Database | PostgreSQL | 16-alpine | Real relational database with `NUMERIC` fixed-point arithmetic. |
| Testing | pytest | 9.1.1 | Fixture-based test framework. |
| Coverage | pytest-cov | 7.1.0 | Line coverage measurement and reporting. |
| HTTP test client | httpx (via TestClient) | 0.28.1 | Drives real HTTP requests against the app in integration tests. |
| Linting & formatting | Ruff | 0.16.3 | Single fast tool for lint + format; enforces §16 mechanically. |

Versions above are the exact versions installed and pinned in `requirements.txt` /
`requirements-dev.txt`, recorded after installation rather than guessed.
| Containerisation | Docker + Compose | v2 | Application and database as reproducible containers. |
| CI | GitHub Actions | — | Runs lint, tests, coverage gate, and image build on every push and PR. |
| Version control | Git + GitHub | — | Branching workflow, commit history, pull request. |

**Money type decision:** `Decimal` in Python, `NUMERIC(12, 2)` in PostgreSQL, `string` in JSON. This is recorded here because it is a design decision that must be defended, not an implementation detail.

---

# 10. System Architecture

## 10.1 Architectural style

A **layered (n-tier) monolith** with a strict, one-directional dependency rule:

```
        HTTP request
             │
             ▼
┌────────────────────────────┐
│  Presentation layer        │   app/routers/
│  routing, status codes     │   FastAPI routers only
└────────────┬───────────────┘
             │  validated DTOs
             ▼
┌────────────────────────────┐
│  Schema layer              │   app/schemas/
│  request/response contract │   Pydantic models
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  Service layer  (PURE)     │   app/services/
│  splitting, balances,      │   plain Python + Decimal
│  settlement planning       │   NO database, NO FastAPI
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  Repository layer          │   app/repositories/
│  all SQL / ORM queries     │   SQLAlchemy sessions
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  Persistence layer         │   app/models/
│  tables, constraints       │   SQLAlchemy ORM models
└────────────┬───────────────┘
             ▼
        PostgreSQL 16
```

## 10.2 The dependency rule

- `routers` may import `schemas`, `services`, `repositories`, `errors`, and `models` (for type annotations and for reading loaded attributes when building responses).
- `repositories` may import `models`, `errors`, and the pure data structures declared in `services` (such as `MemberTotals`), so that aggregate queries can be handed straight to the calculation layer.
- **`services` may import nothing from the project except `errors` and constants.** It must never import FastAPI, SQLAlchemy, or any model.
- `models` and `schemas` import nothing from other layers.

This rule is the reason the core logic is unit-testable without infrastructure (NFR-7) and is the project's principal clean-architecture claim.

## 10.3 Request lifecycle (example: create an expense)

1. `POST /api/v1/groups/1/expenses` arrives at the expenses router.
2. FastAPI validates the body against `ExpenseCreate` (types, lengths, amount bounds) → HTTP 422 on failure.
3. The router obtains a database session from the `get_db` dependency.
4. The repository loads the group and its members → `GroupNotFoundError` → HTTP 404.
5. The router validates domain rules (payer in group, participants valid) → domain error → HTTP 422 with a code.
6. The **service layer** computes each participant's share (`split_equally` or `validate_exact_shares`) — pure Decimal arithmetic.
7. The repository persists the expense and its shares in a single transaction.
8. The router serialises the ORM object through `ExpenseRead` and returns HTTP 201.

## 10.4 Error handling strategy

Domain exceptions are defined in `app/errors.py`, raised by repositories and routers, and translated to HTTP responses by exception handlers registered in `app/main.py`. Routers never build error responses by hand, so error format is consistent across the whole API (FR-33).

## 10.5 Deployment view

```
┌──────────────── docker compose ────────────────┐
│                                                │
│   ┌──────────────┐        ┌────────────────┐   │
│   │  fairshare-  │        │  fairshare-db  │   │
│   │     api      │───────▶│  postgres:16   │   │
│   │  :8000       │  5432  │  volume: pgdata│   │
│   └──────────────┘        └────────────────┘   │
│      depends_on: db healthy                    │
└────────────────────────────────────────────────┘
            │ published :8000
            ▼
        host machine
```

---

# 11. Database Design

## 11.1 Entity-relationship overview

```
groups 1 ──────< members
   │                │
   │                │ paid_by
   ├────────< expenses ─────< expense_shares >───── members
   │                                                   │
   └────────< settlements >────────────────────────────┘
                (from_member, to_member)
```

- A **group** has many **members**, **expenses**, and **settlements**.
- An **expense** is paid by exactly one member and has many **expense_shares**.
- An **expense_share** links one expense to one member with that member's owed amount.
- A **settlement** records a payment from one member to another within a group.

## 11.2 Tables

### `groups`

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PK, auto-increment |
| `name` | VARCHAR(100) | NOT NULL |
| `description` | VARCHAR(500) | NULL |
| `currency` | CHAR(3) | NOT NULL, DEFAULT `'NPR'` |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT now() |

### `members`

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PK, auto-increment |
| `group_id` | INTEGER | NOT NULL, FK → `groups.id` ON DELETE CASCADE |
| `name` | VARCHAR(80) | NOT NULL |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT now() |

Constraints: `UNIQUE (group_id, name)` — named `uq_member_group_name`. Index on `group_id`.
Case-insensitive duplicates are additionally rejected by the application (FR-8).

### `expenses`

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PK, auto-increment |
| `group_id` | INTEGER | NOT NULL, FK → `groups.id` ON DELETE CASCADE |
| `description` | VARCHAR(200) | NOT NULL |
| `amount` | NUMERIC(12,2) | NOT NULL, CHECK (`amount > 0`) |
| `paid_by_id` | INTEGER | NOT NULL, FK → `members.id` ON DELETE RESTRICT |
| `split_type` | VARCHAR(10) | NOT NULL, CHECK IN (`'EQUAL'`, `'EXACT'`) |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT now() |

Index on `group_id`.

### `expense_shares`

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PK, auto-increment |
| `expense_id` | INTEGER | NOT NULL, FK → `expenses.id` ON DELETE CASCADE |
| `member_id` | INTEGER | NOT NULL, FK → `members.id` ON DELETE RESTRICT |
| `share_amount` | NUMERIC(12,2) | NOT NULL, CHECK (`share_amount >= 0`) |

Constraints: `UNIQUE (expense_id, member_id)` — named `uq_share_expense_member`.

### `settlements`

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PK, auto-increment |
| `group_id` | INTEGER | NOT NULL, FK → `groups.id` ON DELETE CASCADE |
| `from_member_id` | INTEGER | NOT NULL, FK → `members.id` ON DELETE RESTRICT |
| `to_member_id` | INTEGER | NOT NULL, FK → `members.id` ON DELETE RESTRICT |
| `amount` | NUMERIC(12,2) | NOT NULL, CHECK (`amount > 0`) |
| `note` | VARCHAR(200) | NULL |
| `settled_at` | TIMESTAMP | NOT NULL, DEFAULT now() |

Constraints: CHECK (`from_member_id <> to_member_id`) — named `ck_settlement_distinct_members`. Index on `group_id`.

## 11.3 Balance formula

For member *m*:

```
balance(m) =   Σ expenses.amount            where paid_by_id = m
             − Σ expense_shares.share_amount where member_id = m
             + Σ settlements.amount          where from_member_id = m
             − Σ settlements.amount          where to_member_id = m
```

Interpretation: **positive** → the group owes *m*; **negative** → *m* owes the group; **zero** → settled.
Invariant: `Σ balance(m) over all m in group = 0.00` (FR-23) — asserted by a dedicated test.

## 11.4 Schema creation

Tables are created from the ORM metadata at application startup (`Base.metadata.create_all`). Migration tooling is out of scope (§4.2); the trade-off is documented here so it can be defended: for a project with no production data and no schema evolution, a migration tool would add ceremony without demonstrating any additional practice.

---

# 12. API Requirements

## 12.1 Conventions

- Base path: `/api/v1` (the health endpoint sits at the root).
- All request and response bodies are JSON.
- Monetary values are JSON **strings** with two decimals (NFR/FR-35).
- Timestamps are ISO-8601 UTC.
- Every route declares a `summary`, a `description`, a `tags` entry, a `response_model`, and its documented error responses.

## 12.2 Endpoint inventory

| # | Method | Path | Success | Purpose |
|---|---|---|---|---|
| 1 | GET | `/` | 200 | Health / service metadata |
| 2 | POST | `/api/v1/groups` | 201 | Create a group |
| 3 | GET | `/api/v1/groups` | 200 | List groups |
| 4 | GET | `/api/v1/groups/{group_id}` | 200 | Group detail with members |
| 5 | PATCH | `/api/v1/groups/{group_id}` | 200 | Update name/description |
| 6 | DELETE | `/api/v1/groups/{group_id}` | 204 | Delete group and all its data |
| 7 | POST | `/api/v1/groups/{group_id}/members` | 201 | Add a member |
| 8 | GET | `/api/v1/groups/{group_id}/members` | 200 | List members |
| 9 | DELETE | `/api/v1/groups/{group_id}/members/{member_id}` | 204 | Remove an uninvolved member |
| 10 | POST | `/api/v1/groups/{group_id}/expenses` | 201 | Record an expense |
| 11 | GET | `/api/v1/groups/{group_id}/expenses` | 200 | List expenses (paginated) |
| 12 | GET | `/api/v1/expenses/{expense_id}` | 200 | Expense detail with shares |
| 13 | DELETE | `/api/v1/expenses/{expense_id}` | 204 | Delete an expense |
| 14 | GET | `/api/v1/groups/{group_id}/balances` | 200 | Net balance per member |
| 15 | GET | `/api/v1/groups/{group_id}/settlement-plan` | 200 | Minimal transfer plan |
| 16 | POST | `/api/v1/groups/{group_id}/settlements` | 201 | Record a payment |
| 17 | GET | `/api/v1/groups/{group_id}/settlements` | 200 | List payments |
| 18 | GET | `/api/v1/groups/{group_id}/summary` | 200 | Group totals |

## 12.3 Representative payloads

**Create an expense (equal split):**
```json
POST /api/v1/groups/1/expenses
{
  "description": "Hotel in Pokhara",
  "amount": "1000.00",
  "paid_by_id": 1,
  "split_type": "EQUAL",
  "participant_ids": [1, 2, 3]
}
```
Response `201`:
```json
{
  "id": 7,
  "group_id": 1,
  "description": "Hotel in Pokhara",
  "amount": "1000.00",
  "paid_by_id": 1,
  "split_type": "EQUAL",
  "created_at": "2026-08-15T10:04:11Z",
  "shares": [
    {"member_id": 1, "member_name": "Sandesh", "share_amount": "333.34"},
    {"member_id": 2, "member_name": "Bikash",  "share_amount": "333.33"},
    {"member_id": 3, "member_name": "Anita",   "share_amount": "333.33"}
  ]
}
```
Note the remainder allocation: `333.34 + 333.33 + 333.33 = 1000.00` exactly (FR-17).

**Create an expense (exact split):**
```json
{
  "description": "Dinner",
  "amount": "1200.00",
  "paid_by_id": 2,
  "split_type": "EXACT",
  "shares": [
    {"member_id": 1, "share_amount": "500.00"},
    {"member_id": 2, "share_amount": "700.00"}
  ]
}
```

**Balances** `GET /api/v1/groups/1/balances` → `200`:
```json
{
  "group_id": 1,
  "currency": "NPR",
  "balances": [
    {"member_id": 1, "member_name": "Sandesh", "balance": "666.66"},
    {"member_id": 2, "member_name": "Bikash",  "balance": "-333.33"},
    {"member_id": 3, "member_name": "Anita",   "balance": "-333.33"}
  ]
}
```

**Settlement plan** `GET /api/v1/groups/1/settlement-plan` → `200`:
```json
{
  "group_id": 1,
  "currency": "NPR",
  "transfers": [
    {"from_member_id": 2, "from_member_name": "Bikash", "to_member_id": 1, "to_member_name": "Sandesh", "amount": "333.33"},
    {"from_member_id": 3, "from_member_name": "Anita",  "to_member_id": 1, "to_member_name": "Sandesh", "amount": "333.33"}
  ],
  "transfer_count": 2
}
```

## 12.4 Error contract

Every error response has this shape (FR-33):

```json
{"detail": "Member 9 does not belong to group 1", "code": "MEMBER_NOT_IN_GROUP"}
```

| HTTP | When | Example codes |
|---|---|---|
| 404 | Referenced resource does not exist | `GROUP_NOT_FOUND`, `MEMBER_NOT_FOUND`, `EXPENSE_NOT_FOUND` |
| 409 | Request conflicts with current state | `DUPLICATE_MEMBER_NAME`, `MEMBER_HAS_ACTIVITY` |
| 422 | Request is well-formed but semantically invalid | `PAYER_NOT_IN_GROUP`, `PARTICIPANT_NOT_IN_GROUP`, `DUPLICATE_PARTICIPANT`, `NO_PARTICIPANTS`, `SHARES_DO_NOT_SUM`, `NEGATIVE_SHARE`, `SAME_MEMBER_SETTLEMENT`, `MEMBER_NOT_IN_GROUP` |
| 422 | Schema validation failure (types, lengths, bounds) | FastAPI's standard validation body |
| 500 | Unexpected server fault | `INTERNAL_ERROR` (no internal details leaked, NFR-12) |

The full list of error codes must be documented in `docs/API.md` and reflected in each route's OpenAPI `responses`.

---

# 13. Testing Requirements

## 13.1 Test layers

| Layer | Location | Database? | Purpose |
|---|---|---|---|
| Unit | `tests/unit/` | **No** | Pure logic: splitting, balances, settlement planning, schema validation. Must run with no Docker and no network. |
| Integration | `tests/integration/` | **Yes** | Real HTTP requests through FastAPI → SQLAlchemy → PostgreSQL. Proves the layers work together. |

## 13.2 Test isolation strategy

- Integration tests run against a **separate database** (`fairshare_test`), never the development database.
- The database URL is supplied by `TEST_DATABASE_URL`, defaulting to a local PostgreSQL test database.
- A session-scoped fixture creates all tables once and drops them at the end.
- A function-scoped fixture truncates all tables (with identity restart) between tests, so every test starts from a known empty state and test order never affects results.

## 13.3 Mandatory unit test scenarios

**Equal split (`services/splitting.py`)**
- Amount divides evenly among participants.
- Amount does not divide evenly — remainder distributed, shares sum exactly to the total.
- Single participant receives the whole amount.
- Smallest possible amount (`0.01`) among 3 participants.
- Large amount with many participants — sum invariant holds.
- Empty participant list raises the documented error.

**Exact split**
- Shares summing exactly to the total are accepted.
- Shares over by `0.01` are rejected.
- Shares under by `0.01` are rejected.
- A zero share for one participant is accepted.
- A negative share is rejected.
- A missing participant in the share list is rejected.

**Balance computation (`services/balances.py`)**
- Single payer, equal split — payer positive, others negative.
- Everyone pays an equal amount — all balances zero.
- Balances always sum to exactly zero (checked across several scenarios).
- Settlements reduce the payer's debt and the receiver's credit correctly.
- A member with no activity has a zero balance.

**Settlement plan (`services/settlement_plan.py`)**
- Already-settled group produces an empty plan.
- Two members, one debt → exactly one transfer.
- Circular debt A→B→C→A nets out to fewer transfers than debts.
- Transfer count never exceeds `n − 1`.
- Executing the plan drives all balances to zero (property-style check).
- The plan is deterministic across repeated runs.
- Amounts in the plan are never negative or zero.

**Schema validation (`schemas/`)**
- Blank and whitespace-only names rejected.
- Over-length name/description rejected.
- Zero, negative, and 3-decimal amounts rejected.
- Invalid currency codes rejected.
- Invalid `split_type` rejected.

## 13.3 Mandatory integration test scenarios

- Health endpoint returns 200 with the expected payload.
- Full happy path: create group → add 3 members → add 2 expenses → check balances → get plan → record settlement → balances updated.
- Every endpoint's 404 path (non-existent group, member, expense).
- Duplicate member name → 409 with the correct code.
- Deleting a member with activity → 409; deleting an uninvolved member → 204.
- Deleting a group cascades: its members and expenses are gone afterwards.
- Deleting an expense changes the balances accordingly.
- Payer not in group → 422 with the correct code.
- Participant not in group / duplicated / empty list → 422 with correct codes.
- Exact shares not summing → 422 with `SHARES_DO_NOT_SUM`.
- Settlement between the same member → 422.
- Pagination: `limit` and `offset` return the expected slices; out-of-range values are rejected.
- Monetary values are returned as two-decimal strings.
- The unequal-split rounding case is visible end-to-end (`1000.00 / 3`).

## 13.4 Test quality rules

- Every test has a descriptive name stating the behaviour it verifies.
- Every test asserts on meaningful values, not merely on the absence of an exception.
- No test exists solely to raise the coverage number.
- Tests must not depend on execution order or on data left behind by other tests.
- Tests must pass identically on a developer machine and in CI.

---

# 14. Docker Requirements

## 14.1 Dockerfile

| ID | Requirement |
|---|---|
| D-1 | Base image `python:3.12-slim` (matches NFR-15). |
| D-2 | Environment: `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`. |
| D-3 | Dependencies installed from `requirements.txt` in a layer **before** the source is copied, so code changes do not invalidate the dependency cache. |
| D-4 | Application runs as a **non-root** user. |
| D-5 | Exposes port 8000 and starts Uvicorn bound to `0.0.0.0:8000`. |
| D-6 | A container `HEALTHCHECK` probes the health endpoint. |
| D-7 | `.dockerignore` excludes `.git`, `.venv`, `__pycache__`, `htmlcov`, `.pytest_cache`, tests-only artefacts, and documentation, keeping the build context small. |

## 14.2 compose.yaml

| ID | Requirement |
|---|---|
| D-8 | Two services: `api` (built locally) and `db` (`postgres:16-alpine`). |
| D-9 | `db` defines a `pg_isready` healthcheck; `api` uses `depends_on: condition: service_healthy`. |
| D-10 | `db` persists data in a named volume `pgdata`. |
| D-11 | `DATABASE_URL` is passed to `api` as an environment variable — never hard-coded in Python. |
| D-12 | `api` publishes `8000:8000`; `db` publishes `5432:5432` so the same instance can serve the local test database. |
| D-13 | `docker compose up --build` brings the whole stack to a working state with one command, from a clean machine. |

## 14.3 Docker verification (must actually be performed)

1. `docker compose config` parses without error.
2. `docker compose up --build -d` starts both containers.
3. `docker compose ps` shows both services running and `db` healthy.
4. The health endpoint responds through the published port.
5. A create-group request and a read-back request succeed against the containerised stack.
6. `docker compose down -v` tears everything down cleanly.

---

# 15. CI Requirements

## 15.1 Workflow

Path: `.github/workflows/ci.yml`, name `CI`.

**Triggers:** every push to `main` and to `feature/**`, and every pull request targeting `main`.

**Job 1 — `test` (ubuntu-latest)**

| ID | Step |
|---|---|
| CI-1 | Start a PostgreSQL 16 **service container** with a health check and the credentials the tests expect. |
| CI-2 | Check out the repository. |
| CI-3 | Set up Python 3.12 with pip caching. |
| CI-4 | Install pinned dependencies from `requirements.txt` and `requirements-dev.txt`. |
| CI-5 | Run `ruff check` and `ruff format --check` — lint failures fail the build. |
| CI-6 | Run the full test suite with coverage against the service database. |
| CI-7 | Enforce the coverage gate `--cov-fail-under=90` — insufficient coverage fails the build. |
| CI-8 | Upload `coverage.xml` and the HTML report as build artefacts. |

**Job 2 — `docker` (ubuntu-latest)**

| ID | Step |
|---|---|
| CI-9 | Build the Docker image from the repository `Dockerfile`. |
| CI-10 | Start the full stack with Compose, wait for health, request the health endpoint, and tear the stack down. Failure of any step fails the build. |

## 15.2 CI rules

- A failing test, a lint error, or coverage below the gate **must** turn the run red. This must be proven at least once (an intentionally broken commit on a branch, observed failing, then fixed).
- The workflow must not depend on any secret, paid service, or manual step.
- The workflow must be green on `main` at submission time.

---

# 16. Clean Coding Requirements

| ID | Requirement |
|---|---|
| C-1 | Names state intent: `suggest_settlements`, `split_equally`, `MemberHasActivityError`. No `data`, `tmp`, `res`, `x`. |
| C-2 | One responsibility per module; the layering rule of §10.2 is not violated anywhere. |
| C-3 | Functions stay under ~40 lines and do one thing (NFR-6). |
| C-4 | Complete type hints on every function signature (NFR-5). |
| C-5 | Docstrings explain *why* a unit exists and any non-obvious rule; they never restate the code. |
| C-6 | No magic numbers — `MONEY_PRECISION`, `MAX_EXPENSE_AMOUNT`, `DEFAULT_CURRENCY` and similar live in `app/constants.py`. |
| C-7 | No duplicated logic: rounding exists in exactly one function; group lookup exists in exactly one place. |
| C-8 | No dead code, no commented-out blocks, no unused imports or variables — enforced by Ruff, not by eye alone. |
| C-9 | Consistent formatting via `ruff format`; the repository must be format-clean. |
| C-10 | Errors are raised as domain exceptions and translated centrally; no ad-hoc error dictionaries in routers. |
| C-11 | No secrets, credentials, or connection strings with real passwords in source (NFR-10). |
| C-12 | Imports ordered and grouped (stdlib / third-party / local) — enforced by Ruff's isort rules. |
| C-13 | A documented self-review pass is performed before submission, and every genuine issue found is fixed in its own commit. |

Ruff configuration lives in `pyproject.toml` and must enable at minimum: `E`, `F`, `I`, `B`, `UP`, `SIM`, `C4`, `ARG`.

---

# 17. API Documentation Requirements

| ID | Requirement |
|---|---|
| A-1 | Interactive Swagger UI available at `/docs`. |
| A-2 | ReDoc reference available at `/redoc`. |
| A-3 | Machine-readable OpenAPI schema at `/openapi.json`. |
| A-4 | The FastAPI app declares `title`, `description`, `version`, `contact`, and `openapi_tags` with a description for every tag (`health`, `groups`, `members`, `expenses`, `balances`, `settlements`). |
| A-5 | Every route declares `summary`, `description`, `tags`, `status_code`, `response_model`, and a `responses` entry for each documented error status. |
| A-6 | Every Pydantic field declares a `description` and, where useful, an `examples` value, so the generated docs explain each field's meaning. |
| A-7 | A written reference `docs/API.md` documents every endpoint with a `curl` example, a sample response, and the error codes it can return. |
| A-8 | A committed snapshot `docs/openapi.json`, exported from the running application by `scripts/export_openapi.py`, proving the documentation is generated rather than hand-written. |
| A-9 | The documentation must be **verified live**: `/docs`, `/redoc`, and `/openapi.json` are opened and confirmed to render all 18 endpoints. |

---

# 18. Test Coverage Requirements

| ID | Requirement |
|---|---|
| T-1 | Coverage is measured with `pytest-cov` over the `app/` package. |
| T-2 | **Minimum overall line coverage: 90%.** The build fails below this (`--cov-fail-under=90`). |
| T-3 | `app/services/` — the core business logic — must reach **100%** line coverage. |
| T-4 | Three report formats are produced: `term-missing` (terminal), `html` (`htmlcov/`), and `xml` (`coverage.xml`, for CI artefacts). |
| T-5 | Coverage configuration lives in `pyproject.toml`; generated reports are git-ignored and never committed. |
| T-6 | The actual measured percentage is recorded verbatim in `PROJECT_NOTES.md` — never estimated, rounded up, or invented. |
| T-7 | Gaps revealed by `term-missing` are closed with tests that assert real behaviour, not with tests written only to execute lines. |

---

# 19. Git / Version Control Workflow

## 19.1 Principles

- Git is initialised **before the first line of code** and every stage of development produces its own commit.
- Commits are genuine: real changes, real timestamps, one author. No empty commits, no backdating, no fabricated collaborators, no padding.
- The repository is developed by one person; the workflow reflects that honestly.

## 19.2 Branch model

```
main                     always working; every merge is a completed stage
 ├── feature/foundation   project skeleton, config, dependencies, database bootstrap
 ├── feature/domain-model ORM models, constraints, Pydantic schemas
 ├── feature/core-logic   pure services: splitting, balances, settlement planning
 ├── feature/api          repositories, routers, error handling
 ├── feature/testing      unit + integration suites, coverage configuration
 ├── feature/docker       Dockerfile, compose stack, .dockerignore
 ├── feature/ci           GitHub Actions workflow
 └── feature/docs         README, API reference, project notes
```

Each branch is created from an up-to-date `main`, developed with several commits, then merged back with `git merge --no-ff` so the merge point is visible in the history graph. Branches are **not deleted**, so the graph remains legible at assessment time.

## 19.3 Commit message convention

Conventional Commits: `type: imperative summary` (≤ 72 characters).

Permitted types: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`, `ci`, `perf`, `style`.

Each commit contains one logical change. Commits are made *at the moment the work is completed*, not reconstructed afterwards.

**Target: 18–25 genuine commits**, driven by the actual work rather than by the number.

## 19.4 GitHub

The remote repository is created manually by the author. The push sequence, the pull-request step, and CI verification are recorded in `PROJECT_NOTES.md` as performed.

At least **one real pull request** must exist: the final branch is pushed *before* being merged, a PR is opened against `main`, CI runs on that PR, and the merge happens on GitHub. This demonstrates the review workflow honestly for a solo developer — self-authored, self-merged, with a genuine CI check.

---

# 20. Expected Project Structure

```text
fairshare-api/
│
├── app/
│   ├── __init__.py
│   ├── main.py                    FastAPI app, handlers, router registration
│   ├── config.py                  environment-driven settings
│   ├── constants.py               named constants (no magic numbers)
│   ├── database.py                engine, session factory, get_db dependency
│   ├── errors.py                  domain exception hierarchy
│   │
│   ├── models/                    SQLAlchemy ORM (persistence layer)
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── group.py
│   │   ├── member.py
│   │   ├── expense.py
│   │   └── settlement.py
│   │
│   ├── schemas/                   Pydantic contracts (API layer)
│   │   ├── __init__.py
│   │   ├── common.py              shared field types (money, non-blank names)
│   │   ├── health.py
│   │   ├── group.py
│   │   ├── member.py
│   │   ├── expense.py
│   │   ├── settlement.py
│   │   └── balance.py
│   │
│   ├── services/                  PURE business logic — no DB, no framework
│   │   ├── __init__.py
│   │   ├── money.py               single rounding/quantisation authority
│   │   ├── splitting.py           equal & exact split algorithms
│   │   ├── balances.py            net balance computation
│   │   └── settlement_plan.py     greedy minimal-transfer planner
│   │
│   ├── repositories/              all database access
│   │   ├── __init__.py
│   │   ├── balances.py            aggregate SUM queries behind balances
│   │   ├── groups.py
│   │   ├── members.py
│   │   ├── expenses.py
│   │   └── settlements.py
│   │
│   └── routers/                   HTTP routing only
│       ├── __init__.py
│       ├── health.py
│       ├── groups.py
│       ├── members.py
│       ├── expenses.py
│       ├── balances.py
│       └── settlements.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                DB fixtures, TestClient, table truncation
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_money.py
│   │   ├── test_splitting.py
│   │   ├── test_balances.py
│   │   ├── test_settlement_plan.py
│   │   └── test_schemas.py
│   └── integration/
│       ├── __init__.py
│       ├── test_health_api.py
│       ├── test_groups_api.py
│       ├── test_members_api.py
│       ├── test_expenses_api.py
│       ├── test_balances_api.py
│       └── test_settlements_api.py
│
├── docs/
│   ├── API.md                     written endpoint reference with curl examples
│   └── openapi.json               exported OpenAPI snapshot
│
├── scripts/
│   └── export_openapi.py          regenerates docs/openapi.json
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── Dockerfile
├── compose.yaml
├── .dockerignore
├── .gitignore
├── .env.example                   documents required variables; holds no secrets
├── pyproject.toml                 ruff + pytest + coverage configuration
├── requirements.txt               pinned runtime dependencies
├── requirements-dev.txt           pinned development/test dependencies
├── README.md
├── PROJECT_NOTES.md               factual notes for the written report
└── GUIDE.md                       this specification
```

---

# 21. Definition of Done

The project is done only when **every** statement below is true and has been observed, not assumed.

**Functionality**
1. All 18 endpoints (§12.2) exist and behave as specified.
2. All 35 functional requirements (§7) are implemented.
3. Every documented error code is reachable and returns the documented status.

**Quality**
4. `ruff check` and `ruff format --check` both pass with zero findings.
5. The full test suite passes locally with zero failures.
6. Overall coverage ≥ 90%; `app/services/` at 100%.
7. The clean-code self-review (§16, C-13) is complete and its fixes are committed.

**Infrastructure**
8. `docker compose up --build` starts the stack, and the API answers requests inside Docker.
9. The GitHub Actions workflow is green on `main`, including the Docker build job.
10. CI has been demonstrated to fail on a broken test at least once.

**Documentation**
11. `/docs`, `/redoc`, and `/openapi.json` all render the complete API.
12. `docs/API.md` documents every endpoint with working `curl` examples.
13. `README.md` explains what the project is, how to run it (Docker and local), and how to test it.
14. `PROJECT_NOTES.md` contains only factual, verified information.

**Version control**
15. 18–25 genuine commits with conventional messages.
16. All feature branches exist in the history with visible `--no-ff` merge points.
17. At least one real pull request exists on GitHub with a CI check.
18. No secrets, virtual environments, or generated artefacts are tracked by Git.

---

# 22. Final Verification Checklist

Every item is verified by running the stated command and observing the stated result. Each is reported at the end as **PASS**, **FAIL**, or **MANUAL ACTION REQUIRED**.

## 22.1 Repository

```text
[ ] Git repository initialised, working tree clean          git status
[ ] 18–25 genuine commits, conventional messages            git log --oneline
[ ] All feature branches present with merge commits         git log --graph --all --oneline
[ ] Current branch is main                                  git branch --show-current
[ ] .gitignore excludes .venv, __pycache__, htmlcov, .env   cat .gitignore
[ ] No secrets or .env file tracked                         git ls-files | grep -i env
```

## 22.2 Code quality

```text
[ ] Lint clean                                              ruff check .
[ ] Format clean                                            ruff format --check .
[ ] Layering rule respected (services import no framework)  manual inspection
[ ] No unused imports, dead code, or magic numbers          ruff + review
```

## 22.3 Tests and coverage

```text
[ ] All tests pass                                          pytest
[ ] Unit tests pass without a database                      pytest tests/unit
[ ] Coverage ≥ 90% overall                                  pytest --cov=app --cov-report=term-missing
[ ] app/services at 100%                                    coverage table
[ ] HTML report generated and opened                        htmlcov/index.html
[ ] coverage.xml generated                                  ls coverage.xml
[ ] Actual percentage recorded in PROJECT_NOTES.md          manual
```

## 22.4 Docker

```text
[ ] Compose file valid                                      docker compose config
[ ] Stack builds and starts                                 docker compose up --build -d
[ ] Both containers running, db healthy                     docker compose ps
[ ] Health endpoint answers through the container           curl localhost:8000/
[ ] A full create → read flow works in Docker               curl POST + GET
[ ] Stack tears down cleanly                                docker compose down -v
```

## 22.5 CI

```text
[ ] Workflow file present and valid                         .github/workflows/ci.yml
[ ] Workflow runs on push and pull request
[ ] Test job green on main                                  GitHub → Actions
[ ] Docker job green on main                                GitHub → Actions
[ ] Coverage artefact downloadable                          GitHub → Actions → Artifacts
[ ] A red run exists proving CI catches failures            GitHub → Actions history
```

## 22.6 API documentation

```text
[ ] Swagger UI lists all 18 endpoints                       http://localhost:8000/docs
[ ] ReDoc renders the API                                   http://localhost:8000/redoc
[ ] OpenAPI JSON served                                     http://localhost:8000/openapi.json
[ ] docs/API.md complete with curl examples                 manual read
[ ] docs/openapi.json exported and current                  python scripts/export_openapi.py
```

## 22.7 Submission

```text
[ ] README.md complete and accurate
[ ] PROJECT_NOTES.md complete and factual
[ ] GUIDE.md (this file) matches what was actually built
[ ] Repository pushed to GitHub, all branches visible
[ ] At least one pull request with a CI check
[ ] Final audit table produced (every requirement PASS/FAIL/MANUAL)
```

---

## END OF SPECIFICATION

This document is the contract for the project. If implementation reveals that a requirement is wrong or impossible, the requirement is **changed here first**, with the reason recorded, and only then in the code. Silent divergence between this specification and the codebase is not permitted.
