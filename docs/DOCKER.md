
# 🐳 GenEWeb Docker Setup

Note: This guide covers Docker deployment for the modern Python version of GenEWeb
(the FastAPI application, exposed by default on port 8000). The legacy admin panel,
if used, may be exposed on different ports (for example 2316 / 2317).

This document explains how to run GenEWeb with Docker so you don't need to install
Python, Node.js or project dependencies on your local machine.

## 🚀 Quick start

For more information about GenEWeb see `README.md` and `CONTRIBUTING.md`.

## See also

- `README.md` — project overview and quickstart
- `CONTRIBUTING.md` — developer workflow

### Prerequisites

- Docker and Docker Compose installed
- At least 4 GB of RAM available
- Ports 8000, 5173, 2316, 2317 should be free

### 1. Build the image

```bash
# Method 1: Use the helper script (recommended)
./docker-run.sh build

# Method 2: Build with Docker directly
docker build -t geneweb-python:latest .

# Method 3: Use Make
make docker-build
```

### 2. Start services

#### API only (production)
```bash
./docker-run.sh start
# or
make docker-start
```
→ **API**: http://localhost:8000/api/docs

#### Full development (API + frontend)
```bash
./docker-run.sh dev
# or
make docker-dev
```
→ **API**: http://localhost:8000/api/docs
→ **Frontend**: http://localhost:5173

#### Fullstack with tmux (equivalent to `make run-fullstack-tmux`)
```bash
./docker-run.sh fullstack
# or
make docker-fullstack
```
→ **API**: http://localhost:8001/api/docs
→ **Frontend**: http://localhost:5174

#### With legacy admin panel
```bash
./docker-run.sh admin
```
→ **API**: http://localhost:8000/api/docs
→ **Admin**: http://localhost:2316

## 📋 Available commands

### Using the helper script `./docker-run.sh`
```bash
./docker-run.sh build           # Build the image
./docker-run.sh start           # API only
./docker-run.sh dev             # Development mode
./docker-run.sh fullstack       # Fullstack using tmux
./docker-run.sh admin           # Start with admin panel
./docker-run.sh stop            # Stop all services
./docker-run.sh restart         # Restart
./docker-run.sh logs            # Show logs
./docker-run.sh logs --follow   # Follow logs in real time
./docker-run.sh shell           # Open a shell in the container
./docker-run.sh status          # Container status
./docker-run.sh clean           # Clean artifacts
./docker-run.sh help            # Full help
```

### Using Make
```bash
make docker-build      # Build the image
make docker-start      # Start (API only)
make docker-dev        # Development mode
make docker-fullstack  # Fullstack with tmux
make docker-stop       # Stop services
make docker-logs       # View logs
make docker-shell      # Shell in container
make docker-status     # Status
make docker-clean      # Clean
```

### Using Docker Compose directly
```bash
# Core services
docker-compose up -d                    # API only
docker-compose --profile dev up -d      # Development mode
docker-compose --profile admin up -d    # With admin panel
docker-compose --profile fullstack up -d # Fullstack with tmux

# Management
docker-compose down                     # Stop
docker-compose logs -f                  # Real-time logs
docker-compose ps                       # Status
```

## 🔧 Configuration

### Environment variables
```bash
# In docker-compose.yml or .env
GENEWEB_DATABASE_PATH=/app/data/showcase.pickle  # Database path
GENEWEB_DEBUG=true                               # Debug mode
PYTHONPATH=/app/src                              # Python path
```

### Persistent volumes

- `./data:/app/data:rw` - Persistent database files
- `./logs:/app/logs:rw` - Application logs
- `./src:/app/src:ro` - Source code (read-only mount for dev)

### Exposed ports

- **8000** - Main FastAPI application
- **5173** - Frontend (Vite dev server)
- **2316** - Legacy admin panel
- **2317** - Legacy admin panel (fullstack)
- **8001** - FastAPI (fullstack mode)
- **5174** - Frontend dev server (fullstack)

## 🛠️ Development

### Open a shell in the container
```bash
./docker-run.sh shell
# Inside the container:
python --version
make status
make test
```

### Follow logs in real time
```bash
./docker-run.sh logs --follow
# or
docker-compose logs -f
```

### Rebuild after changes
```bash
./docker-run.sh start --build
# or
./docker-run.sh dev --build
```

### Development with volumes
The development mode mounts `./src` as a read-only volume so you can test
changes without rebuilding the image.

## 📊 Health checks

The API exposes a health endpoint that Docker can use:
- **Health check**: http://localhost:8000/api/health
- **Detailed status**: http://localhost:8000/api/status

Docker will use these endpoints to determine container health.

## 🗄️ Databases

Database files are stored under `./data/`:
- `showcase.pickle` - demo database (default)
- `ma_famille.pickle` - example family database
- `ged.pickle` - database imported from GEDCOM

To use a different database:
```bash
# Modify GENEWEB_DATABASE_PATH in docker-compose.yml
GENEWEB_DATABASE_PATH=/app/data/ma_famille.pickle
```

## 🚨 Troubleshooting

### Container won't start
```bash
./docker-run.sh logs          # View errors
./docker-run.sh status        # Container status
docker system prune           # Clean up Docker
```

### Port already in use
```bash
# Check which process uses the port
netstat -tulpn | grep :8000
# or
lsof -i :8000

# Stop conflicting services
./docker-run.sh stop
```

### Build issues
```bash
# Clean and rebuild
./docker-run.sh clean
./docker-run.sh build
```

### Accessing logs
```bash
# Logs for all services
docker-compose logs

# Logs for a specific service
docker-compose logs geneweb-app
docker-compose logs geneweb-frontend-dev

# Real-time logs
docker-compose logs -f geneweb-app
```

## 🔄 Migration from local development

If you were developing locally (without Docker):

1. **Backup your data**:
```bash
cp -r data/ data-backup/
```

2. **Stop local services**:
```bash
make stop-fullstack  # If you used tmux
# or press Ctrl+C on running servers
```

3. **Start with Docker**:
```bash
./docker-run.sh build
./docker-run.sh dev
```

4. Verify your data is accessible in the container.

## 📈 Performance

### Recommended resources
- **RAM**: 2-4 GB minimum
- **CPU**: 2 cores minimum
- **Disk**: 5 GB free space

### Optimizations
- Multi-stage builds reduce image size
- Named volumes speed up node_modules access
- Docker cache reuses layers for faster builds

## 🆘 Support

- **Detailed logs**: `./docker-run.sh logs --follow`
- **Debug shell**: `./docker-run.sh shell`
- **Full status**: `./docker-run.sh status`
- **Full help**: `./docker-run.sh help`

For more information about GenEWeb, see `README.md` and `CONTRIBUTING.md`.
