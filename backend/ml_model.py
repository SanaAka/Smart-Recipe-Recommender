import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import os
import math
from collections import defaultdict

# ── Ingredient-based dietary exclusion lists ─────────────────────────
# Instead of relying on rare tags, we determine dietary suitability
# by checking whether a recipe's ingredients contain excluded items.
_MEAT_FISH = {
    'chicken', 'beef', 'pork', 'lamb', 'turkey', 'bacon', 'ham', 'sausage',
    'steak', 'veal', 'duck', 'venison', 'salami', 'pepperoni', 'prosciutto',
    'chorizo', 'meatball', 'meat', 'rib', 'ribs', 'brisket', 'roast',
    'anchovy', 'anchovies', 'fish', 'shrimp', 'salmon', 'tuna', 'crab',
    'lobster', 'clam', 'clams', 'mussel', 'mussels', 'oyster', 'oysters',
    'scallop', 'scallops', 'cod', 'tilapia', 'halibut', 'sardine', 'sardines',
    'mackerel', 'trout', 'catfish', 'squid', 'calamari', 'prawn', 'prawns',
    'octopus', 'crawfish', 'crayfish',
}

_DAIRY_EGG = {
    'egg', 'eggs', 'milk', 'cream', 'butter', 'cheese', 'yogurt', 'yoghurt',
    'whey', 'casein', 'ghee', 'lard', 'gelatin', 'honey',
    'sour cream', 'buttermilk', 'half-and-half', 'whipped cream',
    'cream cheese', 'ricotta', 'mozzarella', 'parmesan', 'cheddar',
    'mascarpone', 'brie', 'gouda', 'feta',
}

_GLUTEN = {
    'flour', 'bread', 'pasta', 'wheat', 'barley', 'rye', 'couscous',
    'cracker', 'crackers', 'breadcrumb', 'breadcrumbs', 'tortilla',
    'noodle', 'noodles', 'spaghetti', 'penne', 'macaroni', 'fettuccine',
    'linguine', 'lasagna', 'biscuit', 'pastry', 'cake', 'pie crust',
    'dough', 'cereal', 'panko', 'orzo', 'ravioli', 'dumpling',
    'wonton', 'pita', 'croissant', 'bagel', 'muffin', 'pretzel',
    'sourdough', 'brioche', 'focaccia',
}

_HIGH_CARB = {
    'sugar', 'flour', 'bread', 'pasta', 'rice', 'potato', 'potatoes',
    'corn', 'cereal', 'oat', 'oats', 'honey', 'syrup', 'molasses',
    'jam', 'jelly', 'noodle', 'noodles', 'tortilla', 'couscous',
    'cornstarch', 'candy', 'chocolate', 'marshmallow', 'cake',
    'banana', 'mango', 'grape', 'grapes', 'raisin', 'raisins',
    'date', 'dates', 'pineapple', 'sweet potato',
}

# Build lookup: diet key → set of excluded ingredient words
_DIET_EXCLUSIONS = {
    'vegetarian': _MEAT_FISH,
    'vegan':      _MEAT_FISH | _DAIRY_EGG,
    'keto':       _HIGH_CARB,
    'low-carb':   _HIGH_CARB,
    'gluten-free': _GLUTEN,
    'dairy-free':  _DAIRY_EGG,
}


def _recipe_matches_diet(diet_key, ingredient_words):
    """Return True if the recipe is compatible with the given diet.
    
    Uses ingredient-based exclusion: if any excluded word appears in the
    recipe's ingredient word set, the recipe is NOT compatible.
    """
    exclusions = _DIET_EXCLUSIONS.get(diet_key)
    if exclusions is None:
        return True  # unknown diet → no filtering
    return not bool(ingredient_words & exclusions)

