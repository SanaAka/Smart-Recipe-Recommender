import mysql.connector
from mysql.connector import Error
from mysql.connector import pooling as mysql_pooling
import os
import json
import hashlib
from collections import OrderedDict
from nutrition_estimator import NutritionEstimator

class Database:
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', '')
        self.database = os.getenv('DB_NAME', 'recipe_recommender')
        self.connection = None
        self.nutrition_estimator = NutritionEstimator()
        # Bounded LRU cache for search/batch results
        self._cache_maxsize = int(os.getenv('SEARCH_CACHE_MAXSIZE', '256'))
        self.search_cache = OrderedDict()
        # MySQL connection pool
        self.pool_name = os.getenv('DB_POOL_NAME', 'recipe_pool')
        self.pool_size = int(os.getenv('DB_POOL_SIZE', '8'))
        self._pool = None

    def connect(self):
        """Create or get a pooled database connection with retry logic"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # Initialize pool lazily
                if self._pool is None:
                    config = {
                        'host': self.host,
                        'user': self.user,
                        'password': self.password,
                        'database': self.database,
                        'use_pure': True,
                        'charset': 'utf8mb4',
                        'collation': 'utf8mb4_unicode_ci',
                        'autocommit': False,
                        'ssl_disabled': True,
                        'connect_timeout': 10,
                        'pool_reset_session': True,
                    }
                    self._pool = mysql_pooling.MySQLConnectionPool(
                        pool_name=self.pool_name,
                        pool_size=self.pool_size,
                        **config
                    )
                # Get a fresh connection from the pool
                conn = self._pool.get_connection()
                self.connection = conn
                return conn
            except Error as e:
                if attempt < max_retries - 1:
                    print(f"Connection attempt {attempt + 1} failed, retrying...")
                    import time
                    time.sleep(retry_delay)
                else:
                    print(f"Error connecting to MySQL: {e}")
                    print(f"Host: {self.host}, User: {self.user}, Database: {self.database}")
                    raise

    def disconnect(self):
        """Close database connection"""
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            finally:
                self.connection = None

    def execute_query(self, query, params=None, fetch=False):
        """Execute a database query with retry on connection failure"""
        max_retries = 2
        
        for attempt in range(max_retries):
            conn = None
            cursor = None
            try:
                conn = self.connect()
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query, params or ())
                
                if fetch:
                    result = cursor.fetchall()
                    return result
                else:
                    conn.commit()
                    last_id = cursor.lastrowid
                    return last_id
            except (Error, IndexError) as e:
                # Force reconnect on next attempt
                self.connection = None
                
                if attempt < max_retries - 1:
                    print(f"Query failed (attempt {attempt + 1}), reconnecting...")
                    import time
                    time.sleep(0.5)
                else:
                    print(f"Database query error: {e}")
                    if fetch:
                        return []  # Return empty list instead of crashing
                    raise
            finally:
                try:
                    if cursor:
                        cursor.close()
                finally:
                    if conn:
                        try:
                            conn.close()  # Return to pool
                        except Exception:
                            pass

    def get_all_recipes(self, limit=1000):
        """Get all recipes for ML model training - optimized for speed"""
        # Fast query - get recipes without expensive GROUP_CONCAT
        query = """
            SELECT id, name, minutes, description
            FROM recipes
            WHERE name IS NOT NULL AND description IS NOT NULL
            ORDER BY id
            LIMIT %s
        """
        
        results = self.execute_query(query, (limit,), fetch=True)
        
        if not results:
            return results
        
        # Get ingredients and tags in separate batch queries
        recipe_ids = [r['id'] for r in results]
        placeholders = ','.join(['%s'] * len(recipe_ids))
        
        # Batch get ingredients
        ing_query = f"""
            SELECT ri.recipe_id, GROUP_CONCAT(i.name SEPARATOR '|') as ingredients
            FROM recipe_ingredients ri
            JOIN ingredients i ON ri.ingredient_id = i.id
            WHERE ri.recipe_id IN ({placeholders})
            GROUP BY ri.recipe_id
        """
        ing_results = self.execute_query(ing_query, tuple(recipe_ids), fetch=True)
        ing_map = {r['recipe_id']: r['ingredients'].split('|') for r in ing_results if r['ingredients']}
        
        # Batch get tags
        tag_query = f"""
            SELECT rt.recipe_id, GROUP_CONCAT(t.name SEPARATOR '|') as tags
            FROM recipe_tags rt
            JOIN tags t ON rt.tag_id = t.id
            WHERE rt.recipe_id IN ({placeholders})
            GROUP BY rt.recipe_id
        """
        tag_results = self.execute_query(tag_query, tuple(recipe_ids), fetch=True)
        tag_map = {r['recipe_id']: r['tags'].split('|') for r in tag_results if r['tags']}
        
        # Merge results
        for recipe in results:
            recipe['ingredients'] = ing_map.get(recipe['id'], [])
            recipe['tags'] = tag_map.get(recipe['id'], [])
        
        return results

    def search_recipes(self, query, search_type='name', limit=20, max_time=None, max_calories=None, min_ingredients=None, max_ingredients=None):
        """Search recipes by name, ingredient, or cuisine with optional filters"""
        # Validate query
        if not query or not query.strip():
            return []
        
        # Create cache key from all parameters
        cache_key = hashlib.md5(
            f"{query}_{search_type}_{limit}_{max_time}_{max_calories}_{min_ingredients}_{max_ingredients}".encode()
        ).hexdigest()
        
        # Check cache first (LRU)
        cached = self.search_cache.get(cache_key)
        if cached is not None:
            # Move to end to mark as recently used
            self.search_cache.move_to_end(cache_key)
            print(f"[CACHE HIT] Returning cached results for query: {query}")
            return cached
        
        # Split query into words for broader matching
        query_words = [w.strip() for w in query.lower().split() if w.strip()]
        
        # If no valid words after cleaning, return empty
        if not query_words:
            return []
        
        # Base filters for nutrition and recipe properties
        additional_filters = []
        additional_params = []
        having_filters = []
        
        if max_time is not None:
            additional_filters.append('r.minutes <= %s')
            additional_params.append(max_time)
        
        if max_calories is not None:
            additional_filters.append('n.calories <= %s')
            additional_params.append(max_calories)
        
        # Add HAVING clause for ingredient count filters (more efficient than post-processing)
        if min_ingredients is not None:
            having_filters.append(f'COUNT(DISTINCT ri.ingredient_id) >= {min_ingredients}')
        
        if max_ingredients is not None:
            having_filters.append(f'COUNT(DISTINCT ri.ingredient_id) <= {max_ingredients}')
        
        if search_type == 'name':
            # Build OR conditions for each word
            where_conditions = ' OR '.join(['r.name LIKE %s'] * len(query_words))
            
            # Add additional filters
            if additional_filters:
                where_conditions = f"({where_conditions}) AND " + ' AND '.join(additional_filters)
            
            # Build HAVING clause
            having_clause = ''
            if having_filters:
                having_clause = 'HAVING ' + ' AND '.join(having_filters)
            
            sql = f"""
                SELECT 
                    r.id, r.name, r.minutes,
                    GROUP_CONCAT(DISTINCT i.name ORDER BY i.name SEPARATOR '|') as ingredients,
                    GROUP_CONCAT(DISTINCT t.name ORDER BY t.name SEPARATOR '|') as tags,
                    n.calories
                FROM recipes r
                LEFT JOIN nutrition n ON r.id = n.recipe_id
                LEFT JOIN recipe_ingredients ri ON r.id = ri.recipe_id
                LEFT JOIN ingredients i ON ri.ingredient_id = i.id
                LEFT JOIN recipe_tags rt ON r.id = rt.recipe_id
                LEFT JOIN tags t ON rt.tag_id = t.id
                WHERE {where_conditions}
                GROUP BY r.id, r.name, r.minutes, n.calories
                {having_clause}
                ORDER BY r.name
                LIMIT %s
            """
            params = tuple([f'%{word}%' for word in query_words] + additional_params + [limit])
            
        elif search_type == 'ingredient':
            # Build OR conditions for each word
            where_conditions = ' OR '.join(['i.name LIKE %s'] * len(query_words))
            
            # Add additional filters
            if additional_filters:
                where_conditions = f"({where_conditions}) AND " + ' AND '.join(additional_filters)
            
            # Build HAVING clause
            having_clause = ''
            if having_filters:
                having_clause = 'HAVING ' + ' AND '.join(having_filters)
            
            sql = f"""
                SELECT DISTINCT
                    r.id, r.name, r.minutes,
                    GROUP_CONCAT(DISTINCT i.name ORDER BY i.name SEPARATOR '|') as ingredients,
                    GROUP_CONCAT(DISTINCT t.name ORDER BY t.name SEPARATOR '|') as tags,
                    n.calories
                FROM recipes r
                JOIN recipe_ingredients ri ON r.id = ri.recipe_id
                JOIN ingredients i ON ri.ingredient_id = i.id
                LEFT JOIN nutrition n ON r.id = n.recipe_id
                LEFT JOIN recipe_tags rt ON r.id = rt.recipe_id
                LEFT JOIN tags t ON rt.tag_id = t.id
                WHERE {where_conditions}
                GROUP BY r.id, r.name, r.minutes, n.calories
                {having_clause}
                ORDER BY r.name
                LIMIT %s
            """
            params = tuple([f'%{word}%' for word in query_words] + additional_params + [limit])
            
        else:  # cuisine
            # Build OR conditions for each word
            where_conditions = ' OR '.join(['t.name LIKE %s'] * len(query_words))
            
            # Add additional filters
            if additional_filters:
                where_conditions = f"({where_conditions}) AND " + ' AND '.join(additional_filters)
            
            # Build HAVING clause
            having_clause = ''
            if having_filters:
                having_clause = 'HAVING ' + ' AND '.join(having_filters)
            
            sql = f"""
                SELECT 
                    r.id, r.name, r.minutes,
                    GROUP_CONCAT(DISTINCT i.name ORDER BY i.name SEPARATOR '|') as ingredients,
                    GROUP_CONCAT(DISTINCT t.name ORDER BY t.name SEPARATOR '|') as tags,
                    n.calories
                FROM recipes r
                JOIN recipe_tags rt ON r.id = rt.recipe_id
                JOIN tags t ON rt.tag_id = t.id
                LEFT JOIN nutrition n ON r.id = n.recipe_id
                LEFT JOIN recipe_ingredients ri ON r.id = ri.recipe_id
                LEFT JOIN ingredients i ON ri.ingredient_id = i.id
                WHERE {where_conditions}
                GROUP BY r.id, r.name, r.minutes, n.calories
                {having_clause}
                ORDER BY r.name
                LIMIT %s
            """
            params = tuple([f'%{word}%' for word in query_words] + additional_params + [limit])

        try:
            results = self.execute_query(sql, params, fetch=True)
            
            # Ensure results is a list
            if results is None:
                results = []
            
            # Process results
            for recipe in results:
                recipe['ingredients'] = recipe['ingredients'].split('|') if recipe['ingredients'] else []
                recipe['tags'] = recipe['tags'].split('|') if recipe['tags'] else []
            
            # Cache the results with LRU eviction
            self.search_cache[cache_key] = results
            if len(self.search_cache) > self._cache_maxsize:
                # Pop the least recently used item
                self.search_cache.popitem(last=False)
            
            return results
        except Exception as e:
            print(f"[ERROR] Search failed for query '{query}': {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_recipe_by_id(self, recipe_id):
        """Get detailed recipe information by ID"""
        query = """
            SELECT 
                r.id, r.name, r.minutes, r.description,
                GROUP_CONCAT(DISTINCT i.name SEPARATOR '|') as ingredients,
                GROUP_CONCAT(DISTINCT t.name SEPARATOR '|') as tags,
                GROUP_CONCAT(DISTINCT s.step_number, ':', s.description ORDER BY s.step_number SEPARATOR '|') as steps,
                n.calories, n.protein, n.total_fat, n.sodium, n.carbohydrates, n.sugar
            FROM recipes r
            LEFT JOIN recipe_ingredients ri ON r.id = ri.recipe_id
            LEFT JOIN ingredients i ON ri.ingredient_id = i.id
            LEFT JOIN recipe_tags rt ON r.id = rt.recipe_id
            LEFT JOIN tags t ON rt.tag_id = t.id
            LEFT JOIN steps s ON r.id = s.recipe_id
            LEFT JOIN nutrition n ON r.id = n.recipe_id
            WHERE r.id = %s
            GROUP BY r.id
        """
        
        results = self.execute_query(query, (recipe_id,), fetch=True)
        
        if not results:
            return None
        
        recipe = results[0]
        
        # Process data
        recipe['ingredients'] = recipe['ingredients'].split('|') if recipe['ingredients'] else []
        recipe['tags'] = recipe['tags'].split('|') if recipe['tags'] else []
        
        # Process steps
        if recipe['steps']:
            steps_data = recipe['steps'].split('|')
            recipe['steps'] = [step.split(':', 1)[1] if ':' in step else step for step in steps_data]
        else:
            recipe['steps'] = []
        
        # Format nutrition data (handle None values or estimate if missing)
        has_nutrition = any([
            recipe.get('calories'), recipe.get('protein'), recipe.get('total_fat'),
            recipe.get('sodium'), recipe.get('carbohydrates'), recipe.get('sugar')
        ])
        
        if not has_nutrition and recipe.get('ingredients'):
            # Estimate nutrition from ingredients
            estimated = self.nutrition_estimator.estimate_nutrition(recipe['ingredients'])
            if estimated:
                recipe['nutrition'] = {
                    'Calories': f"{estimated['calories']:.0f} (est.)",
                    'Protein': f"{estimated['protein']:.1f}g (est.)",
                    'Fat': f"{estimated['total_fat']:.1f}g (est.)",
                    'Sodium': f"{estimated['sodium']:.1f}mg (est.)",
                    'Carbohydrates': f"{estimated['carbohydrates']:.1f}g (est.)",
                    'Sugar': f"{estimated['sugar']:.1f}g (est.)"
                }
            else:
                recipe['nutrition'] = None
        else:
            recipe['nutrition'] = {
                'Calories': f"{recipe.get('calories') or 0:.0f}",
                'Protein': f"{recipe.get('protein') or 0:.1f}g",
                'Fat': f"{recipe.get('total_fat') or 0:.1f}g",
                'Sodium': f"{recipe.get('sodium') or 0:.1f}mg",
                'Carbohydrates': f"{recipe.get('carbohydrates') or 0:.1f}g",
                'Sugar': f"{recipe.get('sugar') or 0:.1f}g"
            }
        
        return recipe

    def get_recipes_by_ids(self, recipe_ids):
        """Get multiple recipes by IDs with caching"""
        try:
            if not recipe_ids:
                return []
            
            # Create cache key from sorted IDs
            cache_key = 'batch_' + hashlib.md5(str(sorted(recipe_ids)).encode()).hexdigest()
            
            # Check cache first
            if cache_key in self.search_cache:
                return self.search_cache[cache_key]
            
            placeholders = ','.join(['%s'] * len(recipe_ids))
            query = f"""
                SELECT 
                    r.id, r.name, r.minutes,
                    GROUP_CONCAT(DISTINCT i.name SEPARATOR '|') as ingredients,
                    GROUP_CONCAT(DISTINCT t.name SEPARATOR '|') as tags,
                    n.calories
                FROM recipes r
                LEFT JOIN recipe_ingredients ri ON r.id = ri.recipe_id
                LEFT JOIN ingredients i ON ri.ingredient_id = i.id
                LEFT JOIN recipe_tags rt ON r.id = rt.recipe_id
                LEFT JOIN tags t ON rt.tag_id = t.id
                LEFT JOIN nutrition n ON r.id = n.recipe_id
                WHERE r.id IN ({placeholders})
                GROUP BY r.id
            """
            
            results = self.execute_query(query, tuple(recipe_ids), fetch=True)

            # Process results
            for recipe in results:
                recipe['ingredients'] = recipe['ingredients'].split('|') if recipe.get('ingredients') else []
                recipe['tags'] = recipe['tags'].split('|') if recipe.get('tags') else []
            
            # Preserve requested order
            order_map = {rid: idx for idx, rid in enumerate(recipe_ids)}
            results.sort(key=lambda r: order_map.get(r.get('id'), len(recipe_ids)))

            # Cache the results with LRU eviction
            self.search_cache[cache_key] = results
            if len(self.search_cache) > self._cache_maxsize:
                self.search_cache.popitem(last=False)
            
            return results
        except Exception as e:
            print(f"[ERROR] get_recipes_by_ids failed: {str(e)}")
            self.connection = None
            return []

    def get_stats(self):
        """Get database statistics"""
        stats = {}
        
        # Count recipes
        result = self.execute_query("SELECT COUNT(*) as count FROM recipes", fetch=True)
        stats['total_recipes'] = result[0]['count'] if result else 0
        
        # Count ingredients
        result = self.execute_query("SELECT COUNT(*) as count FROM ingredients", fetch=True)
        stats['total_ingredients'] = result[0]['count'] if result else 0
        
        # Count tags
        result = self.execute_query("SELECT COUNT(*) as count FROM tags", fetch=True)
        stats['total_tags'] = result[0]['count'] if result else 0
        
        return stats
