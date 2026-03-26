"""
Unit Tests for Recipe Recommender API
Tests authentication, validation, and core functionality
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app_v2 import app, db, auth_manager
from schemas import RecommendationRequest, SearchRequest, UserRegistration
from pydantic import ValidationError


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_headers(client):
    """Generate authentication headers for testing"""
    # Mock successful login
    with patch.object(auth_manager, 'authenticate_user') as mock_auth:
        mock_auth.return_value = {
            'id': 1,
            'username': 'testuser',
            'email': 'test@example.com'
        }
        response = client.post('/api/auth/login',
                               json={'username': 'testuser', 'password': 'TestPass123'})
        token = response.json.get('access_token')
        return {'Authorization': f'Bearer {token}'}


class TestHealthEndpoints:
    """Test health and info endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns API info"""
        response = client.get('/')
        assert response.status_code == 200
        data = response.json
        assert data['name'] == 'Smart Recipe Recommender API'
        assert data['version'] == '2.0.0'
        assert 'endpoints' in data
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'healthy'
        assert 'ml_ready' in data
        assert 'database' in data


class TestValidation:
    """Test request validation"""
    
    def test_recommendation_request_valid(self):
        """Test valid recommendation request"""
        data = {
            'ingredients': ['chicken', 'rice', 'tomato'],
            'dietary_preference': 'vegetarian',
            'cuisine_type': 'italian',
            'limit': 10
        }
        request = RecommendationRequest(**data)
        assert len(request.ingredients) == 3
        assert request.limit == 10
    
    def test_recommendation_request_invalid_empty_ingredients(self):
        """Test recommendation request with empty ingredients"""
        with pytest.raises(ValidationError):
            RecommendationRequest(ingredients=[])
    
    def test_recommendation_request_sanitization(self):
        """Test input sanitization"""
        data = {
            'ingredients': ['chicken', 'rice<script>', 'tomato'],
            'dietary_preference': 'vegetarian<script>alert("xss")</script>',
        }
        request = RecommendationRequest(**data)
        # Check that dangerous characters are removed
        assert '<' not in request.dietary_preference
        assert 'script' not in request.dietary_preference
    
    def test_search_request_valid(self):
        """Test valid search request"""
        data = {
            'query': 'pasta',
            'search_type': 'name',
            'limit': 20,
            'max_time': 30,
            'max_calories': 500
        }
        request = SearchRequest(**data)
        assert request.query == 'pasta'
        assert request.limit == 20
        assert request.max_time == 30
    
    def test_search_request_invalid_query(self):
        """Test search request with empty query"""
        with pytest.raises(ValidationError):
            SearchRequest(query='', search_type='name')
    
    def test_user_registration_valid(self):
        """Test valid user registration"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'SecurePass123'
        }
        request = UserRegistration(**data)
        assert request.username == 'testuser'
        assert request.email == 'test@example.com'
    
    def test_user_registration_invalid_password(self):
        """Test registration with weak password"""
        with pytest.raises(ValidationError) as exc_info:
            UserRegistration(
                username='testuser',
                email='test@example.com',
                password='weak'  # Too short
            )
        assert 'at least 8 characters' in str(exc_info.value)
    
    def test_user_registration_invalid_email(self):
        """Test registration with invalid email"""
        with pytest.raises(ValidationError):
            UserRegistration(
                username='testuser',
                email='invalid-email',
                password='SecurePass123'
            )


