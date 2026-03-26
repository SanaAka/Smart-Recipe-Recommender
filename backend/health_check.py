"""
Backend Health Check and Error Detection Script
Tests all major components and identifies issues
"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test if all modules can be imported"""
    print("=" * 60)
    print("TESTING IMPORTS")
    print("=" * 60)

    modules_to_test = [
        ('dotenv', 'python-dotenv'),
        ('flask', 'flask'),
        ('flask_cors', 'flask-cors'),
        ('flask_limiter', 'flask-limiter'),
        ('flask_jwt_extended', 'flask-jwt-extended'),
        ('mysql.connector', 'mysql-connector-python'),
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('sklearn', 'scikit-learn'),
        ('pydantic', 'pydantic'),
    ]

    errors = []
    for module_name, package_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"[OK] {package_name:30}")
        except ImportError as e:
            print(f"[FAIL] {package_name:30} - MISSING")
            errors.append((package_name, str(e)))

    return errors


def test_configuration():
    """Test configuration loading"""
    print("\n" + "=" * 60)
    print("TESTING CONFIGURATION")
    print("=" * 60)

    from dotenv import load_dotenv

    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        print(f"[OK] .env file found at {env_path}")
        load_dotenv(dotenv_path=env_path)

        required_vars = [
            'DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_NAME',
            'SECRET_KEY', 'JWT_SECRET_KEY'
        ]

        missing = []
        for var in required_vars:
            value = os.getenv(var)
            if value:
                # Mask sensitive values
                display_value = value if var in ['DB_HOST', 'DB_PORT', 'DB_NAME'] else '***'
                print(f"[OK] {var:20} = {display_value}")
            else:
                print(f"[FAIL] {var:20} = NOT SET")
                missing.append(var)

        return missing
    else:
        print(f"[FAIL] .env file not found at {env_path}")
        return ['ENV_FILE_MISSING']


def test_database_connection():
    """Test database connectivity"""
    print("\n" + "=" * 60)
    print("TESTING DATABASE CONNECTION")
    print("=" * 60)

    try:
        from database import Database

        db = Database()
        print(f"Database config:")
        print(f"  Host: {db.host}")
        print(f"  Port: {db.port}")
        print(f"  User: {db.user}")
        print(f"  Database: {db.database}")

        print("\nAttempting connection...")
        db.connect()
        print("[OK] Database connection successful")

        # Test query
        stats = db.get_stats()
        print(f"[OK] Database stats retrieved:")
        print(f"  Total recipes: {stats.get('total_recipes', 0)}")
        print(f"  Total ingredients: {stats.get('total_ingredients', 0)}")
        print(f"  Total tags: {stats.get('total_tags', 0)}")

        db.disconnect()
        return None

    except Exception as e:
        print(f"[FAIL] Database connection failed: {e}")
        return str(e)


def test_ml_model():
    """Test ML model initialization"""
    print("\n" + "=" * 60)
    print("TESTING ML MODEL")
    print("=" * 60)

    try:
        from database import Database
        from ml_model import RecipeRecommender

        db = Database()
        print("Initializing ML model (this may take a moment)...")

        recommender = RecipeRecommender(db)

        if recommender.recipes_df is not None:
            print(f"[OK] ML model loaded with {len(recommender.recipes_df)} recipes")

            # Test recommendation
            test_ingredients = ['chicken', 'garlic', 'onion']
            print(f"\nTesting recommendations for: {test_ingredients}")

            results = recommender.recommend(
                ingredients=test_ingredients,
                limit=5
            )

            if results:
                print(f"[OK] Generated {len(results)} recommendations")
                for i, rec in enumerate(results[:3], 1):
                    print(f"  {i}. {rec['name']} (score: {rec.get('similarity_score', 0):.3f})")
            else:
                print("[FAIL] No recommendations generated")
                return "No recommendations"

            return None
        else:
            print("[FAIL] ML model failed to load recipes")
            return "Model load failed"

    except Exception as e:
        print(f"[FAIL] ML model test failed: {e}")
        import traceback
        traceback.print_exc()
        return str(e)


