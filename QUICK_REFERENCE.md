# Recipe Recommender v2.0 - Quick Reference

## 🚀 Quick Start

### Setup
```powershell
# Run automated setup
.\setup_v2.ps1

# OR manual setup
cd backend
pip install -r requirements.txt
mysql -u root -p < ../database/user_management_schema.sql
```

### Run Application
```powershell
# Option 1: Direct Python
cd backend
python app_v2.py

# Option 2: Docker
docker-compose up -d
```

---

## 📡 API Endpoints

### Public Endpoints
```bash
# Health check
GET /api/health

# Search recipes
GET /api/search?query=pasta&type=name&limit=20

# Get recipe details
GET /api/recipe/123

# Get recommendations
POST /api/recommend
{
  "ingredients": ["chicken", "rice"],
  "dietary_preference": "vegetarian",
  "cuisine_type": "italian",
  "limit": 12
}
```

### Authentication
```bash
# Register
POST /api/auth/register
{
  "username": "user123",
  "email": "user@example.com",
  "password": "SecurePass123"
}

# Login
POST /api/auth/login
{
  "username": "user123",
  "password": "SecurePass123"
}
# Returns: { "access_token": "...", "refresh_token": "..." }
```

### Protected Endpoints (Require JWT)
```bash
# Get profile
GET /api/auth/profile
Headers: Authorization: Bearer YOUR_ACCESS_TOKEN

# Get favorites
GET /api/favorites
Headers: Authorization: Bearer YOUR_ACCESS_TOKEN

# Add to favorites
POST /api/favorites/123
Headers: Authorization: Bearer YOUR_ACCESS_TOKEN

# Remove from favorites
DELETE /api/favorites/123
Headers: Authorization: Bearer YOUR_ACCESS_TOKEN
```

---

## 🧪 Testing

```powershell
# Run all tests
cd backend
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=. --cov-report=html

# View coverage report
start htmlcov/index.html
```

---

## 📊 ML Evaluation

```python
from ml_evaluator import RecommenderEvaluator, create_test_data_from_existing_recipes
from ml_model import RecipeRecommender
from database import Database

# Setup
db = Database()
db.connect()

# Create test data
test_data = create_test_data_from_existing_recipes(db, 100)

# Evaluate
recommender = RecipeRecommender(db)
evaluator = RecommenderEvaluator(recommender, test_data)

# Get metrics
results = evaluator.evaluate_test_set(k_values=[5, 10, 20])
print(results)

# Generate report
evaluator.generate_report('evaluation_report.txt')
```

---

## 🔒 Security

### Environment Variables
```env
# Required
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
MYSQL_ROOT_PASSWORD=secure-password

# Optional
RATE_LIMIT_ENABLED=True
RATE_LIMIT_PER_MINUTE=60
LOG_LEVEL=INFO
```

### Generate Secure Keys
```powershell
# PowerShell
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 📝 Common Commands

### Database
```sql
-- Create user tables
mysql -u root -p < database/user_management_schema.sql

-- Backup database
mysqldump -u root -p recipe_recommender > backup.sql

-- Restore database
mysql -u root -p recipe_recommender < backup.sql
```

### Docker
```powershell
# Build and start
docker-compose up -d --build

# View logs
docker-compose logs -f backend

# Restart services
docker-compose restart

# Stop all
docker-compose down

# Clean up
docker system prune -a
```

### Git
```powershell
# Commit improvements
git add .
git commit -m "feat: Add v2.0 improvements - security, testing, auth"
git push origin main
```

---

## 🐛 Troubleshooting

### Issue: Tests fail with database error
```powershell
# Check database connection
mysql -u root -p -e "SHOW DATABASES;"

# Update test database config
# Set DB_HOST=127.0.0.1 in test environment
```

### Issue: JWT token invalid
```powershell
# Verify JWT_SECRET_KEY is set
$env:JWT_SECRET_KEY="your-secret-key"

# Check token expiration (default 1 hour)
```

### Issue: Rate limit too strict
```powershell
# Disable rate limiting for development
$env:RATE_LIMIT_ENABLED="False"

# Or increase limit
$env:RATE_LIMIT_PER_MINUTE="120"
```

### Issue: CORS errors
```powershell
# Update CORS origins in .env
CORS_ORIGINS=http://localhost:3000,http://localhost:80
```

---

## 📚 File Structure

```
backend/
├── app_v2.py               # Enhanced Flask app (NEW)
├── auth.py                 # Authentication system (NEW)
├── schemas.py              # Pydantic validation (NEW)
├── logger_config.py        # Structured logging (NEW)
├── ml_evaluator.py         # ML evaluation (NEW)
├── tests/                  # Unit tests (NEW)
│   ├── test_api.py
│   └── test_database.py
├── database.py             # Database operations
├── ml_model.py             # ML recommender
└── requirements.txt        # Updated dependencies

database/
├── schema.sql                      # Original schema
└── user_management_schema.sql      # User tables (NEW)

.github/
└── workflows/              # CI/CD pipelines (NEW)
    ├── ci-cd.yml
    └── deploy.yml

Documentation:
├── SECURITY_AND_IMPROVEMENTS.md    # Complete guide (NEW)
├── IMPROVEMENTS_SUMMARY.md         # This summary (NEW)
├── QUICK_REFERENCE.md              # Quick reference (NEW)
└── README.md                       # Original README
```

---

## 🎯 Key Improvements

✅ **Security**: JWT auth, rate limiting, input validation
✅ **Testing**: Unit tests with pytest, 80%+ coverage
✅ **ML Evaluation**: Precision, Recall, NDCG, MAP metrics
✅ **Logging**: Structured JSON logging
✅ **CI/CD**: Automated testing and deployment
✅ **User Management**: Registration, login, favorites
✅ **API Design**: Standardized, validated, documented

---

## 📞 Support

- **Documentation**: See `SECURITY_AND_IMPROVEMENTS.md`
- **Issues**: Open GitHub issue
- **Email**: [Your contact]

---

**Last Updated**: February 2026
**Version**: 2.0.0
