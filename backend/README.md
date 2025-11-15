# Smart Recipe Recommender - Backend API

Flask-based REST API for recipe recommendations using machine learning.

## Setup

1. Create virtual environment:
```powershell
python -m venv venv
.\venv\Scripts\Activate
```

2. Install dependencies:
```powershell
pip install -r requirements.txt
```

3. Configure environment:
```powershell
Copy-Item .env.example .env
notepad .env
```

4. Setup database (see main README.md)

5. Load data:
```powershell
python data_preprocessor.py
```

## Running

```powershell
.\venv\Scripts\Activate
python app.py
```

API runs on: http://localhost:5000

## API Endpoints

### Health Check
```
GET /api/health
```

### Get Recommendations
```
POST /api/recommend
Content-Type: application/json

{
  "ingredients": ["chicken", "tomato", "garlic"],
  "dietary_preference": "low-carb",
  "cuisine_type": "italian"
}
```

### Search Recipes
```
GET /api/search?query=pasta&type=name
```

### Get Recipe Details
```
GET /api/recipe/123
```

### Get Multiple Recipes
```
POST /api/recipes/batch
Content-Type: application/json

{
  "recipe_ids": [1, 2, 3, 4, 5]
}
```

## Project Structure

- `app.py` - Main Flask application
- `database.py` - Database operations
- `ml_model.py` - ML recommendation engine
- `data_preprocessor.py` - Data loading script

## Machine Learning

The recommendation system uses:
- TF-IDF vectorization
- Content-based filtering
- Cosine similarity matching
- Multi-factor scoring (ingredients, dietary, cuisine)

## Database Schema

- `recipes` - Recipe information
- `ingredients` - Unique ingredients
- `tags` - Recipe tags (dietary, cuisine)
- `nutrition` - Nutritional information
- `steps` - Cooking instructions
- Junction tables for relationships

## Environment Variables

```
FLASK_ENV=development
PORT=5000
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=recipe_recommender
```