def test_enhanced_ml_model():
    """Test enhanced ML model"""
    print("\n" + "=" * 60)
    print("TESTING ENHANCED ML MODEL")
    print("=" * 60)

    try:
        from database import Database
        from ml_model_enhanced import HybridRecipeRecommender

        db = Database()
        print("Initializing enhanced ML model...")

        recommender = HybridRecipeRecommender(db)

        if recommender.recipes_df is not None:
            print(f"[OK] Enhanced ML model loaded with {len(recommender.recipes_df)} recipes")

            # Test recommendation
            test_ingredients = ['chicken', 'garlic', 'pasta']
            print(f"\nTesting recommendations for: {test_ingredients}")

            results = recommender.recommend(
                ingredients=test_ingredients,
                limit=5,
                diversify=True
            )

            if results:
                print(f"[OK] Generated {len(results)} diverse recommendations")
                for i, rec in enumerate(results[:3], 1):
                    print(f"  {i}. {rec['name']}")
                    print(f"     - Score: {rec.get('score', 0):.3f}")
                    print(f"     - Matches: {rec.get('ingredient_matches', 0)}")
                    if rec.get('explanation'):
                        print(f"     - {rec['explanation']}")
            else:
                print("[FAIL] No recommendations generated")
                return "No recommendations"

            return None
        else:
            print("[FAIL] Enhanced ML model failed to load recipes")
            return "Model load failed"

    except Exception as e:
        print(f"[FAIL] Enhanced ML model test failed: {e}")
        import traceback
        traceback.print_exc()
        return str(e)


def test_auth_system():
    """Test authentication system"""
    print("\n" + "=" * 60)
    print("TESTING AUTHENTICATION SYSTEM")
    print("=" * 60)

    try:
        from database import Database
        from auth import AuthManager

        db = Database()
        auth = AuthManager(db)

        print("[OK] Authentication system initialized")

        # Test token generation
        test_user_id = 1
        test_username = "test_user"
        tokens = auth.generate_tokens(test_user_id, test_username)

        if 'access_token' in tokens:
            print("[OK] JWT token generation working")
        else:
            print("[FAIL] JWT token generation failed")
            return "Token generation failed"

        return None

    except Exception as e:
        print(f"[FAIL] Authentication system test failed: {e}")
        return str(e)


def main():
    """Run all tests"""
    print("\n")
    print("=" * 60)
    print(" " * 10 + "BACKEND HEALTH CHECK & ERROR DETECTION")
    print("=" * 60)
    print()

    errors = {}

    # Test imports
    import_errors = test_imports()
    if import_errors:
        errors['imports'] = import_errors

    # Test configuration
    config_errors = test_configuration()
    if config_errors:
        errors['configuration'] = config_errors

    # Only proceed if basic requirements are met
    if not import_errors and not config_errors:
        # Test database
        db_error = test_database_connection()
        if db_error:
            errors['database'] = db_error
        else:
            # Test ML models only if database works
            ml_error = test_ml_model()
            if ml_error:
                errors['ml_model'] = ml_error

            enhanced_ml_error = test_enhanced_ml_model()
            if enhanced_ml_error:
                errors['enhanced_ml_model'] = enhanced_ml_error

            # Test auth
            auth_error = test_auth_system()
            if auth_error:
                errors['auth'] = auth_error

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if not errors:
        print("[OK] All tests passed! Backend is healthy.")
        return 0
    else:
        print("[FAIL] Issues detected:")
        for component, error in errors.items():
            print(f"\n{component.upper()}:")
            if isinstance(error, list):
                for item in error:
                    print(f"  - {item}")
            else:
                print(f"  - {error}")

        print("\n" + "=" * 60)
        print("RECOMMENDATIONS:")
        print("=" * 60)

        if 'imports' in errors:
            print("\n1. Install missing packages:")
            print("   pip install -r requirements.txt")

        if 'configuration' in errors:
            print("\n2. Configure environment variables:")
            print("   Copy .env.example to .env and fill in values")

        if 'database' in errors:
            print("\n3. Fix database connection:")
            print("   - Ensure MySQL is running")
            print("   - Verify credentials in .env")
            print("   - Check database exists and is accessible")

        return 1


if __name__ == '__main__':
    exit(main())
