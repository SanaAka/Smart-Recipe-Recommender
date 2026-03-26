"""
Simple Integration Script for Enhanced ML Model
Run this to switch from the original to the enhanced ML model
"""
import os
from pathlib import Path


def backup_file(file_path):
    """Create a backup of the original file"""
    backup_path = f"{file_path}.backup"
    if os.path.exists(file_path) and not os.path.exists(backup_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Backed up {file_path} to {backup_path}")
        return True
    return False


def integrate_enhanced_ml():
    """Integrate the enhanced ML model into app_v2.py"""
    app_file = Path(__file__).parent / 'app_v2.py'

    if not app_file.exists():
        print("✗ app_v2.py not found!")
        return False

    # Backup
    backup_file(str(app_file))

    # Read current content
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if already integrated
    if 'ml_model_enhanced' in content:
        print("✓ Enhanced ML model already integrated")
        return True

    # Replace the import
    original_import = "from ml_model import RecipeRecommender"
    enhanced_import = "from ml_model_enhanced import HybridRecipeRecommender as RecipeRecommender"

    if original_import in content:
        content = content.replace(original_import, enhanced_import)

        # Write back
        with open(app_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✓ Successfully integrated enhanced ML model")
        print("  Changed: from ml_model import RecipeRecommender")
        print("        → from ml_model_enhanced import HybridRecipeRecommender as RecipeRecommender")
        return True
    else:
        print("✗ Could not find import statement to replace")
        print("  Please manually add: from ml_model_enhanced import HybridRecipeRecommender as RecipeRecommender")
        return False


def revert_to_original():
    """Revert to the original ML model"""
    app_file = Path(__file__).parent / 'app_v2.py'
    backup_file = Path(str(app_file) + '.backup')

    if not backup_file.exists():
        print("✗ No backup found to revert to")
        return False

    # Restore from backup
    with open(backup_file, 'r', encoding='utf-8') as f:
        content = f.read()

    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print("✓ Reverted to original ML model")
    return True


def main():
    print("=" * 60)
    print("Enhanced ML Model Integration Tool")
    print("=" * 60)
    print()
    print("What would you like to do?")
    print("1. Integrate enhanced ML model (recommended)")
    print("2. Revert to original ML model")
    print("3. Exit")
    print()

    choice = input("Enter your choice (1-3): ").strip()

    if choice == '1':
        print("\nIntegrating enhanced ML model...")
        if integrate_enhanced_ml():
            print("\n✓ Integration complete!")
            print("\nNext steps:")
            print("1. Restart the Flask application")
            print("2. Run: python health_check.py")
            print("3. Monitor performance in production")
        else:
            print("\n✗ Integration failed. Please check the errors above.")

    elif choice == '2':
        print("\nReverting to original ML model...")
        if revert_to_original():
            print("\n✓ Revert complete!")
            print("\nNext step: Restart the Flask application")
        else:
            print("\n✗ Revert failed. No backup found.")

    elif choice == '3':
        print("Exiting...")
        return

    else:
        print("Invalid choice. Exiting...")


if __name__ == '__main__':
    main()
