"""
Nutrition Estimator
Provides estimated nutrition information based on ingredients
"""

class NutritionEstimator:
    """Estimate nutrition values based on common ingredients"""
    
    # Approximate nutritional values per 100g for common ingredients
    NUTRITION_DATA = {
        # Proteins
        'chicken': {'calories': 165, 'protein': 31, 'fat': 3.6, 'carbs': 0, 'sodium': 82},
        'beef': {'calories': 250, 'protein': 26, 'fat': 15, 'carbs': 0, 'sodium': 72},
        'pork': {'calories': 242, 'protein': 27, 'fat': 14, 'carbs': 0, 'sodium': 62},
        'fish': {'calories': 206, 'protein': 22, 'fat': 12, 'carbs': 0, 'sodium': 90},
        'salmon': {'calories': 208, 'protein': 20, 'fat': 13, 'carbs': 0, 'sodium': 59},
        'tuna': {'calories': 130, 'protein': 28, 'fat': 1, 'carbs': 0, 'sodium': 50},
        'shrimp': {'calories': 99, 'protein': 24, 'fat': 0.3, 'carbs': 0.2, 'sodium': 111},
        'egg': {'calories': 155, 'protein': 13, 'fat': 11, 'carbs': 1.1, 'sodium': 124},
        'turkey': {'calories': 135, 'protein': 30, 'fat': 1, 'carbs': 0, 'sodium': 70},
        
        # Dairy
        'milk': {'calories': 42, 'protein': 3.4, 'fat': 1, 'carbs': 5, 'sodium': 44},
        'cheese': {'calories': 402, 'protein': 25, 'fat': 33, 'carbs': 1.3, 'sodium': 621},
        'butter': {'calories': 717, 'protein': 0.85, 'fat': 81, 'carbs': 0.06, 'sodium': 11},
        'cream': {'calories': 340, 'protein': 2.1, 'fat': 37, 'carbs': 2.8, 'sodium': 38},
        'yogurt': {'calories': 59, 'protein': 10, 'fat': 0.4, 'carbs': 3.6, 'sodium': 36},
        
        # Grains & Carbs
        'rice': {'calories': 130, 'protein': 2.7, 'fat': 0.3, 'carbs': 28, 'sodium': 1},
        'pasta': {'calories': 131, 'protein': 5, 'fat': 1.1, 'carbs': 25, 'sodium': 1},
        'bread': {'calories': 265, 'protein': 9, 'fat': 3.2, 'carbs': 49, 'sodium': 491},
        'flour': {'calories': 364, 'protein': 10, 'fat': 1, 'carbs': 76, 'sodium': 2},
        'oats': {'calories': 389, 'protein': 17, 'fat': 7, 'carbs': 66, 'sodium': 2},
        'quinoa': {'calories': 120, 'protein': 4.4, 'fat': 1.9, 'carbs': 21, 'sodium': 7},
        
        # Vegetables
        'tomato': {'calories': 18, 'protein': 0.9, 'fat': 0.2, 'carbs': 3.9, 'sodium': 5},
        'onion': {'calories': 40, 'protein': 1.1, 'fat': 0.1, 'carbs': 9.3, 'sodium': 4},
        'garlic': {'calories': 149, 'protein': 6.4, 'fat': 0.5, 'carbs': 33, 'sodium': 17},
        'potato': {'calories': 77, 'protein': 2, 'fat': 0.1, 'carbs': 17, 'sodium': 6},
        'carrot': {'calories': 41, 'protein': 0.9, 'fat': 0.2, 'carbs': 10, 'sodium': 69},
        'broccoli': {'calories': 34, 'protein': 2.8, 'fat': 0.4, 'carbs': 7, 'sodium': 33},
        'spinach': {'calories': 23, 'protein': 2.9, 'fat': 0.4, 'carbs': 3.6, 'sodium': 79},
        'pepper': {'calories': 20, 'protein': 0.9, 'fat': 0.2, 'carbs': 4.6, 'sodium': 3},
        'mushroom': {'calories': 22, 'protein': 3.1, 'fat': 0.3, 'carbs': 3.3, 'sodium': 5},
        'lettuce': {'calories': 15, 'protein': 1.4, 'fat': 0.2, 'carbs': 2.9, 'sodium': 28},
        
        # Fruits
        'apple': {'calories': 52, 'protein': 0.3, 'fat': 0.2, 'carbs': 14, 'sodium': 1},
        'banana': {'calories': 89, 'protein': 1.1, 'fat': 0.3, 'carbs': 23, 'sodium': 1},
        'orange': {'calories': 47, 'protein': 0.9, 'fat': 0.1, 'carbs': 12, 'sodium': 0},
        'lemon': {'calories': 29, 'protein': 1.1, 'fat': 0.3, 'carbs': 9, 'sodium': 2},
        'strawberry': {'calories': 32, 'protein': 0.7, 'fat': 0.3, 'carbs': 8, 'sodium': 1},
        
        # Oils & Fats
        'oil': {'calories': 884, 'protein': 0, 'fat': 100, 'carbs': 0, 'sodium': 0},
        'olive oil': {'calories': 884, 'protein': 0, 'fat': 100, 'carbs': 0, 'sodium': 2},
        
        # Sugars & Sweeteners
        'sugar': {'calories': 387, 'protein': 0, 'fat': 0, 'carbs': 100, 'sodium': 1},
        'honey': {'calories': 304, 'protein': 0.3, 'fat': 0, 'carbs': 82, 'sodium': 4},
        
        # Nuts & Seeds
        'almond': {'calories': 579, 'protein': 21, 'fat': 50, 'carbs': 22, 'sodium': 1},
        'peanut': {'calories': 567, 'protein': 26, 'fat': 49, 'carbs': 16, 'sodium': 18},
        'walnut': {'calories': 654, 'protein': 15, 'fat': 65, 'carbs': 14, 'sodium': 2},
        
        # Beans & Legumes
        'bean': {'calories': 127, 'protein': 8.7, 'fat': 0.5, 'carbs': 23, 'sodium': 2},
        'lentil': {'calories': 116, 'protein': 9, 'fat': 0.4, 'carbs': 20, 'sodium': 2},
        'chickpea': {'calories': 164, 'protein': 8.9, 'fat': 2.6, 'carbs': 27, 'sodium': 7},
    }
    
    def estimate_nutrition(self, ingredients, servings=4):
        """
        Estimate nutrition based on ingredient list
        
        Args:
            ingredients: List of ingredient strings
            servings: Number of servings (default 4)
            
        Returns:
            Dictionary with estimated nutrition per serving
        """
        total_nutrition = {
            'calories': 0,
            'protein': 0,
            'fat': 0,
            'carbs': 0,
            'sodium': 0
        }
        
        matched_count = 0
        
        for ingredient in ingredients:
            ingredient_lower = ingredient.lower()
            
            # Try to match ingredient with nutrition data
            for key, nutrition in self.NUTRITION_DATA.items():
                if key in ingredient_lower:
                    # Estimate portion: assume 100g per ingredient mention
                    total_nutrition['calories'] += nutrition['calories']
                    total_nutrition['protein'] += nutrition['protein']
                    total_nutrition['fat'] += nutrition['fat']
                    total_nutrition['carbs'] += nutrition['carbs']
                    total_nutrition['sodium'] += nutrition['sodium']
                    matched_count += 1
                    break
        
        # If we matched at least one ingredient, calculate per serving
        if matched_count > 0:
            return {
                'calories': round(total_nutrition['calories'] / servings, 1),
                'protein': round(total_nutrition['protein'] / servings, 1),
                'total_fat': round(total_nutrition['fat'] / servings, 1),
                'carbohydrates': round(total_nutrition['carbs'] / servings, 1),
                'sodium': round(total_nutrition['sodium'] / servings, 1),
                'sugar': round(total_nutrition['carbs'] * 0.1 / servings, 1)  # Rough estimate
            }
        
        return None
