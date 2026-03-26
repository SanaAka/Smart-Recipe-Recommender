"""
Comprehensive Software Testing for Smart Recipe Recommender API (app_v2)
Tests all 41+ endpoints with mocked database/auth dependencies.
Covers: happy paths, error handling, validation, auth, admin, edge cases.
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from datetime import datetime, timedelta, timezone
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Patch environment before importing app
os.environ.setdefault('DB_PASSWORD', 'test')
os.environ.setdefault('RATE_LIMIT_ENABLED', 'False')  # Disable rate limiting for tests

from app_v2 import app, db, auth_manager, ml_status
from schemas import (
    RecommendationRequest, SearchRequest, BatchRecipeRequest,
    UserRegistration, UserLogin
)
from pydantic import ValidationError


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def disable_rate_limits():
    """Disable rate limiting globally for tests"""
    app.config['RATELIMIT_ENABLED'] = False
    yield


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    app.config['JWT_SECRET_KEY'] = 'test-secret-key-that-is-at-least-32-bytes-long!'
    with app.test_client() as c:
        yield c


@pytest.fixture
def mock_user():
    """Standard test user dict"""
    return {
        'id': 1,
        'username': 'testuser',
        'email': 'test@example.com',
        'role': 'user',
        'profile_pic': None,
        'bio': None,
        'suspended_until': None,
    }


@pytest.fixture
def mock_admin_user():
    """Admin test user dict"""
    return {
        'id': 99,
        'username': 'adminuser',
        'email': 'admin@example.com',
        'role': 'admin',
        'profile_pic': None,
        'bio': None,
        'suspended_until': None,
    }


@pytest.fixture
def auth_headers(client, mock_user):
    """Generate JWT auth headers by mocking login"""
    with patch.object(auth_manager, 'authenticate_user', return_value=mock_user):
        resp = client.post('/api/auth/login',
                           json={'username': 'testuser', 'password': 'TestPass123'})
        token = resp.json.get('access_token')
        return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def admin_headers(client, mock_admin_user):
    """Generate JWT auth headers for an admin user"""
    with patch.object(auth_manager, 'authenticate_user', return_value=mock_admin_user):
        resp = client.post('/api/auth/login',
                           json={'username': 'adminuser', 'password': 'AdminPass123'})
        token = resp.json.get('access_token')
        return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def sample_recipe():
    """Standard recipe dict returned by DB"""
    return {
        'id': 1,
        'name': 'Pasta Carbonara',
        'minutes': 30,
        'description': 'Classic Italian pasta',
        'image_url': 'https://images.unsplash.com/photo-test',
        'ingredients': ['pasta', 'eggs', 'bacon', 'parmesan'],
        'tags': ['italian', 'quick'],
        'steps': ['Boil pasta', 'Cook bacon', 'Mix'],
    }


# ============================================================================
# 1. HEALTH & INFO ENDPOINTS
# ============================================================================

class TestRootAndHealth:
    def test_root_endpoint(self, client):
        resp = client.get('/')
        assert resp.status_code == 200
        data = resp.json
        assert data['name'] == 'Smart Recipe Recommender API'
        assert data['version'] == '2.0.0'
        assert data['status'] == 'running'
        assert 'endpoints' in data

    def test_health_check(self, client):
        resp = client.get('/api/health')
        assert resp.status_code == 200
        data = resp.json
        assert data['status'] == 'healthy'
        assert 'ml_ready' in data
        assert 'ml_loading' in data
        assert 'database' in data

    def test_root_has_all_endpoint_categories(self, client):
        resp = client.get('/')
        endpoints = resp.json['endpoints']
        assert 'health' in endpoints
        assert 'auth' in endpoints
        assert 'recipes' in endpoints
        assert 'favorites' in endpoints


# ============================================================================
# 2. SCHEMA / VALIDATION TESTS
# ============================================================================

class TestSchemaValidation:
    # -- RecommendationRequest --
    def test_recommendation_valid(self):
        req = RecommendationRequest(ingredients=['chicken', 'rice'])
        assert len(req.ingredients) == 2
        assert req.limit == 12  # default

    def test_recommendation_empty_ingredients_rejected(self):
        with pytest.raises(ValidationError):
            RecommendationRequest(ingredients=[])

    def test_recommendation_whitespace_only_ingredients_rejected(self):
        with pytest.raises(ValidationError):
            RecommendationRequest(ingredients=['', '  '])

    def test_recommendation_sanitizes_dietary(self):
        req = RecommendationRequest(
            ingredients=['chicken'],
            dietary_preference='vegan<script>alert("xss")</script>'
        )
        assert '<' not in req.dietary_preference
        assert '(' not in req.dietary_preference
        assert '"' not in req.dietary_preference

    def test_recommendation_limit_clamped(self):
        req = RecommendationRequest(ingredients=['a'], limit=50)
        assert req.limit == 50
        with pytest.raises(ValidationError):
            RecommendationRequest(ingredients=['a'], limit=51)

    # -- SearchRequest --
    def test_search_valid(self):
        req = SearchRequest(query='pasta', search_type='name')
        assert req.query == 'pasta'

    def test_search_empty_query_rejected(self):
        with pytest.raises(ValidationError):
            SearchRequest(query='', search_type='name')

    def test_search_zero_max_time_becomes_none(self):
        req = SearchRequest(query='pasta', max_time=0)
        assert req.max_time is None

    # -- BatchRecipeRequest --
    def test_batch_valid(self):
        req = BatchRecipeRequest(recipe_ids=[1, 2, 3])
        assert len(req.recipe_ids) == 3

    def test_batch_empty_rejected(self):
        with pytest.raises(ValidationError):
            BatchRecipeRequest(recipe_ids=[])

    def test_batch_negative_id_rejected(self):
        with pytest.raises(ValidationError):
            BatchRecipeRequest(recipe_ids=[-1, 2])

    def test_batch_deduplicates_ids(self):
        req = BatchRecipeRequest(recipe_ids=[1, 1, 2])
        assert len(req.recipe_ids) == 2

    # -- UserRegistration --
    def test_registration_valid(self):
        req = UserRegistration(
            username='testuser', email='test@example.com', password='StrongPass1'
        )
        assert req.username == 'testuser'

    def test_registration_weak_password(self):
        with pytest.raises(ValidationError) as exc_info:
            UserRegistration(username='testuser', email='t@e.com', password='weak')
        assert 'at least 8 characters' in str(exc_info.value).lower()

    def test_registration_no_uppercase(self):
        with pytest.raises(ValidationError):
            UserRegistration(username='testuser', email='t@e.com', password='nouppercase1')

    def test_registration_no_digit(self):
        with pytest.raises(ValidationError):
            UserRegistration(username='testuser', email='t@e.com', password='NoDigitHere')

    def test_registration_invalid_email(self):
        with pytest.raises(ValidationError):
            UserRegistration(username='testuser', email='not-an-email', password='StrongPass1')

    def test_registration_short_username(self):
        with pytest.raises(ValidationError):
            UserRegistration(username='ab', email='t@e.com', password='StrongPass1')

    def test_registration_special_chars_in_username(self):
        with pytest.raises(ValidationError):
            UserRegistration(username='user@name!', email='t@e.com', password='StrongPass1')

    # -- UserLogin --
    def test_login_valid(self):
        req = UserLogin(username='testuser', password='TestPass123')
        assert req.username == 'testuser'

    def test_login_empty_password(self):
        with pytest.raises(ValidationError):
            UserLogin(username='testuser', password='')


# ============================================================================
# 3. AUTHENTICATION ENDPOINTS
# ============================================================================

class TestAuthRegister:
    def test_register_success(self, client):
        with patch.object(auth_manager, 'register_user') as mock_reg, \
             patch.object(auth_manager, 'generate_tokens') as mock_tok:
            mock_reg.return_value = {'user_id': 1, 'username': 'newuser', 'email': 'n@e.com'}
            mock_tok.return_value = {
                'access_token': 'tok', 'refresh_token': 'ref', 'expires_in': 3600
            }
            resp = client.post('/api/auth/register', json={
                'username': 'newuser', 'email': 'n@e.com', 'password': 'StrongPass1'
            })
            assert resp.status_code == 201
            assert resp.json['message'] == 'User registered successfully'
            assert 'access_token' in resp.json

    def test_register_duplicate_username(self, client):
        with patch.object(auth_manager, 'register_user',
                          side_effect=ValueError('Username already exists')):
            resp = client.post('/api/auth/register', json={
                'username': 'existing', 'email': 'n@e.com', 'password': 'StrongPass1'
            })
            assert resp.status_code == 400
            assert 'already exists' in resp.json['error']

    def test_register_weak_password(self, client):
        resp = client.post('/api/auth/register', json={
            'username': 'newuser', 'email': 'n@e.com', 'password': 'weak'
        })
        assert resp.status_code == 400

    def test_register_invalid_email(self, client):
        resp = client.post('/api/auth/register', json={
            'username': 'newuser', 'email': 'bad', 'password': 'StrongPass1'
        })
        assert resp.status_code == 400

    def test_register_missing_fields(self, client):
        resp = client.post('/api/auth/register', json={'username': 'u'})
        assert resp.status_code in (400, 422)


class TestAuthLogin:
    def test_login_success(self, client, mock_user):
        with patch.object(auth_manager, 'authenticate_user', return_value=mock_user):
            resp = client.post('/api/auth/login',
                               json={'username': 'testuser', 'password': 'TestPass123'})
            assert resp.status_code == 200
            assert resp.json['message'] == 'Login successful'
            assert 'access_token' in resp.json
            assert resp.json['user']['username'] == 'testuser'

    def test_login_invalid_credentials(self, client):
        with patch.object(auth_manager, 'authenticate_user', return_value=None):
            resp = client.post('/api/auth/login',
                               json={'username': 'wrong', 'password': 'WrongPass1'})
            assert resp.status_code == 401

    def test_login_banned_user(self, client):
        banned_user = {
            'id': 2, 'username': 'banneduser', 'email': 'b@e.com',
            'role': 'banned', 'suspended_until': None
        }
        with patch.object(auth_manager, 'authenticate_user', return_value=banned_user):
            resp = client.post('/api/auth/login',
                               json={'username': 'banneduser', 'password': 'TestPass123'})
            assert resp.status_code == 403
            assert 'banned' in resp.json['error'].lower()

    def test_login_suspended_user(self, client):
        future = datetime.now(timezone.utc) + timedelta(days=1)
        suspended = {
            'id': 3, 'username': 'suspuser', 'email': 's@e.com',
            'role': 'user', 'suspended_until': future
        }
        with patch.object(auth_manager, 'authenticate_user', return_value=suspended):
            resp = client.post('/api/auth/login',
                               json={'username': 'suspuser', 'password': 'TestPass123'})
            assert resp.status_code == 403
            assert 'suspended' in resp.json['error'].lower()

    def test_login_missing_body(self, client):
        resp = client.post('/api/auth/login', json={})
        assert resp.status_code in (400, 422)


class TestAuthProfile:
    def test_get_profile_success(self, client, auth_headers, mock_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_user):
            resp = client.get('/api/auth/profile', headers=auth_headers)
            assert resp.status_code == 200
            assert resp.json['user']['username'] == 'testuser'

    def test_get_profile_no_token(self, client):
        resp = client.get('/api/auth/profile')
        assert resp.status_code == 401

    def test_get_profile_banned_user(self, client, auth_headers):
        banned = {
            'id': 1, 'username': 'testuser', 'email': 't@e.com',
            'role': 'banned', 'suspended_until': None
        }
        with patch.object(auth_manager, 'get_user_by_username', return_value=banned):
            resp = client.get('/api/auth/profile', headers=auth_headers)
            assert resp.status_code == 403


# ============================================================================
# 4. RECIPE ENDPOINTS
# ============================================================================

class TestRecommendations:
    def test_recommend_success(self, client, sample_recipe):
        mock_rec = Mock()
        mock_rec.recommend.return_value = [sample_recipe]
        with patch('app_v2.get_recommender', return_value=mock_rec):
            resp = client.post('/api/recommend',
                               json={'ingredients': ['pasta', 'eggs']})
            assert resp.status_code == 200
            assert resp.json['loading'] is False
            assert len(resp.json['recommendations']) >= 1

    def test_recommend_ml_loading(self, client):
        with patch('app_v2.get_recommender', return_value=None):
            resp = client.post('/api/recommend',
                               json={'ingredients': ['pasta']})
            assert resp.status_code == 202
            assert resp.json['loading'] is True

    def test_recommend_missing_ingredients(self, client):
        resp = client.post('/api/recommend', json={'ingredients': []})
        assert resp.status_code == 400

    def test_recommend_no_body(self, client):
        resp = client.post('/api/recommend',
                           data='not json',
                           content_type='text/plain')
        assert resp.status_code in (400, 422, 500)


class TestSearch:
    def test_search_by_name(self, client):
        with patch.object(db, 'search_recipes', return_value=[
            {'id': 1, 'name': 'Pasta Carbonara'}
        ]):
            resp = client.get('/api/search?query=pasta&type=name')
            assert resp.status_code == 200
            assert len(resp.json['results']) == 1

    def test_search_by_ingredient(self, client):
        with patch.object(db, 'search_recipes', return_value=[]):
            resp = client.get('/api/search?query=chicken&type=ingredient')
            assert resp.status_code == 200
            assert 'results' in resp.json

    def test_search_by_cuisine(self, client):
        with patch.object(db, 'search_recipes', return_value=[]):
            resp = client.get('/api/search?query=italian&type=cuisine')
            assert resp.status_code == 200

    def test_search_empty_query(self, client):
        resp = client.get('/api/search?query=&type=name')
        assert resp.status_code == 400

    def test_search_missing_query(self, client):
        resp = client.get('/api/search?type=name')
        assert resp.status_code == 400

    def test_search_with_filters(self, client):
        with patch.object(db, 'search_recipes', return_value=[]):
            resp = client.get('/api/search?query=soup&type=name&max_time=30&max_calories=500')
            assert resp.status_code == 200


class TestRecipeDetail:
    def test_get_recipe_success(self, client, sample_recipe):
        with patch.object(db, 'get_recipe_by_id', return_value=sample_recipe):
            resp = client.get('/api/recipe/1')
            assert resp.status_code == 200
            assert resp.json['name'] == 'Pasta Carbonara'

    def test_get_recipe_not_found(self, client):
        with patch.object(db, 'get_recipe_by_id', return_value=None):
            resp = client.get('/api/recipe/99999')
            assert resp.status_code == 404

    def test_get_recipe_invalid_id(self, client):
        resp = client.get('/api/recipe/abc')
        assert resp.status_code == 404  # Flask returns 404 for invalid int


class TestBatchRecipes:
    def test_batch_success(self, client):
        with patch.object(db, 'get_recipes_by_ids', return_value=[
            {'id': 1, 'name': 'R1'}, {'id': 2, 'name': 'R2'}
        ]):
            resp = client.post('/api/recipes/batch', json={'recipe_ids': [1, 2]})
            assert resp.status_code == 200
            assert len(resp.json['recipes']) == 2

    def test_batch_with_ids_alias(self, client):
        with patch.object(db, 'get_recipes_by_ids', return_value=[]):
            resp = client.post('/api/recipes/batch', json={'ids': [1]})
            assert resp.status_code == 200

    def test_batch_empty_ids(self, client):
        resp = client.post('/api/recipes/batch', json={'recipe_ids': []})
        assert resp.status_code == 400


class TestListAndBrowse:
    def test_list_recipes(self, client):
        with patch.object(db, 'execute_query') as mock_q:
            mock_q.side_effect = [
                [{'id': 1, 'name': 'R1', 'minutes': 10, 'image_url': None}],
                [{'min_id': 1, 'max_id': 100}],
            ]
            resp = client.get('/api/recipes?limit=10&offset=0')
            assert resp.status_code == 200
            assert 'recipes' in resp.json

    def test_list_recipes_pagination(self, client):
        with patch.object(db, 'execute_query') as mock_q:
            mock_q.side_effect = [
                [{'id': 1, 'name': 'R1', 'minutes': 10, 'image_url': None}],
                [{'min_id': 1, 'max_id': 1000}],
            ]
            resp = client.get('/api/recipes?page=2&per_page=5')
            assert resp.status_code == 200
            assert resp.json['page'] == 2

    def test_browse_recipes(self, client):
        with patch.object(db, 'execute_query') as mock_q:
            mock_q.side_effect = [
                [{'id': 1, 'name': 'R1', 'minutes': 10, 'image_url': None}],
                [],  # ingredients
                [],  # tags
                [],  # nutrition
                [{'total': 100}],
            ]
            resp = client.get('/api/recipes/browse?page=1&limit=10')
            assert resp.status_code == 200
            assert 'recipes' in resp.json
            assert 'total' in resp.json

    def test_random_recipes(self, client):
        with patch.object(db, 'execute_query') as mock_q:
            mock_q.side_effect = [
                [{'min_id': 1, 'max_id': 1000}],
                [{'id': 42, 'name': 'Random', 'minutes': 15, 'image_url': None}],
            ]
            resp = client.get('/api/recipes/random?count=5')
            assert resp.status_code == 200
            assert 'recipes' in resp.json


class TestRecipeOfTheDay:
    def test_recipe_of_the_day(self, client):
        with patch.object(db, 'execute_query') as mock_q:
            mock_q.side_effect = [
                [{'min_id': 1, 'max_id': 1000}],
                [{'id': 42, 'name': 'Daily', 'minutes': 20, 'description': 'yum', 'image_url': None}],
                [{'calories': 350}],
                [{'name': 'italian'}],
                [{'avg_rating': 4.5, 'rating_count': 10}],
            ]
            resp = client.get('/api/recipe-of-the-day')
            assert resp.status_code == 200
            assert 'recipe' in resp.json
            assert 'date' in resp.json


class TestStats:
    def test_stats_endpoint(self, client):
        with patch.object(db, 'execute_query') as mock_q:
            mock_q.return_value = [{
                'total_recipes': 100, 'total_users': 10,
                'total_ratings': 50, 'total_comments': 20,
                'total_tags': 30, 'total_ingredients': 200,
            }]
            resp = client.get('/api/stats')
            assert resp.status_code == 200
            assert 'total_recipes' in resp.json


# ============================================================================
# 5. FAVORITES ENDPOINTS
# ============================================================================

class TestFavorites:
    def test_get_favorites(self, client, auth_headers, mock_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_user), \
             patch.object(auth_manager, 'get_user_favorites', return_value=[1, 2]), \
             patch.object(db, 'get_recipes_by_ids', return_value=[
                 {'id': 1, 'name': 'R1'}, {'id': 2, 'name': 'R2'}
             ]):
            resp = client.get('/api/favorites', headers=auth_headers)
            assert resp.status_code == 200
            assert len(resp.json['favorites']) == 2

    def test_get_favorites_empty(self, client, auth_headers, mock_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_user), \
             patch.object(auth_manager, 'get_user_favorites', return_value=[]):
            resp = client.get('/api/favorites', headers=auth_headers)
            assert resp.status_code == 200
            assert resp.json['favorites'] == []

    def test_get_favorites_no_auth(self, client):
        resp = client.get('/api/favorites')
        assert resp.status_code == 401

    def test_add_favorite(self, client, auth_headers, mock_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_user), \
             patch.object(auth_manager, 'save_user_favorite', return_value=True):
            resp = client.post('/api/favorites/1', headers=auth_headers)
            assert resp.status_code == 200
            assert 'Added' in resp.json['message']

    def test_remove_favorite(self, client, auth_headers, mock_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_user), \
             patch.object(auth_manager, 'remove_user_favorite', return_value=True):
            resp = client.delete('/api/favorites/1', headers=auth_headers)
            assert resp.status_code == 200

    def test_get_favorite_ids(self, client, auth_headers, mock_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_user), \
             patch.object(auth_manager, 'get_user_favorites', return_value=[1, 2, 3]):
            resp = client.get('/api/favorites/ids', headers=auth_headers)
            assert resp.status_code == 200
            assert resp.json['favorite_ids'] == [1, 2, 3]

    def test_sync_favorites(self, client, auth_headers, mock_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_user), \
             patch.object(auth_manager, 'save_user_favorite', return_value=True), \
             patch.object(auth_manager, 'get_user_favorites', return_value=[1, 2]):
            resp = client.post('/api/favorites/sync',
                               headers=auth_headers,
                               json={'recipe_ids': [1, 2]})
            assert resp.status_code == 200
            assert 'favorite_ids' in resp.json


# ============================================================================
# 6. RATINGS ENDPOINTS
# ============================================================================

class TestRatings:
    def test_rate_recipe(self, client, auth_headers, mock_user, sample_recipe):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_user), \
             patch.object(db, 'get_recipe_by_id', return_value=sample_recipe), \
             patch.object(db, 'execute_query') as mock_q:
            mock_q.side_effect = [
                None,  # INSERT rating
                [{'avg_rating': 4.0, 'rating_count': 5}],  # AVG query
            ]
            resp = client.post('/api/recipe/1/rating',
                               headers=auth_headers,
                               json={'rating': 4})
            assert resp.status_code == 200
            assert resp.json['success'] is True
            assert resp.json['rating'] == 4

    def test_rate_recipe_invalid_value(self, client, auth_headers, mock_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_user):
            resp = client.post('/api/recipe/1/rating',
                               headers=auth_headers,
                               json={'rating': 6})
            assert resp.status_code == 400

    def test_rate_recipe_zero(self, client, auth_headers, mock_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_user):
            resp = client.post('/api/recipe/1/rating',
                               headers=auth_headers,
                               json={'rating': 0})
            assert resp.status_code == 400

    def test_rate_nonexistent_recipe(self, client, auth_headers, mock_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_user), \
             patch.object(db, 'get_recipe_by_id', return_value=None):
            resp = client.post('/api/recipe/99999/rating',
                               headers=auth_headers,
                               json={'rating': 3})
            assert resp.status_code == 404

    def test_rate_recipe_no_auth(self, client):
        resp = client.post('/api/recipe/1/rating', json={'rating': 3})
        assert resp.status_code == 401

    def test_delete_rating(self, client, auth_headers, mock_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_user), \
             patch.object(db, 'execute_query') as mock_q:
            mock_q.side_effect = [
                None,  # DELETE
                [{'avg_rating': 3.5, 'rating_count': 4}],
            ]
            resp = client.delete('/api/recipe/1/rating', headers=auth_headers)
            assert resp.status_code == 200
            assert resp.json['success'] is True

    def test_get_rating_stats(self, client):
        with patch.object(db, 'execute_query', return_value=[
            {'avg_rating': 4.2, 'rating_count': 10}
        ]):
            resp = client.get('/api/recipe/1/rating')
            assert resp.status_code == 200
            assert 'avg_rating' in resp.json
            assert 'rating_count' in resp.json


# ============================================================================
# 7. COMMENTS ENDPOINTS
# ============================================================================

class TestComments:
    def test_get_comments(self, client):
        with patch.object(db, 'execute_query') as mock_q:
            mock_q.side_effect = [
                [{'id': 1, 'comment': 'Great!', 'created_at': '2026-01-01',
                  'updated_at': None, 'username': 'alice', 'user_id': 1,
                  'profile_pic': None}],
                [{'total': 1}],
                [],  # reactions
                [],  # replies
            ]
            resp = client.get('/api/recipe/1/comments?page=1&limit=10')
            assert resp.status_code == 200
            assert 'comments' in resp.json
            assert resp.json['total'] == 1

    def test_add_comment(self, client, auth_headers, mock_user, sample_recipe):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_user), \
             patch.object(db, 'get_recipe_by_id', return_value=sample_recipe), \
             patch.object(db, 'execute_query') as mock_q:
            mock_q.side_effect = [
                None,  # INSERT
                [{'id': 10, 'comment': 'Nice recipe!', 'created_at': '2026-01-01',
                  'updated_at': None, 'username': 'testuser', 'user_id': 1}],
            ]
            resp = client.post('/api/recipe/1/comments',
                               headers=auth_headers,
                               json={'comment': 'Nice recipe!'})
            assert resp.status_code == 201
            assert resp.json['success'] is True

    def test_add_comment_too_short(self, client, auth_headers, mock_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_user):
            resp = client.post('/api/recipe/1/comments',
                               headers=auth_headers,
                               json={'comment': 'hi'})
            assert resp.status_code == 400

    def test_add_comment_too_long(self, client, auth_headers, mock_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_user):
            resp = client.post('/api/recipe/1/comments',
                               headers=auth_headers,
                               json={'comment': 'x' * 1001})
            assert resp.status_code == 400

    def test_add_comment_no_auth(self, client):
        resp = client.post('/api/recipe/1/comments', json={'comment': 'Hello'})
        assert resp.status_code == 401

    def test_delete_own_comment(self, client, auth_headers, mock_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_user), \
             patch.object(db, 'execute_query') as mock_q:
            mock_q.side_effect = [
                [{'user_id': 1}],  # CHECK owner
                None,  # DELETE
            ]
            resp = client.delete('/api/recipe/1/comments/10', headers=auth_headers)
            assert resp.status_code == 200

    def test_delete_others_comment_forbidden(self, client, auth_headers, mock_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_user), \
             patch.object(db, 'execute_query', return_value=[{'user_id': 999}]):
            resp = client.delete('/api/recipe/1/comments/10', headers=auth_headers)
            assert resp.status_code == 403

    def test_delete_nonexistent_comment(self, client, auth_headers, mock_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_user), \
             patch.object(db, 'execute_query', return_value=[]):
            resp = client.delete('/api/recipe/1/comments/99999', headers=auth_headers)
            assert resp.status_code == 404


# ============================================================================
# 8. IMAGE ENDPOINTS
# ============================================================================

class TestImages:
    def test_batch_images_success(self, client, sample_recipe):
        with patch.object(db, 'get_recipe_by_id', return_value=sample_recipe):
            resp = client.post('/api/images/batch', json={'ids': [1]})
            assert resp.status_code == 200
            assert 'images' in resp.json

    def test_batch_images_no_ids(self, client):
        resp = client.post('/api/images/batch', json={})
        assert resp.status_code == 400

    def test_auto_image(self, client, sample_recipe):
        with patch.object(db, 'get_recipe_by_id', return_value=sample_recipe):
            resp = client.get('/api/recipe/1/auto-image')
            assert resp.status_code == 200

    def test_image_search(self, client, sample_recipe):
        with patch.object(db, 'get_recipe_by_id', return_value=sample_recipe):
            resp = client.get('/api/recipe/1/image/search')
            assert resp.status_code == 200
            assert 'images' in resp.json

    def test_image_search_not_found(self, client):
        with patch.object(db, 'get_recipe_by_id', return_value=None):
            resp = client.get('/api/recipe/99999/image/search')
            assert resp.status_code == 404

    def test_update_recipe_image(self, client, auth_headers, sample_recipe):
        with patch.object(db, 'get_recipe_by_id', return_value=sample_recipe), \
             patch.object(db, 'execute_query', return_value=None):
            resp = client.post('/api/recipe/1/image',
                               headers=auth_headers,
                               json={'image_url': 'https://images.unsplash.com/test'})
            assert resp.status_code == 200
            assert resp.json['success'] is True

    def test_update_image_no_url(self, client, auth_headers):
        resp = client.post('/api/recipe/1/image',
                           headers=auth_headers,
                           json={'image_url': ''})
        assert resp.status_code == 400

    def test_track_download(self, client):
        resp = client.post('/api/images/track-download', json={})
        assert resp.status_code == 400

    def test_track_download_with_location(self, client):
        with patch('app_v2._trigger_unsplash_download', return_value=True):
            resp = client.post('/api/images/track-download',
                               json={'download_location': 'https://api.unsplash.com/photos/xyz/download'})
            assert resp.status_code == 200


# ============================================================================
# 9. PERSONAL RECOMMENDATIONS
# ============================================================================

class TestPersonalRecommendations:
    def test_personal_no_auth(self, client):
        resp = client.get('/api/recommendations/personal')
        assert resp.status_code == 401

    def test_personal_no_history(self, client, auth_headers, mock_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_user), \
             patch.object(db, 'execute_query') as mock_q:
            mock_q.side_effect = [
                [],  # loved_rows — no history
                [],  # fallback query
            ]
            resp = client.get('/api/recommendations/personal', headers=auth_headers)
            assert resp.status_code == 200
            assert resp.json['strategy'] == 'top-rated'

    def test_personal_with_history(self, client, auth_headers, mock_user):
        mock_rec = Mock()
        mock_rec.recommend.return_value = [
            {'id': 5, 'name': 'Rec1', 'minutes': 20, 'image_url': None, 'tags': ['italian']}
        ]
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_user), \
             patch.object(db, 'execute_query') as mock_q, \
             patch('app_v2.get_recommender', return_value=mock_rec):
            mock_q.side_effect = [
                [{'recipe_id': 1}, {'recipe_id': 2}],  # loved_rows
                [{'name': 'italian', 'freq': 3}],  # tags
                [{'name': 'pasta', 'freq': 2}],  # ingredients
            ]
            resp = client.get('/api/recommendations/personal', headers=auth_headers)
            assert resp.status_code == 200
            assert resp.json['strategy'] == 'personalized'


# ============================================================================
# 10. USER REPORTS
# ============================================================================

class TestUserReports:
    def test_report_user(self, client, auth_headers, mock_user):
        target = dict(mock_user, id=2, username='reported_user')
        with patch.object(auth_manager, 'get_user_by_username') as mock_get:
            # First call returns reporter (current user), second returns target
            mock_get.side_effect = [mock_user, target]
            with patch.object(db, 'execute_query') as mock_q:
                mock_q.side_effect = [
                    [],  # no existing pending report
                    None,  # INSERT
                ]
                resp = client.post('/api/user/reported_user/report',
                                   headers=auth_headers,
                                   json={'reason': 'spam', 'description': 'spamming'})
                assert resp.status_code == 201

    def test_report_self(self, client, auth_headers, mock_user):
        with patch.object(auth_manager, 'get_user_by_username') as mock_get:
            mock_get.side_effect = [mock_user, mock_user]
            resp = client.post('/api/user/testuser/report',
                               headers=auth_headers,
                               json={'reason': 'spam'})
            assert resp.status_code == 400

    def test_report_invalid_reason(self, client, auth_headers, mock_user):
        target = dict(mock_user, id=2, username='other')
        with patch.object(auth_manager, 'get_user_by_username') as mock_get:
            mock_get.side_effect = [mock_user, target]
            resp = client.post('/api/user/other/report',
                               headers=auth_headers,
                               json={'reason': 'invalid_reason'})
            assert resp.status_code == 400

    def test_report_nonexistent_user(self, client, auth_headers, mock_user):
        with patch.object(auth_manager, 'get_user_by_username') as mock_get:
            mock_get.side_effect = [mock_user, None]
            resp = client.post('/api/user/noone/report',
                               headers=auth_headers,
                               json={'reason': 'spam'})
            assert resp.status_code == 404


# ============================================================================
# 11. ADMIN ENDPOINTS
# ============================================================================

class TestAdminUsers:
    def test_admin_list_users(self, client, admin_headers, mock_admin_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_admin_user), \
             patch.object(db, 'execute_query') as mock_q:
            mock_q.side_effect = [
                [{'total': 2}],
                [
                    {'id': 1, 'username': 'user1', 'email': 'u1@e.com', 'role': 'user',
                     'is_active': 1, 'created_at': datetime.now(timezone.utc),
                     'last_login': None, 'profile_pic': None, 'suspended_until': None,
                     'recipe_count': 0, 'comment_count': 0},
                ],
            ]
            resp = client.get('/api/admin/users', headers=admin_headers)
            assert resp.status_code == 200
            assert 'users' in resp.json
            assert resp.json['total'] == 2

    def test_admin_list_users_non_admin(self, client, auth_headers, mock_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_user):
            resp = client.get('/api/admin/users', headers=auth_headers)
            assert resp.status_code == 403

    def test_admin_set_role(self, client, admin_headers, mock_admin_user):
        target = {'id': 2, 'username': 'someuser', 'role': 'user'}
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_admin_user), \
             patch.object(auth_manager, 'get_user_by_id', return_value=target), \
             patch.object(db, 'execute_query', return_value=None):
            resp = client.put('/api/admin/users/2/role',
                              headers=admin_headers,
                              json={'role': 'banned'})
            assert resp.status_code == 200
            assert resp.json['role'] == 'banned'

    def test_admin_set_role_invalid(self, client, admin_headers, mock_admin_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_admin_user):
            resp = client.put('/api/admin/users/2/role',
                              headers=admin_headers,
                              json={'role': 'superuser'})
            assert resp.status_code == 400

    def test_admin_set_own_role(self, client, admin_headers, mock_admin_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_admin_user):
            resp = client.put(f'/api/admin/users/{mock_admin_user["id"]}/role',
                              headers=admin_headers,
                              json={'role': 'user'})
            assert resp.status_code == 400

    def test_admin_delete_user(self, client, admin_headers, mock_admin_user):
        target = {'id': 2, 'username': 'victim'}
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_admin_user), \
             patch.object(auth_manager, 'get_user_by_id', return_value=target), \
             patch.object(db, 'execute_query', return_value=[]):
            resp = client.delete('/api/admin/users/2', headers=admin_headers)
            assert resp.status_code == 200
            assert resp.json['success'] is True

    def test_admin_delete_self(self, client, admin_headers, mock_admin_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_admin_user):
            resp = client.delete(f'/api/admin/users/{mock_admin_user["id"]}',
                                 headers=admin_headers)
            assert resp.status_code == 400

    def test_admin_delete_nonexistent_user(self, client, admin_headers, mock_admin_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_admin_user), \
             patch.object(auth_manager, 'get_user_by_id', return_value=None):
            resp = client.delete('/api/admin/users/99999', headers=admin_headers)
            assert resp.status_code == 404


class TestAdminComments:
    def test_admin_delete_comment(self, client, admin_headers, mock_admin_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_admin_user), \
             patch.object(db, 'execute_query') as mock_q:
            mock_q.side_effect = [
                [{'id': 1}],  # comment exists
                [],  # reply_ids
                None,  # delete replies
                None,  # delete reactions
                None,  # delete comment
            ]
            resp = client.delete('/api/admin/comments/1', headers=admin_headers)
            assert resp.status_code == 200

    def test_admin_delete_nonexistent_comment(self, client, admin_headers, mock_admin_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_admin_user), \
             patch.object(db, 'execute_query', return_value=[]):
            resp = client.delete('/api/admin/comments/99999', headers=admin_headers)
            assert resp.status_code == 404


class TestAdminRecipes:
    def test_admin_delete_recipe(self, client, admin_headers, mock_admin_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_admin_user), \
             patch.object(db, 'execute_query') as mock_q:
            mock_q.side_effect = [
                [{'id': 1, 'name': 'Spam', 'submitted_by': 2}],
                *[None for _ in range(7)],  # delete related tables + recipe
            ]
            resp = client.delete('/api/admin/recipes/1', headers=admin_headers)
            assert resp.status_code == 200

    def test_admin_delete_nonexistent_recipe(self, client, admin_headers, mock_admin_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_admin_user), \
             patch.object(db, 'execute_query', return_value=[]):
            resp = client.delete('/api/admin/recipes/99999', headers=admin_headers)
            assert resp.status_code == 404


class TestAdminStats:
    def test_admin_stats(self, client, admin_headers, mock_admin_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_admin_user), \
             patch.object(db, 'execute_query') as mock_q:
            mock_q.return_value = [{'c': 42}]
            resp = client.get('/api/admin/stats', headers=admin_headers)
            assert resp.status_code == 200


class TestAdminReports:
    def test_admin_list_reports(self, client, admin_headers, mock_admin_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_admin_user), \
             patch.object(db, 'execute_query') as mock_q:
            mock_q.side_effect = [
                [{'total': 1}],
                [{
                    'id': 1, 'reason': 'spam', 'description': 'spamming',
                    'status': 'pending', 'admin_notes': None,
                    'created_at': datetime.now(timezone.utc), 'resolved_at': None,
                    'reporter_username': 'alice', 'reporter_pic': None,
                    'reported_username': 'bob', 'reported_user_id': 2,
                    'reported_pic': None, 'reported_role': 'user',
                    'reported_suspended_until': None,
                    'resolved_by_username': None,
                }],
            ]
            resp = client.get('/api/admin/reports', headers=admin_headers)
            assert resp.status_code == 200
            assert 'reports' in resp.json

    def test_admin_resolve_report(self, client, admin_headers, mock_admin_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_admin_user), \
             patch.object(db, 'execute_query') as mock_q:
            mock_q.side_effect = [
                [{'id': 1, 'status': 'pending'}],
                None,  # UPDATE
            ]
            resp = client.put('/api/admin/reports/1/resolve',
                              headers=admin_headers,
                              json={'action': 'resolve', 'admin_notes': 'done'})
            assert resp.status_code == 200
            assert resp.json['status'] == 'resolved'

    def test_admin_dismiss_report(self, client, admin_headers, mock_admin_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_admin_user), \
             patch.object(db, 'execute_query') as mock_q:
            mock_q.side_effect = [
                [{'id': 1, 'status': 'pending'}],
                None,
            ]
            resp = client.put('/api/admin/reports/1/resolve',
                              headers=admin_headers,
                              json={'action': 'dismiss'})
            assert resp.status_code == 200
            assert resp.json['status'] == 'dismissed'

    def test_admin_resolve_invalid_action(self, client, admin_headers, mock_admin_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_admin_user):
            resp = client.put('/api/admin/reports/1/resolve',
                              headers=admin_headers,
                              json={'action': 'invalidaction'})
            assert resp.status_code == 400


class TestAdminSuspend:
    def test_suspend_user(self, client, admin_headers, mock_admin_user):
        target = {'id': 2, 'username': 'baduser', 'role': 'user'}
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_admin_user), \
             patch.object(auth_manager, 'get_user_by_id', return_value=target), \
             patch.object(db, 'execute_query', return_value=None):
            resp = client.put('/api/admin/users/2/suspend',
                              headers=admin_headers,
                              json={'duration': '1_day'})
            assert resp.status_code == 200
            assert 'suspended_until' in resp.json

    def test_lift_suspension(self, client, admin_headers, mock_admin_user):
        target = {'id': 2, 'username': 'baduser', 'role': 'user'}
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_admin_user), \
             patch.object(auth_manager, 'get_user_by_id', return_value=target), \
             patch.object(db, 'execute_query', return_value=None):
            resp = client.put('/api/admin/users/2/suspend',
                              headers=admin_headers,
                              json={'duration': 'lift'})
            assert resp.status_code == 200
            assert resp.json['suspended_until'] is None

    def test_suspend_invalid_duration(self, client, admin_headers, mock_admin_user):
        target = {'id': 2, 'username': 'u', 'role': 'user'}
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_admin_user), \
             patch.object(auth_manager, 'get_user_by_id', return_value=target):
            resp = client.put('/api/admin/users/2/suspend',
                              headers=admin_headers,
                              json={'duration': '1_year'})
            assert resp.status_code == 400

    def test_suspend_self(self, client, admin_headers, mock_admin_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_admin_user):
            resp = client.put(f'/api/admin/users/{mock_admin_user["id"]}/suspend',
                              headers=admin_headers,
                              json={'duration': '1_day'})
            assert resp.status_code == 400

    def test_suspend_admin(self, client, admin_headers, mock_admin_user):
        other_admin = {'id': 50, 'username': 'admin2', 'role': 'admin'}
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_admin_user), \
             patch.object(auth_manager, 'get_user_by_id', return_value=other_admin):
            resp = client.put('/api/admin/users/50/suspend',
                              headers=admin_headers,
                              json={'duration': '1_day'})
            assert resp.status_code == 400


# ============================================================================
# 12. SECURITY HEADER TESTS
# ============================================================================

class TestSecurityHeaders:
    def test_security_headers_present(self, client):
        resp = client.get('/')
        assert resp.headers.get('X-Content-Type-Options') == 'nosniff'
        assert resp.headers.get('X-Frame-Options') == 'DENY'
        assert resp.headers.get('X-XSS-Protection') == '1; mode=block'
        assert 'Strict-Transport-Security' in resp.headers

    def test_csp_header(self, client):
        resp = client.get('/')
        csp = resp.headers.get('Content-Security-Policy', '')
        assert "default-src 'self'" in csp


# ============================================================================
# 13. ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    def test_404_nonexistent_route(self, client):
        resp = client.get('/api/nonexistent')
        assert resp.status_code == 404

    def test_method_not_allowed(self, client):
        resp = client.put('/')  # Root only supports GET
        assert resp.status_code == 405

    def test_search_db_error(self, client):
        with patch.object(db, 'search_recipes', side_effect=Exception('DB error')):
            resp = client.get('/api/search?query=test&type=name')
            assert resp.status_code == 500

    def test_recipe_detail_db_error(self, client):
        with patch.object(db, 'get_recipe_by_id', side_effect=Exception('DB error')):
            resp = client.get('/api/recipe/1')
            assert resp.status_code == 500


# ============================================================================
# 14. EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    def test_search_special_characters(self, client):
        with patch.object(db, 'search_recipes', return_value=[]):
            resp = client.get('/api/search?query=pasta%20carbonara&type=name')
            assert resp.status_code == 200

    def test_recommendation_single_ingredient(self, client):
        mock_rec = Mock()
        mock_rec.recommend.return_value = []
        with patch('app_v2.get_recommender', return_value=mock_rec):
            resp = client.post('/api/recommend',
                               json={'ingredients': ['salt']})
            assert resp.status_code == 200

    def test_batch_large_request(self, client):
        with patch.object(db, 'get_recipes_by_ids', return_value=[]):
            ids = list(range(1, 101))
            resp = client.post('/api/recipes/batch', json={'recipe_ids': ids})
            assert resp.status_code == 200

    def test_favorites_sync_non_list(self, client, auth_headers, mock_user):
        with patch.object(auth_manager, 'get_user_by_username', return_value=mock_user):
            resp = client.post('/api/favorites/sync',
                               headers=auth_headers,
                               json={'recipe_ids': 'not-a-list'})
            assert resp.status_code == 400

    def test_browse_with_max_time_filter(self, client):
        with patch.object(db, 'execute_query') as mock_q:
            mock_q.side_effect = [
                [],  # recipes
                [{'total': 0}],
            ]
            resp = client.get('/api/recipes/browse?max_time=30')
            assert resp.status_code == 200

    def test_browse_with_sort_options(self, client):
        for sort in ['popular', 'recent', 'rating', 'name']:
            with patch.object(db, 'execute_query') as mock_q:
                mock_q.side_effect = [[], [{'total': 0}]]
                resp = client.get(f'/api/recipes/browse?sort={sort}')
                assert resp.status_code == 200, f"Failed for sort={sort}"

    def test_comment_pagination(self, client):
        with patch.object(db, 'execute_query') as mock_q:
            mock_q.side_effect = [
                [],  # no comments
                [{'total': 0}],
            ]
            resp = client.get('/api/recipe/1/comments?page=1&limit=5')
            assert resp.status_code == 200
            assert resp.json['comments'] == []
            assert resp.json['has_more'] is False

    def test_random_recipes_max_count(self, client):
        with patch.object(db, 'execute_query') as mock_q:
            mock_q.side_effect = [
                [{'min_id': 1, 'max_id': 100}],
                [],
            ]
            resp = client.get('/api/recipes/random?count=25')  # max is 20
            assert resp.status_code == 200


# ============================================================================
# 15. CONTENT-TYPE & RESPONSE FORMAT TESTS
# ============================================================================

class TestResponseFormat:
    def test_json_content_type(self, client):
        resp = client.get('/')
        assert 'application/json' in resp.content_type

    def test_health_returns_json(self, client):
        resp = client.get('/api/health')
        assert resp.is_json

    def test_error_response_is_json(self, client):
        with patch.object(db, 'get_recipe_by_id', return_value=None):
            resp = client.get('/api/recipe/99999')
            assert resp.is_json
            assert 'error' in resp.json