class RecipeRecommender:
    def __init__(self, database):
        self.db = database
        self.recipes_df = None
        self.tfidf_matrix = None
        self.vectorizer = None
        self.ingredient_index = {}   # word -> set of df indices
        self.ingredient_idf = {}     # word -> IDF weight
        self.load_and_train()

    def load_and_train(self):
        """Load recipes and train the content-based filtering model"""
        print("Loading recipes from database...")
        limit = int(os.getenv('ML_MODEL_LIMIT', 5000))
        recipes = self.db.get_all_recipes(limit=limit)
        
        if not recipes:
            print("No recipes found in database!")
            return
        
        self.recipes_df = pd.DataFrame(recipes)
        
        # Create combined text features for TF-IDF
        # Weight ingredients more heavily (repeat x2) since they are the
        # primary signal for a recipe recommender.  Name is also boosted.
        self.recipes_df['combined_features'] = self.recipes_df.apply(
            lambda row: self._build_features(row),
            axis=1
        )

        # Pre-compute lowercase ingredient lists and inverted index
        self._build_ingredient_index()
        
        # Train TF-IDF vectorizer with improved parameters
        print("Training TF-IDF model...")
        self.vectorizer = TfidfVectorizer(
            max_features=10000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.85,
            sublinear_tf=True,
            norm='l2',
        )
        
        self.tfidf_matrix = self.vectorizer.fit_transform(
            self.recipes_df['combined_features']
        )
        
        print(f"Model trained on {len(self.recipes_df)} recipes")

    def _build_features(self, row):
        """Build enhanced content features for a recipe"""
        parts = []
        # Name x2
        name = str(row.get('name', ''))
        parts.append(name + ' ' + name)

        # Ingredients x2
        ings = ' '.join(row.get('ingredients', []))
        parts.append(ings + ' ' + ings)

        # Tags
        parts.append(' '.join(row.get('tags', [])))

        # Time bucket (more granular)
        minutes = row.get('minutes', 0)
        if minutes:
            if minutes <= 10:
                parts.append('super_quick under_10_min fast')
            elif minutes <= 20:
                parts.append('quick fast under_20_min')
            elif minutes <= 30:
                parts.append('medium_time half_hour')
            elif minutes <= 60:
                parts.append('long_cooking one_hour')
            else:
                parts.append('very_long slow_cook')

        # Calorie bucket
        calories = row.get('calories', None)
        if calories is not None and not pd.isna(calories):
            cal = float(calories)
            if cal <= 200:
                parts.append('low_calorie light_meal')
            elif cal <= 400:
                parts.append('moderate_calorie balanced_meal')
            elif cal <= 600:
                parts.append('medium_calorie standard_meal')
            elif cal <= 800:
                parts.append('high_calorie hearty_meal')
            else:
                parts.append('very_high_calorie indulgent_meal')

        return ' '.join(parts).lower()

    def _build_ingredient_index(self):
        """Build inverted ingredient word index and IDF weights."""
        N = len(self.recipes_df)
        word_to_indices = defaultdict(set)
        ingredients_lower_col = []

        for idx in range(N):
            row = self.recipes_df.iloc[idx]
            ings = row.get('ingredients', [])
            ings_lower = [str(i).lower() for i in ings]
            ingredients_lower_col.append(ings_lower)
            for ing_str in ings_lower:
                for word in ing_str.split():
                    if len(word) > 2:
                        word_to_indices[word].add(idx)

        self.recipes_df['_ingredients_lower'] = ingredients_lower_col
        self.ingredient_index = dict(word_to_indices)

        # IDF: rare ingredients get higher weight
        self.ingredient_idf = {}
        for word, indices in self.ingredient_index.items():
            df = len(indices)
            self.ingredient_idf[word] = math.log((N + 1) / (df + 1)) + 1.0

    def recommend(self, ingredients, dietary_preference='', cuisine_type='', limit=10):
        """
        Get recipe recommendations based on content-based filtering
        
        Args:
            ingredients: List of available ingredients
            dietary_preference: Dietary preference filter (vegetarian, vegan, etc.)
            cuisine_type: Cuisine type filter
            limit: Number of recommendations to return
        """
        if self.recipes_df is None or self.tfidf_matrix is None:
            print("Model not trained yet!")
            return []

        # Create query from user ingredients only.
        # Dietary/cuisine preferences are handled as hard filters later,
        # not as TF-IDF query terms (they would bias similarity scores).
        query_text = ' '.join(ingredients).lower()

        # Transform query using trained vectorizer
        query_vector = self.vectorizer.transform([query_text])

        # Calculate cosine similarity
        similarity_scores = cosine_similarity(query_vector, self.tfidf_matrix).flatten()

        # Pre-compute user ingredient word set
        user_words = set()
        for ing in ingredients:
            for w in ing.lower().split():
                if len(w) > 2:
                    user_words.add(w)

        # Compute IDF ingredient bonus per recipe (for coverage)
        idf_bonus = {}
        for word in user_words:
            idf_w = self.ingredient_idf.get(word, 0)
            for idx in self.ingredient_index.get(word, set()):
                rid = int(self.recipes_df.iloc[idx]['id'])
                idf_bonus[rid] = idf_bonus.get(rid, 0) + idf_w
        # Normalise
        if idf_bonus:
            max_b = max(idf_bonus.values())
            if max_b > 0:
                idf_bonus = {k: v / max_b for k, v in idf_bonus.items()}

        has_precomputed = '_ingredients_lower' in self.recipes_df.columns

        # --- Detect "zero similarity" case (common ingredients removed by max_df) ---
        max_sim = float(similarity_scores.max()) if len(similarity_scores) > 0 else 0

        # If TF-IDF gives us nothing useful, fall back to ingredient-index based
        # candidate selection so we don't iterate over the entire recipe set.
        if max_sim < 0.01 and user_words:
            # Gather candidate indices from the inverted ingredient index
            candidate_indices = set()
            for word in user_words:
                candidate_indices.update(self.ingredient_index.get(word, set()))

            # Sort candidates by how many user-ingredient words they contain
            def _count_matches(idx):
                if has_precomputed:
                    recipe_ings = self.recipes_df.iloc[idx]['_ingredients_lower']
                else:
                    recipe_ings = [i.lower() for i in self.recipes_df.iloc[idx].get('ingredients', [])]
                recipe_words = set()
                for ring in recipe_ings:
                    for w in ring.split():
                        recipe_words.add(w)
                return len(user_words & recipe_words)

            top_indices = sorted(candidate_indices, key=_count_matches, reverse=True)
        else:
            top_indices = similarity_scores.argsort()[::-1]

        # Filter results
        recommendations = []
        seen_ids = set()

        for idx in top_indices:
            if len(recommendations) >= limit:
                break

            recipe = self.recipes_df.iloc[idx]
            recipe_id = int(recipe['id'])

            # Skip duplicates
            if recipe_id in seen_ids:
                continue

            # Filter by dietary preference (ingredient-based exclusion)
            if dietary_preference:
                # Get ingredient words for this recipe
                if has_precomputed:
                    recipe_ings_list = recipe['_ingredients_lower']
                else:
                    recipe_ings_list = [ing.lower() for ing in recipe.get('ingredients', [])]
                
                ing_words = set()
                for ring in recipe_ings_list:
                    for w in ring.split():
                        if len(w) > 1:
                            ing_words.add(w)
                
                diet_key = dietary_preference.lower()
                if not _recipe_matches_diet(diet_key, ing_words):
                    continue

            # Filter by cuisine type (tag-based, always applied)
            if cuisine_type:
                tags_lower = [tag.lower() for tag in recipe.get('tags', [])]
                combined_text = ' '.join(tags_lower + [recipe.get('name', '').lower()])
                if cuisine_type.lower() not in combined_text:
                    continue

            # Check ingredient match using pre-computed sets (vectorized)
            if has_precomputed:
                recipe_ings = recipe['_ingredients_lower']
            else:
                recipe_ings = [ing.lower() for ing in recipe.get('ingredients', [])]

            recipe_words = set()
            for ring in recipe_ings:
                for w in ring.split():
                    recipe_words.add(w)

            matches = 0
            for user_ing in [ing.lower() for ing in ingredients]:
                u_words = set(user_ing.split())
                if u_words & recipe_words:
                    matches += 1

            # TIGHTER GATE: require ingredient match or strong similarity
            # In fallback mode (max_sim near 0), candidates were already pre-filtered
            # via the ingredient index, so always accept them.
            if matches > 0 or similarity_scores[idx] > 0.15 or max_sim < 0.01:
                # Add IDF bonus to the sort score (10% weight)
                bonus = idf_bonus.get(recipe_id, 0)
                recommendations.append({
                    'id': recipe_id,
                    'name': recipe['name'],
                    'minutes': int(recipe['minutes']) if recipe.get('minutes') else None,
                    'ingredients': recipe.get('ingredients', []),
                    'tags': recipe.get('tags', []),
                    'similarity_score': float(similarity_scores[idx]),
                    'ingredient_matches': matches,
                    '_idf_bonus': bonus
                })
                seen_ids.add(recipe_id)

        # Sort by weighted combination: matches + similarity + IDF bonus
        recommendations.sort(
            key=lambda x: (x['ingredient_matches'] * 2.0 + x['similarity_score'] + x['_idf_bonus'] * 0.3),
            reverse=True
        )

        # Remove internal field
        for r in recommendations:
            r.pop('_idf_bonus', None)

        return recommendations

    def get_similar_recipes(self, recipe_id, limit=5):
        """Get similar recipes to a given recipe"""
        if self.recipes_df is None or self.tfidf_matrix is None:
            return []

        # Find recipe index
        recipe_idx = self.recipes_df[self.recipes_df['id'] == recipe_id].index
        
        if len(recipe_idx) == 0:
            return []

        recipe_idx = recipe_idx[0]

        # Get recipe vector
        recipe_vector = self.tfidf_matrix[recipe_idx]

        # Calculate similarity with all recipes
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
                'calories': float(recipe['calories']) if recipe['calories'] else None,
                'similarity_score': float(similarity_scores[idx])
            })

        return recommendations
