from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_compress import Compress
import os
import threading
from pathlib import Path
from dotenv import load_dotenv
from database import Database
import traceback

# Load environment variables from .env file in the same directory as this script
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)
print(f"Loaded .env from: {env_path}")
print(f"DB_PASSWORD loaded: {'Yes' if os.getenv('DB_PASSWORD') else 'No'}")

app = Flask(__name__)
CORS(app)
Compress(app)  # Enable gzip compression for all responses

# Initialize database and ML model
db = Database()
recommender = None
ml_status = {'loading': False, 'ready': False, 'error': None}
ml_lock = threading.Lock()

def init_recommender_async():
    """Initialize ML recommender in background thread"""
    global recommender, ml_status
    try:
        with ml_lock:
            if recommender is None and not ml_status['loading']:
                ml_status['loading'] = True
                print("[ML] Initializing recommender in background...")
        
        # Lazy import to avoid slow sklearn import blocking startup
        from ml_model import RecipeRecommender
        temp_recommender = RecipeRecommender(db)
        
        with ml_lock:
            recommender = temp_recommender
            ml_status['loading'] = False
            ml_status['ready'] = True
            print("[ML] Recommender ready!")
    except Exception as e:
        with ml_lock:
            ml_status['loading'] = False
            ml_status['error'] = str(e)
            print(f"[ML] Failed to initialize: {e}")

def get_recommender():
    """Get ML recommender, starting initialization if needed"""
    global recommender
    with ml_lock:
        if recommender is None and not ml_status['loading']:
            # Start async initialization
            thread = threading.Thread(target=init_recommender_async, daemon=True)
            thread.start()
        return recommender

@app.route('/', methods=['GET'])
def index():
    """Root endpoint with API information"""
    return jsonify({
        'name': 'Smart Recipe Recommender API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'health': '/api/health',
            'ml_status': '/api/ml/status',
            'recommend': '/api/recommend (POST)',
            'search': '/api/search?query=<term>&type=<name|ingredient|tag>',
            'recipe': '/api/recipe/<id>',
            'recipes_batch': '/api/recipes/batch (POST)',
            'stats': '/api/stats'
        },
        'frontend': 'http://localhost',
        'docs': 'https://github.com/SanaAka/Smart-Recipe-Recommender'
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy', 
        'message': 'API is running',
        'ml_ready': ml_status['ready'],
        'ml_loading': ml_status['loading']
    })

@app.route('/api/ml/status', methods=['GET'])
def ml_status_check():
    """Check ML model status"""
    return jsonify(ml_status)

@app.route('/api/recommend', methods=['POST'])
def get_recommendations():
    """Get recipe recommendations based on user input"""
    try:
        data = request.json
        ingredients = data.get('ingredients', [])
        dietary_preference = data.get('dietary_preference', '')
        cuisine_type = data.get('cuisine_type', '')

        if not ingredients:
            return jsonify({'error': 'Ingredients are required'}), 400

        # Get recommendations from ML model
        rec = get_recommender()
        
        if rec is None:
            # ML model still loading
            return jsonify({
                'loading': True,
                'message': 'AI recommendation engine is loading... Try search instead!',
                'recommendations': []
            }), 202
        
        recommendations = rec.recommend(
            ingredients=ingredients,
            dietary_preference=dietary_preference,
            cuisine_type=cuisine_type,
            limit=12
        )

        return jsonify({'recommendations': recommendations, 'loading': False})

    except Exception as e:
        print(f"Error in get_recommendations: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/search', methods=['GET'])
def search_recipes():
    """Search recipes by name, ingredient, or cuisine with optional filters"""
    try:
        import time
        start_time = time.time()
        
        query = request.args.get('query', '').strip()
        search_type = request.args.get('type', 'name')
        limit = request.args.get('limit', default=50, type=int)
        limit = max(1, min(limit, 100))  # Clamp between 1 and 100
        
        # Validate inputs
        if not query:
            return jsonify({'error': 'Query parameter is required', 'results': []}), 400
        
        if search_type not in ['name', 'ingredient', 'cuisine']:
            return jsonify({'error': 'Invalid search type. Must be name, ingredient, or cuisine', 'results': []}), 400
        
        # Get filter parameters with validation
        try:
            max_time = request.args.get('max_time', type=int)
            max_calories = request.args.get('max_calories', type=int)
            min_ingredients = request.args.get('min_ingredients', type=int)
            max_ingredients = request.args.get('max_ingredients', type=int)
        except (ValueError, TypeError) as e:
            return jsonify({'error': 'Invalid filter values. Must be numbers.', 'results': []}), 400

        results = db.search_recipes(
            query, 
            search_type, 
            limit=limit,
            max_time=max_time,
            max_calories=max_calories,
            min_ingredients=min_ingredients,
            max_ingredients=max_ingredients
        )
        
        # Ensure results is a list
        if results is None:
            results = []
        
        elapsed_time = time.time() - start_time
        print(f"[SEARCH] Query: '{query}' | Type: {search_type} | Results: {len(results)} | Time: {elapsed_time:.3f}s")
        
        from hashlib import md5
        # Build a weak ETag from query and top result ids
        top_ids = ','.join(str(r.get('id')) for r in results[:20])
        etag = 'W/"' + md5(f"{query.lower()}|{search_type}|{limit}|{top_ids}".encode()).hexdigest() + '"'

        # Conditional request handling
        if request.headers.get('If-None-Match') == etag:
            resp = app.response_class(status=304)
            resp.headers['ETag'] = etag
            resp.headers['Cache-Control'] = 'public, max-age=30'
            return resp

        resp = jsonify({'results': results})
        resp.headers['ETag'] = etag
        resp.headers['Cache-Control'] = 'public, max-age=30'
        return resp

    except Exception as e:
        print(f"Error in search_recipes: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/recipe/<int:recipe_id>', methods=['GET'])
def get_recipe_detail(recipe_id):
    """Get detailed information about a specific recipe"""
    try:
        recipe = db.get_recipe_by_id(recipe_id)
        
        if not recipe:
            return jsonify({'error': 'Recipe not found'}), 404

        return jsonify(recipe)

    except Exception as e:
        print(f"Error in get_recipe_detail: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/recipes/batch', methods=['POST'])
def get_recipes_batch():
    """Get multiple recipes by IDs (for favorites)"""
    try:
        data = request.json
        recipe_ids = data.get('recipe_ids', [])

        if not recipe_ids:
            return jsonify({'recipes': []})

        recipes = db.get_recipes_by_ids(recipe_ids)
        print(f"[BATCH] Retrieved {len(recipes)} recipes for {len(recipe_ids)} IDs")
        
        return jsonify({'recipes': recipes})

    except Exception as e:
        print(f"[ERROR] Batch request failed: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    try:
        stats = db.get_stats()
        return jsonify(stats)

    except Exception as e:
        print(f"Error in get_stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    print(f"Starting server on port {port}, debug={debug}")
    
    # Test database connection before starting server
    try:
        print("Testing database connection...")
        db.connect()
        print("[OK] Database connected successfully")
        db.disconnect()
        # Start ML recommender initialization in background so first requests don't wait
        try:
            print("[ML] Starting background recommender initialization...")
            thread = threading.Thread(target=init_recommender_async, daemon=True)
            thread.start()
        except Exception as e:
            print(f"[ML] Failed to start background init: {e}")
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        traceback.print_exc()
        import sys
        sys.exit(1)
    
    try:
        app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False, threaded=True)
    except Exception as e:
        print(f"Failed to start server: {str(e)}")
        traceback.print_exc()
    finally:
        print("Server stopped")
