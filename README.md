# SchemaTrace

> A developer tool for building queryable audit logs of database schema evolution

In Active Development - CLI in progress

---

## Overview

SchemaTrace analyzes database migration files to create a **structured, queryable history** of how your database schema has evolved over time. Instead of manually diffing migration files or running databases to understand changes, SchemaTrace provides:

- **Event-sourced schema tracking** - Every schema change is stored as a discrete event
- **Time-travel queries** - Reconstruct your schema at any point in history
- **Change explanations** - Understand what changed, when, and why
- **Risk detection** - Flag potentially dangerous migrations (dropping columns, removing indexes)


**Key Components:**
- **FastAPI Backend**: REST API for managing projects, models, and schema events
- **PostgreSQL Database**: Event-sourced storage with materialized field views
- **CLI Tool**: Scans migration files and uploads events to backend
- **Adapter System**: Pluggable parsers for different frameworks (Django, Alembic, etc.)

---

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 16+
- Poetry (dependency management)

### Installation

```bash
# Clone repository
git clone <repo-url>
cd schema-trace

# Install dependencies
poetry install

# Start PostgreSQL (using Docker)
docker-compose up -d

# Create database tables
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head

# Start backend server
poetry run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

API docs: `http://localhost:8000/docs`

### CLI Setup (When Implemented)

```bash
# Install CLI globally
poetry install

# Initialize configuration
schematrace config --set-api-url http://localhost:8000
schematrace config --set-api-key your-key-here

# Create a project
schematrace init --project "my-django-app"

# Scan migrations
schematrace scan ./my_app/migrations/ --project "my-django-app"

# View results
schematrace projects
```


## API Examples

### Create a Project

```bash
curl -X POST http://localhost:8000/projects/ \
  -H "Content-Type: application/json" \
  -d '{"name": "ecommerce", "description": "E-commerce platform"}'
```

### Get Model with Fields

```bash
curl http://localhost:8000/models/1/full?include_removed=false
```

Response:
```json
{
  "id": 1,
  "name": "User",
  "description": "User accounts",
  "project_id": 1,
  "created_at": "2024-01-12T10:30:00",
  "fields": [
    {
      "name": "email",
      "field_type": "varchar(120)",
      "nullable": false,
      "unique": true,
      "default_value": null,
      "added_at": "2024-01-12T10:30:00"
    }
  ]
}
```

### Bulk Upload Events (CLI Workflow)

```bash
curl -X POST http://localhost:8000/events/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {
        "model_id": 1,
        "event_type": "ADD_COLUMN",
        "field_name": "email",
        "timestamp": "2024-01-12T10:30:00",
        "metadata": {"type": "varchar(120)", "nullable": false},
        "risk_level": "low"
      }
    ]
  }'
```

---

## Technology Stack

**Backend:**
- FastAPI 0.128.0
- SQLAlchemy 2.0.46
- PostgreSQL 16
- Alembic 1.18.3 (migrations)
- Pydantic 2.x (validation)
- Uvicorn 0.40.0 (ASGI server)

**CLI:**
- Click 8.1.0 (command framework)
- Rich 13.7.0 (terminal formatting)
- Requests 2.31.0 (HTTP client)
- Pydantic-settings 2.0.0 (config)

**Development:**
- Poetry (dependency management)
- Docker Compose (PostgreSQL)
- Python 3.11+

---

## Development Workflow

```bash
# Start PostgreSQL
docker-compose up -d

# Run backend with auto-reload
poetry run uvicorn app.main:app --reload --log-level debug

# Run tests (when implemented)
poetry run pytest

# Create new migration
alembic revision --autogenerate -m "Description"
alembic upgrade head

# Format code
poetry run black .
poetry run isort .
```

### Testing with Sample Migrations

Place test Django migrations in `tests/fixtures/django_migrations/`:

```python
# tests/fixtures/django_migrations/0001_initial.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = []

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(primary_key=True)),
                ('email', models.EmailField(unique=True)),
            ],
        ),
    ]
```

---

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps

# View logs
docker-compose logs -f postgres

# Restart container
docker-compose restart postgres
```

### Alembic Migration Issues

```bash
# Check current revision
alembic current

# View migration history
alembic history

# Rollback one migration
alembic downgrade -1

# Reset database (destructive!)
alembic downgrade base
alembic upgrade head
```