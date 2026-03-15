# Pi-Gateway API

FastAPI-based RESTful API for managing proxy gateway infrastructure, user authentication, domain filtering, and access logging.

High-performance backend service built with **FastAPI**, **SQLAlchemy**, and **SQLite** providing comprehensive REST endpoints for the Pi-Gateway system.

## Table of Contents

- [Features](#features)
- [Local Development Setup](#local-development-setup)
- [Available Scripts](#available-scripts)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Database](#database)
- [Authentication](#authentication)
- [Configuration](#configuration)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Dependencies](#dependencies)

## Features

- 🔐 **JWT Authentication**: Secure token-based API authentication
- 👥 **User Management**: Create, update, and manage application users
- 🌐 **Domain Management**: Whitelist/blacklist domain filtering with approval workflow
- 📊 **Access Logging**: Comprehensive audit logs of proxy access and activities
- 🔄 **Hot Reload**: Fast development with automatic reload support
- 📝 **Auto Documentation**: FastAPI built-in API documentation
- 🗄️ **Database Migrations**: Alembic for schema management
- 🧪 **Testing**: Pytest integration with async support

## Local Development Setup

### Prerequisites

- **Python** 3.12+
- **uv** package manager or pip
- **SQLite3** (usually included with Python)
- **Git**

### Quick Start

#### 1. Install Dependencies

```bash
cd api
pip install -e .
```

Or using `uv`:
```bash
uv pip install -e .
```

#### 2. Set Environment Variables

```bash
export API_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=admin-password
export DB_URL="sqlite+aiosqlite:///./dev.db"
export SQUID_CONTAINER=localhost
```

#### 3. Initialize Database

```bash
alembic upgrade head
```

This runs database migrations to set up the schema with necessary tables.

#### 4. Start Development Server

```bash
python -m uvicorn src.api.main:app --reload --port 8000
```

The API will be available at **http://localhost:8000**

#### 5. Test the API

```bash
# Health check
curl http://localhost:8000/healthz

# Get proxy.pac file (requires valid token)
curl "http://localhost:8000/proxy.pac?token=YOUR_TOKEN"
```

### Full Development Stack

To run the complete stack locally with API, UI, and optionally Squid:

**Terminal 1: API Server**
```bash
cd api
export API_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=admin-password
export DB_URL="sqlite+aiosqlite:///./dev.db"
python -m uvicorn src.api.main:app --reload --port 8000
```

**Terminal 2: Frontend UI**
```bash
cd ui
npm install
npm run dev
```

**Terminal 3: Run Tests (optional)**
```bash
cd api
python -m pytest -v
```

## Available Scripts

### Development

- **`python -m uvicorn src.api.main:app --reload`** - Start development server with hot reload
  - Runs on http://localhost:8000
  - Watches for file changes and auto-reloads

### Database

- **`alembic upgrade head`** - Run all pending migrations
- **`alembic revision --autogenerate -m "Description"`** - Create new migration
- **`alembic downgrade -1`** - Rollback last migration

### Testing

- **`python -m pytest`** - Run all tests
- **`python -m pytest -v`** - Run with verbose output
- **`python -m pytest tests/test_auth.py -v`** - Run specific test file
- **`python -m pytest -k test_login`** - Run tests matching pattern

## Project Structure

```
api/
├── src/api/
│   ├── __init__.py
│   ├── auth.py              # Authentication logic
│   ├── config.py            # Configuration and settings
│   ├── database.py          # Database configuration
│   ├── main.py              # FastAPI application entry point
│   ├── models.py            # SQLAlchemy ORM models
│   ├── routers/             # API route handlers
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── domains.py       # Domain management endpoints
│   │   ├── logs.py          # Access logs endpoints
│   │   └── users.py         # User management endpoints
│   ├── services/            # Business logic services
│   │   ├── htpasswd.py      # Password file management
│   │   ├── pac.py           # Proxy Auto-Config generation
│   │   └── squid.py         # Squid proxy integration
│   └── templates/           # Jinja2 templates
│       └── proxy.pac.j2     # PAC file template
├── tests/
│   ├── conftest.py          # Pytest fixtures
│   ├── test_auth.py         # Authentication tests
│   ├── test_domains.py      # Domain tests
│   ├── test_e2e.py          # End-to-end tests
│   ├── test_integration.py  # Integration tests
│   └── test_users.py        # User management tests
├── migrations/              # Alembic database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── pyproject.toml           # Project metadata and dependencies
├── pytest.ini               # Pytest configuration
└── alembic.ini              # Alembic configuration
```

## API Endpoints

### Authentication

- `POST /auth/login` - User login (email/username + password)
- `POST /auth/logout` - User logout
- `GET /auth/me` - Get current user info

### Users

- `GET /users` - List all users
- `POST /users` - Create new user
- `GET /users/{user_id}` - Get user details
- `PUT /users/{user_id}` - Update user
- `DELETE /users/{user_id}` - Delete user

### Domains

- `GET /domains` - List all domains
- `POST /domains` - Create domain entry
- `GET /domains/{domain_id}` - Get domain details
- `PUT /domains/{domain_id}` - Update domain
- `DELETE /domains/{domain_id}` - Delete domain

### Logs

- `GET /logs` - Get proxy access logs
- `GET /logs?limit=100&offset=0` - Paginated logs

### System

- `GET /healthz` - Health check endpoint
- `GET /proxy.pac?token=<token>` - Proxy Auto-Config file

## Database

### Overview

The API uses SQLite with SQLAlchemy ORM for data persistence. In development, the database is stored as a local SQLite file.

### Models

**UIUser** - Application user account
- username, password_hash, role, created_at, updated_at

**ProxyUser** - Proxy authentication credentials
- proxy_user, proxy_pass, pac_token, ui_user_id

**Domain** - Proxy domain filtering rules
- domain, status, approval_date, created_by

**AccessLog** - Proxy access audit trail
- user, domain, timestamp, status, ip_address

### Migrations

Database schema changes are managed using Alembic:

```bash
# Create new migration
alembic revision --autogenerate -m "Add new column"

# Apply pending migrations
alembic upgrade head

# See migration history
alembic history

# Rollback to previous version
alembic downgrade -1
```

## Authentication

### JWT Token Flow

1. User logs in with credentials (`POST /auth/login`)
2. API returns JWT token
3. Client includes token in `Authorization: Bearer <token>` header
4. API validates token on protected endpoints

### Roles

- **admin** - Full system access
- **user** - Limited access to own data

### Token Configuration

- Algorithm: HS256
- Secret key: `API_SECRET_KEY` environment variable
- Expiration: Configurable (default 24 hours)

## Configuration

### Environment Variables

Create a `.env` file in the api directory or set these environment variables:

```env
# API Configuration
API_SECRET_KEY=your-secure-key-here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin-password

# Database
DB_URL=sqlite+aiosqlite:///./dev.db

# Proxy Integration
SQUID_CONTAINER=localhost
DOMAINS_FILE=/path/to/domains.txt
HTPASSWD_FILE=/path/to/passwd

# Application
DOMAIN=localhost
DEBUG=false
LOG_LEVEL=INFO
```

### settings.py

Configuration is loaded from `src/api/config.py` using **pydantic-settings**:

```python
from api.config import settings

# Access settings
print(settings.api_secret_key)
print(settings.admin_username)
print(settings.db_url)
```

## Development Workflow

### Adding a New Endpoint

1. Create route handler in `src/api/routers/` or add to existing router
2. Define request/response models using Pydantic
3. Add authentication dependency if needed
4. Add database logic in `services/` if complex
5. Write tests in `tests/`

Example:
```python
# src/api/routers/example.py
from fastapi import APIRouter, Depends
from api.database import get_db

router = APIRouter(prefix="/example", tags=["example"])

@router.get("/")
async def list_examples(db=Depends(get_db)):
    """List all examples"""
    result = await db.execute(select(Example))
    return result.scalars().all()

@router.post("/")
async def create_example(example: ExampleCreate, db=Depends(get_db)):
    """Create new example"""
    db_example = Example(**example.dict())
    db.add(db_example)
    await db.commit()
    await db.refresh(db_example)
    return db_example
```

### Adding Database Models

1. Create model in `src/api/models.py`
2. Create migration: `alembic revision --autogenerate -m "Add new model"`
3. Apply migration: `alembic upgrade head`

### Using Services

Business logic is organized in `src/api/services/`:

```python
# src/api/services/example.py
from api.database import async_session

async def process_example(data):
    async with async_session() as db:
        # Perform operations
        await db.commit()
```

## Testing

### Test Structure

Tests are organized by feature in `tests/`:

```bash
tests/
├── conftest.py          # Shared fixtures
├── test_auth.py         # Authentication tests
├── test_users.py        # User management tests
├── test_domains.py      # Domain tests
├── test_e2e.py          # End-to-end scenarios
└── test_integration.py  # Integration with Squid
```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific file
python -m pytest tests/test_auth.py -v

# Run specific test
python -m pytest tests/test_auth.py::test_login -v

# Run with coverage
python -m pytest --cov=src/api

# Run and stop on first failure
python -m pytest -x
```

### Writing Tests

```python
# tests/test_example.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_example(client: AsyncClient):
    response = await client.get("/example/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_create_example(client: AsyncClient):
    response = await client.post(
        "/example/",
        json={"name": "Test"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test"
```

## Troubleshooting

### Port 8000 Already in Use

```bash
# Find process using port
lsof -i :8000

# Or run on different port
python -m uvicorn src.api.main:app --port 8001
```

### Database Errors

```bash
# Reset database (deletes all data)
rm dev.db
alembic upgrade head

# Check migration status
alembic current
alembic history
```

### Import Errors

```bash
# Reinstall in development mode
pip install -e .

# Or clear cache and try again
rm -rf .venv
pip install -e .
```

### Async Errors

Ensure you're using async properly:

```python
# ✅ Correct
async def get_data():
    async with async_session() as db:
        result = await db.execute(select(Model))

# ❌ Incorrect - missing async/await
def get_data():
    result = db.execute(select(Model))  # Won't work
```

### CORS Issues

If frontend can't access API:

1. Check `settings.domain` in config
2. Verify CORS middleware in `main.py`
3. Check browser console for specific errors
4. Ensure API is running on correct port

## Dependencies

| Package | Purpose |
|---------|---------|
| fastapi | Web framework |
| uvicorn | ASGI server |
| sqlalchemy | ORM |
| aiosqlite | Async SQLite driver |
| alembic | Database migrations |
| python-jose | JWT handling |
| bcrypt | Password hashing |
| pydantic-settings | Configuration management |
| docker | Docker SDK |
| jinja2 | Template rendering |

## Development Tips

- **Hot Reload**: Changes to Python files automatically restart the server
- **Type Hints**: Use full type hints for better IDE support and error detection
- **Async All The Way**: Keep async/await consistent throughout
- **Database Sessions**: Always use `async_session()` context manager for queries
- **Error Handling**: Use FastAPI HTTPException for API errors
- **Logging**: Use Python's logging module for debugging

```python
import logging
logger = logging.getLogger(__name__)
logger.info("Important event: %s", event)
```

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Python José](https://python-jose.readthedocs.io/)
