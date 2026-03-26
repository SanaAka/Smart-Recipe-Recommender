# Production Deployment Guide

## 🚀 Smart Recipe Recommender - Production Deployment

This guide covers deploying the application to production environments.

---

## 📋 Pre-Deployment Checklist

### Frontend
- [ ] Set production environment variables
- [ ] Run production build: `npm run build`
- [ ] Test production build locally
- [ ] Enable analytics and monitoring
- [ ] Configure CDN for static assets
- [ ] Set up SSL/TLS certificates
- [ ] Configure CORS properly

### Backend
- [ ] Set strong SECRET_KEY and JWT_SECRET_KEY
- [ ] Configure production database
- [ ] Enable rate limiting
- [ ] Set up logging and monitoring
- [ ] Configure reverse proxy (nginx/Apache)
- [ ] Set up SSL/TLS certificates
- [ ] Review security headers

---

## 🔧 Environment Configuration

### Frontend (.env.production)
```bash
REACT_APP_API_URL=https://api.yourproduction.com
REACT_APP_ENV=production
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENABLE_SENTRY=true
```

### Backend (.env)
```bash
# Flask Settings
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# Database
DB_HOST=your-db-host
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_NAME=recipe_recommender

# Security
CORS_ORIGINS=https://yourfrontend.com
RATE_LIMIT_STORAGE_URL=redis://localhost:6379

# Monitoring
SENTRY_DSN=your-sentry-dsn
```

---

## 🌐 Deployment Options

### Option 1: Docker Deployment (Recommended)

#### Build Images
```bash
# Frontend
cd frontend
docker build -t recipe-frontend:latest .

# Backend
cd ../backend
docker build -t recipe-backend:latest .
```

#### Run with Docker Compose
```bash
docker-compose up -d
```

### Option 2: Cloud Platform (Azure/AWS/GCP)

#### Azure App Service
```bash
# Frontend
az webapp up --name recipe-frontend --resource-group myResourceGroup --runtime "NODE|18-lts"

# Backend
az webapp up --name recipe-backend --resource-group myResourceGroup --runtime "PYTHON|3.11"
```

#### AWS Elastic Beanstalk
```bash
# Initialize EB
eb init -p python-3.11 recipe-backend

# Deploy
eb create recipe-production
eb deploy
```

### Option 3: Traditional VPS (DigitalOcean/Linode)

#### Frontend (Static Hosting)
```bash
# Build
npm run build

# Upload to server
scp -r build/* user@server:/var/www/recipe-frontend/

# Configure nginx
sudo nano /etc/nginx/sites-available/recipe-frontend
```

#### Backend (Python Application)
```bash
# Install dependencies
pip install -r requirements.txt

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app_v2:app

# Or use systemd service
sudo systemctl start recipe-backend
```

---

## 🔒 Security Hardening

### 1. Enable HTTPS
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}
```

### 2. Configure Security Headers
Already implemented in `app_v2.py`:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security

### 3. Rate Limiting
Already configured with Flask-Limiter (30-100 req/min)

### 4. Database Security
- Use SSL connections
- Implement connection pooling
- Regular backups
- Principle of least privilege

---

## 📊 Monitoring & Logging

### Frontend Monitoring
```javascript
// Add to index.js for analytics
if (process.env.REACT_APP_ENABLE_ANALYTICS === 'true') {
  // Google Analytics
  // window.gtag('config', process.env.REACT_APP_ANALYTICS_ID);
}
```

### Backend Monitoring
```python
# Already configured in logger_config.py
# Logs to: logs/app.log
# Error tracking with Sentry (if configured)
```

### Health Checks
```bash
# Backend health endpoint
curl https://api.yourdomain.com/api/health

# Expected response
{
  "status": "healthy",
  "timestamp": "2026-02-07T12:00:00Z",
  "version": "2.0.0"
}
```

---

## 🚦 Performance Optimization

### Frontend
✅ Code splitting (lazy loading implemented)
✅ Service worker for offline capability
✅ Image optimization
✅ Bundle analysis: `npm run build:analyze`

### Backend
✅ Database connection pooling
✅ Response compression (Flask-Compress)
✅ Caching headers
✅ Rate limiting

### Database
- Create indexes (already done via migration scripts)
- Regular VACUUM operations
- Query optimization

---

## 📦 Build & Deploy Workflow

### Automated CI/CD (GitHub Actions Example)

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Frontend
        run: |
          cd frontend
          npm ci
          npm run build
      - name: Deploy to CDN
        run: # Your deployment command
        
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy Backend
        run: # Your deployment command
```

---

## 🧪 Testing in Production

### Smoke Tests
```bash
# Test API endpoints
curl https://api.yourdomain.com/api/health
curl https://api.yourdomain.com/api/recipes?limit=1

# Test frontend
curl https://yourdomain.com
```

### Load Testing
```bash
# Using Apache Bench
ab -n 1000 -c 10 https://api.yourdomain.com/api/health

# Using Artillery
artillery quick --count 10 --num 100 https://api.yourdomain.com/
```

---

## 🔄 Rollback Plan

### Quick Rollback
```bash
# Docker
docker-compose down
docker-compose up -d --build previous-version

# Git-based
git revert HEAD
git push
# Trigger deployment
```

---

## 📝 Post-Deployment

### 1. Verify Deployment
- [ ] All pages load correctly
- [ ] API endpoints respond
- [ ] Authentication works
- [ ] Database connections stable
- [ ] SSL certificates valid

### 2. Monitor Metrics
- [ ] Response times < 200ms
- [ ] Error rate < 1%
- [ ] CPU usage < 70%
- [ ] Memory usage stable

### 3. Set Up Alerts
- [ ] Error rate threshold
- [ ] Downtime alerts
- [ ] SSL expiration warnings
- [ ] Database connection issues

---

## 🆘 Troubleshooting

### Common Issues

**CORS Errors**
- Verify `CORS_ORIGINS` in backend .env
- Check frontend `REACT_APP_API_URL`

**Database Connection Failed**
- Verify database credentials
- Check firewall rules
- Ensure SSL is configured

**502 Bad Gateway**
- Check backend service is running
- Verify reverse proxy configuration
- Check logs: `journalctl -u recipe-backend`

**High Memory Usage**
- Review connection pool settings
- Check for memory leaks
- Monitor with: `top` or `htop`

---

## 📞 Support

For issues or questions:
- Check logs: `logs/app.log`
- Review error monitoring dashboard
- Contact DevOps team

---

## 🎯 Success Metrics

After deployment, monitor:
- ✅ 99.9% uptime
- ✅ < 200ms average response time
- ✅ < 1% error rate
- ✅ Successful database backups
- ✅ SSL grade A+ (SSL Labs)

---

**Deployment Date:** _____________  
**Deployed By:** _____________  
**Version:** 2.0.0  
**Status:** 🟢 Production Ready
