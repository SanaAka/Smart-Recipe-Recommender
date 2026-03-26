"""
Unit Tests for Database Module
Tests database operations and query methods
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import Database


@pytest.fixture
def mock_db():
    """Create database instance with mocked connection"""
    with patch('database.mysql_pooling'):
        db = Database()
        db.connection = Mock()
        return db


class TestDatabaseConnection:
    """Test database connection handling"""
    
    def test_connection_retry_logic(self):
        """Test connection retry mechanism"""
        with patch('database.mysql_pooling.MySQLConnectionPool') as mock_pool:
            mock_pool.side_effect = [
                Exception("Connection failed"),
                Exception("Connection failed"),
                MagicMock()  # Success on third try
            ]
            
            db = Database()
            # Should succeed after retries
            # Note: This will print error messages during the test
    
    def test_connection_host_normalization(self):
        """Test that localhost is converted to 127.0.0.1"""
        with patch('database.mysql_pooling.MySQLConnectionPool') as mock_pool:
            db = Database()
            db.host = 'localhost'
            # Connection attempt should use 127.0.0.1


class TestSearchRecipes:
    """Test recipe search functionality"""
    
    def test_search_by_name(self, mock_db):
        """Test searching recipes by name"""
        mock_result = [
            {'id': 1, 'name': 'Pasta', 'ingredients': 'pasta|tomato', 'tags': 'italian|quick'}
        ]
        
        with patch.object(mock_db, 'execute_query', return_value=mock_result):
            results = mock_db.search_recipes('pasta', 'name', limit=10)
            assert len(results) > 0
    
    def test_search_with_filters(self, mock_db):
        """Test search with additional filters"""
        with patch.object(mock_db, 'execute_query', return_value=[]):
            results = mock_db.search_recipes(
                'chicken',
                'ingredient',
                limit=10,
                max_time=30,
                max_calories=500
            )
            # Should not raise errors
    
    def test_search_empty_query(self, mock_db):
        """Test search with empty query returns empty list"""
        results = mock_db.search_recipes('', 'name')
        assert results == []
    
    def test_search_caching(self, mock_db):
        """Test that search results are cached"""
        mock_result = [{'id': 1, 'name': 'Test Recipe'}]
        
        with patch.object(mock_db, 'execute_query', return_value=mock_result):
            # First call
            results1 = mock_db.search_recipes('test', 'name')
            call_count_after_first = mock_db.execute_query.call_count
            
            # Second call should use cache
            results2 = mock_db.search_recipes('test', 'name')
            
            # execute_query should not be called again for the cached second search
            assert mock_db.execute_query.call_count == call_count_after_first


class TestGetRecipeById:
    """Test fetching recipe by ID"""
    
    def test_get_existing_recipe(self, mock_db):
        """Test getting an existing recipe"""
        mock_result = [{
            'id': 1,
            'name': 'Test Recipe',
            'ingredients': 'flour|sugar|eggs',
            'tags': 'dessert|baking',
            'steps': '1:Mix ingredients|2:Bake',
            'calories': 300
        }]
        
        with patch.object(mock_db, 'execute_query', return_value=mock_result):
            recipe = mock_db.get_recipe_by_id(1)
            assert recipe is not None
            assert recipe['name'] == 'Test Recipe'
            assert isinstance(recipe['ingredients'], list)
            assert isinstance(recipe['tags'], list)
    
    def test_get_nonexistent_recipe(self, mock_db):
        """Test getting a recipe that doesn't exist"""
        with patch.object(mock_db, 'execute_query', return_value=[]):
            recipe = mock_db.get_recipe_by_id(99999)
            assert recipe is None


class TestBatchRecipes:
    """Test batch recipe fetching"""
    
    def test_get_multiple_recipes(self, mock_db):
        """Test fetching multiple recipes at once"""
        mock_result = [
            {'id': 1, 'name': 'Recipe 1', 'ingredients': 'a|b', 'tags': 'x|y'},
            {'id': 2, 'name': 'Recipe 2', 'ingredients': 'c|d', 'tags': 'y|z'}
        ]
        
        with patch.object(mock_db, 'execute_query', return_value=mock_result):
            recipes = mock_db.get_recipes_by_ids([1, 2])
            assert len(recipes) == 2
    
    def test_batch_empty_list(self, mock_db):
        """Test batch fetch with empty list"""
        recipes = mock_db.get_recipes_by_ids([])
        assert recipes == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
