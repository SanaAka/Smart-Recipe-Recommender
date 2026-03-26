"""
Smart Recipe Recommender API v3.0
New features on top of v2:
  1. Comment replies (nested replies on comments)
  2. Comment & reply reactions (like/dislike)
  3. User-posted recipes (create, edit, delete, view by user)
"""
import os
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request, create_access_token

v3_bp = Blueprint('v3', __name__)

# Image upload config
UPLOAD_FOLDER = Path(__file__).parent / 'uploads' / 'recipe_images'
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
PROFILE_PIC_FOLDER = Path(__file__).parent / 'uploads' / 'profile_pics'
PROFILE_PIC_FOLDER.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# These will be injected by init_v3()
_db = None
_auth = None
_logger = None
_limiter = None


def init_v3(db, auth_manager, logger, limiter):
    global _db, _auth, _logger, _limiter
    _db = db
    _auth = auth_manager
    _logger = logger
    _limiter = limiter


def _get_user():
    """Helper: get the authenticated user dict or None."""
    username = get_jwt_identity()
    return _auth.get_user_by_username(username) if username else None


# ============================================================================
# IMAGE UPLOAD
# ============================================================================

@v3_bp.route('/api/upload/image', methods=['POST'])
@jwt_required()
def upload_image():
    """Upload a recipe image. Returns the URL to use as image_url."""
    try:
        user = _get_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not _allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed: PNG, JPG, JPEG, GIF, WEBP'}), 400

        # Check file size
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        if size > MAX_IMAGE_SIZE:
            return jsonify({'error': f'Image too large. Maximum size is {MAX_IMAGE_SIZE // (1024*1024)} MB'}), 400

        # Generate unique filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        save_path = UPLOAD_FOLDER / unique_name
        file.save(str(save_path))

        # Return the URL path that the static route will serve
        image_url = f"/api/uploads/recipe_images/{unique_name}"

        _logger.info(f"User {user['username']} uploaded image: {unique_name}")
        return jsonify({
            'success': True,
            'image_url': image_url,
            'filename': unique_name
        }), 201

    except Exception as e:
        _logger.error(f"Image upload error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to upload image'}), 500


@v3_bp.route('/api/uploads/recipe_images/<filename>', methods=['GET'])
def serve_uploaded_image(filename):
    """Serve an uploaded recipe image."""
    safe_name = secure_filename(filename)
    return send_from_directory(str(UPLOAD_FOLDER), safe_name)


@v3_bp.route('/api/uploads/profile_pics/<filename>', methods=['GET'])
def serve_profile_pic(filename):
    """Serve an uploaded profile picture."""
    safe_name = secure_filename(filename)
    return send_from_directory(str(PROFILE_PIC_FOLDER), safe_name)


# ============================================================================
# PROFILE PICTURE UPLOAD
# ============================================================================

@v3_bp.route('/api/user/profile-pic', methods=['PUT'])
@jwt_required()
def upload_profile_pic():
    """Upload or update the current user's profile picture."""
    try:
        user = _get_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not _allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed: PNG, JPG, JPEG, GIF, WEBP'}), 400

        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        if size > MAX_IMAGE_SIZE:
            return jsonify({'error': f'Image too large. Maximum size is {MAX_IMAGE_SIZE // (1024*1024)} MB'}), 400

        # Delete old profile pic file if it exists
        old_pic = user.get('profile_pic')
        if old_pic:
            old_filename = old_pic.rsplit('/', 1)[-1]
            old_path = PROFILE_PIC_FOLDER / old_filename
            if old_path.exists():
                old_path.unlink()

        # Save new file
        ext = file.filename.rsplit('.', 1)[1].lower()
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        save_path = PROFILE_PIC_FOLDER / unique_name
        file.save(str(save_path))

        profile_pic_url = f"/api/uploads/profile_pics/{unique_name}"

        # Update DB
        _db.execute_query(
            "UPDATE users SET profile_pic = %s WHERE id = %s",
            (profile_pic_url, user['id']),
            fetch=False
        )

        _logger.info(f"User {user['username']} updated profile pic: {unique_name}")
        return jsonify({
            'success': True,
            'profile_pic': profile_pic_url
        })

    except Exception as e:
        _logger.error(f"Profile pic upload error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to upload profile picture'}), 500


@v3_bp.route('/api/user/profile-pic', methods=['DELETE'])
@jwt_required()
def delete_profile_pic():
    """Remove the current user's profile picture."""
    try:
        user = _get_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        old_pic = user.get('profile_pic')
        if old_pic:
            old_filename = old_pic.rsplit('/', 1)[-1]
            old_path = PROFILE_PIC_FOLDER / old_filename
            if old_path.exists():
                old_path.unlink()

        _db.execute_query(
            "UPDATE users SET profile_pic = NULL WHERE id = %s",
            (user['id'],),
            fetch=False
        )

        _logger.info(f"User {user['username']} removed profile pic")
        return jsonify({'success': True, 'profile_pic': None})

    except Exception as e:
        _logger.error(f"Delete profile pic error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to delete profile picture'}), 500


# ============================================================================
# COMMENT REPLIES
# ============================================================================

@v3_bp.route('/api/comments/<int:comment_id>/replies', methods=['GET'])
def get_replies(comment_id):
    """Get all replies for a comment."""
    try:
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 20)), 50)
        offset = (page - 1) * limit

        query = """
            SELECT r.id, r.comment_id, r.reply, r.created_at, r.updated_at,
                   u.username, u.id as user_id, u.profile_pic
            FROM comment_replies r
            JOIN users u ON r.user_id = u.id
            WHERE r.comment_id = %s
            ORDER BY r.created_at ASC
            LIMIT %s OFFSET %s
        """
        replies = _db.execute_query(query, (comment_id, limit, offset), fetch=True) or []

        count_q = "SELECT COUNT(*) as total FROM comment_replies WHERE comment_id = %s"
        total = _db.execute_query(count_q, (comment_id,), fetch=True)[0]['total']

        # Attach reaction counts to each reply
        for reply in replies:
            reply['likes'] = 0
            reply['dislikes'] = 0
            reply['user_reaction'] = None

        if replies:
            rids = [r['id'] for r in replies]
            ph = ','.join(['%s'] * len(rids))
            reaction_rows = _db.execute_query(f"""
                SELECT reply_id, reaction_type, COUNT(*) as cnt
                FROM reply_reactions
                WHERE reply_id IN ({ph})
                GROUP BY reply_id, reaction_type
            """, tuple(rids), fetch=True) or []

            for row in reaction_rows:
                for reply in replies:
                    if reply['id'] == row['reply_id']:
                        if row['reaction_type'] == 'like':
                            reply['likes'] = row['cnt']
                        else:
                            reply['dislikes'] = row['cnt']

            # Get current user's reactions
            try:
                verify_jwt_in_request(optional=True)
                username = get_jwt_identity()
                if username:
                    user = _auth.get_user_by_username(username)
                    if user:
                        user_reactions = _db.execute_query(f"""
                            SELECT reply_id, reaction_type
                            FROM reply_reactions
                            WHERE reply_id IN ({ph}) AND user_id = %s
                        """, tuple(rids) + (user['id'],), fetch=True) or []
                        for ur in user_reactions:
                            for reply in replies:
                                if reply['id'] == ur['reply_id']:
                                    reply['user_reaction'] = ur['reaction_type']
            except:
                pass

        return jsonify({
            'replies': replies,
            'total': total,
            'page': page,
            'has_more': (page * limit) < total
        })
    except Exception as e:
        _logger.error(f"Get replies error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch replies'}), 500


@v3_bp.route('/api/comments/<int:comment_id>/replies', methods=['POST'])
@jwt_required()
def add_reply(comment_id):
    """Add a reply to a comment."""
    try:
        user = _get_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()
        reply_text = data.get('reply', '').strip()

        if not reply_text or len(reply_text) < 1:
            return jsonify({'error': 'Reply cannot be empty'}), 400
        if len(reply_text) > 1000:
            return jsonify({'error': 'Reply must be under 1000 characters'}), 400

        # Verify comment exists
        check = _db.execute_query(
            "SELECT id FROM recipe_comments WHERE id = %s", (comment_id,), fetch=True
        )
        if not check:
            return jsonify({'error': 'Comment not found'}), 404

        _db.execute_query(
            "INSERT INTO comment_replies (comment_id, user_id, reply) VALUES (%s, %s, %s)",
            (comment_id, user['id'], reply_text)
        )

        # Fetch the new reply
        new_reply = _db.execute_query("""
            SELECT r.id, r.comment_id, r.reply, r.created_at, r.updated_at,
                   u.username, u.id as user_id, u.profile_pic
            FROM comment_replies r
            JOIN users u ON r.user_id = u.id
            WHERE r.comment_id = %s AND r.user_id = %s
            ORDER BY r.created_at DESC LIMIT 1
        """, (comment_id, user['id']), fetch=True)[0]

        new_reply['likes'] = 0
        new_reply['dislikes'] = 0
        new_reply['user_reaction'] = None

        _logger.info(f"User {user['username']} replied to comment {comment_id}")
        return jsonify({'success': True, 'reply': new_reply}), 201

    except Exception as e:
        _logger.error(f"Add reply error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to add reply'}), 500


@v3_bp.route('/api/replies/<int:reply_id>', methods=['DELETE'])
@jwt_required()
def delete_reply(reply_id):
    """Delete a reply (owner only)."""
    try:
        user = _get_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        check = _db.execute_query(
            "SELECT user_id FROM comment_replies WHERE id = %s", (reply_id,), fetch=True
        )
        if not check:
            return jsonify({'error': 'Reply not found'}), 404
        if check[0]['user_id'] != user['id']:
            return jsonify({'error': 'Unauthorized'}), 403

        _db.execute_query("DELETE FROM comment_replies WHERE id = %s", (reply_id,))
        return jsonify({'success': True})

    except Exception as e:
        _logger.error(f"Delete reply error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to delete reply'}), 500


# ============================================================================
# COMMENT REACTIONS (LIKE / DISLIKE)
# ============================================================================

@v3_bp.route('/api/comments/<int:comment_id>/react', methods=['POST'])
@jwt_required()
def react_to_comment(comment_id):
    """Like or dislike a comment. Toggle off if same reaction sent again."""
    try:
        user = _get_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()
        reaction_type = data.get('reaction')  # 'like' or 'dislike'

        if reaction_type not in ('like', 'dislike'):
            return jsonify({'error': 'Reaction must be "like" or "dislike"'}), 400

        # Verify comment exists
        comment_check = _db.execute_query(
            "SELECT id FROM recipe_comments WHERE id = %s", (comment_id,), fetch=True
        )
        if not comment_check:
            return jsonify({'error': 'Comment not found'}), 404

        # Check existing reaction
        existing = _db.execute_query(
            "SELECT id, reaction_type FROM comment_reactions WHERE comment_id = %s AND user_id = %s",
            (comment_id, user['id']), fetch=True
        )

        if existing:
            if existing[0]['reaction_type'] == reaction_type:
                # Same reaction — toggle off (remove)
                _db.execute_query(
                    "DELETE FROM comment_reactions WHERE id = %s", (existing[0]['id'],)
                )
                user_reaction = None
            else:
                # Different reaction — update
                _db.execute_query(
                    "UPDATE comment_reactions SET reaction_type = %s WHERE id = %s",
                    (reaction_type, existing[0]['id'])
                )
                user_reaction = reaction_type
        else:
            # New reaction
            _db.execute_query(
                "INSERT INTO comment_reactions (comment_id, user_id, reaction_type) VALUES (%s, %s, %s)",
                (comment_id, user['id'], reaction_type)
            )
            user_reaction = reaction_type

        # Get updated counts
        counts = _db.execute_query("""
            SELECT reaction_type, COUNT(*) as cnt
            FROM comment_reactions WHERE comment_id = %s
            GROUP BY reaction_type
        """, (comment_id,), fetch=True) or []

        likes = 0
        dislikes = 0
        for c in counts:
            if c['reaction_type'] == 'like':
                likes = c['cnt']
            else:
                dislikes = c['cnt']

        return jsonify({
            'success': True,
            'likes': likes,
            'dislikes': dislikes,
            'user_reaction': user_reaction
        })

    except Exception as e:
        _logger.error(f"Comment reaction error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to react to comment'}), 500


@v3_bp.route('/api/replies/<int:reply_id>/react', methods=['POST'])
@jwt_required()
def react_to_reply(reply_id):
    """Like or dislike a reply. Toggle off if same reaction sent again."""
    try:
        user = _get_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()
        reaction_type = data.get('reaction')

        if reaction_type not in ('like', 'dislike'):
            return jsonify({'error': 'Reaction must be "like" or "dislike"'}), 400

        existing = _db.execute_query(
            "SELECT id, reaction_type FROM reply_reactions WHERE reply_id = %s AND user_id = %s",
            (reply_id, user['id']), fetch=True
        )

        if existing:
            if existing[0]['reaction_type'] == reaction_type:
                _db.execute_query("DELETE FROM reply_reactions WHERE id = %s", (existing[0]['id'],))
                user_reaction = None
            else:
                _db.execute_query(
                    "UPDATE reply_reactions SET reaction_type = %s WHERE id = %s",
                    (reaction_type, existing[0]['id'])
                )
                user_reaction = reaction_type
        else:
            _db.execute_query(
                "INSERT INTO reply_reactions (reply_id, user_id, reaction_type) VALUES (%s, %s, %s)",
                (reply_id, user['id'], reaction_type)
            )
            user_reaction = reaction_type

        counts = _db.execute_query("""
            SELECT reaction_type, COUNT(*) as cnt
            FROM reply_reactions WHERE reply_id = %s
            GROUP BY reaction_type
        """, (reply_id,), fetch=True) or []

        likes = 0
        dislikes = 0
        for c in counts:
            if c['reaction_type'] == 'like':
                likes = c['cnt']
            else:
                dislikes = c['cnt']

        return jsonify({
            'success': True,
            'likes': likes,
            'dislikes': dislikes,
            'user_reaction': user_reaction
        })

    except Exception as e:
        _logger.error(f"Reply reaction error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to react to reply'}), 500


# ============================================================================
# USER-POSTED RECIPES
# ============================================================================

def _build_search_text(recipe_id, name, ingredients, tags):
    """Build denormalized search_text for fulltext search."""
    parts = [name.lower()]
    parts.extend(ing.strip().lower() for ing in ingredients if ing.strip())
    parts.extend(tag.strip().lower() for tag in tags if tag.strip())
    search_text = ' '.join(parts)
    _db.execute_query(
        "UPDATE recipes SET search_text = %s WHERE id = %s",
        (search_text, recipe_id)
    )


@v3_bp.route('/api/recipes/create', methods=['POST'])
@jwt_required()
def create_user_recipe():
    """Create a new recipe submitted by a user."""
    try:
        user = _get_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()

        name = (data.get('name') or '').strip()
        description = (data.get('description') or '').strip()
        minutes = data.get('minutes')
        ingredients = data.get('ingredients', [])  # list of strings
        steps = data.get('steps', [])              # list of strings
        tags = data.get('tags', [])                # list of strings
        image_url = (data.get('image_url') or '').strip()

        # Validation
        if not name or len(name) < 3:
            return jsonify({'error': 'Recipe name must be at least 3 characters'}), 400
        if len(name) > 200:
            return jsonify({'error': 'Recipe name is too long'}), 400
        if description and len(description) > 5000:
            return jsonify({'error': 'Description is too long'}), 400
        if not ingredients or len(ingredients) < 1:
            return jsonify({'error': 'At least 1 ingredient is required'}), 400
        if not steps or len(steps) < 1:
            return jsonify({'error': 'At least 1 step is required'}), 400
        if minutes is not None:
            minutes = int(minutes)
            if minutes < 1 or minutes > 10000:
                return jsonify({'error': 'Cooking time must be between 1 and 10000 minutes'}), 400

        # Insert recipe (execute_query returns cursor.lastrowid for non-fetch)
        recipe_id = _db.execute_query(
            """INSERT INTO recipes (name, minutes, description, image_url, submitted_by, is_approved)
               VALUES (%s, %s, %s, %s, %s, 1)""",
            (name, minutes, description, image_url or None, user['id'])
        )

        if not recipe_id:
            return jsonify({'error': 'Failed to create recipe'}), 500

        # Insert ingredients
        for ing_name in ingredients:
            ing_name = ing_name.strip()
            if not ing_name:
                continue
            # Get or create ingredient
            existing = _db.execute_query(
                "SELECT id FROM ingredients WHERE name = %s", (ing_name,), fetch=True
            )
            if existing:
                ing_id = existing[0]['id']
            else:
                ing_id = _db.execute_query("INSERT INTO ingredients (name) VALUES (%s)", (ing_name,))

            try:
                _db.execute_query(
                    "INSERT INTO recipe_ingredients (recipe_id, ingredient_id) VALUES (%s, %s)",
                    (recipe_id, ing_id)
                )
            except:
                pass  # Duplicate, skip

        # Insert steps
        for i, step_text in enumerate(steps, 1):
            step_text = step_text.strip()
            if not step_text:
                continue
            _db.execute_query(
                "INSERT INTO steps (recipe_id, step_number, description) VALUES (%s, %s, %s)",
                (recipe_id, i, step_text)
            )

        # Insert tags
        for tag_name in tags:
            tag_name = tag_name.strip().lower()
            if not tag_name:
                continue
            existing = _db.execute_query(
                "SELECT id FROM tags WHERE name = %s", (tag_name,), fetch=True
            )
            if existing:
                tag_id = existing[0]['id']
            else:
                tag_id = _db.execute_query("INSERT INTO tags (name) VALUES (%s)", (tag_name,))

            try:
                _db.execute_query(
                    "INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (%s, %s)",
                    (recipe_id, tag_id)
                )
            except:
                pass

        # Populate search_text for fulltext search
        _build_search_text(recipe_id, name, ingredients, tags)

        _logger.info(f"User {user['username']} created recipe '{name}' (id={recipe_id})")
        return jsonify({
            'success': True,
            'recipe_id': recipe_id,
            'message': 'Recipe created successfully!'
        }), 201

    except Exception as e:
        _logger.error(f"Create recipe error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to create recipe'}), 500


@v3_bp.route('/api/recipes/user', methods=['GET'])
@jwt_required()
def get_user_recipes():
    """Get all recipes posted by the current user."""
    try:
        user = _get_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        recipes = _db.execute_query("""
            SELECT r.id, r.name, r.minutes, r.description, r.image_url, r.is_approved,
                   (SELECT AVG(rating) FROM recipe_ratings WHERE recipe_id = r.id) as avg_rating,
                   (SELECT COUNT(*) FROM recipe_ratings WHERE recipe_id = r.id) as rating_count,
                   (SELECT COUNT(*) FROM recipe_comments WHERE recipe_id = r.id) as comment_count
            FROM recipes r
            WHERE r.submitted_by = %s
            ORDER BY r.id DESC
        """, (user['id'],), fetch=True) or []

        for r in recipes:
            r['avg_rating'] = round(float(r['avg_rating']), 1) if r['avg_rating'] else 0

        return jsonify({'recipes': recipes, 'count': len(recipes)})

    except Exception as e:
        _logger.error(f"Get user recipes error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch your recipes'}), 500


@v3_bp.route('/api/recipes/<int:recipe_id>/edit', methods=['PUT'])
@jwt_required()
def edit_user_recipe(recipe_id):
    """Edit a user-posted recipe (owner only)."""
    try:
        user = _get_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Check ownership
        recipe = _db.execute_query(
            "SELECT submitted_by FROM recipes WHERE id = %s", (recipe_id,), fetch=True
        )
        if not recipe:
            return jsonify({'error': 'Recipe not found'}), 404
        if recipe[0]['submitted_by'] != user['id']:
            return jsonify({'error': 'You can only edit your own recipes'}), 403

        data = request.get_json()

        # Build update query dynamically
        updates = []
        params = []

        if 'name' in data:
            name = data['name'].strip()
            if len(name) < 3:
                return jsonify({'error': 'Name too short'}), 400
            updates.append('name = %s')
            params.append(name)

        if 'description' in data:
            updates.append('description = %s')
            params.append(data['description'].strip())

        if 'minutes' in data:
            updates.append('minutes = %s')
            params.append(int(data['minutes']))

        if 'image_url' in data:
            updates.append('image_url = %s')
            params.append(data['image_url'].strip() or None)

        if updates:
            params.append(recipe_id)
            _db.execute_query(
                f"UPDATE recipes SET {', '.join(updates)} WHERE id = %s",
                tuple(params)
            )

        # Update ingredients if provided
        if 'ingredients' in data:
            # Clear existing
            _db.execute_query(
                "DELETE FROM recipe_ingredients WHERE recipe_id = %s", (recipe_id,)
            )
            for ing_name in data['ingredients']:
                ing_name = ing_name.strip()
                if not ing_name:
                    continue
                existing = _db.execute_query(
                    "SELECT id FROM ingredients WHERE name = %s", (ing_name,), fetch=True
                )
                if existing:
                    ing_id = existing[0]['id']
                else:
                    ing_id = _db.execute_query("INSERT INTO ingredients (name) VALUES (%s)", (ing_name,))
                try:
                    _db.execute_query(
                        "INSERT INTO recipe_ingredients (recipe_id, ingredient_id) VALUES (%s, %s)",
                        (recipe_id, ing_id)
                    )
                except:
                    pass

        # Update steps if provided
        if 'steps' in data:
            _db.execute_query("DELETE FROM steps WHERE recipe_id = %s", (recipe_id,))
            for i, step_text in enumerate(data['steps'], 1):
                step_text = step_text.strip()
                if not step_text:
                    continue
                _db.execute_query(
                    "INSERT INTO steps (recipe_id, step_number, description) VALUES (%s, %s, %s)",
                    (recipe_id, i, step_text)
                )

        # Update tags if provided
        if 'tags' in data:
            _db.execute_query("DELETE FROM recipe_tags WHERE recipe_id = %s", (recipe_id,))
            for tag_name in data['tags']:
                tag_name = tag_name.strip().lower()
                if not tag_name:
                    continue
                existing = _db.execute_query(
                    "SELECT id FROM tags WHERE name = %s", (tag_name,), fetch=True
                )
                if existing:
                    tag_id = existing[0]['id']
                else:
                    tag_id = _db.execute_query("INSERT INTO tags (name) VALUES (%s)", (tag_name,))
                try:
                    _db.execute_query(
                        "INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (%s, %s)",
                        (recipe_id, tag_id)
                    )
                except:
                    pass

        # Rebuild search_text
        updated = _db.execute_query(
            "SELECT name FROM recipes WHERE id = %s", (recipe_id,), fetch=True
        )
        cur_name = updated[0]['name'] if updated else ''
        cur_ings = data.get('ingredients', [])
        cur_tags = data.get('tags', [])
        # If ingredients/tags weren't in the edit payload, fetch current ones
        if 'ingredients' not in data:
            rows = _db.execute_query(
                "SELECT i.name FROM ingredients i JOIN recipe_ingredients ri ON i.id=ri.ingredient_id WHERE ri.recipe_id=%s",
                (recipe_id,), fetch=True
            ) or []
            cur_ings = [r['name'] for r in rows]
        if 'tags' not in data:
            rows = _db.execute_query(
                "SELECT t.name FROM tags t JOIN recipe_tags rt ON t.id=rt.tag_id WHERE rt.recipe_id=%s",
                (recipe_id,), fetch=True
            ) or []
            cur_tags = [r['name'] for r in rows]
        _build_search_text(recipe_id, cur_name, cur_ings, cur_tags)

        _logger.info(f"User {user['username']} edited recipe {recipe_id}")
        return jsonify({'success': True, 'message': 'Recipe updated'})

    except Exception as e:
        _logger.error(f"Edit recipe error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to update recipe'}), 500


@v3_bp.route('/api/recipes/<int:recipe_id>/delete', methods=['DELETE'])
@jwt_required()
def delete_user_recipe(recipe_id):
    """Delete a user-posted recipe (owner only)."""
    try:
        user = _get_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        recipe = _db.execute_query(
            "SELECT submitted_by FROM recipes WHERE id = %s", (recipe_id,), fetch=True
        )
        if not recipe:
            return jsonify({'error': 'Recipe not found'}), 404
        if recipe[0]['submitted_by'] != user['id']:
            return jsonify({'error': 'You can only delete your own recipes'}), 403

        # Delete in correct order (FK constraints)
        _db.execute_query("DELETE FROM steps WHERE recipe_id = %s", (recipe_id,))
        _db.execute_query("DELETE FROM recipe_ingredients WHERE recipe_id = %s", (recipe_id,))
        _db.execute_query("DELETE FROM recipe_tags WHERE recipe_id = %s", (recipe_id,))
        _db.execute_query("DELETE FROM recipe_ratings WHERE recipe_id = %s", (recipe_id,))
        _db.execute_query("DELETE FROM recipe_comments WHERE recipe_id = %s", (recipe_id,))
        try:
            _db.execute_query("DELETE FROM nutrition WHERE recipe_id = %s", (recipe_id,))
        except:
            pass
        _db.execute_query("DELETE FROM recipes WHERE id = %s", (recipe_id,))

        _logger.info(f"User {user['username']} deleted recipe {recipe_id}")
        return jsonify({'success': True, 'message': 'Recipe deleted'})

    except Exception as e:
        _logger.error(f"Delete recipe error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to delete recipe'}), 500


@v3_bp.route('/api/user/<username>/recipes', methods=['GET'])
def get_public_user_recipes(username):
    """Get recipes posted by a specific user (public)."""
    try:
        target_user = _auth.get_user_by_username(username)
        if not target_user:
            return jsonify({'error': 'User not found'}), 404

        recipes = _db.execute_query("""
            SELECT r.id, r.name, r.minutes, r.description, r.image_url,
                   (SELECT AVG(rating) FROM recipe_ratings WHERE recipe_id = r.id) as avg_rating,
                   (SELECT COUNT(*) FROM recipe_ratings WHERE recipe_id = r.id) as rating_count
            FROM recipes r
            WHERE r.submitted_by = %s AND r.is_approved = 1
            ORDER BY r.id DESC
        """, (target_user['id'],), fetch=True) or []

        for r in recipes:
            r['avg_rating'] = round(float(r['avg_rating']), 1) if r['avg_rating'] else 0

        return jsonify({
            'username': username,
            'recipes': recipes,
            'count': len(recipes)
        })

    except Exception as e:
        _logger.error(f"Get public user recipes error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch recipes'}), 500


# ── Public User Profile ──────────────────────────────────────────────
@v3_bp.route('/api/user/<username>/profile', methods=['GET'])
def get_public_user_profile(username):
    """Get a public user profile with stats."""
    try:
        target_user = _auth.get_user_by_username(username)
        if not target_user:
            return jsonify({'error': 'User not found'}), 404

        uid = target_user['id']

        # Recipe count
        recipe_rows = _db.execute_query(
            "SELECT COUNT(*) as cnt FROM recipes WHERE submitted_by = %s AND is_approved = 1",
            (uid,), fetch=True
        )
        recipe_count = recipe_rows[0]['cnt'] if recipe_rows else 0

        # Comment count
        comment_rows = _db.execute_query(
            "SELECT COUNT(*) as cnt FROM recipe_comments WHERE user_id = %s",
            (uid,), fetch=True
        )
        comment_count = comment_rows[0]['cnt'] if comment_rows else 0

        # Average rating received on their recipes
        avg_rows = _db.execute_query("""
            SELECT AVG(rr.rating) as avg_rat, COUNT(rr.id) as rat_cnt
            FROM recipe_ratings rr
            JOIN recipes r ON rr.recipe_id = r.id
            WHERE r.submitted_by = %s
        """, (uid,), fetch=True)
        avg_rating = round(float(avg_rows[0]['avg_rat']), 1) if avg_rows and avg_rows[0]['avg_rat'] else 0
        rating_count = avg_rows[0]['rat_cnt'] if avg_rows else 0

        return jsonify({
            'username': target_user['username'],
            'profile_pic': target_user.get('profile_pic'),
            'bio': target_user.get('bio'),
            'member_since': target_user['created_at'].isoformat() if target_user.get('created_at') else None,
            'recipe_count': recipe_count,
            'comment_count': comment_count,
            'avg_rating_received': avg_rating,
            'rating_count': rating_count
        })

    except Exception as e:
        _logger.error(f"Get public profile error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch profile'}), 500


# ============================================================================
# ACCOUNT SETTINGS (change password, update email, update bio, delete account)
# ============================================================================

@v3_bp.route('/api/user/change-username', methods=['PUT'])
@jwt_required()
def change_username():
    """Change the current user's username. Requires password confirmation."""
    try:
        from werkzeug.security import check_password_hash
        import re

        user = _get_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json() or {}
        new_username = data.get('new_username', '').strip()
        password = data.get('password', '').strip()

        if not new_username or not password:
            return jsonify({'error': 'New username and password are required'}), 400

        if len(new_username) < 3 or len(new_username) > 30:
            return jsonify({'error': 'Username must be 3-30 characters'}), 400

        if not re.match(r'^[a-zA-Z0-9_]+$', new_username):
            return jsonify({'error': 'Username can only contain letters, numbers, and underscores'}), 400

        # Verify password
        row = _db.execute_query(
            "SELECT password_hash FROM users WHERE id = %s",
            (user['id'],), fetch=True
        )
        if not row or not check_password_hash(row[0]['password_hash'], password):
            return jsonify({'error': 'Password is incorrect'}), 403

        # Check if username already taken
        existing = _db.execute_query(
            "SELECT id FROM users WHERE username = %s AND id != %s",
            (new_username, user['id']), fetch=True
        )
        if existing:
            return jsonify({'error': 'Username is already taken'}), 409

        # Update username
        _db.execute_query(
            "UPDATE users SET username = %s WHERE id = %s",
            (new_username, user['id']), fetch=False
        )

        # Issue a new JWT token with the new username as identity
        new_token = create_access_token(identity=new_username)

        _logger.info(f"User {user['username']} changed username to {new_username}")
        return jsonify({
            'success': True,
            'message': 'Username updated successfully',
            'username': new_username,
            'access_token': new_token
        })

    except Exception as e:
        _logger.error(f"Change username error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to change username'}), 500


@v3_bp.route('/api/user/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    """Change the current user's password. Requires current_password + new_password."""
    try:
        from werkzeug.security import generate_password_hash, check_password_hash

        user = _get_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json() or {}
        current_password = data.get('current_password', '').strip()
        new_password = data.get('new_password', '').strip()

        if not current_password or not new_password:
            return jsonify({'error': 'Current password and new password are required'}), 400

        if len(new_password) < 6:
            return jsonify({'error': 'New password must be at least 6 characters'}), 400

        # Verify current password
        row = _db.execute_query(
            "SELECT password_hash FROM users WHERE id = %s",
            (user['id'],), fetch=True
        )
        if not row or not check_password_hash(row[0]['password_hash'], current_password):
            return jsonify({'error': 'Current password is incorrect'}), 403

        # Update password
        new_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
        _db.execute_query(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (new_hash, user['id']), fetch=False
        )

        _logger.info(f"User {user['username']} changed their password")
        return jsonify({'success': True, 'message': 'Password changed successfully'})

    except Exception as e:
        _logger.error(f"Change password error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to change password'}), 500


@v3_bp.route('/api/user/update-email', methods=['PUT'])
@jwt_required()
def update_email():
    """Update the current user's email. Requires password confirmation."""
    try:
        from werkzeug.security import check_password_hash

        user = _get_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json() or {}
        new_email = data.get('email', '').strip()
        password = data.get('password', '').strip()

        if not new_email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        # Basic email validation
        import re
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', new_email):
            return jsonify({'error': 'Invalid email format'}), 400

        # Verify password
        row = _db.execute_query(
            "SELECT password_hash FROM users WHERE id = %s",
            (user['id'],), fetch=True
        )
        if not row or not check_password_hash(row[0]['password_hash'], password):
            return jsonify({'error': 'Password is incorrect'}), 403

        # Check if email already taken by another user
        existing = _db.execute_query(
            "SELECT id FROM users WHERE email = %s AND id != %s",
            (new_email, user['id']), fetch=True
        )
        if existing:
            return jsonify({'error': 'Email is already in use'}), 409

        _db.execute_query(
            "UPDATE users SET email = %s WHERE id = %s",
            (new_email, user['id']), fetch=False
        )

        _logger.info(f"User {user['username']} updated email to {new_email}")
        return jsonify({'success': True, 'message': 'Email updated successfully', 'email': new_email})

    except Exception as e:
        _logger.error(f"Update email error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to update email'}), 500


@v3_bp.route('/api/user/update-bio', methods=['PUT'])
@jwt_required()
def update_bio():
    """Update the current user's bio."""
    try:
        user = _get_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json() or {}
        bio = data.get('bio', '').strip()

        # Limit bio length
        if len(bio) > 500:
            return jsonify({'error': 'Bio must be 500 characters or fewer'}), 400

        _db.execute_query(
            "UPDATE users SET bio = %s WHERE id = %s",
            (bio if bio else None, user['id']), fetch=False
        )

        _logger.info(f"User {user['username']} updated bio")
        return jsonify({'success': True, 'message': 'Bio updated', 'bio': bio if bio else None})

    except Exception as e:
        _logger.error(f"Update bio error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to update bio'}), 500


@v3_bp.route('/api/user/delete-account', methods=['DELETE'])
@jwt_required()
def delete_own_account():
    """Delete the current user's account. Requires password confirmation."""
    try:
        from werkzeug.security import check_password_hash

        user = _get_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json() or {}
        password = data.get('password', '').strip()

        if not password:
            return jsonify({'error': 'Password is required to delete your account'}), 400

        # Verify password
        row = _db.execute_query(
            "SELECT password_hash FROM users WHERE id = %s",
            (user['id'],), fetch=True
        )
        if not row or not check_password_hash(row[0]['password_hash'], password):
            return jsonify({'error': 'Password is incorrect'}), 403

        uid = user['id']

        # Delete profile pic file if exists
        pic = user.get('profile_pic')
        if pic:
            pic_filename = pic.split('/')[-1]
            pic_path = PROFILE_PIC_FOLDER / pic_filename
            if pic_path.exists():
                pic_path.unlink()

        # Cascade delete user data
        _db.execute_query("DELETE FROM comment_reactions WHERE user_id = %s", (uid,))
        _db.execute_query("DELETE FROM recipe_comments WHERE user_id = %s", (uid,))
        _db.execute_query("DELETE FROM recipe_ratings WHERE user_id = %s", (uid,))
        _db.execute_query("DELETE FROM user_favorites WHERE user_id = %s", (uid,))

        # Delete user-submitted recipes & their related data
        user_recipes = _db.execute_query(
            "SELECT id FROM recipes WHERE submitted_by = %s", (uid,), fetch=True
        ) or []
        for r in user_recipes:
            rid = r['id']
            _db.execute_query("DELETE FROM steps WHERE recipe_id = %s", (rid,))
            _db.execute_query("DELETE FROM recipe_ingredients WHERE recipe_id = %s", (rid,))
            _db.execute_query("DELETE FROM recipe_tags WHERE recipe_id = %s", (rid,))
            _db.execute_query("DELETE FROM recipe_ratings WHERE recipe_id = %s", (rid,))
            _db.execute_query("DELETE FROM recipe_comments WHERE recipe_id = %s", (rid,))
            try:
                _db.execute_query("DELETE FROM nutrition WHERE recipe_id = %s", (rid,))
            except Exception:
                pass
            _db.execute_query("DELETE FROM recipes WHERE id = %s", (rid,))

        # Finally delete user
        _db.execute_query("DELETE FROM users WHERE id = %s", (uid,))

        _logger.info(f"User {user['username']} (id={uid}) deleted their account")
        return jsonify({'success': True, 'message': 'Account deleted successfully'})

    except Exception as e:
        _logger.error(f"Delete account error: {e}", exc_info=True)
        return jsonify({'error': 'Failed to delete account'}), 500
