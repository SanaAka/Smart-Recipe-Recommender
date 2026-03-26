"""
Enhanced Flask Application with Security, Rate Limiting, Logging, and Authentication
Refactored with best practices for production use
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_compress import Compress
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import (
    JWTManager, jwt_required, get_jwt_identity, create_access_token
)
import os
import threading
import logging
import hashlib
import requests
from pathlib import Path
from dotenv import load_dotenv
from datetime import date, timedelta
from pydantic import ValidationError

# Import local modules
from database import Database
from auth import AuthManager
from schemas import (
    RecommendationRequest, SearchRequest, BatchRecipeRequest,
    UserRegistration, UserLogin, ErrorResponse
)
from logger_config import setup_logging

# Import standout features module
try:
    from standout_features import standout_bp, init_standout_features
    STANDOUT_FEATURES_AVAILABLE = True
except ImportError:
    STANDOUT_FEATURES_AVAILABLE = False

# Import v3 features module
try:
    from v3_features import v3_bp, init_v3
    V3_FEATURES_AVAILABLE = True
except ImportError:
    V3_FEATURES_AVAILABLE = False

# Load environment variables
env_path = Path(__file__).parent / '.env'
# Ensure backend/.env takes precedence over inherited shell variables.
load_dotenv(dotenv_path=env_path, override=True)

# Setup structured logging
logger = setup_logging()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-me-in-production')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'change-me-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(
    seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '3600'))
)

# Initialize extensions
CORS(app, 
     origins=os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:3001,http://localhost:3002').split(','),
     supports_credentials=True)
Compress(app)
jwt = JWTManager(app)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[os.getenv('RATE_LIMIT_PER_MINUTE', '60') + " per minute"],
    storage_uri="memory://",
    enabled=os.getenv('RATE_LIMIT_ENABLED', 'True').lower() == 'true'
)

# Initialize database and services
db = Database()
auth_manager = AuthManager(db)
recommender = None
ml_status = {'loading': False, 'ready': False, 'error': None}
ml_lock = threading.Lock()

# Register standout features blueprint
if STANDOUT_FEATURES_AVAILABLE:
    init_standout_features(db, auth_manager, logger, limiter)
    app.register_blueprint(standout_bp)
    logger.info("Standout features registered successfully")
else:
    logger.warning("Standout features module not available")

# Register v3 features blueprint
if V3_FEATURES_AVAILABLE:
    init_v3(db, auth_manager, logger, limiter)
    app.register_blueprint(v3_bp)
    logger.info("V3 features registered: replies, reactions, user recipes")
else:
    logger.warning("V3 features module not available")


# Security headers middleware
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses (preserves CORS headers set by flask-cors)"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    # Only set CSP if not already set, and allow cross-origin API connections
    if 'Content-Security-Policy' not in response.headers:
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' http://localhost:*"
        )
    return response


# Error handlers
@app.errorhandler(ValidationError)
def handle_validation_error(error):
    """Handle Pydantic validation errors"""
    logger.warning(f"Validation error: {error}")
    return jsonify({
        'error': 'Validation error',
        'code': 'VALIDATION_ERROR',
        'details': error.errors()
    }), 400


@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded"""
    logger.warning(f"Rate limit exceeded: {get_remote_address()}")
    return jsonify({
        'error': 'Rate limit exceeded',
        'code': 'RATE_LIMIT_EXCEEDED',
        'details': str(e)
    }), 429


@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {error}", exc_info=True)
    return jsonify({
        'error': 'Internal server error',
        'code': 'INTERNAL_ERROR'
    }), 500


# ML Model initialization
def init_recommender_async():
    """Initialize ML recommender in background thread"""
    global recommender, ml_status
    try:
        with ml_lock:
            if recommender is None and not ml_status['loading']:
                ml_status['loading'] = True
                logger.info("Initializing ML recommender in background...")
        
        from ml_model_enhanced import HybridRecipeRecommender as RecipeRecommender
        temp_recommender = RecipeRecommender(db)
        
        with ml_lock:
            recommender = temp_recommender
            ml_status['loading'] = False
            ml_status['ready'] = True
            logger.info("ML recommender ready!")
    except Exception as e:
        with ml_lock:
            ml_status['loading'] = False
            ml_status['error'] = str(e)
            logger.error(f"Failed to initialize ML recommender: {e}", exc_info=True)


def get_recommender():
    """Get ML recommender, starting initialization if needed"""
    global recommender
    with ml_lock:
        if recommender is None and not ml_status['loading']:
            thread = threading.Thread(target=init_recommender_async, daemon=True)
            thread.start()
        return recommender


# Health and info endpoints
@app.route('/', methods=['GET'])
def index():
    """Root endpoint with API information"""
    return jsonify({
        'name': 'Smart Recipe Recommender API',
        'version': '2.0.0',
        'status': 'running',
        'endpoints': {
            'health': '/api/health',
            'auth': {
                'register': '/api/auth/register (POST)',
                'login': '/api/auth/login (POST)',
                'profile': '/api/auth/profile (GET - requires auth)'
            },
            'recipes': {
                'recommend': '/api/recommend (POST)',
                'search': '/api/search (GET)',
                'detail': '/api/recipe/<id> (GET)',
                'batch': '/api/recipes/batch (POST)'
            },
            'favorites': {
                'add': '/api/favorites/<recipe_id> (POST - requires auth)',
                'remove': '/api/favorites/<recipe_id> (DELETE - requires auth)',
                'list': '/api/favorites (GET - requires auth)'
            }
        }
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'ml_ready': ml_status['ready'],
        'ml_loading': ml_status['loading'],
        'database': 'connected'
    })


# Authentication endpoints
@app.route('/api/auth/register', methods=['POST'])
@limiter.limit("20 per hour")
def register():
    """Register a new user"""
    try:
        data = UserRegistration(**request.json)
        result = auth_manager.register_user(
            username=data.username,
            email=data.email,
            password=data.password
        )
        
        # Generate tokens
        tokens = auth_manager.generate_tokens(result['user_id'], result['username'])
        
        logger.info(f"New user registered: {data.username}")
        return jsonify({
            'message': 'User registered successfully',
            'user': {
                'id': result['user_id'],
                'username': result['username'],
                'email': result['email'],
                'role': 'user',
                'profile_pic': None,
                'bio': None
            },
            **tokens
        }), 201
        
    except ValidationError as e:
        # Pydantic validation failed — extract human-readable messages
        messages = [err.get('msg', '').replace('Value error, ', '') for err in e.errors()]
        error_msg = '; '.join(messages) if messages else 'Invalid input'
        logger.warning(f"Registration validation failed: {error_msg}")
        return jsonify({'error': error_msg, 'code': 'VALIDATION_ERROR'}), 400
    except ValueError as e:
        logger.warning(f"Registration failed: {e}")
        return jsonify({'error': str(e), 'code': 'REGISTRATION_FAILED'}), 400
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        return jsonify({'error': 'Registration failed', 'code': 'INTERNAL_ERROR'}), 500


@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("30 per minute")
def login():
    """Authenticate user and return JWT tokens"""
    try:
        data = UserLogin(**request.json)
        user = auth_manager.authenticate_user(data.username, data.password)
        
        if not user:
            logger.warning(f"Failed login attempt for: {data.username}")
            return jsonify({
                'error': 'Invalid credentials',
                'code': 'INVALID_CREDENTIALS'
            }), 401
        
        # Block banned users
        if user.get('role') == 'banned':
            logger.warning(f"Banned user login attempt: {data.username}")
            return jsonify({
                'error': 'Your account has been permanently banned. Contact support for help.',
                'code': 'ACCOUNT_BANNED'
            }), 403

        # Check temporary suspension
        suspended_until = user.get('suspended_until')
        if suspended_until:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            if isinstance(suspended_until, str):
                suspended_until = datetime.fromisoformat(suspended_until)
            if hasattr(suspended_until, 'tzinfo') and suspended_until.tzinfo is None:
                suspended_until = suspended_until.replace(tzinfo=timezone.utc)
            if suspended_until > now:
                remaining = suspended_until - now
                days = remaining.days
                hours = remaining.seconds // 3600
                time_str = f"{days}d {hours}h" if days > 0 else f"{hours}h"
                logger.warning(f"Suspended user login attempt: {data.username} (until {suspended_until})")
                return jsonify({
                    'error': f'Your account is suspended for {time_str}. Suspension ends {suspended_until.strftime("%b %d, %Y at %H:%M UTC")}.',
                    'code': 'ACCOUNT_SUSPENDED',
                    'suspended_until': suspended_until.isoformat()
                }), 403
            else:
                # Suspension expired — lift it
                db.execute_query(
                    "UPDATE users SET suspended_until = NULL WHERE id = %s",
                    (user['id'],), fetch=False
                )
        
        tokens = auth_manager.generate_tokens(user['id'], user['username'])
        
        logger.info(f"User logged in: {data.username}")
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user.get('role', 'user'),
                'profile_pic': user.get('profile_pic'),
                'bio': user.get('bio')
            },
            **tokens
        })
        
    except ValidationError as e:
        messages = [err.get('msg', '').replace('Value error, ', '') for err in e.errors()]
        error_msg = '; '.join(messages) if messages else 'Invalid input'
        return jsonify({'error': error_msg, 'code': 'VALIDATION_ERROR'}), 400
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        return jsonify({'error': 'Login failed', 'code': 'INTERNAL_ERROR'}), 500