class TestAuthenticationEndpoints:
    """Test authentication endpoints"""
    
    def test_register_success(self, client):
        """Test successful user registration"""
        with patch.object(auth_manager, 'register_user') as mock_register:
            mock_register.return_value = {
                'user_id': 1,
                'username': 'newuser',
                'email': 'new@example.com'
            }
            with patch.object(auth_manager, 'generate_tokens') as mock_tokens:
                mock_tokens.return_value = {
                    'access_token': 'test_token',
                    'refresh_token': 'test_refresh',
                    'expires_in': 3600
                }
                
                response = client.post('/api/auth/register',
                                       json={
                                           'username': 'newuser',
                                           'email': 'new@example.com',
                                           'password': 'SecurePass123'
                                       })
                
                assert response.status_code == 201
                data = response.json
                assert data['message'] == 'User registered successfully'
                assert 'access_token' in data
    
    def test_register_duplicate_username(self, client):
        """Test registration with existing username"""
        with patch.object(auth_manager, 'register_user') as mock_register:
            mock_register.side_effect = ValueError('Username already exists')
            
            response = client.post('/api/auth/register',
                                   json={
                                       'username': 'existinguser',
                                       'email': 'new@example.com',
                                       'password': 'SecurePass123'
                                   })
            
            assert response.status_code == 400
            assert 'already exists' in response.json['error']
    
    def test_login_success(self, client):
        """Test successful login"""
        with patch.object(auth_manager, 'authenticate_user') as mock_auth:
            mock_auth.return_value = {
                'id': 1,
                'username': 'testuser',
                'email': 'test@example.com'
            }
            with patch.object(auth_manager, 'generate_tokens') as mock_tokens:
                mock_tokens.return_value = {
                    'access_token': 'test_token',
                    'refresh_token': 'test_refresh',
                    'expires_in': 3600
                }
                
                response = client.post('/api/auth/login',
                                       json={
                                           'username': 'testuser',
                                           'password': 'TestPass123'
                                       })
                
                assert response.status_code == 200
                data = response.json
                assert data['message'] == 'Login successful'
                assert 'access_token' in data
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        with patch.object(auth_manager, 'authenticate_user') as mock_auth:
            mock_auth.return_value = None
            
            response = client.post('/api/auth/login',
                                   json={
                                       'username': 'testuser',
                                       'password': 'WrongPass'
                                   })
            
            assert response.status_code == 401
            assert response.json['error'] == 'Invalid credentials'


class TestRecipeEndpoints:
    """Test recipe-related endpoints"""
    
    def test_search_recipes(self, client):
        """Test recipe search"""
        with patch.object(db, 'search_recipes') as mock_search:
            mock_search.return_value = [
                {
                    'id': 1,
                    'name': 'Pasta Carbonara',
                    'minutes': 30,
                    'ingredients': ['pasta', 'eggs', 'bacon'],
                    'tags': ['italian', 'quick']
                }
            ]
            
            response = client.get('/api/search?query=pasta&type=name&limit=10')
            
            assert response.status_code == 200
            data = response.json
            assert 'results' in data
            assert len(data['results']) == 1
            assert data['results'][0]['name'] == 'Pasta Carbonara'
    
    def test_search_invalid_query(self, client):
        """Test search with invalid query"""
        response = client.get('/api/search?query=&type=name')
        assert response.status_code == 400
    
    def test_get_recipe_by_id(self, client):
        """Test getting recipe by ID"""
        with patch.object(db, 'get_recipe_by_id') as mock_get:
            mock_get.return_value = {
                'id': 1,
                'name': 'Pasta Carbonara',
                'description': 'Classic Italian pasta',
                'ingredients': ['pasta', 'eggs', 'bacon'],
                'steps': ['Boil pasta', 'Cook bacon', 'Mix together']
            }
            
            response = client.get('/api/recipe/1')
            
            assert response.status_code == 200
            data = response.json
            assert data['name'] == 'Pasta Carbonara'
    
    def test_get_recipe_not_found(self, client):
        """Test getting non-existent recipe"""
        with patch.object(db, 'get_recipe_by_id') as mock_get:
            mock_get.return_value = None
            
            response = client.get('/api/recipe/99999')
            assert response.status_code == 404
    
    def test_batch_recipes(self, client):
        """Test batch recipe fetch"""
        with patch.object(db, 'get_recipes_by_ids') as mock_batch:
            mock_batch.return_value = [
                {'id': 1, 'name': 'Recipe 1'},
                {'id': 2, 'name': 'Recipe 2'}
            ]
            
            response = client.post('/api/recipes/batch',
                                   json={'recipe_ids': [1, 2]})
            
            assert response.status_code == 200
            data = response.json
            assert len(data['recipes']) == 2


class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_rate_limit_exceeded(self, client):
        """Test that rate limiting works"""
        # This test requires rate limiting to be enabled
        # Make multiple requests quickly
        with patch.object(db, 'search_recipes', return_value=[]):
            responses = []
            for _ in range(65):  # Exceed the 60 per minute limit
                response = client.get('/api/search?query=test&type=name')
                responses.append(response.status_code)
            
            # At least one request should be rate limited
            assert 429 in responses


class TestSecurityHeaders:
    """Test security headers are present"""
    
    def test_security_headers_present(self, client):
        """Test that security headers are added to responses"""
        response = client.get('/')
        
        assert 'X-Content-Type-Options' in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
        assert 'X-Frame-Options' in response.headers
        assert response.headers['X-Frame-Options'] == 'DENY'
        assert 'X-XSS-Protection' in response.headers
        assert 'Strict-Transport-Security' in response.headers


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
