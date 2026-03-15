# Pi-Gateway

A comprehensive proxy gateway system designed to manage and secure internet access through a centralized hub. Pi-Gateway combines multiple services to provide domain filtering, user authentication, rate limiting, and comprehensive logging.

## Overview

Pi-Gateway is a containerized application that implements a full-featured proxy infrastructure with the following components:

- **Caddy**: Modern reverse proxy server providing automated HTTPS/TLS termination with Let's Encrypt support
- **Squid**: High-performance HTTP proxy with domain-based access control and basic authentication
- **FastAPI Backend**: RESTful API for managing users, domains, authentication, and accessing logs
- **React Frontend**: User-friendly web interface for administration and configuration

## Features

- 🔐 **User Management**: Create and manage user accounts with secure authentication
- 🌐 **Domain Filtering**: Whitelist/blacklist domains to control access
- 📊 **Activity Logging**: Comprehensive audit logs of proxy access and activities
- 🔒 **HTTPS Support**: Automatic SSL/TLS certificates via Caddy and Let's Encrypt
- 💻 **Web UI**: Modern React-based admin dashboard
- 🐳 **Docker Containerized**: Simple deployment with Docker Compose

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Caddy     │ (Reverse Proxy + HTTPS)
└──────┬──────┘
       │
       ├──────────────┬──────────────┐
       ▼              ▼              ▼
    ┌────┐       ┌─────────┐    ┌────────┐
    │Squid       │ FastAPI │    │  React │
    │(Proxy)     │ (API)   │    │  (UI)  │
    └────┘       └─────────┘    └────────┘
```

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Git

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Kung-Fu-Stalin/pi-gateway.git
cd pi-gateway
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory with the required configuration:

```env
# Caddy Configuration
DOMAIN=example.com
ACME_EMAIL=admin@example.com

# API Configuration
API_SECRET_KEY=your-secret-key-here-change-this
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin-password-here
```

### 3. Initialize the Database (First Run Only)

```bash
cd api
uv run alembic upgrade head
```

This runs database migrations to set up the schema with necessary tables.

### 4. Start the Services

```bash
docker-compose up -d
```

This will:
- Build and start all services (Caddy, Squid, API, UI)
- Create necessary data directories and volumes
- Apply any pending migrations

### 5. Access the Application

Once services are running:

- **Web UI**: https://your-domain.com (admin dashboard)
- **Squid Proxy**: http://your-server.com:3128 (configure clients to use this proxy)
- **API**: https://your-domain.com/api (REST API endpoints)

## Local Development

### Quick Setup for Development

For local development without Docker, you can run components individually for faster iteration:

#### Prerequisites for Local Development

- **Node.js** 18+ (for UI development)
- **Python** 3.12+ (for API development)
- **uv** package manager (recommended for Python)
- **SQLite3**
- Docker & Docker Compose (optional, but recommended for proxy testing)

#### Option 1: Running Everything Locally (Recommended for Development)

**Terminal 1: Start the Backend API**

```bash
cd api
pip install -e .
export API_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=admin-password
export DB_URL="sqlite+aiosqlite:///./dev.db"
export SQUID_CONTAINER=localhost
python -m uvicorn src.api.main:app --reload --port 8000
```

**Terminal 2: Start the Frontend UI**

```bash
cd ui
npm install
npm run dev
```

Access the application at **http://localhost:5173**

The UI automatically proxies API requests to `http://localhost:8000` (configured in `vite.config.ts`).

#### Option 2: Docker Compose for Full Stack

For testing with actual Squid proxy and all services:

```bash
python setup.py    # Follow prompts to configure environment
docker-compose up -d
```

### Environment Configurations

The project supports two different configurations:

| Environment | Configuration File | Use Case |
|-------------|-------------------|----------|
| **Local Development** | `Caddyfile.local` | HTTP on port :80, local SSL certificates, no domain needed |
| **Production (Raspberry Pi)** | `Caddyfile` | HTTPS with Let's Encrypt, custom domain, real SSL certificates |

The `setup.py` script will automatically select the appropriate Caddyfile based on your environment choice.

### Running Migrations Locally

If running the API locally and need to update the database schema:

```bash
cd api
alembic upgrade head
```