@app.route('/api/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        username = get_jwt_identity()  # Now returns username string
        user = auth_manager.get_user_by_username(username)
        
        if not user:
            return jsonify({'error': 'User not found', 'code': 'USER_NOT_FOUND'}), 404
        
        # Block banned users from using their token
        if user.get('role') == 'banned':
            return jsonify({'error': 'Account suspended', 'code': 'ACCOUNT_BANNED'}), 403

        # Block temporarily suspended users
        suspended_until = user.get('suspended_until')
        if suspended_until:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            if isinstance(suspended_until, str):
                suspended_until = datetime.fromisoformat(suspended_until)
            if hasattr(suspended_until, 'tzinfo') and suspended_until.tzinfo is None:
                suspended_until = suspended_until.replace(tzinfo=timezone.utc)
            if suspended_until > now:
                return jsonify({'error': 'Account temporarily suspended', 'code': 'ACCOUNT_SUSPENDED'}), 403
        
        return jsonify({'user': user})
        
    except Exception as e:
        logger.error(f"Profile fetch error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch profile', 'code': 'INTERNAL_ERROR'}), 500


# ── Admin helpers ────────────────────────────────────────────────────
from functools import wraps

def admin_required(fn):
    """Decorator: requires JWT + admin role."""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        username = get_jwt_identity()
        user = auth_manager.get_user_by_username(username)
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required', 'code': 'FORBIDDEN'}), 403
        return fn(*args, **kwargs)
    return wrapper


# ── Admin API endpoints ──────────────────────────────────────────────
@app.route('/api/admin/users', methods=['GET'])
@admin_required
def admin_list_users():
    """List all users with stats (admin only)."""
    try:
        page = max(1, request.args.get('page', 1, type=int))
        per_page = min(50, max(1, request.args.get('per_page', 20, type=int)))
        search = request.args.get('search', '').strip()
        role_filter = request.args.get('role', '').strip()
        offset = (page - 1) * per_page

        where_clauses = []
        params = []
        if search:
            where_clauses.append("(u.username LIKE %s OR u.email LIKE %s)")
            params.extend([f'%{search}%', f'%{search}%'])
        if role_filter in ('user', 'admin', 'banned'):
            where_clauses.append("u.role = %s")
            params.append(role_filter)

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        count_rows = db.execute_query(
            f"SELECT COUNT(*) as total FROM users u {where_sql}",
            tuple(params), fetch=True
        )
        total = count_rows[0]['total'] if count_rows else 0

        rows = db.execute_query(f"""
            SELECT u.id, u.username, u.email, u.role, u.is_active,
                   u.created_at, u.last_login, u.profile_pic, u.suspended_until,
                   (SELECT COUNT(*) FROM recipes WHERE submitted_by = u.id) as recipe_count,
                   (SELECT COUNT(*) FROM recipe_comments WHERE user_id = u.id) as comment_count
            FROM users u
            {where_sql}
            ORDER BY u.created_at DESC
            LIMIT %s OFFSET %s
        """, tuple(params) + (per_page, offset), fetch=True) or []

        # Serialize datetimes
        for r in rows:
            for k in ('created_at', 'last_login', 'suspended_until'):
                if r.get(k):
                    r[k] = r[k].isoformat()

        return jsonify({
            'users': rows,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        })
    except Exception as e:
        logger.error(f"Admin list users error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to list users'}), 500


@app.route('/api/admin/users/<int:user_id>/role', methods=['PUT'])
@admin_required
def admin_set_role(user_id):
    """Change a user's role (admin only). Body: { "role": "user"|"admin"|"banned" }"""
    try:
        data = request.get_json(silent=True) or {}
        new_role = data.get('role', '')
        if new_role not in ('user', 'admin', 'banned'):
            return jsonify({'error': 'Invalid role. Must be user, admin, or banned'}), 400

        # Prevent self-demotion
        me = auth_manager.get_user_by_username(get_jwt_identity())
        if me and me['id'] == user_id:
            return jsonify({'error': "You can't change your own role"}), 400

        target = auth_manager.get_user_by_id(user_id)
        if not target:
            return jsonify({'error': 'User not found'}), 404

        db.execute_query(
            "UPDATE users SET role = %s WHERE id = %s",
            (new_role, user_id), fetch=False
        )
        logger.info(f"Admin {me['username']} set role of user {target['username']} to {new_role}")
        return jsonify({'success': True, 'user_id': user_id, 'role': new_role})
    except Exception as e:
        logger.error(f"Admin set role error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to update role'}), 500


@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def admin_delete_user(user_id):
    """Delete a user and their content (admin only)."""
    try:
        me = auth_manager.get_user_by_username(get_jwt_identity())
        if me and me['id'] == user_id:
            return jsonify({'error': "You can't delete your own account"}), 400

        target = auth_manager.get_user_by_id(user_id)
        if not target:
            return jsonify({'error': 'User not found'}), 404

        # Delete user's content in order (foreign keys)
        db.execute_query("DELETE FROM comment_reactions WHERE user_id = %s", (user_id,), fetch=False)
        db.execute_query("DELETE FROM reply_reactions WHERE user_id = %s", (user_id,), fetch=False)
        db.execute_query("DELETE FROM comment_replies WHERE user_id = %s", (user_id,), fetch=False)
        db.execute_query("DELETE FROM recipe_comments WHERE user_id = %s", (user_id,), fetch=False)
        db.execute_query("DELETE FROM recipe_ratings WHERE user_id = %s", (user_id,), fetch=False)
        db.execute_query("DELETE FROM user_favorites WHERE user_id = %s", (user_id,), fetch=False)
        # Delete user-posted recipes (ingredients, tags, steps, nutrition first)
        recipe_ids = db.execute_query(
            "SELECT id FROM recipes WHERE submitted_by = %s", (user_id,), fetch=True
        ) or []
        for r in recipe_ids:
            rid = r['id']
            for tbl in ('recipe_ingredients', 'recipe_tags', 'steps', 'nutrition',
                        'recipe_ratings', 'recipe_comments'):
                db.execute_query(f"DELETE FROM {tbl} WHERE recipe_id = %s", (rid,), fetch=False)
            db.execute_query("DELETE FROM recipes WHERE id = %s", (rid,), fetch=False)
        db.execute_query("DELETE FROM users WHERE id = %s", (user_id,), fetch=False)

        logger.info(f"Admin {me['username']} deleted user {target['username']} (id={user_id})")
        return jsonify({'success': True, 'message': f"User {target['username']} deleted"})
    except Exception as e:
        logger.error(f"Admin delete user error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to delete user'}), 500


@app.route('/api/admin/comments/<int:comment_id>', methods=['DELETE'])
@admin_required
def admin_delete_comment(comment_id):
    """Delete any comment (admin only)."""
    try:
        comment = db.execute_query(
            "SELECT id FROM recipe_comments WHERE id = %s", (comment_id,), fetch=True
        )
        if not comment:
            return jsonify({'error': 'Comment not found'}), 404

        # Delete reactions & replies first
        reply_ids = db.execute_query(
            "SELECT id FROM comment_replies WHERE comment_id = %s", (comment_id,), fetch=True
        ) or []
        for rpl in reply_ids:
            db.execute_query("DELETE FROM reply_reactions WHERE reply_id = %s", (rpl['id'],), fetch=False)
        db.execute_query("DELETE FROM comment_replies WHERE comment_id = %s", (comment_id,), fetch=False)
        db.execute_query("DELETE FROM comment_reactions WHERE comment_id = %s", (comment_id,), fetch=False)
        db.execute_query("DELETE FROM recipe_comments WHERE id = %s", (comment_id,), fetch=False)

        me = auth_manager.get_user_by_username(get_jwt_identity())
        logger.info(f"Admin {me['username']} deleted comment {comment_id}")
        return jsonify({'success': True, 'message': 'Comment deleted'})
    except Exception as e:
        logger.error(f"Admin delete comment error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to delete comment'}), 500


@app.route('/api/admin/recipes/<int:recipe_id>', methods=['DELETE'])
@admin_required
def admin_delete_recipe(recipe_id):
    """Delete any user-submitted recipe (admin only)."""
    try:
        recipe = db.execute_query(
            "SELECT id, name, submitted_by FROM recipes WHERE id = %s", (recipe_id,), fetch=True
        )
        if not recipe:
            return jsonify({'error': 'Recipe not found'}), 404

        rid = recipe[0]['id']
        for tbl in ('recipe_ingredients', 'recipe_tags', 'steps', 'nutrition',
                     'recipe_ratings', 'recipe_comments'):
            db.execute_query(f"DELETE FROM {tbl} WHERE recipe_id = %s", (rid,), fetch=False)
        db.execute_query("DELETE FROM recipes WHERE id = %s", (rid,), fetch=False)

        me = auth_manager.get_user_by_username(get_jwt_identity())
        logger.info(f"Admin {me['username']} deleted recipe {recipe[0]['name']} (id={rid})")
        return jsonify({'success': True, 'message': 'Recipe deleted'})
    except Exception as e:
        logger.error(f"Admin delete recipe error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to delete recipe'}), 500


@app.route('/api/admin/stats', methods=['GET'])
@admin_required
def admin_stats():
    """Get dashboard stats (admin only)."""
    try:
        stats = {}
        for label, sql in [
            ('total_users', "SELECT COUNT(*) as c FROM users"),
            ('banned_users', "SELECT COUNT(*) as c FROM users WHERE role='banned'"),
            ('suspended_users', "SELECT COUNT(*) as c FROM users WHERE suspended_until IS NOT NULL AND suspended_until > NOW()"),
            ('total_recipes', "SELECT COUNT(*) as c FROM recipes"),
            ('user_recipes', "SELECT COUNT(*) as c FROM recipes WHERE submitted_by IS NOT NULL"),
            ('total_comments', "SELECT COUNT(*) as c FROM recipe_comments"),
            ('total_ratings', "SELECT COUNT(*) as c FROM recipe_ratings"),
            ('pending_reports', "SELECT COUNT(*) as c FROM user_reports WHERE status='pending'"),
            ('total_reports', "SELECT COUNT(*) as c FROM user_reports"),
        ]:
            row = db.execute_query(sql, fetch=True)
            stats[label] = row[0]['c'] if row else 0
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Admin stats error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch stats'}), 500


# ── Database fallback helper for filtered recommendations ────────────
def _db_filter_fallback(ingredients, dietary_preference, cuisine_type,
                        limit, exclude_ids):
    """Query the database directly when the ML model's 20k sample has
    too few recipes matching the given dietary/cuisine filters.

    Strategy: fast 2-step approach
      1. Find candidate recipe IDs via indexed tag lookup (cuisine)
         or random sampling (diet-only). No expensive RAND on full table.
      2. Fetch ingredients/tags for candidates, then apply diet exclusion
         in Python.

    Returns a list of recipe dicts in the same format as ml_model.recommend().
    """
    from ml_model import _DIET_EXCLUSIONS
    try:
        # Step 1: get candidate recipe IDs (fast)
        candidate_ids = []

        if cuisine_type:
            # Use the indexed tag join — already fast with tag index
            sql = (
                "SELECT rt.recipe_id AS id "
                "FROM recipe_tags rt JOIN tags t ON rt.tag_id=t.id "
                "WHERE t.name=%s ORDER BY RAND() LIMIT %s"
            )
            rows = db.execute_query(sql, (cuisine_type.lower(), limit * 5), fetch=True)
            candidate_ids = [r['id'] for r in (rows or [])]
        else:
            # No cuisine filter — pick random IDs from the recipes table
            # Using a fast random-offset technique instead of ORDER BY RAND()
            max_id_row = db.execute_query(
                "SELECT MAX(id) as mx FROM recipes", fetch=True
            )
            max_id = max_id_row[0]['mx'] if max_id_row else 2000000
            import random
            # Generate random IDs and check which exist
            rand_ids = set()
            while len(rand_ids) < limit * 8:
                rand_ids.add(random.randint(1, max_id))
            placeholders = ','.join(['%s'] * len(rand_ids))
            rows = db.execute_query(
                f"SELECT id FROM recipes WHERE id IN ({placeholders}) LIMIT %s",
                tuple(rand_ids) + (limit * 5,), fetch=True
            )
            candidate_ids = [r['id'] for r in (rows or [])]

        # Remove already-known IDs
        if exclude_ids:
            candidate_ids = [cid for cid in candidate_ids if cid not in exclude_ids]

        if not candidate_ids:
            return []

        # Step 2: fetch details for candidates
        placeholders = ','.join(['%s'] * len(candidate_ids))

        # Basic recipe info
        recipe_rows = db.execute_query(
            f"SELECT id, name, minutes FROM recipes WHERE id IN ({placeholders})",
            tuple(candidate_ids), fetch=True
        )
        recipe_map = {r['id']: r for r in (recipe_rows or [])}

        # Ingredients
        ing_q = db.execute_query(
            f"SELECT ri.recipe_id, GROUP_CONCAT(i.name SEPARATOR '|') as ings "
            f"FROM recipe_ingredients ri JOIN ingredients i ON ri.ingredient_id=i.id "
            f"WHERE ri.recipe_id IN ({placeholders}) GROUP BY ri.recipe_id",
            tuple(candidate_ids), fetch=True
        )
        ing_map = {r['recipe_id']: r['ings'].split('|') for r in (ing_q or []) if r.get('ings')}

        # Tags
        tag_q = db.execute_query(
            f"SELECT rt.recipe_id, GROUP_CONCAT(t.name SEPARATOR '|') as tgs "
            f"FROM recipe_tags rt JOIN tags t ON rt.tag_id=t.id "
            f"WHERE rt.recipe_id IN ({placeholders}) GROUP BY rt.recipe_id",
            tuple(candidate_ids), fetch=True
        )
        tag_map = {r['recipe_id']: r['tgs'].split('|') for r in (tag_q or []) if r.get('tgs')}

        # Step 3: apply dietary exclusion in Python
        exclusions = _DIET_EXCLUSIONS.get(dietary_preference.lower()) if dietary_preference else None

        # Build user ingredient words for scoring
        user_words = set()
        for ing in ingredients:
            for w in ing.lower().split():
                if len(w) > 2:
                    user_words.add(w)

        results = []
        for rid in candidate_ids:
            if rid not in recipe_map:
                continue
            row = recipe_map[rid]
            ings = ing_map.get(rid, [])

            ing_word_set = set()
            for ring in ings:
                for w in ring.lower().split():
                    if len(w) > 1:
                        ing_word_set.add(w)

            # Diet exclusion check
            if exclusions and (ing_word_set & exclusions):
                continue

            # Score by ingredient overlap
            matches = len(user_words & ing_word_set) if user_words else 0

            results.append({
                'id': rid,
                'name': row['name'],
                'minutes': int(row['minutes']) if row.get('minutes') else None,
                'ingredients': ings,
                'tags': tag_map.get(rid, []),
                'similarity_score': 0.0,
                'ingredient_matches': matches,
            })

        # Sort by ingredient overlap, best matches first
        results.sort(key=lambda x: x['ingredient_matches'], reverse=True)
        return results[:limit]

    except Exception as e:
        logger.error(f"DB fallback error: {e}", exc_info=True)
        return []


# Recipe endpoints
@app.route('/api/recommend', methods=['POST'])
@limiter.limit("30 per minute")
def get_recommendations():
    """Get recipe recommendations based on user input"""
    try:
        data = RecommendationRequest(**request.json)
        
        rec = get_recommender()
        if rec is None:
            return jsonify({
                'loading': True,
                'message': 'AI recommendation engine is loading...',
                'recommendations': []
            }), 202
        
        recommendations = rec.recommend(
            ingredients=data.ingredients,
            dietary_preference=data.dietary_preference or '',
            cuisine_type=data.cuisine_type or '',
            limit=data.limit
        )
        
        # ── Database fallback for rare cuisine/dietary combos ────────
        # The ML model only holds ~20k recipes.  If the filter yields
        # too few results, query the database directly.
        if len(recommendations) < data.limit and (data.cuisine_type or data.dietary_preference):
            existing_ids = {r['id'] for r in recommendations}
            needed = data.limit - len(recommendations)
            fallback = _db_filter_fallback(
                data.ingredients,
                data.dietary_preference or '',
                data.cuisine_type or '',
                needed + 10,  # fetch extras to compensate for dupes
                existing_ids
            )
            recommendations.extend(fallback[:needed])
        
        logger.info(f"Recommendations generated: {len(recommendations)} results")
        return jsonify({'recommendations': recommendations, 'loading': False})
        
    except ValidationError as e:
        raise
    except Exception as e:
        logger.error(f"Recommendation error: {e}", exc_info=True)
        return jsonify({'error': 'Recommendation failed', 'code': 'INTERNAL_ERROR'}), 500


@app.route('/api/search', methods=['GET'])
@limiter.limit("60 per minute")
def search_recipes():
    """Search recipes with filters"""
    try:
        # Build request from query params (treat 0 as "no filter")
        def _pos_int(key):
            """Return positive int from query param, or None for absent/zero."""
            if key not in request.args:
                return None
            val = int(request.args[key])
            return val if val >= 1 else None

        data = SearchRequest(
            query=request.args.get('query', ''),
            search_type=request.args.get('type', 'name'),
            limit=int(request.args.get('limit', 50)),
            max_time=_pos_int('max_time'),
            max_calories=_pos_int('max_calories'),
            min_ingredients=_pos_int('min_ingredients'),
            max_ingredients=_pos_int('max_ingredients')
        )
        
        results = db.search_recipes(
            query=data.query,
            search_type=data.search_type.value,
            limit=data.limit,
            max_time=data.max_time,
            max_calories=data.max_calories,
            min_ingredients=data.min_ingredients,
            max_ingredients=data.max_ingredients
        )
        
        logger.info(f"Search completed: '{data.query}' returned {len(results)} results")
        return jsonify({'results': results or []})
        
    except ValidationError as e:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        return jsonify({'error': 'Search failed', 'code': 'INTERNAL_ERROR'}), 500


@app.route('/api/recipe/<int:recipe_id>', methods=['GET'])
@limiter.limit("120 per minute")
def get_recipe_detail(recipe_id):
    """Get detailed recipe information"""
    try:
        recipe = db.get_recipe_by_id(recipe_id)
        if not recipe:
            return jsonify({'error': 'Recipe not found', 'code': 'NOT_FOUND'}), 404
        
        return jsonify(recipe)
        
    except Exception as e:
        logger.error(f"Recipe fetch error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch recipe', 'code': 'INTERNAL_ERROR'}), 500


@app.route('/api/recipes/batch', methods=['POST'])
@limiter.limit("30 per minute")
def get_recipes_batch():
    """Get multiple recipes by IDs.
    Accepts: { "recipe_ids": [1,2,3] } or { "ids": [1,2,3] }
    """
    try:
        raw = request.get_json(silent=True) or {}
        # Accept both 'recipe_ids' and 'ids' for flexibility
        if 'ids' in raw and 'recipe_ids' not in raw:
            raw['recipe_ids'] = raw.pop('ids')
        data = BatchRecipeRequest(**raw)
        recipes = db.get_recipes_by_ids(data.recipe_ids)
        
        return jsonify({'recipes': recipes})
        
    except ValidationError as e:
        raise
    except Exception as e:
        logger.error(f"Batch fetch error: {e}", exc_info=True)
        return jsonify({'error': 'Batch fetch failed', 'code': 'INTERNAL_ERROR'}), 500


# Favorites endpoints (require authentication)
@app.route('/api/favorites', methods=['GET'])
@jwt_required()
@limiter.limit("60 per minute")
def get_favorites():
    """Get user's favorite recipes"""
    try:
        username = get_jwt_identity()
        user = auth_manager.get_user_by_username(username)
        recipe_ids = auth_manager.get_user_favorites(user['id'])
        
        if recipe_ids:
            recipes = db.get_recipes_by_ids(recipe_ids)
        else:
            recipes = []
        
        return jsonify({'favorites': recipes})
        
    except Exception as e:
        logger.error(f"Favorites fetch error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch favorites', 'code': 'INTERNAL_ERROR'}), 500


# ============================================================================
# RATINGS ENDPOINTS
# ============================================================================

@app.route('/api/recipe/<int:recipe_id>/rating', methods=['POST'])
@jwt_required()
@limiter.limit("30 per minute")
def rate_recipe(recipe_id):
    """Rate a recipe (1-5 stars)"""
    try:
        username = get_jwt_identity()
        user = auth_manager.get_user_by_username(username)
        
        if not user:
            return jsonify({'error': 'User not found', 'code': 'USER_NOT_FOUND'}), 404
        
        data = request.get_json()
        rating = data.get('rating')
        
        if not rating or not isinstance(rating, (int, float)) or rating < 1 or rating > 5:
            return jsonify({'error': 'Rating must be between 1 and 5', 'code': 'INVALID_RATING'}), 400
        
        # Check if recipe exists
        recipe = db.get_recipe_by_id(recipe_id)
        if not recipe:
            return jsonify({'error': 'Recipe not found', 'code': 'NOT_FOUND'}), 404
        
        # Insert or update rating
        query = """
            INSERT INTO recipe_ratings (recipe_id, user_id, rating)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE rating = %s, updated_at = CURRENT_TIMESTAMP
        """
        db.execute_query(query, (recipe_id, user['id'], rating, rating))
        
        # Get updated average rating
        avg_query = """
            SELECT AVG(rating) as avg_rating, COUNT(*) as rating_count
            FROM recipe_ratings
            WHERE recipe_id = %s
        """
        stats = db.execute_query(avg_query, (recipe_id,), fetch=True)[0]
        
        logger.info(f"User {username} rated recipe {recipe_id}: {rating} stars")
        return jsonify({
            'success': True,
            'rating': rating,
            'avg_rating': float(stats['avg_rating']) if stats['avg_rating'] else 0,
            'rating_count': stats['rating_count']
        })
        
    except Exception as e:
        logger.error(f"Rating error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to rate recipe', 'code': 'INTERNAL_ERROR'}), 500


@app.route('/api/recipe/<int:recipe_id>/rating', methods=['DELETE'])
@jwt_required()
@limiter.limit("30 per minute")
def delete_recipe_rating(recipe_id):
    """Remove user's rating from a recipe"""
    try:
        username = get_jwt_identity()
        user = auth_manager.get_user_by_username(username)

        if not user:
            return jsonify({'error': 'User not found', 'code': 'USER_NOT_FOUND'}), 404

        # Delete the rating
        delete_query = "DELETE FROM recipe_ratings WHERE recipe_id = %s AND user_id = %s"
        db.execute_query(delete_query, (recipe_id, user['id']))

        # Get updated average rating
        avg_query = """
            SELECT AVG(rating) as avg_rating, COUNT(*) as rating_count
            FROM recipe_ratings
            WHERE recipe_id = %s
        """
        stats = db.execute_query(avg_query, (recipe_id,), fetch=True)[0]

        logger.info(f"User {username} removed rating from recipe {recipe_id}")
        return jsonify({
            'success': True,
            'avg_rating': float(stats['avg_rating']) if stats['avg_rating'] else 0,
            'rating_count': stats['rating_count']
        })

    except Exception as e:
        logger.error(f"Delete rating error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to remove rating', 'code': 'INTERNAL_ERROR'}), 500


@app.route('/api/recipe/<int:recipe_id>/rating', methods=['GET'])
@limiter.limit("120 per minute")
def get_recipe_rating(recipe_id):
    """Get recipe rating statistics and user's rating if authenticated"""
    try:
        # Get overall rating stats
        query = """
            SELECT AVG(rating) as avg_rating, COUNT(*) as rating_count
            FROM recipe_ratings
            WHERE recipe_id = %s
        """
        stats = db.execute_query(query, (recipe_id,), fetch=True)
        
        if not stats:
            return jsonify({'avg_rating': 0, 'rating_count': 0, 'user_rating': None})
        
        result = {
            'avg_rating': float(stats[0]['avg_rating']) if stats[0]['avg_rating'] else 0,
            'rating_count': stats[0]['rating_count'],
            'user_rating': None
        }
        
        # If user is authenticated, get their rating
        try:
            from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
            verify_jwt_in_request(optional=True)
            username = get_jwt_identity()
            
            if username:
                user = auth_manager.get_user_by_username(username)
                if user:
                    user_query = """
                        SELECT rating FROM recipe_ratings
                        WHERE recipe_id = %s AND user_id = %s
                    """
                    user_rating = db.execute_query(user_query, (recipe_id, user['id']), fetch=True)
                    if user_rating:
                        result['user_rating'] = user_rating[0]['rating']
        except:
            pass  # JWT not present or invalid, continue without user rating
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Get rating error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch rating', 'code': 'INTERNAL_ERROR'}), 500


# ============================================================================
# COMMENTS ENDPOINTS
# ============================================================================

@app.route('/api/recipe/<int:recipe_id>/comments', methods=['GET'])
@limiter.limit("120 per minute")
def get_recipe_comments(recipe_id):
    """Get comments for a recipe with pagination"""
    try:
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 20)), 50)
        offset = (page - 1) * limit
        
        # Get comments with user info
        query = """
            SELECT 
                c.id, c.comment, c.created_at, c.updated_at,
                u.username, u.id as user_id, u.profile_pic
            FROM recipe_comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.recipe_id = %s
            ORDER BY c.created_at DESC
            LIMIT %s OFFSET %s
        """
        comments = db.execute_query(query, (recipe_id, limit, offset), fetch=True) or []
        
        # Get total count
        count_query = "SELECT COUNT(*) as total FROM recipe_comments WHERE recipe_id = %s"
        total = db.execute_query(count_query, (recipe_id,), fetch=True)[0]['total']
        
        # Enrich comments with reaction counts and reply counts
        if comments:
            cids = [c['id'] for c in comments]
            ph = ','.join(['%s'] * len(cids))

            # Reaction counts per comment
            try:
                reaction_rows = db.execute_query(f"""
                    SELECT comment_id, reaction_type, COUNT(*) as cnt
                    FROM comment_reactions WHERE comment_id IN ({ph})
                    GROUP BY comment_id, reaction_type
                """, tuple(cids), fetch=True) or []
            except:
                reaction_rows = []

            # Reply counts per comment
            try:
                reply_rows = db.execute_query(f"""
                    SELECT comment_id, COUNT(*) as cnt
                    FROM comment_replies WHERE comment_id IN ({ph})
                    GROUP BY comment_id
                """, tuple(cids), fetch=True) or []
            except:
                reply_rows = []

            reply_map = {r['comment_id']: r['cnt'] for r in reply_rows}

            for c in comments:
                c['likes'] = 0
                c['dislikes'] = 0
                c['reply_count'] = reply_map.get(c['id'], 0)
                c['user_reaction'] = None

            for row in reaction_rows:
                for c in comments:
                    if c['id'] == row['comment_id']:
                        if row['reaction_type'] == 'like':
                            c['likes'] = row['cnt']
                        else:
                            c['dislikes'] = row['cnt']

            # Get current user's reactions if authenticated
            try:
                from flask_jwt_extended import verify_jwt_in_request
                verify_jwt_in_request(optional=True)
                uname = get_jwt_identity()
                if uname:
                    u = auth_manager.get_user_by_username(uname)
                    if u:
                        user_reactions = db.execute_query(f"""
                            SELECT comment_id, reaction_type
                            FROM comment_reactions WHERE comment_id IN ({ph}) AND user_id = %s
                        """, tuple(cids) + (u['id'],), fetch=True) or []
                        for ur in user_reactions:
                            for c in comments:
                                if c['id'] == ur['comment_id']:
                                    c['user_reaction'] = ur['reaction_type']
            except:
                pass

        return jsonify({
            'comments': comments,
            'total': total,
            'page': page,
            'limit': limit,
            'has_more': (page * limit) < total
        })
        
    except Exception as e:
        logger.error(f"Get comments error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch comments', 'code': 'INTERNAL_ERROR'}), 500


@app.route('/api/recipe/<int:recipe_id>/comments', methods=['POST'])
@jwt_required()
@limiter.limit("10 per minute")
def add_recipe_comment(recipe_id):
    """Add a comment to a recipe"""
    try:
        username = get_jwt_identity()
        user = auth_manager.get_user_by_username(username)
        
        if not user:
            return jsonify({'error': 'User not found', 'code': 'USER_NOT_FOUND'}), 404
        
        data = request.get_json()
        comment = data.get('comment', '').strip()
        
        if not comment or len(comment) < 3:
            return jsonify({'error': 'Comment must be at least 3 characters', 'code': 'INVALID_COMMENT'}), 400
        
        if len(comment) > 1000:
            return jsonify({'error': 'Comment must be less than 1000 characters', 'code': 'COMMENT_TOO_LONG'}), 400
        
        # Check if recipe exists
        recipe = db.get_recipe_by_id(recipe_id)
        if not recipe:
            return jsonify({'error': 'Recipe not found', 'code': 'NOT_FOUND'}), 404
        
        # Insert comment
        query = """
            INSERT INTO recipe_comments (recipe_id, user_id, comment)
            VALUES (%s, %s, %s)
        """
        db.execute_query(query, (recipe_id, user['id'], comment))
        
        # Get the newly created comment
        get_query = """
            SELECT 
                c.id, c.comment, c.created_at, c.updated_at,
                u.username, u.id as user_id, u.profile_pic
            FROM recipe_comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.recipe_id = %s AND c.user_id = %s
            ORDER BY c.created_at DESC
            LIMIT 1
        """
        new_comment = db.execute_query(get_query, (recipe_id, user['id']), fetch=True)[0]
        
        logger.info(f"User {username} commented on recipe {recipe_id}")
        return jsonify({'success': True, 'comment': new_comment}), 201
        
    except Exception as e:
        logger.error(f"Add comment error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to add comment', 'code': 'INTERNAL_ERROR'}), 500


@app.route('/api/recipe/<int:recipe_id>/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
@limiter.limit("30 per minute")
def delete_recipe_comment(recipe_id, comment_id):
    """Delete a comment (only by comment author)"""
    try:
        username = get_jwt_identity()
        user = auth_manager.get_user_by_username(username)
        
        if not user:
            return jsonify({'error': 'User not found', 'code': 'USER_NOT_FOUND'}), 404
        
        # Check if comment exists and belongs to user
        check_query = """
            SELECT user_id FROM recipe_comments
            WHERE id = %s AND recipe_id = %s
        """
        comment = db.execute_query(check_query, (comment_id, recipe_id), fetch=True)
        
        if not comment:
            return jsonify({'error': 'Comment not found', 'code': 'NOT_FOUND'}), 404
        
        if comment[0]['user_id'] != user['id']:
            return jsonify({'error': 'Unauthorized to delete this comment', 'code': 'UNAUTHORIZED'}), 403
        
        # Delete comment
        delete_query = "DELETE FROM recipe_comments WHERE id = %s"
        db.execute_query(delete_query, (comment_id,))
        
        logger.info(f"User {username} deleted comment {comment_id}")
        return jsonify({'success': True, 'message': 'Comment deleted'})
        
    except Exception as e:
        logger.error(f"Delete comment error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to delete comment', 'code': 'INTERNAL_ERROR'}), 500


# ============================================================================
# UNSPLASH IMAGE SEARCH
# ============================================================================

# In-memory cache to avoid hitting the API repeatedly for the same recipe
_image_cache = {}  # recipe_id -> {'url': ..., 'thumb': ..., 'photographer': ..., etc.}

# UTM params for Unsplash attribution (required for API compliance)
_UTM_SOURCE = 'smart_recipe_recommender'
_UTM_MEDIUM = 'referral'

# Unsplash API rate tracker
# Auto-detect tier: set UNSPLASH_PRODUCTION=true in .env when approved
_unsplash_calls = []  # timestamps of API calls
_unsplash_lock = threading.Lock()
_UNSPLASH_PRODUCTION = os.environ.get('UNSPLASH_PRODUCTION', '').lower() in ('true', '1', 'yes')
_UNSPLASH_HOURLY_LIMIT = 4500 if _UNSPLASH_PRODUCTION else 45  # production: 5000/hr with 500 buffer

def _can_call_unsplash():
    """Check if we're under the Unsplash hourly rate limit"""
    import time
    now = time.time()
    with _unsplash_lock:
        _unsplash_calls[:] = [t for t in _unsplash_calls if now - t < 3600]
        if len(_unsplash_calls) >= _UNSPLASH_HOURLY_LIMIT:
            return False
        _unsplash_calls.append(now)
        return True

def _is_broken_url(url):
    """Check if an image_url is a dead source.unsplash.com link"""
    if not url:
        return True
    return 'source.unsplash.com' in url

def _resolve_image(recipe_id, unsplash_key):
    """Resolve a single recipe's image. Returns {url, thumb, ...} dict.
    Used by both single and batch endpoints."""
    # Check in-memory cache
    if recipe_id in _image_cache:
        return _image_cache[recipe_id]

    # Get recipe from DB
    recipe = db.get_recipe_by_id(recipe_id)
    if not recipe:
        return {'url': None, 'thumb': None}

    # If it already has a good image, cache & return
    existing_url = recipe.get('image_url', '')
    if existing_url and not _is_broken_url(existing_url):
        result = {'url': existing_url, 'thumb': existing_url, 'cached': True}
        _image_cache[recipe_id] = result
        return result

    # No API key? Return null
    if not unsplash_key or unsplash_key == 'your-access-key-here':
        return {'url': None, 'error': 'API key not configured'}

    # Check rate limit before calling Unsplash
    if not _can_call_unsplash():
        return {'url': None, 'thumb': None, 'rate_limited': True}

    try:
        search_query = recipe['name'] + ' food dish'
        resp = requests.get('https://api.unsplash.com/search/photos', params={
            'query': search_query,
            'per_page': 1,
            'orientation': 'landscape',
            'content_filter': 'high'
        }, headers={'Authorization': f'Client-ID {unsplash_key}'}, timeout=5)

        if resp.status_code == 200 and resp.json().get('results'):
            img = resp.json()['results'][0]
            image_url = img['urls'].get('small', img['urls']['regular'])
            thumb_url = img['urls'].get('thumb', image_url)

            # Unsplash attribution data (required by API guidelines)
            photographer_name = img['user']['name']
            photographer_username = img['user'].get('username', '')
            photographer_url = (
                f"https://unsplash.com/@{photographer_username}"
                f"?utm_source={_UTM_SOURCE}&utm_medium={_UTM_MEDIUM}"
            )
            unsplash_url = (
                f"https://unsplash.com/?utm_source={_UTM_SOURCE}&utm_medium={_UTM_MEDIUM}"
            )
            download_location = img.get('links', {}).get('download_location', '')

            # Save to DB
            db.execute_query(
                "UPDATE recipes SET image_url = %s WHERE id = %s",
                (image_url, recipe_id)
            )

            result = {
                'url': image_url,
                'thumb': thumb_url,
                'photographer': photographer_name,
                'photographer_url': photographer_url,
                'unsplash_url': unsplash_url,
                'download_location': download_location,
                'cached': False
            }
            _image_cache[recipe_id] = result
            logger.info(f"Auto-fetched image for recipe {recipe_id}: {recipe['name']}")
            return result
        else:
            _image_cache[recipe_id] = {'url': None, 'thumb': None}
            return {'url': None}
    except requests.RequestException as e:
        logger.warning(f"Unsplash API error for recipe {recipe_id}: {e}")
        return {'url': None, 'error': 'Image service unavailable'}


@app.route('/api/images/batch', methods=['POST'])
@limiter.exempt
def batch_images():
    """Resolve images for multiple recipes in a single request.
    Accepts: { "ids": [1, 2, 3] } or { "recipe_ids": [1, 2, 3] }  (max 50)
    Returns: { "images": { "1": {"url": "..."}, "2": {"url": "..."} } }
    """
    data = request.get_json(silent=True) or {}
    ids = data.get('ids', data.get('recipe_ids', []))

    if not ids or not isinstance(ids, list):
        return jsonify({'error': 'Provide a list of recipe ids'}), 400

    # Cap at 50 per request
    ids = [int(i) for i in ids[:50]]
    unsplash_key = os.getenv('UNSPLASH_ACCESS_KEY')
    images = {}

    for rid in ids:
        images[str(rid)] = _resolve_image(rid, unsplash_key)

    return jsonify({'images': images})


@app.route('/api/recipe/<int:recipe_id>/auto-image', methods=['GET'])
@limiter.exempt
def auto_image(recipe_id):
    """Auto-fetch a real image for a recipe from Unsplash API.
    Caches the result in the DB so it only hits the API once per recipe."""
    try:
        unsplash_key = os.getenv('UNSPLASH_ACCESS_KEY')
        result = _resolve_image(recipe_id, unsplash_key)
        if result.get('error') == 'Image service unavailable':
            return jsonify(result), 503
        return jsonify(result)
    except Exception as e:
        logger.error(f"Auto-image error for recipe {recipe_id}: {e}", exc_info=True)
        return jsonify({'url': None}), 500


@app.route('/api/recipe/<int:recipe_id>/image/search', methods=['GET'])
@limiter.limit("30 per minute")
def search_recipe_image(recipe_id):
    """Search Unsplash for recipe images"""
    try:
        recipe = db.get_recipe_by_id(recipe_id)
        if not recipe:
            return jsonify({'error': 'Recipe not found', 'code': 'NOT_FOUND'}), 404
        
        unsplash_key = os.getenv('UNSPLASH_ACCESS_KEY')
        if not unsplash_key or unsplash_key == 'your-access-key-here':
            # Fallback to default placeholder
            return jsonify({
                'images': [],
                'message': 'Unsplash API key not configured'
            })
        
        # Search query based on recipe name
        query = recipe['name']
        url = 'https://api.unsplash.com/search/photos'
        params = {
            'query': f"{query} food",
            'per_page': 6,
            'orientation': 'landscape'
        }
        headers = {'Authorization': f'Client-ID {unsplash_key}'}
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            images = [{
                'id': img['id'],
                'url': img['urls']['regular'],
                'thumb': img['urls']['thumb'],
                'photographer': img['user']['name'],
                'photographer_url': (
                    f"https://unsplash.com/@{img['user'].get('username', '')}"
                    f"?utm_source={_UTM_SOURCE}&utm_medium={_UTM_MEDIUM}"
                ),
                'unsplash_url': (
                    f"https://unsplash.com/?utm_source={_UTM_SOURCE}&utm_medium={_UTM_MEDIUM}"
                ),
                'download_location': img.get('links', {}).get('download_location', '')
            } for img in data.get('results', [])]
            
            return jsonify({'images': images})
        else:
            return jsonify({'images': [], 'error': 'Failed to fetch images'})
        
    except requests.RequestException as e:
        logger.error(f"Unsplash API error: {e}")
        return jsonify({'images': [], 'error': 'Image search unavailable'}), 503
    except Exception as e:
        logger.error(f"Image search error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to search images', 'code': 'INTERNAL_ERROR'}), 500


@app.route('/api/recipe/<int:recipe_id>/image', methods=['POST'])
@jwt_required()
@limiter.limit("20 per minute")
def update_recipe_image(recipe_id):
    """Update recipe image URL. Also triggers Unsplash download tracking
    when a user selects an image (required by Unsplash API guidelines)."""
    try:
        username = get_jwt_identity()
        
        data = request.get_json()
        image_url = data.get('image_url', '').strip()
        download_location = data.get('download_location', '').strip()
        
        if not image_url:
            return jsonify({'error': 'Image URL is required', 'code': 'INVALID_INPUT'}), 400
        
        # Check if recipe exists
        recipe = db.get_recipe_by_id(recipe_id)
        if not recipe:
            return jsonify({'error': 'Recipe not found', 'code': 'NOT_FOUND'}), 404
        
        # Trigger Unsplash download tracking when user selects an image
        # (required by Unsplash API guidelines — "Triggering a Download")
        if download_location:
            _trigger_unsplash_download(download_location)
        
        # Update image URL
        query = "UPDATE recipes SET image_url = %s WHERE id = %s"
        db.execute_query(query, (image_url, recipe_id))
        
        # Update in-memory cache with new image
        _image_cache[recipe_id] = {
            'url': image_url,
            'thumb': image_url,
            'photographer': data.get('photographer', ''),
            'photographer_url': data.get('photographer_url', ''),
            'unsplash_url': f"https://unsplash.com/?utm_source={_UTM_SOURCE}&utm_medium={_UTM_MEDIUM}",
            'cached': True
        }
        
        logger.info(f"User {username} updated image for recipe {recipe_id}")
        return jsonify({'success': True, 'image_url': image_url})
        
    except Exception as e:
        logger.error(f"Update image error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to update image', 'code': 'INTERNAL_ERROR'}), 500


@app.route('/api/images/track-download', methods=['POST'])
@limiter.limit("60 per minute")
def track_unsplash_download():
    """Trigger an Unsplash download event.
    Required by Unsplash API guidelines when a user performs an action
    that is similar to a download (selecting an image, setting it as header, etc.).
    See: https://help.unsplash.com/en/articles/2511258-guideline-triggering-a-download
    """
    data = request.get_json(silent=True) or {}
    download_location = data.get('download_location', '').strip()
    
    if not download_location:
        return jsonify({'error': 'download_location is required'}), 400
    
    success = _trigger_unsplash_download(download_location)
    if success:
        return jsonify({'success': True, 'message': 'Download tracked'})
    else:
        return jsonify({'success': False, 'error': 'Failed to trigger download'}), 502


def _trigger_unsplash_download(download_location):
    """Send a request to the Unsplash download tracking endpoint.
    This must be called when a user selects/uses an Unsplash image.
    https://help.unsplash.com/en/articles/2511258-guideline-triggering-a-download
    """
    if not download_location or 'unsplash.com' not in download_location:
        return False
    
    unsplash_key = os.getenv('UNSPLASH_ACCESS_KEY')
    if not unsplash_key or unsplash_key == 'your-access-key-here':
        return False
    
    try:
        resp = requests.get(
            download_location,
            headers={'Authorization': f'Client-ID {unsplash_key}'},
            timeout=5
        )
        if resp.status_code == 200:
            logger.info(f"Unsplash download triggered: {download_location}")
            return True
        else:
            logger.warning(f"Unsplash download tracking failed ({resp.status_code})")
            return False
    except requests.RequestException as e:
        logger.warning(f"Unsplash download tracking error: {e}")
        return False


# ============================================================================
# RECIPE OF THE DAY & PERSONALIZED RECOMMENDATIONS
# ============================================================================

@app.route('/api/recipe-of-the-day', methods=['GET'])
@limiter.limit("120 per minute")
def recipe_of_the_day():
    """Return a deterministic 'Recipe of the Day' — same for ALL users on a given date.
    Uses a date-based seed so everyone sees the same pick and it rotates daily.
    Optimized: uses 2 fast queries instead of 4."""
    try:
        today_str = date.today().isoformat()  # e.g. "2026-02-08"

        # Deterministic hash -> integer seed
        seed = int(hashlib.md5(f"rotd-{today_str}".encode()).hexdigest(), 16)

        # Get ID range (fast - uses index extremes, not COUNT)
        range_row = db.execute_query(
            "SELECT MIN(id) AS min_id, MAX(id) AS max_id FROM recipes", fetch=True
        )
        if not range_row or range_row[0]['min_id'] is None:
            return jsonify({'recipe': None})
        min_id = range_row[0]['min_id']
        max_id = range_row[0]['max_id']

        # Pick a deterministic ID within [min_id, max_id] using seed
        target_id = min_id + (seed % (max_id - min_id + 1))

        # Fast primary-key lookup (avoid LEFT JOIN which confuses optimizer on 2M rows)
        recipe_row = db.execute_query("""
            SELECT id, name, minutes, description, image_url
            FROM recipes
            WHERE id >= %s
            ORDER BY id
            LIMIT 1
        """, (target_id,), fetch=True)

        # If we overshot (gaps at the end), wrap around to min_id
        if not recipe_row:
            recipe_row = db.execute_query("""
                SELECT id, name, minutes, description, image_url
                FROM recipes
                WHERE id >= %s
                ORDER BY id
                LIMIT 1
            """, (min_id,), fetch=True)

        if not recipe_row:
            return jsonify({'recipe': None})

        recipe = recipe_row[0]
        rid = recipe['id']

        # Fetch nutrition, tags, rating with fast indexed lookups (3 tiny queries)
        nut = db.execute_query(
            "SELECT calories FROM nutrition WHERE recipe_id = %s", (rid,), fetch=True
        )
        recipe['calories'] = nut[0]['calories'] if nut else None

        tags_rows = db.execute_query("""
            SELECT t.name FROM recipe_tags rt JOIN tags t ON rt.tag_id = t.id
            WHERE rt.recipe_id = %s LIMIT 5
        """, (rid,), fetch=True) or []
        recipe['tags'] = [t['name'] for t in tags_rows]

        rating_row = db.execute_query("""
            SELECT AVG(rating) AS avg_rating, COUNT(*) AS rating_count
            FROM recipe_ratings WHERE recipe_id = %s
        """, (rid,), fetch=True)
        recipe['avg_rating'] = round(float(rating_row[0]['avg_rating']), 1) if rating_row and rating_row[0]['avg_rating'] else 0
        recipe['rating_count'] = rating_row[0]['rating_count'] if rating_row and rating_row[0]['rating_count'] else 0

        return jsonify({'recipe': recipe, 'date': today_str})

    except Exception as e:
        logger.error(f"Recipe of the Day error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get recipe of the day'}), 500


@app.route('/api/recommendations/personal', methods=['GET'])
@jwt_required()
@limiter.limit("30 per minute")
def personal_recommendations():
    """Return personalized recipe picks based on the user's ratings & favorites.

    Fast strategy (uses ML model, not heavy SQL):
    1. Find tags/ingredients the user likes (small query on user's recipes only)
    2. Feed those tags as "ingredients" into the ML recommender (instant)
    3. Filter out recipes the user already interacted with
    Falls back to top-rated recipes if no user history.
    """
    try:
        username = get_jwt_identity()
        user = auth_manager.get_user_by_username(username)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        limit = min(int(request.args.get('limit', 6)), 20)
        user_id = user['id']

        # 1. Collect recipe IDs the user rated highly (>= 4) or favorited
        loved_rows = db.execute_query("""
            SELECT DISTINCT recipe_id FROM (
                SELECT recipe_id FROM recipe_ratings
                WHERE user_id = %s AND rating >= 4
                UNION
                SELECT recipe_id FROM user_favorites
                WHERE user_id = %s
            ) AS loved
        """, (user_id, user_id), fetch=True) or []

        loved_ids = set(r['recipe_id'] for r in loved_rows)

        if not loved_ids:
            # No history — fall back to globally top-rated recipes
            fallback = db.execute_query("""
                SELECT r.id, r.name, r.minutes, r.image_url, n.calories,
                       s.avg_rating, s.rating_count
                FROM (
                    SELECT recipe_id,
                           ROUND(AVG(rating), 1) AS avg_rating,
                           COUNT(id) AS rating_count
                    FROM recipe_ratings
                    GROUP BY recipe_id
                    HAVING COUNT(id) >= 2
                    ORDER BY AVG(rating) DESC, COUNT(id) DESC
                    LIMIT %s
                ) s
                JOIN recipes r ON r.id = s.recipe_id
                LEFT JOIN nutrition n ON r.id = n.recipe_id
                ORDER BY s.avg_rating DESC, s.rating_count DESC
            """, (limit,), fetch=True) or []
            return jsonify({
                'recipes': fallback,
                'strategy': 'top-rated',
                'message': 'Rate or favorite some recipes to get personalized picks!'
            })

        # 2. Find the user's preferred tags & top ingredients (small query,
        #    only touches the user's few loved recipes — fast)
        ph = ','.join(['%s'] * len(loved_ids))
        tag_rows = db.execute_query(f"""
            SELECT t.name, COUNT(*) AS freq
            FROM recipe_tags rt
            JOIN tags t ON rt.tag_id = t.id
            WHERE rt.recipe_id IN ({ph})
            GROUP BY t.id
            ORDER BY freq DESC
            LIMIT 10
        """, tuple(loved_ids), fetch=True) or []

        top_tags = [t['name'] for t in tag_rows[:5]]

        # Also grab top ingredients from loved recipes
        ing_rows = db.execute_query(f"""
            SELECT i.name, COUNT(*) AS freq
            FROM recipe_ingredients ri
            JOIN ingredients i ON ri.ingredient_id = i.id
            WHERE ri.recipe_id IN ({ph})
            GROUP BY i.id
            ORDER BY freq DESC
            LIMIT 8
        """, tuple(loved_ids), fetch=True) or []

        top_ings = [i['name'] for i in ing_rows[:5]]

        # 3. Use the ML recommender (instant — ~0.03ms) instead of
        #    scanning 17M recipe_tags rows
        rec = get_recommender()
        if rec is not None:
            # Feed user's favorite tags + ingredients as the query
            query_terms = top_ings if top_ings else top_tags
            raw = rec.recommend(
                ingredients=query_terms,
                user_id=user_id,
                limit=limit + len(loved_ids),  # fetch extras to compensate filtering
                diversify=True,
            )
            # Filter out already-loved recipes
            recommended = []
            for r in raw:
                if r['id'] not in loved_ids:
                    recommended.append({
                        'id': r['id'],
                        'name': r['name'],
                        'minutes': r.get('minutes'),
                        'image_url': r.get('image_url'),
                        'calories': None,
                        'tags': r.get('tags', [])[:5],
                    })
                if len(recommended) >= limit:
                    break
        else:
            # ML model not ready — use fast random fallback
            import random as _rand
            max_id_row = db.execute_query(
                'SELECT MAX(id) AS mx FROM recipes', fetch=True
            )
            max_id = (max_id_row[0]['mx'] if max_id_row else 2000000) or 2000000
            rand_start = _rand.randint(1, max(1, max_id - 1000))
            ph_excl = ','.join(['%s'] * len(loved_ids))
            recommended = db.execute_query(f"""
                SELECT r.id, r.name, r.minutes, r.image_url, n.calories
                FROM recipes r
                LEFT JOIN nutrition n ON r.id = n.recipe_id
                WHERE r.id >= %s AND r.id NOT IN ({ph_excl})
                LIMIT %s
            """, (rand_start,) + tuple(loved_ids) + (limit,), fetch=True) or []

        return jsonify({
            'recipes': recommended,
            'strategy': 'personalized',
            'based_on_tags': top_tags
        })

    except Exception as e:
        logger.error(f"Personal recommendations error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get recommendations'}), 500


# ============================================================================
# PAGINATION SUPPORT FOR BROWSING
# ============================================================================


@app.route('/api/stats', methods=['GET'])
@limiter.limit("60 per minute")
def api_stats():
    """Get overall platform statistics (cached for 5 minutes)"""
    try:
        import time as _time
        cache_key = '_stats_cache'
        cache_ttl = 300  # 5 minutes

        # Check in-memory cache
        if hasattr(api_stats, '_cache') and _time.time() - api_stats._cache.get('ts', 0) < cache_ttl:
            return jsonify(api_stats._cache['data'])

        row = db.execute_query("""
            SELECT
                (SELECT COUNT(*) FROM recipes) AS total_recipes,
                (SELECT COUNT(*) FROM users) AS total_users,
                (SELECT COUNT(*) FROM recipe_ratings) AS total_ratings,
                (SELECT COUNT(*) FROM recipe_comments) AS total_comments,
                (SELECT COUNT(DISTINCT name) FROM tags) AS total_tags,
                (SELECT COUNT(DISTINCT name) FROM ingredients) AS total_ingredients
        """, fetch=True)

        stats = row[0] if row else {}
        stats['ml_ready'] = ml_status.get('ready', False)

        # Cache the result
        api_stats._cache = {'data': stats, 'ts': _time.time()}

        return jsonify(stats)
    except Exception as e:
        logger.error(f"Stats error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get stats', 'code': 'INTERNAL_ERROR'}), 500


@app.route('/api/recipes/random', methods=['GET'])
@limiter.limit("60 per minute")
def random_recipes():
    """Get random recipes for discovery. ?count=5 (default 5, max 20)"""
    try:
        count = min(int(request.args.get('count', 5)), 20)

        # Fast random selection using ID range (avoids ORDER BY RAND() on 2M rows)
        range_row = db.execute_query(
            "SELECT MIN(id) AS min_id, MAX(id) AS max_id FROM recipes", fetch=True
        )
        if not range_row or range_row[0]['min_id'] is None:
            return jsonify({'recipes': []})

        import random
        min_id = range_row[0]['min_id']
        max_id = range_row[0]['max_id']
        # Generate more random IDs than needed to handle gaps
        candidates = set()
        while len(candidates) < count * 3:
            candidates.add(random.randint(min_id, max_id))
        candidates = list(candidates)[:count * 3]

        ph = ','.join(['%s'] * len(candidates))
        recipes = db.execute_query(f"""
            SELECT id, name, minutes, image_url
            FROM recipes
            WHERE id IN ({ph})
            LIMIT %s
        """, tuple(candidates) + (count,), fetch=True) or []

        return jsonify({'recipes': recipes, 'count': len(recipes)})

    except Exception as e:
        logger.error(f"Random recipes error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get random recipes', 'code': 'INTERNAL_ERROR'}), 500


@app.route('/api/recipes', methods=['GET'])
@limiter.limit("60 per minute")
def list_recipes():
    """List recipes with pagination. Supports both limit/offset and page/per_page styles."""
    try:
        # Support both pagination styles
        page = int(request.args.get('page', 0))
        per_page = int(request.args.get('per_page', 0))
        limit = min(int(request.args.get('limit', per_page or 20)), 100)
        offset = int(request.args.get('offset', 0))
        if page > 0:
            offset = (page - 1) * limit

        query = """
            SELECT id, name, minutes, image_url
            FROM recipes
            ORDER BY id
            LIMIT %s OFFSET %s
        """
        recipes = db.execute_query(query, (limit, offset), fetch=True) or []

        current_page = page if page > 0 else (offset // limit) + 1

        # Only compute total when the client actually paginates (avoids slow COUNT on 2M rows)
        # Use fast estimate from ID range instead of exact COUNT(*)
        range_row = db.execute_query(
            "SELECT MIN(id) AS min_id, MAX(id) AS max_id FROM recipes", fetch=True
        )
        total = (range_row[0]['max_id'] - range_row[0]['min_id'] + 1) if range_row and range_row[0]['min_id'] else 0

        return jsonify({
            'recipes': recipes,
            'total': total,
            'page': current_page,
            'per_page': limit,
            'has_more': len(recipes) == limit
        })

    except Exception as e:
        logger.error(f"List recipes error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to list recipes', 'code': 'INTERNAL_ERROR'}), 500


@app.route('/api/recipes/browse', methods=['GET'])
@limiter.limit("60 per minute")
def browse_recipes():
    """Browse recipes with pagination, sorting, and filters"""
    try:
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 20)), 100)
        offset = (page - 1) * limit
        
        sort_by = request.args.get('sort', 'popular')  # popular, recent, rating, name
        max_time = request.args.get('max_time')
        max_calories = request.args.get('max_calories')
        
        # Build WHERE clause
        where_conditions = []
        params = []
        
        if max_time:
            where_conditions.append('r.minutes <= %s')
            params.append(int(max_time))
        
        if max_calories:
            where_conditions.append('n.calories <= %s')
            params.append(int(max_calories))
        
        where_clause = ' AND ' + ' AND '.join(where_conditions) if where_conditions else ''
        
        # Build ORDER BY clause  (avoid joining stats table for non-stat sorts)
        order_map = {
            'popular': 'r.id DESC',   # approximate; avoids extra JOIN
            'recent': 'r.id DESC',
            'rating': 'r.id DESC',
            'name': 'r.name ASC'
        }
        order_by = order_map.get(sort_by, 'r.id DESC')
        
        # ---- Step 1: lightweight paginated query (no GROUP_CONCAT) ----
        needs_nutrition_join = bool(max_calories)
        if needs_nutrition_join:
            base_query = f"""
                SELECT r.id, r.name, r.minutes, r.image_url, n.calories
                FROM recipes r
                LEFT JOIN nutrition n ON r.id = n.recipe_id
                WHERE 1=1{where_clause}
                ORDER BY {order_by}
                LIMIT %s OFFSET %s
            """
        else:
            base_query = f"""
                SELECT r.id, r.name, r.minutes, r.image_url
                FROM recipes r
                WHERE 1=1{where_clause}
                ORDER BY {order_by}
                LIMIT %s OFFSET %s
            """
        
        params.extend([limit, offset])
        recipes = db.execute_query(base_query, tuple(params), fetch=True) or []
        
        # ---- Step 2: batch-fetch tags & ingredients for the page ----
        if recipes:
            ids = [r['id'] for r in recipes]
            ph = ','.join(['%s'] * len(ids))
            
            # Ingredients
            ing_rows = db.execute_query(
                f"SELECT ri.recipe_id, GROUP_CONCAT(i.name ORDER BY i.name SEPARATOR '|') as ingredients "
                f"FROM recipe_ingredients ri JOIN ingredients i ON ri.ingredient_id = i.id "
                f"WHERE ri.recipe_id IN ({ph}) GROUP BY ri.recipe_id",
                tuple(ids), fetch=True) or []
            ing_map = {r['recipe_id']: r['ingredients'].split('|') for r in ing_rows if r.get('ingredients')}
            
            # Tags
            tag_rows = db.execute_query(
                f"SELECT rt.recipe_id, GROUP_CONCAT(t.name ORDER BY t.name SEPARATOR '|') as tags "
                f"FROM recipe_tags rt JOIN tags t ON rt.tag_id = t.id "
                f"WHERE rt.recipe_id IN ({ph}) GROUP BY rt.recipe_id",
                tuple(ids), fetch=True) or []
            tag_map = {r['recipe_id']: r['tags'].split('|') for r in tag_rows if r.get('tags')}
            
            # Nutrition (if not already fetched)
            if not needs_nutrition_join:
                nut_rows = db.execute_query(
                    f"SELECT recipe_id, calories FROM nutrition WHERE recipe_id IN ({ph})",
                    tuple(ids), fetch=True) or []
                nut_map = {r['recipe_id']: r['calories'] for r in nut_rows}
            else:
                nut_map = {}
            
            for recipe in recipes:
                recipe['ingredients'] = ing_map.get(recipe['id'], [])
                recipe['tags'] = tag_map.get(recipe['id'], [])
                if not needs_nutrition_join:
                    recipe['calories'] = nut_map.get(recipe['id'])
                recipe['avg_rating'] = 0
                recipe['rating_count'] = 0
        
        # ---- Step 3: total count (lightweight) ----
        if needs_nutrition_join:
            count_query = f"""
                SELECT COUNT(DISTINCT r.id) as total
                FROM recipes r LEFT JOIN nutrition n ON r.id = n.recipe_id
                WHERE 1=1{where_clause}
            """
            count_params = tuple(params[:-2]) if where_conditions else ()
        else:
            count_query = f"""
                SELECT COUNT(*) as total FROM recipes r WHERE 1=1{where_clause}
            """
            count_params = tuple(params[:-2]) if where_conditions else ()
        
        total = db.execute_query(count_query, count_params, fetch=True)[0]['total']
        
        return jsonify({
            'recipes': recipes,
            'total': total,
            'page': page,
            'limit': limit,
            'has_more': (page * limit) < total
        })
        
    except Exception as e:
        logger.error(f"Browse recipes error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to browse recipes', 'code': 'INTERNAL_ERROR'}), 500



# ============================================================================
# USER REPORTS
# ============================================================================

@app.route('/api/user/<username>/report', methods=['POST'])
@jwt_required()
@limiter.limit("10 per hour")
def report_user(username):
    """Report a user. Body: { reason, description }"""
    try:
        reporter = auth_manager.get_user_by_username(get_jwt_identity())
        target = auth_manager.get_user_by_username(username)
        if not target:
            return jsonify({'error': 'User not found'}), 404
        if reporter['id'] == target['id']:
            return jsonify({'error': 'You cannot report yourself'}), 400

        data = request.get_json(silent=True) or {}
        reason = data.get('reason', '').strip()
        description = data.get('description', '').strip()

        valid_reasons = ['spam', 'harassment', 'inappropriate_content', 'fake_account', 'other']
        if reason not in valid_reasons:
            return jsonify({'error': f'Invalid reason. Must be one of: {", ".join(valid_reasons)}'}), 400
        if len(description) > 1000:
            return jsonify({'error': 'Description too long (max 1000 characters)'}), 400

        # Prevent duplicate reports (same reporter + target with pending status)
        existing = db.execute_query(
            "SELECT id FROM user_reports WHERE reporter_id = %s AND reported_user_id = %s AND status = 'pending'",
            (reporter['id'], target['id']), fetch=True
        )
        if existing:
            return jsonify({'error': 'You already have a pending report for this user'}), 409

        db.execute_query(
            "INSERT INTO user_reports (reporter_id, reported_user_id, reason, description) VALUES (%s, %s, %s, %s)",
            (reporter['id'], target['id'], reason, description), fetch=False
        )
        logger.info(f"User {reporter['username']} reported {username} for {reason}")
        return jsonify({'message': 'Report submitted successfully. An admin will review it.'}), 201
    except Exception as e:
        logger.error(f"Report user error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to submit report'}), 500


@app.route('/api/admin/reports', methods=['GET'])
@admin_required
def admin_list_reports():
    """List all user reports with filters."""
    try:
        page = max(1, request.args.get('page', 1, type=int))
        per_page = min(50, max(1, request.args.get('per_page', 15, type=int)))
        status_filter = request.args.get('status', '').strip()
        offset = (page - 1) * per_page

        where_clauses = []
        params = []
        if status_filter in ('pending', 'reviewed', 'resolved', 'dismissed'):
            where_clauses.append("r.status = %s")
            params.append(status_filter)

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        count_rows = db.execute_query(
            f"SELECT COUNT(*) as total FROM user_reports r {where_sql}",
            tuple(params), fetch=True
        )
        total = count_rows[0]['total'] if count_rows else 0

        rows = db.execute_query(f"""
            SELECT r.id, r.reason, r.description, r.status, r.admin_notes,
                   r.created_at, r.resolved_at,
                   reporter.username as reporter_username,
                   reporter.profile_pic as reporter_pic,
                   reported.username as reported_username,
                   reported.id as reported_user_id,
                   reported.profile_pic as reported_pic,
                   reported.role as reported_role,
                   reported.suspended_until as reported_suspended_until,
                   resolver.username as resolved_by_username
            FROM user_reports r
            JOIN users reporter ON r.reporter_id = reporter.id
            JOIN users reported ON r.reported_user_id = reported.id
            LEFT JOIN users resolver ON r.resolved_by = resolver.id
            {where_sql}
            ORDER BY
              CASE r.status WHEN 'pending' THEN 0 WHEN 'reviewed' THEN 1 ELSE 2 END,
              r.created_at DESC
            LIMIT %s OFFSET %s
        """, tuple(params) + (per_page, offset), fetch=True) or []

        # Serialize datetimes
        for row in rows:
            for k in ('created_at', 'resolved_at', 'reported_suspended_until'):
                if row.get(k) and hasattr(row[k], 'isoformat'):
                    row[k] = row[k].isoformat()

        return jsonify({
            'reports': rows,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        })
    except Exception as e:
        logger.error(f"Admin list reports error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to list reports'}), 500


@app.route('/api/admin/reports/<int:report_id>/resolve', methods=['PUT'])
@admin_required
def admin_resolve_report(report_id):
    """Resolve or dismiss a report. Body: { action: 'resolve'|'dismiss', admin_notes? }"""
    try:
        data = request.get_json(silent=True) or {}
        action = data.get('action', '').strip()
        admin_notes = data.get('admin_notes', '').strip()

        if action not in ('resolve', 'dismiss'):
            return jsonify({'error': 'action must be resolve or dismiss'}), 400

        report = db.execute_query(
            "SELECT id, status FROM user_reports WHERE id = %s", (report_id,), fetch=True
        )
        if not report:
            return jsonify({'error': 'Report not found'}), 404

        me = auth_manager.get_user_by_username(get_jwt_identity())
        new_status = 'resolved' if action == 'resolve' else 'dismissed'

        db.execute_query(
            "UPDATE user_reports SET status = %s, admin_notes = %s, resolved_by = %s, resolved_at = NOW() WHERE id = %s",
            (new_status, admin_notes, me['id'], report_id), fetch=False
        )
        logger.info(f"Admin {me['username']} {new_status} report #{report_id}")
        return jsonify({'success': True, 'status': new_status})
    except Exception as e:
        logger.error(f"Admin resolve report error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to resolve report'}), 500


@app.route('/api/admin/users/<int:user_id>/suspend', methods=['PUT'])
@admin_required
def admin_suspend_user(user_id):
    """Temporarily suspend a user. Body: { duration: '1_day'|'3_days'|'1_week'|'2_weeks'|'lift' }"""
    try:
        from datetime import datetime, timedelta, timezone

        data = request.get_json(silent=True) or {}
        duration = data.get('duration', '')

        duration_map = {
            '1_day': timedelta(days=1),
            '3_days': timedelta(days=3),
            '1_week': timedelta(weeks=1),
            '2_weeks': timedelta(weeks=2),
        }

        me = auth_manager.get_user_by_username(get_jwt_identity())
        if me and me['id'] == user_id:
            return jsonify({'error': "You can't suspend yourself"}), 400

        target = auth_manager.get_user_by_id(user_id)
        if not target:
            return jsonify({'error': 'User not found'}), 404
        if target.get('role') == 'admin':
            return jsonify({'error': 'Cannot suspend an admin'}), 400

        if duration == 'lift':
            db.execute_query(
                "UPDATE users SET suspended_until = NULL WHERE id = %s",
                (user_id,), fetch=False
            )
            logger.info(f"Admin {me['username']} lifted suspension for {target['username']}")
            return jsonify({'success': True, 'message': f"Suspension lifted for {target['username']}", 'suspended_until': None})

        if duration not in duration_map:
            return jsonify({'error': f'Invalid duration. Must be one of: {", ".join(list(duration_map.keys()) + ["lift"])}'}), 400

        until = datetime.now(timezone.utc) + duration_map[duration]
        db.execute_query(
            "UPDATE users SET suspended_until = %s WHERE id = %s",
            (until, user_id), fetch=False
        )
        logger.info(f"Admin {me['username']} suspended {target['username']} until {until}")
        return jsonify({
            'success': True,
            'message': f"{target['username']} suspended until {until.strftime('%b %d, %Y %H:%M UTC')}",
            'suspended_until': until.isoformat()
        })
    except Exception as e:
        logger.error(f"Admin suspend user error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to suspend user'}), 500


@app.route('/api/favorites/ids', methods=['GET'])
@jwt_required()
@limiter.limit("60 per minute")
def get_favorite_ids():
    """Get just the recipe IDs of user's favorites (lightweight)"""
    try:
        username = get_jwt_identity()
        user = auth_manager.get_user_by_username(username)
        recipe_ids = auth_manager.get_user_favorites(user['id'])
        return jsonify({'favorite_ids': recipe_ids})
    except Exception as e:
        logger.error(f"Favorite IDs fetch error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch favorites', 'code': 'INTERNAL_ERROR'}), 500


@app.route('/api/favorites/sync', methods=['POST'])
@jwt_required()
@limiter.limit("10 per minute")
def sync_favorites():
    """Merge a list of recipe IDs into the user's favorites (used on login migration)"""
    try:
        username = get_jwt_identity()
        user = auth_manager.get_user_by_username(username)
        data = request.get_json() or {}
        recipe_ids = data.get('recipe_ids', [])

        if not isinstance(recipe_ids, list):
            return jsonify({'error': 'recipe_ids must be a list'}), 400

        added = 0
        for rid in recipe_ids:
            if isinstance(rid, int) and rid > 0:
                if auth_manager.save_user_favorite(user['id'], rid):
                    added += 1

        # Return the full updated list
        all_ids = auth_manager.get_user_favorites(user['id'])
        return jsonify({'message': f'Synced {added} favorites', 'favorite_ids': all_ids})
    except Exception as e:
        logger.error(f"Favorite sync error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to sync favorites', 'code': 'INTERNAL_ERROR'}), 500


@app.route('/api/favorites/<int:recipe_id>', methods=['POST'])
@jwt_required()
@limiter.limit("30 per minute")
def add_favorite(recipe_id):
    """Add recipe to favorites"""
    try:
        username = get_jwt_identity()
        user = auth_manager.get_user_by_username(username)
        success = auth_manager.save_user_favorite(user['id'], recipe_id)
        
        if success:
            return jsonify({'message': 'Added to favorites'})
        else:
            return jsonify({'error': 'Failed to add favorite', 'code': 'OPERATION_FAILED'}), 500
            
    except Exception as e:
        logger.error(f"Add favorite error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to add favorite', 'code': 'INTERNAL_ERROR'}), 500


@app.route('/api/favorites/<int:recipe_id>', methods=['DELETE'])
@jwt_required()
@limiter.limit("30 per minute")
def remove_favorite(recipe_id):
    """Remove recipe from favorites"""
    try:
        username = get_jwt_identity()
        user = auth_manager.get_user_by_username(username)
        success = auth_manager.remove_user_favorite(user['id'], recipe_id)
        
        if success:
            return jsonify({'message': 'Removed from favorites'})
        else:
            return jsonify({'error': 'Failed to remove favorite', 'code': 'OPERATION_FAILED'}), 500
            
    except Exception as e:
        logger.error(f"Remove favorite error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to remove favorite', 'code': 'INTERNAL_ERROR'}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    
    logger.info(f"Starting Smart Recipe Recommender API v3.0 on port {port}")
    
    # Test database connection with extended retries for slow MySQL startup
    max_startup_retries = 5
    for startup_attempt in range(max_startup_retries):
        try:
            db.connect()
            logger.info("Database connected successfully")
            db.disconnect()
            break
        except Exception as e:
            if startup_attempt < max_startup_retries - 1:
                wait = 2 * (startup_attempt + 1)
                logger.warning(f"DB connection attempt {startup_attempt + 1}/{max_startup_retries} failed, retrying in {wait}s... ({e})")
                import time
                time.sleep(wait)
            else:
                logger.critical(f"Database connection failed after {max_startup_retries} attempts: {e}", exc_info=True)
                import sys
                sys.exit(1)
    
    # Start ML initialization
    try:
        thread = threading.Thread(target=init_recommender_async, daemon=True)
        thread.start()
    except Exception as e:
        logger.error(f"ML initialization failed to start: {e}")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False, threaded=True)
    except Exception as e:
        logger.critical(f"Failed to start server: {e}", exc_info=True)
    finally:
        logger.info("Server stopped")
