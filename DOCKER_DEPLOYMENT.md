# Docker Deployment Guide

## Prerequisites
- Docker Desktop installed and running
- Docker Compose v2.0+

## Quick Start

1. **Build and start all services:**
   ```bash
   docker-compose up -d --build
   ```

2. **Check service status:**
   ```bash
   docker-compose ps
   ```

3. **View logs:**
   ```bash
   # All services
   docker-compose logs -f

   # Specific service
   docker-compose logs -f backend
   docker-compose logs -f frontend
   docker-compose logs -f mysql
   ```

## Access the Application

- **Frontend:** http://localhost
- **Backend API:** http://localhost:5000/api
- **MySQL Database:** localhost:3306

## Management Commands

**Stop services:**
```bash
docker-compose stop
```

**Start services:**
```bash
docker-compose start
```

**Restart services:**
```bash
docker-compose restart
```

**Stop and remove containers:**
```bash
docker-compose down
```

**Stop and remove containers + volumes (WARNING: deletes database):**
```bash
docker-compose down -v
```

**Rebuild specific service:**
```bash
docker-compose up -d --build backend
docker-compose up -d --build frontend
```

## Database Setup

The database schema is automatically initialized from `database/schema.sql` on first run.

**Import data manually:**
```bash
# Copy CSV to backend container
docker cp backend/data/recipes_data.csv recipe_backend:/app/data/

# Run import script
docker exec -it recipe_backend python check_and_import.py
```

## Troubleshooting

**Check backend health:**
```bash
curl http://localhost:5000/api/health
```

**Access container shell:**
```bash
docker exec -it recipe_backend bash
docker exec -it recipe_frontend sh
docker exec -it recipe_db mysql -u root -p
```

**Reset everything:**
```bash
docker-compose down -v
docker system prune -a
docker-compose up -d --build
```

## Production Notes

- Change database passwords in `docker-compose.yml`
- Update `CORS_ORIGINS` for production domain
- Consider using Docker secrets for sensitive data
- Set up reverse proxy (nginx/traefik) for HTTPS
- Configure volume backups for `mysql_data`
