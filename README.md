
# MDM Platform — Development Setup

Master Data Management platform built using Django and Django REST Framework.

The initial domain will manage:

- Consumers
- Service Points
- Devices

## Technology Stack

- Python 3.13
- Django 6
- Django REST Framework
- Django Tasks
- Celery
- django-celery-beat
- Redis
- PostgreSQL 15
- pgAdmin
- `uv` for Python dependency and virtual environment management
- Docker Compose for local infrastructure

---

## 1. Initialize the Python Project

Create the project directory and initialize it using `uv`.

```bash
uv init
```

This creates the initial `pyproject.toml`.

---

## 2. Install Django and Required Dependencies

Install Django, Django REST Framework, Django Tasks, Celery, and Celery Beat:

```bash
uv add django djangorestframework django-tasks django-celery-beat celery
```

Install the Redis Python client:

```bash
uv add redis
```

Install Psycopg 3 for PostgreSQL connectivity:

```bash
uv add "psycopg[binary]"
```

### Verify Installed Dependencies

```bash
uv tree
```

The important dependencies should include:

```text
django
djangorestframework
django-tasks
celery
django-celery-beat
redis
psycopg
```

`psycopg[binary]` installs the precompiled Psycopg implementation, avoiding the need to compile the PostgreSQL driver locally.

---

## 3. Create the Django Project

Create the Django project in the current directory:

```bash
uv run django-admin startproject config .
```

The project should now look approximately like:

```text
mdm-platform/
├── config/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
├── pyproject.toml
└── uv.lock
```

Verify the Django configuration:

```bash
uv run python manage.py check
```

Expected result:

```text
System check identified no issues (0 silenced).
```

---

## 4. Configure Local Infrastructure

Create a `docker-compose.yaml` file in the project root.

```yaml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: mdm-platform
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d mdm-platform"]
      interval: 10s
      timeout: 5s
      retries: 5
    volumes:
      - postgres_data:/var/lib/postgresql/data

  pgadmin:
    image: dpage/pgadmin4
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@admin.com
      PGADMIN_DEFAULT_PASSWORD: root
    ports:
      - "80:80"
    depends_on:
      postgres:
        condition: service_healthy

  redis:
    image: redis:8-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Services

| Service    | Host          |     Port |
| ---------- | ------------- | -------: |
| PostgreSQL | `localhost` | `5432` |
| pgAdmin    | `localhost` |   `80` |
| Redis      | `localhost` | `6379` |

pgAdmin can therefore be opened at:

```text
http://localhost
```

The development credentials are:

```text
Email:    admin@admin.com
Password: root
```

---

## 5. Start the Docker Services

Start PostgreSQL, Redis, and pgAdmin:

```bash
docker compose up -d
```

Check their status:

```bash
docker compose ps
```

PostgreSQL and Redis should eventually show:

```text
(healthy)
```

Redis can also be tested directly:

```bash
docker compose exec redis redis-cli ping
```

Expected response:

```text
PONG
```

To stop the infrastructure:

```bash
docker compose down
```

To start it again:

```bash
docker compose up -d
```

> The PostgreSQL and Redis data are stored in Docker named volumes, so `docker compose down` does not normally delete the data.

---

## 6. Configure Django to Use PostgreSQL

Django uses SQLite by default.

Replace the default `DATABASES` configuration in:

```text
config/settings.py
```

with:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "mdm-platform",
        "USER": "postgres",
        "PASSWORD": "password",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
```

The local connection is therefore:

```text
Django
   │
   │ localhost:5432
   ▼
Docker
   │
   ▼
PostgreSQL :5432
   │
   ▼
mdm-platform
```

Because Django currently runs directly on the host machine, `localhost` is used.

If Django is later containerized in the same Docker Compose network, the configuration would instead use:

```text
HOST=postgres
PORT=5432
```

---

## 7. Run Django Database Migrations

Apply Django's built-in migrations:

```bash
uv run python manage.py migrate
```

This creates the standard Django tables for:

```text
admin
auth
contenttypes
sessions
```

Verify migration status:

```bash
uv run python manage.py showmigrations
```

Applied migrations are displayed with:

```text
[X]
```

For example:

```text
admin
 [X] 0001_initial
 [X] 0002_logentry_remove_auto_add
 [X] 0003_logentry_add_action_flag_choices
```

---

## 8. Run the Django Development Server

Start Django:

```bash
uv run python manage.py runserver
```

The development server is available at:

```text
http://127.0.0.1:8000/
```

---

## 9. Planned Background Task Architecture

The MDM platform will use Django Tasks as the application-facing task abstraction.

The intended architecture is:

