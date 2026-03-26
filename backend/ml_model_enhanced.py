"""
Enhanced ML Model for Recipe Recommendations
Implements hybrid recommendation system with:
- Content-based filtering (TF-IDF + advanced features)
- Collaborative filtering (user-item matrix)
- Popularity-based recommendations
- Model persistence and caching
- Diversity optimization
- Explanation generation
"""
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import TruncatedSVD
from scipy.sparse import csr_matrix
import pickle
import os
import hashlib
from pathlib import Path
from collections import defaultdict
import json


class HybridRecipeRecommender:
    """Advanced hybrid recommendation system"""

    def __init__(self, database, cache_dir='ml_cache'):
        self.db = database
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # Models
        self.recipes_df = None
        self.tfidf_matrix = None
        self.content_vectorizer = None
        self.user_item_matrix = None
        self.svd_model = None
        self.popularity_scores = None
        self.scaler = MinMaxScaler()

        # Precomputed structures for fast ingredient matching & coverage
        self.ingredient_index = {}      # ingredient_name -> set of df indices
        self.ingredient_idf = {}        # ingredient_name -> IDF weight
        self.favorites_map = {}         # user_id -> set of recipe_ids

        # Cache for recommendations
        self.recommendation_cache = {}
        self.cache_maxsize = 500

        # Model version for cache invalidation
        self.model_version = self._compute_model_version()

        # Feature weights for hybrid model
        # When collaborative data is available these are the ideal weights;
        # _combine_scores will dynamically re-weight when collab is empty.
        self.weights = {
            'content': 0.60,
            'collaborative': 0.20,
            'popularity': 0.10,
            'ingredient_bonus': 0.10,
        }

        self.load_or_train()

    def _compute_model_version(self):
        """Compute model version based on data"""
        try:
            stats = self.db.get_stats()
            version_string = f"{stats.get('total_recipes', 0)}_{stats.get('total_ingredients', 0)}"
            return hashlib.md5(version_string.encode()).hexdigest()[:8]
        except:
            return 'v1'

    def _get_cache_path(self, name):
        """Get cache file path"""
        return self.cache_dir / f"{name}_{self.model_version}.pkl"

    def _load_from_cache(self, name):
        """Load model component from cache"""
        cache_path = self._get_cache_path(name)
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"Failed to load {name} from cache: {e}")
        return None

    def _save_to_cache(self, name, data):
        """Save model component to cache"""
        try:
            cache_path = self._get_cache_path(name)
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            print(f"Failed to save {name} to cache: {e}")

    def load_or_train(self):
        """Load models from cache or train new ones"""
        print("Checking for cached models...")

        # Try to load from cache
        self.recipes_df = self._load_from_cache('recipes_df')
        self.tfidf_matrix = self._load_from_cache('tfidf_matrix')
        self.content_vectorizer = self._load_from_cache('content_vectorizer')
        self.popularity_scores = self._load_from_cache('popularity_scores')
        self.ingredient_index = self._load_from_cache('ingredient_index') or {}
        self.ingredient_idf = self._load_from_cache('ingredient_idf') or {}
        self.favorites_map = self._load_from_cache('favorites_map') or {}

        if all([self.recipes_df is not None,
                self.tfidf_matrix is not None,
                self.content_vectorizer is not None]):
            print(f"Loaded models from cache (version {self.model_version})")
            print(f"Loaded {len(self.recipes_df)} recipes")
            return

        # Train new models
        print("Training new models...")
        self.train_models()

    def train_models(self):
        """Train all recommendation models"""
        print("Loading recipes from database...")
        limit = int(os.getenv('ML_MODEL_LIMIT', 10000))
        recipes = self.db.get_all_recipes(limit=limit)

        if not recipes:
            print("No recipes found in database!")
            return

        self.recipes_df = pd.DataFrame(recipes)
        print(f"Loaded {len(self.recipes_df)} recipes")

        # Train content-based model
        self._train_content_model()

        # Build ingredient index for fast matching & IDF coverage bonus
        self._build_ingredient_index()

        # Train collaborative filtering model (ratings + implicit favorites)
        self._train_collaborative_model()

        # Calculate popularity scores
        self._calculate_popularity()

        # Save to cache
        self._save_to_cache('recipes_df', self.recipes_df)
        self._save_to_cache('tfidf_matrix', self.tfidf_matrix)
        self._save_to_cache('content_vectorizer', self.content_vectorizer)
        self._save_to_cache('popularity_scores', self.popularity_scores)
        self._save_to_cache('ingredient_index', self.ingredient_index)
        self._save_to_cache('ingredient_idf', self.ingredient_idf)
        self._save_to_cache('favorites_map', self.favorites_map)

        print("Model training complete and cached!")

    def _train_content_model(self):
        """Train content-based filtering model"""
        print("Training content-based model...")

        # Enhanced feature engineering
        self.recipes_df['content_features'] = self.recipes_df.apply(
            lambda row: self._create_content_features(row),
            axis=1
        )

        # Train TF-IDF with optimized parameters
        self.content_vectorizer = TfidfVectorizer(
            max_features=8000,
            stop_words='english',
            ngram_range=(1, 3),
            min_df=2,
            max_df=0.8,
            sublinear_tf=True,
            norm='l2'
        )

        self.tfidf_matrix = self.content_vectorizer.fit_transform(
            self.recipes_df['content_features']
        )

        print(f"TF-IDF matrix shape: {self.tfidf_matrix.shape}")

    def _create_content_features(self, row):
        """Create enhanced content features for a recipe"""
        features = []

        # Recipe name (weighted higher)
        name = str(row.get('name', ''))
        features.append(name * 3)  # Weight name more

        # Ingredients
        ingredients = row.get('ingredients', [])
        features.append(' '.join(ingredients) * 2)  # Weight ingredients

        # Tags
        tags = row.get('tags', [])
        features.append(' '.join(tags))

        # Time bucket (more granular)
        minutes = row.get('minutes', 0)
        if minutes:
            if minutes <= 10:
                features.append('super_quick under_10_min fast express')
            elif minutes <= 20:
                features.append('quick fast under_20_min')
            elif minutes <= 30:
                features.append('medium_time half_hour')
            elif minutes <= 45:
                features.append('medium_long 45_min')
            elif minutes <= 60:
                features.append('long_cooking one_hour')
            elif minutes <= 120:
                features.append('very_long slow_cook two_hours')
            else:
                features.append('extra_long extended_cooking')

        # Calorie bucket
        calories = row.get('calories', None)
        if calories is not None and not pd.isna(calories):
            cal = float(calories)
            if cal <= 200:
                features.append('low_calorie light_meal diet_friendly')
            elif cal <= 400:
                features.append('moderate_calorie balanced_meal')
            elif cal <= 600:
                features.append('medium_calorie standard_meal')
            elif cal <= 800:
                features.append('high_calorie hearty_meal')
            else:
                features.append('very_high_calorie indulgent_meal')

        # Description
        description = str(row.get('description', ''))
        features.append(description)

        return ' '.join(features).lower()

    def _build_ingredient_index(self):
        """Build inverted ingredient index and IDF weights for fast matching & coverage bonus."""
        print("Building ingredient index...")
        import math
        N = len(self.recipes_df)
        word_to_indices = defaultdict(set)  # word -> set of df row indices

        # Pre-compute per-recipe lowercase ingredient lists
        ingredients_lower_col = []
        for idx in range(N):
            row = self.recipes_df.iloc[idx]
            ings = row.get('ingredients', [])
            ings_lower = [str(i).lower() for i in ings]
            ingredients_lower_col.append(ings_lower)
            for ing_str in ings_lower:
                for word in ing_str.split():
                    if len(word) > 2:  # skip tiny words
                        word_to_indices[word].add(idx)

        self.recipes_df['_ingredients_lower'] = ingredients_lower_col

        # Store the inverted index
        self.ingredient_index = {w: indices for w, indices in word_to_indices.items()}

        # IDF weights: rare ingredients get higher weight
        self.ingredient_idf = {}
        for word, indices in self.ingredient_index.items():
            df = len(indices)
            self.ingredient_idf[word] = math.log((N + 1) / (df + 1)) + 1.0  # smoothed IDF

        print(f"  Indexed {len(self.ingredient_index)} unique ingredient terms")

    def _train_collaborative_model(self):
        """Train collaborative filtering model using ratings + implicit favorites"""
        print("Training collaborative filtering model...")

        try:
            # Get explicit user ratings
            query = """
                SELECT user_id, recipe_id, rating
                FROM recipe_ratings
                LIMIT 50000
            """
            ratings = self.db.execute_query(query, fetch=True) or []

            # Get implicit favorites as positive signals (treated as rating 4.5)
            fav_query = """
                SELECT user_id, recipe_id, 4.5 as rating
                FROM user_favorites
                LIMIT 50000
            """
            favorites = self.db.execute_query(fav_query, fetch=True) or []

            # Build favorites_map for runtime use
            self.favorites_map = defaultdict(set)
            for fav in favorites:
                self.favorites_map[fav['user_id']].add(fav['recipe_id'])

            # Merge explicit + implicit signals
            all_signals = list(ratings) + list(favorites)

            if len(all_signals) < 10:
                print(f"Not enough signals for collaborative filtering "
                      f"(ratings={len(ratings)}, favorites={len(favorites)})")
                return

            # Create user-item matrix (explicit ratings override implicit)
            signals_df = pd.DataFrame(all_signals)
            # Ensure rating column is numeric (MySQL returns Decimal objects)
            signals_df['rating'] = pd.to_numeric(signals_df['rating'], errors='coerce').fillna(0).astype('float64')
            signals_df['user_id'] = signals_df['user_id'].astype(int)
            signals_df['recipe_id'] = signals_df['recipe_id'].astype(int)

            user_item = signals_df.pivot_table(
                index='user_id',
                columns='recipe_id',
                values='rating',
                aggfunc='max',  # if both rating & favorite exist, take max
                fill_value=0
            )

            # Convert to sparse matrix (ensure float64)
            self.user_item_matrix = csr_matrix(user_item.values.astype('float64'))

            # Apply SVD for dimensionality reduction
            n_components = min(50, min(self.user_item_matrix.shape) - 1)
            if n_components > 0:
                self.svd_model = TruncatedSVD(n_components=n_components, random_state=42)
                self.svd_model.fit(self.user_item_matrix)
                print(f"Collaborative filtering trained with {n_components} latent factors "
                      f"(ratings={len(ratings)}, favorites={len(favorites)})")

        except Exception as e:
            print(f"Collaborative filtering training failed: {e}")

    def _calculate_popularity(self):
        """Calculate popularity scores for recipes"""
        print("Calculating popularity scores...")

        try:
            # Get recipe statistics
            query = """
                SELECT
                    r.id,
                    COALESCE(COUNT(DISTINCT f.user_id), 0) as favorite_count,
                    COALESCE(AVG(rt.rating), 0) as avg_rating,
                    COALESCE(COUNT(DISTINCT rt.user_id), 0) as rating_count,
                    COALESCE(COUNT(DISTINCT c.user_id), 0) as comment_count
                FROM recipes r
                LEFT JOIN user_favorites f ON r.id = f.recipe_id
                LEFT JOIN recipe_ratings rt ON r.id = rt.recipe_id
                LEFT JOIN recipe_comments c ON r.id = c.recipe_id
                GROUP BY r.id
            """
            stats = self.db.execute_query(query, fetch=True)

            if stats:
                stats_df = pd.DataFrame(stats)

                # Convert Decimal to float (MySQL returns Decimals)
                stats_df['favorite_count'] = pd.to_numeric(stats_df['favorite_count'], errors='coerce').fillna(0)
                stats_df['avg_rating'] = pd.to_numeric(stats_df['avg_rating'], errors='coerce').fillna(0)
                stats_df['rating_count'] = pd.to_numeric(stats_df['rating_count'], errors='coerce').fillna(0)
                stats_df['comment_count'] = pd.to_numeric(stats_df['comment_count'], errors='coerce').fillna(0)

                # Normalize scores
                stats_df['popularity_score'] = (
                    stats_df['favorite_count'] * 0.4 +
                    stats_df['avg_rating'] * 10 * 0.3 +
                    stats_df['rating_count'] * 0.2 +
                    stats_df['comment_count'] * 0.1
                )

                # Normalize to 0-1 range
                if len(stats_df) > 0:
                    max_score = stats_df['popularity_score'].max()
                    if max_score > 0:
                        stats_df['popularity_score'] = stats_df['popularity_score'] / max_score

                self.popularity_scores = dict(zip(
                    stats_df['id'],
                    stats_df['popularity_score']
                ))
            else:
                self.popularity_scores = {}

        except Exception as e:
            print(f"Popularity calculation failed: {e}")
            self.popularity_scores = {}

    def recommend(self, ingredients, dietary_preference='', cuisine_type='',
                   user_id=None, limit=10, diversify=True):
        """
        Get hybrid recommendations

        Args:
            ingredients: List of available ingredients
            dietary_preference: Dietary preference filter
            cuisine_type: Cuisine type filter
            user_id: User ID for personalization
            limit: Number of recommendations
            diversify: Whether to diversify results

        Returns:
            List of recommendations with scores and explanations
        """
        if self.recipes_df is None or self.tfidf_matrix is None:
            print("Model not trained yet!")
            return []

        # Check cache
        cache_key = self._get_recommendation_cache_key(
            ingredients, dietary_preference, cuisine_type, user_id, limit
        )

        if cache_key in self.recommendation_cache:
            print("[CACHE HIT] Returning cached recommendations")
            return self.recommendation_cache[cache_key]

        # Get content-based scores
        content_scores = self._get_content_scores(
            ingredients, dietary_preference, cuisine_type
        )

        # Get collaborative scores
        collab_scores = self._get_collaborative_scores(user_id)

        # Get popularity scores
        pop_scores = self._get_popularity_scores()

        # Get IDF-weighted ingredient bonus scores (boosts rare-ingredient matches)
        ingredient_bonus_scores = self._get_ingredient_bonus_scores(ingredients)

        # Combine scores
        final_scores = self._combine_scores(
            content_scores, collab_scores, pop_scores, ingredient_bonus_scores
        )

        # Filter and rank
        recommendations = self._filter_and_rank(
            final_scores, ingredients, dietary_preference,
            cuisine_type, limit, diversify, content_scores
        )

        # Add explanations
        recommendations = self._add_explanations(
            recommendations, ingredients, content_scores
        )

        # Cache results
        if len(self.recommendation_cache) >= self.cache_maxsize:
            # Remove oldest entry
            self.recommendation_cache.pop(next(iter(self.recommendation_cache)))
        self.recommendation_cache[cache_key] = recommendations

        return recommendations

    def _get_recommendation_cache_key(self, ingredients, dietary_pref, cuisine, user_id, limit):
        """Generate cache key for recommendation"""
        key_str = f"{sorted(ingredients)}_{dietary_pref}_{cuisine}_{user_id}_{limit}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_content_scores(self, ingredients, dietary_preference, cuisine_type):
        """Get content-based similarity scores"""
        # Create query
        query_text = ' '.join(ingredients).lower()
        if dietary_preference:
            query_text += ' ' + dietary_preference.lower()
        if cuisine_type:
            query_text += ' ' + cuisine_type.lower()

        # Transform and calculate similarity
        query_vector = self.content_vectorizer.transform([query_text])
        similarity_scores = cosine_similarity(query_vector, self.tfidf_matrix).flatten()

        return dict(zip(
            self.recipes_df['id'].values,
            similarity_scores
        ))

    def _get_collaborative_scores(self, user_id):
        """Get collaborative filtering scores"""
        if user_id is None or self.svd_model is None:
            return {}

        # Placeholder for collaborative filtering
        # Would use user's rating history to generate scores
        return {}

    def _get_popularity_scores(self):
        """Get popularity scores"""
        return self.popularity_scores or {}

    def _get_ingredient_bonus_scores(self, ingredients):
        """Compute IDF-weighted ingredient match bonus for each recipe.

        Recipes that match rare (high-IDF) user ingredients get a bigger
        bonus, which helps surface niche recipes and improve coverage.
        """
        if not ingredients or not self.ingredient_index:
            return {}

        bonus = defaultdict(float)
        user_words = set()
        for ing in ingredients:
            for w in ing.lower().split():
                if len(w) > 2:
                    user_words.add(w)

        if not user_words:
            return {}

        # For each user-ingredient word, add its IDF weight to matching recipes
        for word in user_words:
            idf = self.ingredient_idf.get(word, 0)
            for idx in self.ingredient_index.get(word, set()):
                recipe_id = self.recipes_df.iloc[idx]['id']
                bonus[recipe_id] += idf

        # Normalise to 0-1 range
        if bonus:
            max_bonus = max(bonus.values())
            if max_bonus > 0:
                bonus = {rid: v / max_bonus for rid, v in bonus.items()}

        return dict(bonus)

    def _combine_scores(self, content_scores, collab_scores, pop_scores,
                        ingredient_bonus_scores=None):
        """Combine different scoring methods with dynamic re-weighting.

        When collaborative data is missing the content weight absorbs the
        collaborative budget so that popularity can never dominate.
        """
        ingredient_bonus_scores = ingredient_bonus_scores or {}
        final_scores = {}
        all_recipe_ids = set(content_scores.keys())

        # Dynamic weights: redistribute collab budget to content when empty
        w_content = self.weights['content']
        w_collab  = self.weights['collaborative']
        w_pop     = self.weights['popularity']
        w_bonus   = self.weights['ingredient_bonus']

        has_collab = bool(collab_scores)
        if not has_collab:
            # Give collab budget to content so popularity stays small
            w_content += w_collab
            w_collab = 0.0

        for recipe_id in all_recipe_ids:
            content = content_scores.get(recipe_id, 0)
            collab  = collab_scores.get(recipe_id, 0)
            pop     = pop_scores.get(recipe_id, 0)
            bonus   = ingredient_bonus_scores.get(recipe_id, 0)

            # Clamp popularity contribution – it should never rescue an
            # irrelevant recipe.  Cap pop boost at 50% of content score.
            max_pop_boost = content * 0.5
            effective_pop = min(pop, max_pop_boost) if content > 0 else 0.0

            final_score = (
                content * w_content +
                collab  * w_collab +
                effective_pop * w_pop +
                bonus   * w_bonus
            )

            final_scores[recipe_id] = final_score

        return final_scores

    def _filter_and_rank(self, scores, ingredients, dietary_pref,
                          cuisine, limit, diversify, content_scores=None):
        """Filter and rank recommendations with vectorized ingredient matching"""
        # Sort by score
        sorted_recipes = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        recommendations = []
        seen_ids = set()
        user_ingredients_lower = [ing.lower() for ing in ingredients]

        # Pre-build an id→index lookup for fast access
        id_to_idx = pd.Series(self.recipes_df.index, index=self.recipes_df['id'])

        # Check if pre-computed lowercase ingredients exist
        has_precomputed = '_ingredients_lower' in self.recipes_df.columns

        for recipe_id, score in sorted_recipes:
            if len(recommendations) >= limit * 3:  # Get extras for diversity
                break

            if recipe_id in seen_ids:
                continue

            # Get recipe details (fast lookup)
            if recipe_id not in id_to_idx.index:
                continue
            idx = id_to_idx[recipe_id]
            recipe = self.recipes_df.iloc[idx]

            # Apply filters
            if not self._passes_filters(recipe, dietary_pref, cuisine):
                continue

            # Vectorized ingredient matching using pre-computed lowercase lists
            if has_precomputed:
                recipe_ings_lower = recipe['_ingredients_lower']
            else:
                recipe_ings_lower = [str(i).lower() for i in recipe.get('ingredients', [])]

            # Build recipe word set once, then do O(1) lookups per user ingredient
            recipe_words = set()
            for ring in recipe_ings_lower:
                for w in ring.split():
                    recipe_words.add(w)

            # Count user ingredient matches via word-level set intersection
            matches = 0
            for user_ing in user_ingredients_lower:
                u_words = set(user_ing.split())
                if u_words & recipe_words:  # set intersection
                    matches += 1

            # TIGHTER GATE: require at least 1 ingredient match OR strong content sim
            content_sim = (content_scores or {}).get(recipe_id, 0)
            if matches == 0 and content_sim < 0.08:
                continue

            recommendations.append({
                'id': int(recipe_id),
                'name': recipe['name'],
                'minutes': int(recipe['minutes']) if recipe.get('minutes') else None,
                'ingredients': recipe.get('ingredients', []),
                'tags': recipe.get('tags', []),
                'image_url': recipe.get('image_url'),
                'score': float(score),
                'ingredient_matches': matches,
                'match_percentage': matches / len(ingredients) * 100 if ingredients else 0
            })
            seen_ids.add(recipe_id)

        # Sort by combined criteria: ingredient matches first, break ties with score
        recommendations.sort(
            key=lambda x: (x['ingredient_matches'], x['score']),
            reverse=True
        )

        # Apply diversity if requested
        if diversify:
            recommendations = self._diversify_recommendations(recommendations, limit)
        else:
            recommendations = recommendations[:limit]

        return recommendations

    def _passes_filters(self, recipe, dietary_pref, cuisine):
        """Check if recipe passes filters"""
        # Dietary preference filter
        if dietary_pref:
            tags_lower = [tag.lower() for tag in recipe.get('tags', [])]
            ingredients_lower = [ing.lower() for ing in recipe.get('ingredients', [])]
            combined_text = ' '.join(tags_lower + ingredients_lower + [recipe.get('name', '').lower()])

            dietary_keywords = {
                'vegetarian': ['vegetarian', 'veggie', 'vegetables', 'meatless'],
                'vegan': ['vegan', 'plant-based'],
                'low-carb': ['low carb', 'lowcarb', 'keto'],
                'keto': ['keto', 'ketogenic', 'low carb'],
                'gluten-free': ['gluten free', 'gluten-free'],
                'dairy-free': ['dairy free', 'dairy-free', 'non-dairy']
            }

            keywords = dietary_keywords.get(dietary_pref.lower(), [dietary_pref.lower()])
            if not any(keyword in combined_text for keyword in keywords):
                return False

        # Cuisine filter
        if cuisine:
            tags_lower = [tag.lower() for tag in recipe.get('tags', [])]
            combined_text = ' '.join(tags_lower + [recipe.get('name', '').lower()])
            if cuisine.lower() not in combined_text:
                return False

        return True

    def _diversify_recommendations(self, recommendations, limit):
        """Diversify recommendations using MMR (Maximal Marginal Relevance).

        Balances relevance and diversity.  Lambda=0.85 means we strongly
        prefer relevance and only gently push for diversity.
        """
        if len(recommendations) <= limit:
            return recommendations

        LAMBDA = 0.85  # Higher = more relevance, less diversity

        # Normalise scores for the MMR formula
        max_score = max(r['score'] for r in recommendations) or 1.0

        selected = [recommendations[0]]
        remaining = list(recommendations[1:])

        while len(selected) < limit and remaining:
            best_mmr = -1
            best_idx = 0

            for idx, candidate in enumerate(remaining):
                relevance = candidate['score'] / max_score

                max_sim = max(
                    1.0 - self._recipe_distance(candidate, sel)
                    for sel in selected
                )

                mmr_score = LAMBDA * relevance - (1 - LAMBDA) * max_sim

                if mmr_score > best_mmr:
                    best_mmr = mmr_score
                    best_idx = idx

            selected.append(remaining.pop(best_idx))

        return selected

    def _recipe_distance(self, recipe1, recipe2):
        """Calculate diversity distance between two recipes"""
        # Use ingredient overlap as distance metric
        ings1 = set(recipe1['ingredients'])
        ings2 = set(recipe2['ingredients'])

        if not ings1 or not ings2:
            return 1.0

        overlap = len(ings1 & ings2)
        total = len(ings1 | ings2)

        # Higher value = more different
        return 1.0 - (overlap / total if total > 0 else 0)

    def _add_explanations(self, recommendations, ingredients, content_scores):
        """Add explanation for each recommendation"""
        for rec in recommendations:
            explanation = []

            # Ingredient match explanation
            if rec['ingredient_matches'] > 0:
                explanation.append(
                    f"Uses {rec['ingredient_matches']} of your ingredients"
                )

            # High similarity explanation
            recipe_id = rec['id']
            if recipe_id in content_scores and content_scores[recipe_id] > 0.3:
                explanation.append("Highly relevant to your search")

            # Popularity explanation
            if self.popularity_scores and recipe_id in self.popularity_scores:
                if self.popularity_scores[recipe_id] > 0.7:
                    explanation.append("Popular choice")

            rec['explanation'] = ' • '.join(explanation) if explanation else None

        return recommendations

    def get_similar_recipes(self, recipe_id, limit=5):
        """Get similar recipes using content-based filtering"""
        if self.recipes_df is None or self.tfidf_matrix is None:
            return []

        # Find recipe index
        recipe_idx = self.recipes_df[self.recipes_df['id'] == recipe_id].index

        if len(recipe_idx) == 0:
            return []

        recipe_idx = recipe_idx[0]

        # Get recipe vector
        recipe_vector = self.tfidf_matrix[recipe_idx]

        # Calculate similarity
        similarity_scores = cosine_similarity(recipe_vector, self.tfidf_matrix).flatten()

        # Get top indices (excluding the recipe itself)
        top_indices = similarity_scores.argsort()[::-1][1:limit+1]

        # Format results
        recommendations = []
        for idx in top_indices:
            recipe = self.recipes_df.iloc[idx]
            recommendations.append({
                'id': int(recipe['id']),
                'name': recipe['name'],
                'minutes': int(recipe['minutes']) if recipe['minutes'] else None,
                'ingredients': recipe.get('ingredients', []),
                'tags': recipe.get('tags', []),
                'image_url': recipe.get('image_url'),
                'similarity_score': float(similarity_scores[idx])
            })

        return recommendations

    def invalidate_cache(self):
        """Invalidate all caches"""
        self.recommendation_cache.clear()
        print("Recommendation cache cleared")
