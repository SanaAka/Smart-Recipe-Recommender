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
        self.port = int(os.getenv('DB_PORT', '3306'))
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', '')
        self.database = os.getenv('DB_NAME', 'recipe_recommender')
        self.connection = None
        self.nutrition_estimator = NutritionEstimator()
        # Bounded LRU cache for search/batch results
        self._cache_maxsize = int(os.getenv('SEARCH_CACHE_MAXSIZE', '256'))
        self.search_cache = OrderedDict()
        # Cache for fulltext availability checks per table
        self._fts_cache = {}
        # MySQL connection pool
        self.pool_name = os.getenv('DB_POOL_NAME', 'recipe_pool')
        self.pool_size = int(os.getenv('DB_POOL_SIZE', '16'))
        self._pool = None

    def connect(self):
        """Create or get a pooled database connection with retry logic"""
        max_retries = 3
        retry_delay = 2
        
        # Force TCP connection for Windows compatibility
        effective_host = '127.0.0.1' if self.host == 'localhost' else self.host
        
        for attempt in range(max_retries):
            try:
                # Initialize pool lazily
                if self._pool is None:
                    config = {
                        'host': effective_host,
                        'port': self.port,
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
                # Reset pool on error for next retry
                self._pool = None
                err_str = str(e)
                if attempt < max_retries - 1:
                    print(f"Connection attempt {attempt + 1} failed, retrying... ({err_str})")
                    import time
                    time.sleep(retry_delay)
                else:
                    # Final attempt failed — provide actionable guidance
                    print(f"Error connecting to MySQL: {e}")
                    print(f"Host: {effective_host}, Port: {self.port}, User: {self.user}, Database: {self.database}")
                    print("Common causes: incorrect credentials in .env, MySQL not running, or root access restricted.")
                    print("Try: 1) verify credentials; 2) use 127.0.0.1 instead of localhost; 3) create a dedicated DB user with privileges.")
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

    def _supports_fulltext_on(self, table_name: str) -> bool:
        """Check (and cache) whether a table has a FULLTEXT index.

        Uses INFORMATION_SCHEMA.STATISTICS to detect any FULLTEXT index on the
        specified table. Returns False on error (safe fallback).
        """
        if table_name in self._fts_cache:
            return self._fts_cache[table_name]

        try:
            sql = ("SELECT COUNT(*) as cnt FROM INFORMATION_SCHEMA.STATISTICS "
                   "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND INDEX_TYPE='FULLTEXT'")
            rows = self.execute_query(sql, (self.database, table_name), fetch=True)
            has = bool(rows and rows[0].get('cnt', 0) > 0)
        except Exception:
            has = False

        self._fts_cache[table_name] = has
        return has

    def _has_column(self, table_name: str, column_name: str) -> bool:
        """Check whether a given column exists on a table."""
        try:
            sql = ("SELECT COUNT(*) as cnt FROM INFORMATION_SCHEMA.COLUMNS "
                   "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME=%s")
            rows = self.execute_query(sql, (self.database, table_name, column_name), fetch=True)
            return bool(rows and rows[0].get('cnt', 0) > 0)
        except Exception:
            return False

    def _fulltext_index_covers(self, table_name: str, columns: tuple) -> bool:
        """Return True if any FULLTEXT index on `table_name` covers the given columns.

        `columns` should be a tuple of column names in the order expected. This method
        checks INFORMATION_SCHEMA.STATISTICS for FULLTEXT indexes and compares the
        ordered concatenated column list against the requested columns.
        """
        try:
            # Get index->columns for FULLTEXT indexes on the table
            sql = ("SELECT INDEX_NAME, GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX SEPARATOR ',') as cols "
                   "FROM INFORMATION_SCHEMA.STATISTICS "
                   "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND INDEX_TYPE='FULLTEXT' "
                   "GROUP BY INDEX_NAME")
            rows = self.execute_query(sql, (self.database, table_name), fetch=True)

            if not rows:
                return False

            requested = ','.join(columns)
            for r in rows:
                cols = r.get('cols') or ''
                # Exact match or superset (requested cols all present in index cols)
                # We'll treat index that contains requested columns (in any order) as valid.
                idx_cols_set = set([c.strip().lower() for c in cols.split(',') if c.strip()])
                req_cols_set = set([c.strip().lower() for c in requested.split(',') if c.strip()])
                if req_cols_set.issubset(idx_cols_set):
                    return True
            return False
        except Exception:
            return False

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
        # Fast query - get recipes with calories for ML features
        query = """
            SELECT r.id, r.name, r.minutes, r.description, r.image_url,
                   n.calories
            FROM recipes r
            LEFT JOIN nutrition n ON r.id = n.recipe_id
            WHERE r.name IS NOT NULL AND r.description IS NOT NULL
            ORDER BY r.id
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
        
        # MySQL FULLTEXT stopwords — these are never indexed so requiring
        # them with '+' in BOOLEAN MODE returns zero results.
        _MYSQL_STOPWORDS = {
            'a', 'about', 'an', 'are', 'as', 'at', 'be', 'by', 'com',
            'de', 'en', 'for', 'from', 'how', 'i', 'in', 'is', 'it',
            'la', 'of', 'on', 'or', 'that', 'the', 'this', 'to', 'was',
            'what', 'when', 'where', 'who', 'will', 'with', 'und',
            'www', 'not', 'no', 'can', 'had', 'has', 'have', 'he',
            'her', 'his', 'if', 'its', 'let', 'may', 'me', 'my',
            'nor', 'our', 'own', 'say', 'she', 'too', 'us', 'we',
            'yet', 'you', 'your',
        }

        import re as _re
        # Split query into words, strip non-alphanumeric chars, drop
        # stopwords and very short tokens (ft_min_word_len defaults to 3).
        # Also split on apostrophes so "mother's" → "mother" (matching MySQL
        # tokenization which treats apostrophe as a word separator).
        raw_words = [w.strip() for w in query.lower().split() if w.strip()]
        query_words = []
        for w in raw_words:
            # Split on apostrophes first, then clean each part
            parts = w.split("'")
            for part in parts:
                cleaned = _re.sub(r"[^a-z0-9]", "", part)
                if cleaned and len(cleaned) >= 3 and cleaned not in _MYSQL_STOPWORDS:
                    query_words.append(cleaned)

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
            additional_filters.append('(n.calories IS NULL OR n.calories <= %s)')
            additional_params.append(max_calories)
        
        # Add HAVING clause for ingredient count filters (more efficient than post-processing)
        if min_ingredients is not None:
            having_filters.append(f'COUNT(DISTINCT ri.ingredient_id) >= {min_ingredients}')
        
        if max_ingredients is not None:
            having_filters.append(f'COUNT(DISTINCT ri.ingredient_id) <= {max_ingredients}')
        
        # Two-step search: first find matching recipe IDs (fast), then batch-fetch details
        # When filters are active, fetch a bigger pool in Step 1 so Step 2 has enough to filter
        has_filters = (max_time is not None or max_calories is not None
                       or min_ingredients is not None or max_ingredients is not None)
        step1_limit = limit * 10 if has_filters else limit

        # Build helper for max_time WHERE clause applied in Step 1
        time_where = ''
        time_params = []
        if max_time is not None:
            time_where = ' AND r.minutes <= %s'
            time_params = [max_time]

        def _build_fts_query(words):
            # Build boolean-mode fulltext query requiring each word
            return ' '.join('+' + w + '*' for w in words)

        def _fetch_details_for_ids(id_list):
            if not id_list:
                return []

            placeholders = ','.join(['%s'] * len(id_list))

            having_clause = ''
            if having_filters:
                having_clause = 'HAVING ' + ' AND '.join(having_filters)

            # Apply additional filters to WHERE (they refer to r or n)
            additional_where = ''
            if additional_filters:
                additional_where = ' AND ' + ' AND '.join(additional_filters)

            # Build the details query regardless of whether additional filters exist
            # Add relevance scoring: exact match gets highest score, then partial matches
            query_lower = query.lower()
            query_like = f'%{query_lower}%'
            
            sql = f"""
                SELECT
                    r.id, r.name, r.minutes, r.image_url,
                    GROUP_CONCAT(DISTINCT i.name ORDER BY i.name SEPARATOR '|') as ingredients,
                    GROUP_CONCAT(DISTINCT t.name ORDER BY t.name SEPARATOR '|') as tags,
                    n.calories,
                    CASE
                        WHEN LOWER(r.name) = %s THEN 1000
                        WHEN LOWER(r.name) LIKE %s THEN 500
                        ELSE 100
                    END as relevance_score
                FROM recipes r
                LEFT JOIN nutrition n ON r.id = n.recipe_id
                LEFT JOIN recipe_ingredients ri ON r.id = ri.recipe_id
                LEFT JOIN ingredients i ON ri.ingredient_id = i.id
                LEFT JOIN recipe_tags rt ON r.id = rt.recipe_id
                LEFT JOIN tags t ON rt.tag_id = t.id
                WHERE r.id IN ({placeholders}){additional_where}
                GROUP BY r.id, r.name, r.minutes, r.image_url, n.calories
                {having_clause}
                ORDER BY relevance_score DESC, r.name
                LIMIT %s
            """

            params = (query_lower, query_like) + tuple(id_list) + tuple(additional_params) + (limit,)
            return self.execute_query(sql, params, fetch=True)

        id_list = []

        try:
            # Try to use FULLTEXT for recipe name/description searches
            if search_type == 'name':
                fts = _build_fts_query(query_words)
                # Prefer denormalized `search_text` fulltext if present
                if self._has_column('recipes', 'search_text') and self._fulltext_index_covers('recipes', ('search_text',)):
                    id_rows = self.execute_query(
                        f"SELECT id FROM recipes r WHERE MATCH(search_text) AGAINST(%s IN BOOLEAN MODE){time_where} LIMIT %s",
                        tuple([fts] + time_params + [step1_limit]),
                        fetch=True
                    )
                    id_list = [r['id'] for r in id_rows] if id_rows else []
                # Fall back to MATCH(name) if a fulltext index exists on name
                elif self._fulltext_index_covers('recipes', ('name',)):
                    id_rows = self.execute_query(
                        f"SELECT id FROM recipes r WHERE MATCH(name) AGAINST(%s IN BOOLEAN MODE){time_where} LIMIT %s",
                        tuple([fts] + time_params + [step1_limit]),
                        fetch=True
                    )
                    id_list = [r['id'] for r in id_rows] if id_rows else []
                else:
                    # Fall back to LIKE-based id search
                    like_where = ' OR '.join(['r.name LIKE %s'] * len(query_words))
                    sql_ids = f"SELECT DISTINCT r.id FROM recipes r WHERE ({like_where}){time_where} LIMIT %s"
                    like_params = tuple([f'%{w}%' for w in query_words] + time_params + [step1_limit])
                    id_rows = self.execute_query(sql_ids, like_params, fetch=True)
                    id_list = [r['id'] for r in id_rows] if id_rows else []

            elif search_type == 'ingredient':
                # Try fulltext on ingredients
                fts = _build_fts_query(query_words)
                # Prefer fulltext on ingredients if available
                if self._fulltext_index_covers('ingredients', ('name',)):
                    rows = self.execute_query(
                        f"SELECT DISTINCT ri.recipe_id as id FROM ingredients i JOIN recipe_ingredients ri ON i.id=ri.ingredient_id JOIN recipes r ON ri.recipe_id=r.id WHERE MATCH(i.name) AGAINST(%s IN BOOLEAN MODE){time_where} LIMIT %s",
                        tuple([fts] + time_params + [step1_limit]),
                        fetch=True
                    )
                    id_list = [r['id'] for r in rows] if rows else []
                else:
                    like_where = ' OR '.join(['i.name LIKE %s'] * len(query_words))
                    params = tuple([f'%{w}%' for w in query_words] + time_params + [step1_limit])
                    sql = f"SELECT DISTINCT ri.recipe_id as id FROM ingredients i JOIN recipe_ingredients ri ON i.id=ri.ingredient_id JOIN recipes r ON ri.recipe_id=r.id WHERE ({like_where}){time_where} LIMIT %s"
                    rows = self.execute_query(sql, params, fetch=True)
                    id_list = [r['id'] for r in rows] if rows else []

            else:  # cuisine/tag search
                # Search in tags only (cuisine column doesn't exist in this schema)
                if True:
                    fts = _build_fts_query(query_words)
                    if self._fulltext_index_covers('tags', ('name',)):
                        rows = self.execute_query(
                            f"SELECT DISTINCT rt.recipe_id as id FROM tags t JOIN recipe_tags rt ON t.id=rt.tag_id JOIN recipes r ON rt.recipe_id=r.id WHERE MATCH(t.name) AGAINST(%s IN BOOLEAN MODE){time_where} LIMIT %s",
                            tuple([fts] + time_params + [step1_limit]),
                            fetch=True
                        )
                        id_list = [r['id'] for r in rows] if rows else []
                    else:
                        like_where = ' OR '.join(['t.name LIKE %s'] * len(query_words))
                        params = tuple([f'%{w}%' for w in query_words] + time_params + [step1_limit])
                        sql = f"SELECT DISTINCT rt.recipe_id as id FROM tags t JOIN recipe_tags rt ON t.id=rt.tag_id JOIN recipes r ON rt.recipe_id=r.id WHERE ({like_where}){time_where} LIMIT %s"
                        rows = self.execute_query(sql, params, fetch=True)
                        id_list = [r['id'] for r in rows] if rows else []

            # If no ids found, try fallbacks for better UX
            if not id_list:
                # If searching by name returned nothing, fall back to ingredient and cuisine/tag searches
                if search_type == 'name':
                    print(f"[SEARCH] No name matches for '{query}', falling back to ingredient and cuisine searches")
                    fts = _build_fts_query(query_words)
                    alt_ids = set()

                    # ingredient fallback
                    if self._supports_fulltext_on('ingredients'):
                        rows = self.execute_query(
                            f"SELECT DISTINCT ri.recipe_id as id FROM ingredients i JOIN recipe_ingredients ri ON i.id=ri.ingredient_id JOIN recipes r ON ri.recipe_id=r.id WHERE MATCH(i.name) AGAINST(%s IN BOOLEAN MODE){time_where} LIMIT %s",
                            tuple([fts] + time_params + [step1_limit]),
                            fetch=True
                        )
                        alt_ids.update(r['id'] for r in rows or [])
                    else:
                        like_where = ' OR '.join(['i.name LIKE %s'] * len(query_words))
                        params = tuple([f'%{w}%' for w in query_words] + time_params + [step1_limit])
                        rows = self.execute_query(
                            f"SELECT DISTINCT ri.recipe_id as id FROM ingredients i JOIN recipe_ingredients ri ON i.id=ri.ingredient_id JOIN recipes r ON ri.recipe_id=r.id WHERE ({like_where}){time_where} LIMIT %s",
                            params,
                            fetch=True
                        )
                        alt_ids.update(r['id'] for r in rows or [])

                    # cuisine/tag fallback
                    if self._supports_fulltext_on('tags'):
                        rows = self.execute_query(
                            f"SELECT DISTINCT rt.recipe_id as id FROM tags t JOIN recipe_tags rt ON t.id=rt.tag_id JOIN recipes r ON rt.recipe_id=r.id WHERE MATCH(t.name) AGAINST(%s IN BOOLEAN MODE){time_where} LIMIT %s",
                            tuple([fts] + time_params + [step1_limit]),
                            fetch=True
                        )
                        alt_ids.update(r['id'] for r in rows or [])
                    else:
                        like_where = ' OR '.join(['t.name LIKE %s'] * len(query_words))
                        params = tuple([f'%{w}%' for w in query_words] + time_params + [step1_limit])
                        rows = self.execute_query(
                            f"SELECT DISTINCT rt.recipe_id as id FROM tags t JOIN recipe_tags rt ON t.id=rt.tag_id JOIN recipes r ON rt.recipe_id=r.id WHERE ({like_where}){time_where} LIMIT %s",
                            params,
                            fetch=True
                        )
                        alt_ids.update(r['id'] for r in rows or [])

                    if not alt_ids:
                        return []

                    # Limit and convert to list
                    id_list = list(alt_ids)[:step1_limit]
                else:
                    return []

            # Fetch full details for the matched ids
            results = _fetch_details_for_ids(id_list)

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

        # End of search_recipes

    def get_recipe_by_id(self, recipe_id):
        """Get detailed recipe information by ID"""
        query = """
            SELECT 
                r.id, r.name, r.minutes, r.description, r.image_url,
                r.submitted_by,
                u.username AS submitted_by_username,
                GROUP_CONCAT(DISTINCT i.name SEPARATOR '|') as ingredients,
                GROUP_CONCAT(DISTINCT t.name SEPARATOR '|') as tags,
                GROUP_CONCAT(DISTINCT s.step_number, ':', s.description ORDER BY s.step_number SEPARATOR '|') as steps,
                n.calories, n.protein, n.total_fat, n.sodium, n.carbohydrates, n.sugar
            FROM recipes r
            LEFT JOIN users u ON r.submitted_by = u.id
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
                    r.id, r.name, r.minutes, r.image_url,
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