```text
              Django / DRF
                   │
                   ▼
             Django Tasks
                   │
                   ▼
              Celery
                   │
              Redis Broker
                   │
                   ▼
            Celery Workers
```

Responsibilities:

### Django Tasks

Application-facing API for defining and enqueueing background work.

### Celery

Runs background tasks using worker processes.

### Redis

Acts as the messaging/broker infrastructure used by the task execution system.

### django-celery-beat

Provides database-backed scheduling for periodic Celery jobs.

Potential MDM background jobs include:

```text
Bulk device imports
        │
        ├── Validation
        ├── Transformation
        ├── Consumer creation/update
        ├── Service Point creation/update
        └── Device creation/update

Device synchronization

External system synchronization

Master-data reconciliation

Bulk exports

Scheduled cleanup jobs

Scheduled reconciliation jobs
```

---

## 10. Planned MDM Domain Structure

The initial Django applications are expected to represent the main MDM domains:

```text
mdm-platform/
│
├── config/
│
├── consumers/
│
├── service_points/
│
├── devices/
│
├── integrations/
│
├── manage.py
├── docker-compose.yaml
├── pyproject.toml
└── uv.lock
```

Potential commands for creating these applications:

```bash
uv run python manage.py startapp consumers
uv run python manage.py startapp service_points
uv run python manage.py startapp devices
```

The initial domain relationship is expected to resemble:

```text
Consumer
    │
    ▼
Service Point
    │
    ▼
Device Installation
    │
    ▼
Device
```

Using an installation/association model instead of simply storing a device foreign key on a Service Point allows the MDM to retain historical relationships when meters are replaced.

For example:

```text
Service Point: SP000123

Meter ABC123
2024-01-01 ────────────── 2026-05-15

                         Meter XYZ789
                         2026-05-15 ──────────>
```

The exact domain model will be designed before creating the migrations.

---

## 11. Useful Development Commands

### Check Django configuration

```bash
uv run python manage.py check
```

### Create migrations

```bash
uv run python manage.py makemigrations
```

### Apply migrations

```bash
uv run python manage.py migrate
```

### Show migration status

```bash
uv run python manage.py showmigrations
```

### Start Django

```bash
uv run python manage.py runserver
```

### Show Python dependency tree

```bash
uv tree
```

### Start infrastructure

```bash
docker compose up -d
```

### Check containers

```bash
docker compose ps
```

### Stop infrastructure

```bash
docker compose down
```

### Check Redis

```bash
docker compose exec redis redis-cli ping
```

### View container logs

```bash
docker compose logs
```

Follow logs continuously:

```bash
docker compose logs -f
```

---

## 12. Local Development Architecture

```text
                         ┌─────────────────────┐
                         │    Django + DRF     │
                         │   localhost:8000    │
                         └──────────┬──────────┘
                                    │
                 ┌──────────────────┴──────────────────┐
                 │                                     │
                 ▼                                     ▼
        ┌─────────────────┐                   ┌─────────────────┐
        │   PostgreSQL    │                   │  Django Tasks   │
        │ localhost:5432  │                   └────────┬────────┘
        │  mdm-platform   │                            │
        └─────────────────┘                            ▼
                                                   Celery
                                                      │
                                                      ▼
                                             ┌─────────────────┐
                                             │      Redis      │
                                             │ localhost:6379  │
                                             └─────────────────┘
                                                      │
                                                      ▼
                                               Celery Workers


        ┌─────────────────┐
        │     pgAdmin     │
        │ localhost:80    │
        └─────────────────┘
```

---

## Current Status

Completed:

- [X] Initialized project with `uv`
- [X] Installed Django
- [X] Installed Django REST Framework
- [X] Installed Django Tasks
- [X] Installed Celery
- [X] Installed django-celery-beat
- [X] Installed Redis Python client
- [X] Installed Psycopg
- [X] Created Django project
- [X] Created PostgreSQL Docker service
- [X] Created Redis Docker service
- [X] Created pgAdmin Docker service
- [X] Connected Django to PostgreSQL
- [X] Applied initial Django migrations
- [X] Verified Django configuration

Next:

- [ ] Design MDM domain models
- [ ] Create Consumer application
- [ ] Create Service Point application
- [ ] Create Device application
- [ ] Configure Django REST Framework
- [ ] Configure Django Tasks
- [ ] Configure Celery workers
- [ ] Connect task execution to Redis
- [ ] Configure django-celery-beat
- [ ] Implement first real MDM background task

---

## Development Notes

The database credentials currently stored in `settings.py` and `docker-compose.yaml` are intended for local development only.

Before production deployment, database credentials and other secrets should be supplied through environment variables or a secrets-management mechanism rather than committed directly to source control.
