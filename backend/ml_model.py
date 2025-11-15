import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import os

class RecipeRecommender:
    def __init__(self, database):
        self.db = database
        self.recipes_df = None
        self.tfidf_matrix = None
        self.vectorizer = None
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
        self.recipes_df['combined_features'] = self.recipes_df.apply(
            lambda row: ' '.join([
                str(row.get('name', '')),
                ' '.join(row.get('ingredients', [])),
                ' '.join(row.get('tags', []))
            ]).lower(),
            axis=1
        )
        
        # Train TF-IDF vectorizer
        print("Training TF-IDF model...")
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        self.tfidf_matrix = self.vectorizer.fit_transform(
            self.recipes_df['combined_features']
        )
        
        print(f"Model trained on {len(self.recipes_df)} recipes")

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

        # Create query from user input
        query_text = ' '.join(ingredients).lower()
        if dietary_preference:
            query_text += ' ' + dietary_preference.lower()
        if cuisine_type:
            query_text += ' ' + cuisine_type.lower()

        # Transform query using trained vectorizer
        query_vector = self.vectorizer.transform([query_text])

        # Calculate cosine similarity
        similarity_scores = cosine_similarity(query_vector, self.tfidf_matrix).flatten()

        # Get top recipe indices
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

            # Filter by dietary preference (more flexible matching)
            if dietary_preference:
                tags_lower = [tag.lower() for tag in recipe.get('tags', [])]
                ingredients_lower = [ing.lower() for ing in recipe.get('ingredients', [])]
                combined_text = ' '.join(tags_lower + ingredients_lower + [recipe.get('name', '').lower()])
                
                # Dietary preference mapping for flexible matching
                dietary_keywords = {
                    'vegetarian': ['vegetarian', 'veggie', 'vegetables', 'meatless'],
                    'vegan': ['vegan', 'plant-based'],
                    'low-carb': ['low carb', 'lowcarb', 'keto', 'atkins'],
                    'keto': ['keto', 'ketogenic', 'low carb'],
                    'gluten-free': ['gluten free', 'gluten-free', 'glutenfree'],
                    'dairy-free': ['dairy free', 'dairy-free', 'non-dairy', 'lactose free']
                }
                
                diet_key = dietary_preference.lower()
                keywords = dietary_keywords.get(diet_key, [diet_key])
                
                # Skip if dietary preference is specified but recipe doesn't match
                # However, be lenient - if similarity is very high, include it anyway
                if similarity_scores[idx] < 0.2:  # Only filter if similarity is low
                    has_match = any(keyword in combined_text for keyword in keywords)
                    if not has_match:
                        continue

            # Filter by cuisine type (more flexible matching)
            if cuisine_type:
                tags_lower = [tag.lower() for tag in recipe.get('tags', [])]
                combined_text = ' '.join(tags_lower + [recipe.get('name', '').lower()])
                
                # Only apply strict filtering if similarity is low
                if similarity_scores[idx] < 0.15:
                    if cuisine_type.lower() not in combined_text:
                        continue

            # Check ingredient match
            recipe_ingredients = [ing.lower() for ing in recipe.get('ingredients', [])]
            user_ingredients = [ing.lower() for ing in ingredients]
            
            # Calculate ingredient match percentage
            matches = sum(1 for user_ing in user_ingredients 
                         if any(user_ing in recipe_ing for recipe_ing in recipe_ingredients))
            
            # Only include if at least one ingredient matches or similarity is high
            if matches > 0 or similarity_scores[idx] > 0.1:
                recommendations.append({
                    'id': recipe_id,
                    'name': recipe['name'],
                    'minutes': int(recipe['minutes']) if recipe.get('minutes') else None,
                    'ingredients': recipe.get('ingredients', []),
                    'tags': recipe.get('tags', []),
                    'similarity_score': float(similarity_scores[idx]),
                    'ingredient_matches': matches
                })
                seen_ids.add(recipe_id)

        # Sort by ingredient matches and similarity score
        recommendations.sort(
            key=lambda x: (x['ingredient_matches'], x['similarity_score']),
            reverse=True
        )

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
