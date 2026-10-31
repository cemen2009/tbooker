# TBooker 🍽️

> A restaurant table-booking API-shaped playground. Built to try technologies,
> learn by shipping, and see what breaks — not to solve a business problem.
> It's not wind, gang; it's a side project. 😭🌹

## The vibe

TBooker models a world where people book restaurant tables across cities,
restaurants have opening hours, and tables should not get double-booked. The
domain is here to give the tech something real to work with; there is no
business plan, production promise, or grand startup arc. Just curiosity,
experiments, and the occasional "holy molly, why is that failing?" 🙏

The goal is to explore modern Python backend practices in a small project:
typed models, async database access, validation at API boundaries, migrations,
and database constraints for rules that must survive concurrent requests.
No fake "enterprise-grade" flex — learn the pattern, test it, keep it moving.
✌️

## Stack right now

- **Python 3.12+**
- **FastAPI** for the ASGI application
- **Pydantic 2** for settings and request/response schemas
- **SQLAlchemy 2** with its async ORM API
- **PostgreSQL** via `asyncpg`
- **Alembic** for database migrations
- **Redis** and **MinIO** are part of the planned/available infrastructure
- **pytest**, **pytest-asyncio**, **testcontainers**, and **Ruff** for tests and
  code quality
- **Docker Compose** for local PostgreSQL and Redis services

## How it's put together

- `src/models/orm/` contains SQLAlchemy entities for cities, restaurants,
  tables, bookings, and users.
- `src/models/schemas/` contains Pydantic schemas for API inputs and outputs.
- `src/repositories/` is where persistence/query logic is being organized.
- `src/core/` holds configuration, database sessions, migrations, logging, and
  security helpers.
- `src/main.py` creates the FastAPI app and currently exposes a health check.

The intent is to keep responsibilities understandable: schemas validate and
shape API data, repositories handle persistence and queries, application
services (as they arrive) coordinate use cases, and PostgreSQL enforces
important invariants. For example, preventing overlapping bookings for one
table belongs at the database boundary too, because two requests can race.

## Status

This is an evolving learning project, not a finished booking product. The
domain models, schemas, migrations, and foundational plumbing are being built
out; the API currently has a health endpoint, and the booking workflows are
still a work in progress. Expect experiments, refactors, and the occasional
airball. 🏀

## Run locally

Install dependencies with Poetry:

```bash
poetry install
```

Start the local infrastructure:

```bash
docker compose up -d postgres redis
```

Configure the environment using `.env.example` as a guide, then run the
application:

```bash
poetry run uvicorn main:app --app-dir src --reload
```

Run the test suite:

```bash
poetry run pytest
```

Tests that use PostgreSQL run it with Testcontainers, so Docker needs to be
available. Check `/health` for the tiny "we're alive" signal.

## Project motto

Try the thing. Read the docs. Add the test. Refactor when the pattern gets
clearer. If the first attempt is an airball, that's data — not a tragedy.
Tung tung sahur, 67, we go again. 🙏✌️😭
