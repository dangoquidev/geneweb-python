# GenEWeb Deployment Guide

This guide provides step-by-step instructions for deploying the GenEWeb application on a VPS without a domain name.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Deployment](#quick-deployment)
- [Detailed Setup](#detailed-setup)
- [Configuration](#configuration)
- [Management Commands](#management-commands)
- [Accessing the Application](#accessing-the-application)
- [Troubleshooting](#troubleshooting)
- [Production Recommendations](#production-recommendations)

---

## Prerequisites

### Required Software

- **Docker Engine** (version 20.10+)
- **Docker Compose** (version 2.0+)
- **Git** (for cloning the repository)
- **curl** (for health checks)

### System Requirements

- **RAM**: Minimum 2GB, recommended 4GB+
- **Disk**: Minimum 10GB free space
- **OS**: Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+, etc.)
- **Ports**: 8080 (or your chosen port) must be available

### Check Prerequisites

```bash
# Check Docker installation
docker --version
docker compose version

# Check available ports
sudo netstat -tulpn | grep :8080

# Check system resources
free -h
df -h
```

---

## Quick Deployment

For the fastest deployment on a fresh VPS:

```bash
# 1. Clone the repository
git clone <YOUR_REPOSITORY_URL>
cd Awkward_legacy

# 2. Build and start the application
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# 3. Check if it's running
docker ps
curl http://localhost:8080/api/health

# 4. Access the application
# Open your browser to: http://YOUR_VPS_IP:8080
```

That's it! The application should now be running.

---

## Detailed Setup

### Step 1: Clone the Repository

```bash
# Navigate to your preferred directory
cd /home/ubuntu  # or /var/www or any location

# Clone the repository
git clone <YOUR_REPOSITORY_URL>
cd Awkward_legacy
```

### Step 2: Configure Environment (Optional)

The application works with default settings, but you can customize:

```bash
# Copy the example environment file
cp .env.example .env

# Edit configuration
nano .env
```

**Available environment variables:**

```env
# Application Settings
GENEWEB_DEBUG=false              # Set to true for debug mode
GENEWEB_DATABASE_PATH=/app/data/showcase.pickle  # Database file path

# Server Settings
HOST=0.0.0.0                     # Listen on all interfaces
PORT=8000                        # Internal container port
```

### Step 3: Build the Application

```bash
# Build Docker images (this may take 3-5 minutes on first run)
docker compose -f docker-compose.prod.yml build

# You should see output like:
# [+] Building 60.9s (31/31) FINISHED
```

**What happens during build:**
- Frontend React app is compiled (Vite build)
- Python dependencies are installed
- Demo database is created if needed
- Application is packaged into a Docker image

### Step 4: Start the Application

```bash
# Start the container in detached mode
docker compose -f docker-compose.prod.yml up -d

# Check container status
docker ps
```

### Step 5: Verify Deployment

```bash
# Check application health
curl http://localhost:8080/api/health

# Expected output:
# {"status":"healthy","timestamp":"...","version":"1.0.0","database_accessible":true}

# Check if frontend is served
curl http://localhost:8080/ | grep "GenEWeb"

# View logs
docker logs geneweb-app --tail 50
```

---

## Configuration

### Port Configuration

By default, the application is exposed on **port 8080**. To change this:

1. Edit `docker-compose.prod.yml`:

```yaml
services:
  geneweb-app:
    ports:
      - "YOUR_PORT:8000"  # Change YOUR_PORT to desired port
```

2. Rebuild and restart:

```bash
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

### Database Configuration

#### Using a Custom Database

1. Place your database file in the `data/` directory:

```bash
cp /path/to/your/database.pickle data/my_family.pickle
```

2. Update `.env`:

```env
GENEWEB_DATABASE_PATH=/app/data/my_family.pickle
```

3. Restart the container:

```bash
docker compose -f docker-compose.prod.yml restart
```

#### Creating a New Database

```bash
# Enter the container
docker exec -it geneweb-app bash

# Use the CLI to create a database
python -m backend.cli create-db my_new_family --database-dir /app/data

# Exit the container
exit
```

### Persistent Data

The following directories are automatically persisted:

- `./data/` - Database files
- `./logs/` - Application logs

**Backup your data:**

```bash
# Backup databases
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Copy to safe location
scp backup-*.tar.gz user@backup-server:/backups/
```

---

## Management Commands

### Start/Stop/Restart

```bash
# Start the application
docker compose -f docker-compose.prod.yml up -d

# Stop the application
docker compose -f docker-compose.prod.yml down

# Restart the application
docker compose -f docker-compose.prod.yml restart

# View status
docker compose -f docker-compose.prod.yml ps
```

### View Logs

```bash
# View live logs
docker logs -f geneweb-app

# View last 100 lines
docker logs geneweb-app --tail 100

# View logs since 1 hour ago
docker logs geneweb-app --since 1h
```

### Update the Application

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### Execute Commands Inside Container

```bash
# Get a shell in the container
docker exec -it geneweb-app bash

# Run a specific command
docker exec -it geneweb-app python -m backend.cli list-db --database-dir /app/data
```

### Clean Up

```bash
# Stop and remove containers
docker compose -f docker-compose.prod.yml down

# Remove all data (WARNING: This deletes databases!)
docker compose -f docker-compose.prod.yml down -v

# Remove Docker images
docker rmi awkward_legacy-geneweb-app

# Full cleanup (including build cache)
docker system prune -a
```

---

## Accessing the Application

### Get Your VPS IP Address

```bash
# Method 1: Using hostname
hostname -I | awk '{print $1}'

# Method 2: Using ip command
ip addr show | grep "inet " | grep -v 127.0.0.1

# Method 3: Using curl
curl -4 ifconfig.me
```

### Access URLs

Once deployed, access the application at:

- **Frontend**: `http://YOUR_VPS_IP:8080/`
- **API Documentation**: `http://YOUR_VPS_IP:8080/api/docs`
- **API ReDoc**: `http://YOUR_VPS_IP:8080/api/redoc`
- **Health Check**: `http://YOUR_VPS_IP:8080/api/health`

**Example** (if your VPS IP is 51.75.203.14):
- Frontend: http://51.75.203.14:8080/
- API Docs: http://51.75.203.14:8080/api/docs

### Testing from Your Computer

```bash
# Test health endpoint
curl http://YOUR_VPS_IP:8080/api/health

# Test database list
curl http://YOUR_VPS_IP:8080/api/databases
```

---

## Troubleshooting

### Container Won't Start

**Check logs:**
```bash
docker logs geneweb-app
```

**Common issues:**

1. **Port already in use**
   ```bash
   # Check what's using the port
   sudo lsof -i :8080
   
   # Change port in docker-compose.prod.yml
   ```

2. **Permission errors**
   ```bash
   # Fix data directory permissions
   sudo chown -R $USER:$USER data/ logs/
   ```

3. **Out of disk space**
   ```bash
   # Check disk usage
   df -h
   
   # Clean Docker cache
   docker system prune -a
   ```

### Application Health Check Fails

```bash
# 1. Check if container is running
docker ps

# 2. Check container logs
docker logs geneweb-app --tail 100

# 3. Try restarting
docker compose -f docker-compose.prod.yml restart

# 4. Check from inside container
docker exec -it geneweb-app curl http://localhost:8000/api/health
```

### Frontend Not Loading

```bash
# 1. Verify frontend files exist
docker exec -it geneweb-app ls -la /app/src/frontend/dist/

# 2. Rebuild to ensure frontend is compiled
docker compose -f docker-compose.prod.yml build --no-cache

# 3. Check browser console for errors
```

### Database Issues

```bash
# 1. Check if database file exists
docker exec -it geneweb-app ls -la /app/data/

# 2. Verify database path in environment
docker exec -it geneweb-app env | grep GENEWEB_DATABASE_PATH

# 3. Test database access
docker exec -it geneweb-app python -c "import pickle; print(pickle.load(open('/app/data/showcase.pickle', 'rb')))"
```

### Can't Access from External Network

```bash
# 1. Check if firewall is blocking the port
sudo ufw status
sudo ufw allow 8080/tcp

# 2. Check if the application is listening
netstat -tulpn | grep :8080

# 3. For cloud providers (AWS, GCP, Azure, OVH, etc.):
#    - Check Security Groups / Firewall Rules
#    - Ensure port 8080 is allowed for inbound traffic
```

### High Memory Usage

```bash
# 1. Check container resource usage
docker stats geneweb-app

# 2. Set memory limits in docker-compose.prod.yml
services:
  geneweb-app:
    deploy:
      resources:
        limits:
          memory: 2G

# 3. Restart with limits
docker compose -f docker-compose.prod.yml up -d
```

---

## Production Recommendations

### Security

1. **Use HTTPS with a Reverse Proxy**
   ```bash
   # Install nginx
   sudo apt install nginx
   
   # Configure reverse proxy (see nginx configuration below)
   ```

2. **Set up a firewall**
   ```bash
   sudo ufw enable
   sudo ufw allow ssh
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw deny 8080/tcp  # Block direct access, use nginx
   ```

3. **Disable debug mode**
   ```env
   GENEWEB_DEBUG=false
   ```

4. **Regular security updates**
   ```bash
   # Update system packages
   sudo apt update && sudo apt upgrade -y
   
   # Update application
   git pull origin main
   docker compose -f docker-compose.prod.yml build
   docker compose -f docker-compose.prod.yml up -d
   ```

### Monitoring

1. **Enable health check monitoring**
   ```bash
   # Add to crontab
   */5 * * * * curl -f http://localhost:8080/api/health || systemctl restart docker
   ```

2. **Log rotation**
   ```bash
   # Docker automatically handles log rotation
   # Configure in /etc/docker/daemon.json:
   {
     "log-driver": "json-file",
     "log-opts": {
       "max-size": "10m",
       "max-file": "3"
     }
   }
   ```

### Backups

1. **Automated database backups**
   ```bash
   # Create backup script
   cat > /usr/local/bin/backup-geneweb.sh << 'EOF'
   #!/bin/bash
   BACKUP_DIR="/backups/geneweb"
   DATE=$(date +%Y%m%d_%H%M%S)
   mkdir -p $BACKUP_DIR
   tar -czf $BACKUP_DIR/geneweb-backup-$DATE.tar.gz /home/ubuntu/Awkward_legacy/data/
   # Keep only last 7 days
   find $BACKUP_DIR -name "geneweb-backup-*.tar.gz" -mtime +7 -delete
   EOF
   
   chmod +x /usr/local/bin/backup-geneweb.sh
   
   # Add to crontab (daily at 2 AM)
   0 2 * * * /usr/local/bin/backup-geneweb.sh
   ```

### Performance

1. **Resource limits**
   ```yaml
   # In docker-compose.prod.yml
   services:
     geneweb-app:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 2G
           reservations:
             cpus: '1'
             memory: 1G
   ```

2. **Enable container auto-restart**
   ```yaml
   # Already configured in docker-compose.prod.yml
   restart: unless-stopped
   ```

### Nginx Reverse Proxy (Optional)

If you want to use port 80 or add HTTPS:

```nginx
# /etc/nginx/sites-available/geneweb
server {
    listen 80;
    server_name YOUR_VPS_IP;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/geneweb /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Support & Resources

- **Project Documentation**: See `README.md` and `CONTRIBUTING.md`
- **API Documentation**: http://YOUR_VPS_IP:8080/api/docs
- **Check Logs**: `docker logs geneweb-app`
- **Report Issues**: Create an issue in the repository

---

## Summary

You've successfully deployed GenEWeb! Here's a quick reference:

```bash
# Start application
docker compose -f docker-compose.prod.yml up -d

# Stop application
docker compose -f docker-compose.prod.yml down

# View logs
docker logs -f geneweb-app

# Access application
http://YOUR_VPS_IP:8080/
```

**Your application is now running at: `http://YOUR_VPS_IP:8080`**

Enjoy using GenEWeb! 🎉