### Development Tips

- **Hot Reload**: Both UI (`npm run dev`) and API (`--reload` flag) support hot reloading
- **Debug Logging**: Set `DEBUG=1` environment variable for verbose logging
- **Database**: Local development uses SQLite at `api/dev.db` for easy inspection/reset
- **API Documentation**: FastAPI auto-generates docs at `http://localhost:8000/docs`

For detailed UI development instructions, see [ui/README.md](ui/README.md).

## Deployment

### Raspberry Pi Deployment

1. Configure production environment:
```bash
python setup.py
# Select "production" environment
# Enter your domain (e.g., pi-gateway.example.com)
# Enter admin credentials
```

2. Start services:
```bash
docker-compose up -d
```

The system will:
- Use `Caddyfile` (production configuration)
- Request SSL certificates from Let's Encrypt automatically
- Run on your custom domain with HTTPS

### Scaling Considerations

- **Database**: Currently uses SQLite. For high-traffic scenarios, consider migrating to PostgreSQL
- **Squid Cache**: Configure cache size in `squid/squid.conf` based on available disk space
- **Caddy**: Can handle thousands of concurrent connections on Raspberry Pi 4+

### 6. Login

Use the credentials specified in your `.env` file:
- Username: `ADMIN_USERNAME`
- Password: `ADMIN_PASSWORD`

## Development

### Database Migrations

The project uses [Alembic](https://alembic.sqlalchemy.org/) for database schema management.

**Run pending migrations**:
```bash
cd api
python -m alembic upgrade head
```

**Create a new migration** (after modifying models):
```bash
cd api
python -m alembic revision --autogenerate -m "Description of changes"
```

**View migration history**:
```bash
cd api
python -m alembic history
```

Current schema includes:
- `ui_users`: User accounts with roles (admin/user) and authentication tokens
- `domain_groups`: Domain whitelists/blacklists for filtering

### Running Services Individually

**API Development**:
```bash
cd api
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn api.main:app --reload --port 8000
```

**UI Development**:
```bash
cd ui
npm install
npm run dev
```

**Squid**:
```bash
# Edit squid/squid.conf as needed
docker build -t squid-local ./squid
docker run -p 3128:3128 squid-local
```

## Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DOMAIN` | Domain name for the gateway | `gateway.example.com` |
| `ACME_EMAIL` | Email for Let's Encrypt certificates | `admin@example.com` |
| `API_SECRET_KEY` | Secret key for JWT tokens | `very-secret-key` |
| `ADMIN_USERNAME` | Initial admin username | `admin` |
| `ADMIN_PASSWORD` | Initial admin password | `secure-password` |

### File Locations

- **Data Directory**: `./data/` - Contains database, password files, and domain lists
- **Caddy Config**: `./caddy/` - Caddy configuration files
- **Squid Config**: `./squid/` - Squid proxy configuration and domain lists
- **API**: `./api/` - FastAPI application source code
- **UI**: `./ui/` - React frontend application

## Docker Compose Services

### caddy
- **Port**: 80, 443 (HTTP/HTTPS)
- **Function**: Reverse proxy and SSL termination
- **Volumes**: Caddy data and configuration storage

### squid
- **Port**: 3128 (HTTP Proxy)
- **Function**: HTTP proxy with domain filtering
- **Configuration**: `./squid/squid.conf`

### api
- **Function**: FastAPI backend for management
- **Database**: SQLite at `./data/db.sqlite3`
- **Dependencies**: Squid service

### ui
- **Function**: React frontend dashboard
- **Build**: Node.js/Vite build process

## API Documentation

Once running, access the interactive API documentation at:
- Swagger UI: `https://your-domain.com/api/docs`
- ReDoc: `https://your-domain.com/api/redoc`

## Stopping Services

```bash
docker-compose down
```

To also remove volumes (warning: deletes data):
```bash
docker-compose down -v
```

## Troubleshooting

### Services not starting
```bash
docker-compose logs -f
```

### Port already in use
Change ports in `docker-compose.yml` or stop conflicting services

### Database issues
```bash
rm ./data/db.sqlite3
docker-compose restart api
```

## License

See LICENSE file for details.

## Contributors

Built with ❤️ for secure gateway management.
