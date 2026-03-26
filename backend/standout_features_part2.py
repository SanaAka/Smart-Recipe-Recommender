"""
Continuation of 8 Unique Standout Features
Part 2: Nutrition Goals, Difficulty Predictor, Wine Pairing, Leftover Transformer, AI Coach
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import re

# This will be merged with standout_features.py

# ============================================================================
# 4. NUTRITION GOALS TRACKER - Daily/weekly nutrition monitoring
# ============================================================================

@jwt_required()
def get_nutrition_goals():
    """Get user's nutrition goals"""
    try:
        username = get_jwt_identity()
        user = auth_manager.get_user_by_username(username)
        
        query = """
            SELECT * FROM nutrition_goals
            WHERE user_id = %s AND is_active = 1
            ORDER BY created_at DESC
            LIMIT 1
        """
        
        goal = db.execute_query(query, (user['id'],), fetch=True)
        
        if not goal:
            return jsonify({'goal': None, 'message': 'No active nutrition goal found'})
        
        return jsonify({'goal': goal[0]})
        
    except Exception as e:
        logger.error(f"Get nutrition goals error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get goals', 'code': 'INTERNAL_ERROR'}), 500


@jwt_required()
def set_nutrition_goal():
    """Set or update nutrition goal"""
    try:
        username = get_jwt_identity()
        user = auth_manager.get_user_by_username(username)
        
        data = request.get_json()
        
        # Deactivate existing goals
        db.execute_query(
            "UPDATE nutrition_goals SET is_active = 0 WHERE user_id = %s",
            (user['id'],)
        )
        
        # Create new goal
        query = """
            INSERT INTO nutrition_goals 
            (user_id, goal_type, target_calories, target_protein, target_carbs, 
             target_fat, target_fiber, start_date, end_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        db.execute_query(query, (
            user['id'],
            data.get('goal_type', 'daily'),
            data.get('target_calories'),
            data.get('target_protein'),
            data.get('target_carbs'),
            data.get('target_fat'),
            data.get('target_fiber'),
            data.get('start_date', datetime.now().date()),
            data.get('end_date')
        ))
        
        return jsonify({'success': True, 'message': 'Nutrition goal set'}), 201
        
    except Exception as e:
        logger.error(f"Set nutrition goal error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to set goal', 'code': 'INTERNAL_ERROR'}), 500


@jwt_required()
def log_nutrition():
    """Log nutrition intake for a meal"""
    try:
        username = get_jwt_identity()
        user = auth_manager.get_user_by_username(username)
        
        data = request.get_json()
        
        query = """
            INSERT INTO nutrition_logs 
            (user_id, recipe_id, meal_type, calories, protein, carbs, fat, fiber, logged_date, serving_size)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        db.execute_query(query, (
            user['id'],
            data.get('recipe_id'),
            data.get('meal_type', 'lunch'),
            data.get('calories'),
            data.get('protein'),
            data.get('carbs'),
            data.get('fat'),
            data.get('fiber'),
            data.get('logged_date', datetime.now().date()),
            data.get('serving_size', 1.0)
        ))
        
        return jsonify({'success': True, 'message': 'Nutrition logged'}), 201
        
    except Exception as e:
        logger.error(f"Log nutrition error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to log nutrition', 'code': 'INTERNAL_ERROR'}), 500


@jwt_required()
def get_nutrition_progress():
    """Get nutrition progress for a date or date range"""
    try:
        username = get_jwt_identity()
        user = auth_manager.get_user_by_username(username)
        
        date = request.args.get('date', datetime.now().date())
        period = request.args.get('period', 'daily')  # daily or weekly
        
        if period == 'weekly':
            start_date = datetime.strptime(str(date), '%Y-%m-%d').date() - timedelta(days=7)
            end_date = date
        else:
            start_date = end_date = date
        
        # Get logs for the period
        logs_query = """
            SELECT 
                COALESCE(SUM(calories), 0) as total_calories,
                COALESCE(SUM(protein), 0) as total_protein,
                COALESCE(SUM(carbs), 0) as total_carbs,
                COALESCE(SUM(fat), 0) as total_fat,
                COALESCE(SUM(fiber), 0) as total_fiber
            FROM nutrition_logs
            WHERE user_id = %s AND logged_date BETWEEN %s AND %s
        """
        
        totals = db.execute_query(logs_query, (user['id'], start_date, end_date), fetch=True)
        
        # Get active goal
        goal_query = "SELECT * FROM nutrition_goals WHERE user_id = %s AND is_active = 1 LIMIT 1"
        goal = db.execute_query(goal_query, (user['id'],), fetch=True)
        
        if not totals or not goal:
            return jsonify({'progress': None, 'message': 'No data found'})
        
        totals = totals[0]
        goal = goal[0]
        
        # Calculate progress percentages
        progress = {
            'period': period,
            'start_date': str(start_date),
            'end_date': str(end_date),
            'consumed': {
                'calories': float(totals['total_calories'] or 0),
                'protein': float(totals['total_protein'] or 0),
                'carbs': float(totals['total_carbs'] or 0),
                'fat': float(totals['total_fat'] or 0),
                'fiber': float(totals['total_fiber'] or 0)
            },
            'target': {
                'calories': float(goal['target_calories'] or 0),
                'protein': float(goal['target_protein'] or 0),
                'carbs': float(goal['target_carbs'] or 0),
                'fat': float(goal['target_fat'] or 0),
                'fiber': float(goal['target_fiber'] or 0)
            },
            'progress_percentage': {}
        }
        
        # Calculate percentages
        for nutrient in ['calories', 'protein', 'carbs', 'fat', 'fiber']:
            target = progress['target'][nutrient]
            if target > 0:
                progress['progress_percentage'][nutrient] = round(
                    (progress['consumed'][nutrient] / target) * 100, 1
                )
            else:
                progress['progress_percentage'][nutrient] = 0
        
        return jsonify({'progress': progress})
        
    except Exception as e:
        logger.error(f"Get nutrition progress error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get progress', 'code': 'INTERNAL_ERROR'}), 500


# ============================================================================
# 5. RECIPE DIFFICULTY PREDICTOR - ML-based skill matching
# ============================================================================

def calculate_recipe_difficulty(recipe):
    """Calculate difficulty score based on recipe attributes"""
    score = 0
    
    # Cooking time factor (0-30 points)
    cook_time = recipe.get('cook_time_minutes', 30)
    if cook_time > 120:
        score += 30
    elif cook_time > 60:
        score += 20
    elif cook_time > 30:
        score += 10
    
    # Number of ingredients (0-25 points)
    num_ingredients = len(recipe.get('ingredients', []))
    if num_ingredients > 15:
        score += 25
    elif num_ingredients > 10:
        score += 15
    elif num_ingredients > 5:
        score += 10
    
    # Number of steps (0-25 points)
    num_steps = len(recipe.get('instructions', []))
    if num_steps > 10:
        score += 25
    elif num_steps > 7:
        score += 15
    elif num_steps > 4:
        score += 10
    
    # Technique complexity (0-20 points)
    complex_techniques = ['sauté', 'braise', 'deglaze', 'emulsify', 'fold', 'blanch', 
                          'flambe', 'julienne', 'sous vide', 'tempering']
    instructions_text = ' '.join(recipe.get('instructions', [])).lower()
    
    technique_count = sum(1 for tech in complex_techniques if tech in instructions_text)
    score += min(technique_count * 5, 20)
    
    # Determine difficulty level
    if score >= 70:
        return 'expert', score
    elif score >= 50:
        return 'advanced', score
    elif score >= 30:
        return 'intermediate', score
    else:
        return 'beginner', score


@jwt_required()
def get_recipe_difficulty(recipe_id):
    """Get or calculate recipe difficulty"""
    try:
        # Check if difficulty already calculated
        query = "SELECT * FROM recipe_difficulty WHERE recipe_id = %s"
        existing = db.execute_query(query, (recipe_id,), fetch=True)
        
        if existing:
            return jsonify({'difficulty': existing[0]})
        
        # Calculate difficulty
        recipe = db.get_recipe_by_id(recipe_id)
        if not recipe:
            return jsonify({'error': 'Recipe not found', 'code': 'NOT_FOUND'}), 404
        
        difficulty_level, score = calculate_recipe_difficulty(recipe)
        
        # Save to database
        insert_query = """
            INSERT INTO recipe_difficulty (recipe_id, difficulty_level, difficulty_score)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                difficulty_level = VALUES(difficulty_level),
                difficulty_score = VALUES(difficulty_score)
        """
        
        db.execute_query(insert_query, (recipe_id, difficulty_level, score))
        
        return jsonify({
            'difficulty': {
                'recipe_id': recipe_id,
                'difficulty_level': difficulty_level,
                'difficulty_score': score
            }
        })
        
    except Exception as e:
        logger.error(f"Get recipe difficulty error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get difficulty', 'code': 'INTERNAL_ERROR'}), 500


@jwt_required()
def get_recommended_recipes_by_skill():
    """Get recipes matching user's skill level"""
    try:
        username = get_jwt_identity()
        user = auth_manager.get_user_by_username(username)
        
        # Get user's skill level
        skill_query = "SELECT * FROM user_cooking_skills WHERE user_id = %s ORDER BY updated_at DESC LIMIT 1"
        user_skill = db.execute_query(skill_query, (user['id'],), fetch=True)
        
        if not user_skill:
            skill_level = 'beginner'
        else:
            skill_level = user_skill[0]['skill_level']
        
        # Get recipes matching skill level
        query = """
            SELECT r.*, rd.difficulty_level, rd.difficulty_score
            FROM recipes r
            LEFT JOIN recipe_difficulty rd ON r.id = rd.recipe_id
            WHERE rd.difficulty_level = %s
            ORDER BY RAND()
            LIMIT 20
        """
        
        recipes = db.execute_query(query, (skill_level,), fetch=True)
        
        return jsonify({
            'user_skill_level': skill_level,
            'recommended_recipes': recipes or []
        })
        
    except Exception as e:
        logger.error(f"Get recommended by skill error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get recommendations', 'code': 'INTERNAL_ERROR'}), 500


# ============================================================================
# 6. WINE PAIRING SUGGESTIONS - ML-based recommendations
# ============================================================================

WINE_PAIRING_RULES = {
    'chicken': ['Chardonnay', 'Pinot Grigio', 'Sauvignon Blanc', 'Riesling'],
    'beef': ['Cabernet Sauvignon', 'Malbec', 'Syrah', 'Merlot'],
    'pork': ['Pinot Noir', 'Riesling', 'Chardonnay', 'Zinfandel'],
    'fish': ['Sauvignon Blanc', 'Pinot Grigio', 'Chablis', 'Champagne'],
    'seafood': ['Sauvignon Blanc', 'Albariño', 'Vermentino', 'Champagne'],
    'lamb': ['Cabernet Sauvignon', 'Syrah', 'Bordeaux', 'Tempranillo'],
    'pasta': ['Chianti', 'Pinot Noir', 'Barbera', 'Sangiovese'],
    'cheese': ['Chardonnay', 'Port', 'Riesling', 'Sauternes'],
    'spicy': ['Riesling', 'Gewürztraminer', 'Moscato', 'Prosecco'],
    'dessert': ['Port', 'Moscato', 'Ice Wine', 'Sauternes']
}


def suggest_wine_pairing(recipe):
    """Suggest wine pairings based on recipe ingredients and type"""
    ingredients_text = ' '.join(recipe.get('ingredients', [])).lower()
    suggestions = []
    confidence_scores = {}
    
    # Check for main proteins
    for protein, wines in WINE_PAIRING_RULES.items():
        if protein in ingredients_text:
            for wine in wines:
                if wine not in confidence_scores:
                    confidence_scores[wine] = 0
                confidence_scores[wine] += 0.3
    
    # Check for flavor profiles
    if any(word in ingredients_text for word in ['spicy', 'chili', 'pepper', 'hot']):
        for wine in WINE_PAIRING_RULES['spicy']:
            if wine not in confidence_scores:
                confidence_scores[wine] = 0
            confidence_scores[wine] += 0.2
    
    # Sort by confidence
    sorted_wines = sorted(confidence_scores.items(), key=lambda x: x[1], reverse=True)
    
    for wine, confidence in sorted_wines[:5]:
        suggestions.append({
            'wine_name': wine,
            'wine_type': 'Red' if wine in ['Cabernet Sauvignon', 'Malbec', 'Syrah', 'Merlot', 
                                           'Pinot Noir', 'Chianti', 'Bordeaux'] else 'White',
            'confidence_score': round(confidence, 2),
            'pairing_notes': f'Pairs well with the flavors in this recipe'
        })
    
    return suggestions


@jwt_required()
def get_wine_pairings(recipe_id):
    """Get wine pairing suggestions for a recipe"""
    try:
        # Check if pairings already exist
        query = "SELECT * FROM wine_pairings WHERE recipe_id = %s ORDER BY confidence_score DESC"
        existing = db.execute_query(query, (recipe_id,), fetch=True)
        
        if existing:
            return jsonify({'pairings': existing})
        
        # Generate pairings
        recipe = db.get_recipe_by_id(recipe_id)
        if not recipe:
            return jsonify({'error': 'Recipe not found', 'code': 'NOT_FOUND'}), 404
        
        suggestions = suggest_wine_pairing(recipe)
        
        # Save to database
        for suggestion in suggestions:
            insert_query = """
                INSERT INTO wine_pairings (recipe_id, wine_name, wine_type, pairing_notes, confidence_score)
                VALUES (%s, %s, %s, %s, %s)
            """
            db.execute_query(insert_query, (
                recipe_id,
                suggestion['wine_name'],
                suggestion['wine_type'],
                suggestion['pairing_notes'],
                suggestion['confidence_score']
            ))
        
        return jsonify({'pairings': suggestions})
        
    except Exception as e:
        logger.error(f"Get wine pairings error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get wine pairings', 'code': 'INTERNAL_ERROR'}), 500


# ============================================================================
# 7. LEFTOVER TRANSFORMER - Turn leftovers into new recipes
# ============================================================================

@jwt_required()
def add_leftover():
    """Add leftover ingredient"""
    try:
        username = get_jwt_identity()
        user = auth_manager.get_user_by_username(username)
        
        data = request.get_json()
        
        query = """
            INSERT INTO leftovers (user_id, ingredient_name, quantity, unit, added_date, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        db.execute_query(query, (
            user['id'],
            data.get('ingredient_name'),
            data.get('quantity'),
            data.get('unit'),
            datetime.now().date(),
            data.get('notes', '')
        ))
        
        return jsonify({'success': True, 'message': 'Leftover added'}), 201
        
    except Exception as e:
        logger.error(f"Add leftover error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to add leftover', 'code': 'INTERNAL_ERROR'}), 500


@jwt_required()
def find_recipes_from_leftovers():
    """Find recipes that can be made with current leftovers"""
    try:
        username = get_jwt_identity()
        user = auth_manager.get_user_by_username(username)
        
        # Get user's leftovers
        leftovers_query = "SELECT ingredient_name FROM leftovers WHERE user_id = %s AND used = 0"
        leftovers = db.execute_query(leftovers_query, (user['id'],), fetch=True)
        
        if not leftovers:
            return jsonify({'recipes': [], 'message': 'No leftovers found'})
        
        leftover_ingredients = [item['ingredient_name'].lower() for item in leftovers]
        
        # Find recipes containing these ingredients
        matching_recipes = []
        recipes_query = "SELECT * FROM recipes LIMIT 1000"  # Sample for performance
        recipes = db.execute_query(recipes_query, fetch=True)
        
        for recipe in recipes or []:
            if not recipe.get('ingredients'):
                continue
            
            recipe_ingredients = ' '.join(recipe['ingredients']).lower()
            match_count = sum(1 for leftover in leftover_ingredients if leftover in recipe_ingredients)
            
            if match_count > 0:
                matching_recipes.append({
                    **recipe,
                    'match_count': match_count,
                    'match_percentage': round((match_count / len(leftover_ingredients)) * 100, 1)
                })
        
        # Sort by match percentage
        matching_recipes.sort(key=lambda x: x['match_percentage'], reverse=True)
        
        return jsonify({
            'leftover_ingredients': leftover_ingredients,
            'recipes': matching_recipes[:20],
            'total_matches': len(matching_recipes)
        })
        
    except Exception as e:
        logger.error(f"Find recipes from leftovers error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to find recipes', 'code': 'INTERNAL_ERROR'}), 500


# ============================================================================
# 8. AI COOKING COACH - Step-by-step voice guidance
# ============================================================================

@jwt_required()
def start_cooking_session(recipe_id):
    """Start a guided cooking session"""
    try:
        username = get_jwt_identity()
        user = auth_manager.get_user_by_username(username)
        
        recipe = db.get_recipe_by_id(recipe_id)
        if not recipe:
            return jsonify({'error': 'Recipe not found', 'code': 'NOT_FOUND'}), 404
        
        # Create cooking session
        query = """
            INSERT INTO cooking_sessions (user_id, recipe_id, total_steps)
            VALUES (%s, %s, %s)
        """
        
        total_steps = len(recipe.get('instructions', []))
        db.execute_query(query, (user['id'], recipe_id, total_steps))
        
        session_id = db.execute_query("SELECT LAST_INSERT_ID() as id", fetch=True)[0]['id']
        
        return jsonify({
            'session_id': session_id,
            'recipe': recipe,
            'total_steps': total_steps,
            'current_step': 1
        }), 201
        
    except Exception as e:
        logger.error(f"Start cooking session error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to start session', 'code': 'INTERNAL_ERROR'}), 500


@jwt_required()
def update_cooking_progress(session_id):
    """Update progress in cooking session"""
    try:
        data = request.get_json()
        current_step = data.get('current_step')
        completed = data.get('completed', False)
        
        query = """
            UPDATE cooking_sessions 
            SET current_step = %s, completed = %s, updated_at = NOW()
            WHERE id = %s
        """
        
        db.execute_query(query, (current_step, completed, session_id))
        
        return jsonify({'success': True, 'current_step': current_step})
        
    except Exception as e:
        logger.error(f"Update cooking progress error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to update progress', 'code': 'INTERNAL_ERROR'}), 500
