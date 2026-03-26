"""
ML Model Training Script
Trains both original and enhanced ML models on your database
Provides comprehensive metrics and validation
"""
import os
import sys
import time
import shutil
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from database import Database
from ml_model import RecipeRecommender
from ml_model_enhanced import HybridRecipeRecommender
from ml_evaluator_enhanced import EnhancedRecommenderEvaluator, create_test_data_from_user_behavior


def clear_caches():
    """Clear all ML model caches"""
    print("=" * 80)
    print("CLEARING OLD CACHES")
    print("=" * 80)

    cache_dirs = ['ml_cache', 'ml_cache_test', '__pycache__']

    for cache_dir in cache_dirs:
        cache_path = Path(__file__).parent / cache_dir
        if cache_path.exists():
            try:
                shutil.rmtree(cache_path)
                print(f"[OK] Cleared {cache_dir}")
            except Exception as e:
                print(f"[WARN] Could not clear {cache_dir}: {e}")
        else:
            print(f"[SKIP] {cache_dir} does not exist")

    print()


def train_original_model(db):
    """Train the original TF-IDF model"""
    print("=" * 80)
    print("TRAINING ORIGINAL ML MODEL")
    print("=" * 80)

    start_time = time.time()

    try:
        print("Initializing RecipeRecommender...")
        recommender = RecipeRecommender(db)

        training_time = time.time() - start_time

        if recommender.recipes_df is not None:
            print(f"\n[OK] Original model trained successfully!")
            print(f"  Training time: {training_time:.2f}s")
            print(f"  Recipes loaded: {len(recommender.recipes_df)}")
            print(f"  TF-IDF matrix shape: {recommender.tfidf_matrix.shape}")
            print(f"  Feature count: {len(recommender.vectorizer.vocabulary_)}")

            # Test recommendation
            print("\n  Testing recommendations...")
            test_ingredients = ['chicken', 'garlic', 'pasta']
            results = recommender.recommend(ingredients=test_ingredients, limit=5)

            if results:
                print(f"  [OK] Generated {len(results)} test recommendations")
                for i, rec in enumerate(results[:3], 1):
                    print(f"    {i}. {rec['name']} (score: {rec.get('similarity_score', 0):.3f})")
            else:
                print("  [WARN] No recommendations generated")

            return recommender, training_time
        else:
            print("[FAIL] Model failed to load recipes")
            return None, 0

    except Exception as e:
        print(f"[FAIL] Training failed: {e}")
        import traceback
        traceback.print_exc()
        return None, 0


def train_enhanced_model(db):
    """Train the enhanced hybrid model"""
    print("\n" + "=" * 80)
    print("TRAINING ENHANCED HYBRID ML MODEL")
    print("=" * 80)

    start_time = time.time()

    try:
        print("Initializing HybridRecipeRecommender...")
        recommender = HybridRecipeRecommender(db)

        training_time = time.time() - start_time

        if recommender.recipes_df is not None:
            print(f"\n[OK] Enhanced model trained successfully!")
            print(f"  Training time: {training_time:.2f}s")
            print(f"  Recipes loaded: {len(recommender.recipes_df)}")
            print(f"  TF-IDF matrix shape: {recommender.tfidf_matrix.shape}")
            print(f"  Feature count: {len(recommender.content_vectorizer.vocabulary_)}")

            # Check collaborative filtering
            if recommender.svd_model:
                print(f"  Collaborative filtering: ENABLED ({recommender.svd_model.n_components} factors)")
            else:
                print(f"  Collaborative filtering: DISABLED (not enough rating data)")

            # Check popularity scores
            if recommender.popularity_scores:
                print(f"  Popularity scores: {len(recommender.popularity_scores)} recipes")
            else:
                print(f"  Popularity scores: NONE")

            # Test recommendation with all features
            print("\n  Testing recommendations...")
            test_ingredients = ['chicken', 'garlic', 'pasta']
            results = recommender.recommend(
                ingredients=test_ingredients,
                limit=5,
                diversify=True
            )

            if results:
                print(f"  [OK] Generated {len(results)} diverse recommendations")
                for i, rec in enumerate(results[:3], 1):
                    print(f"    {i}. {rec['name']}")
                    print(f"       Score: {rec.get('score', 0):.3f} | Matches: {rec.get('ingredient_matches', 0)}")
                    if rec.get('explanation'):
                        print(f"       {rec['explanation']}")
            else:
                print("  [WARN] No recommendations generated")

            return recommender, training_time
        else:
            print("[FAIL] Model failed to load recipes")
            return None, 0

    except Exception as e:
        print(f"[FAIL] Training failed: {e}")
        import traceback
        traceback.print_exc()
        return None, 0


def evaluate_models(db, original_model, enhanced_model):
    """Evaluate both models and compare"""
    print("\n" + "=" * 80)
    print("EVALUATING MODELS")
    print("=" * 80)

    if not original_model and not enhanced_model:
        print("[SKIP] No models to evaluate")
        return

    try:
        # Create test data from user behavior
        print("\nCreating test dataset from user behavior...")
        test_data = create_test_data_from_user_behavior(db, num_test_cases=50)

        if not test_data:
            print("[WARN] No test data available (need user favorites/ratings)")
            print("       Skipping evaluation...")
            return

        print(f"[OK] Created {len(test_data)} test cases")

        results = {}

        # Evaluate original model
        if original_model:
            print("\nEvaluating original model...")
            evaluator = EnhancedRecommenderEvaluator(original_model, db, test_data)
            results['original'] = evaluator.evaluate_test_set(k_values=[5, 10])
            print("[OK] Original model evaluated")

        # Evaluate enhanced model
        if enhanced_model:
            print("\nEvaluating enhanced model...")
            evaluator = EnhancedRecommenderEvaluator(enhanced_model, db, test_data)
            results['enhanced'] = evaluator.evaluate_test_set(k_values=[5, 10])
            print("[OK] Enhanced model evaluated")

        # Display comparison
        print("\n" + "=" * 80)
        print("EVALUATION RESULTS")
        print("=" * 80)

        if 'original' in results and 'enhanced' in results:
            print("\nComparison (Original vs Enhanced):")
            print("-" * 80)

            metrics_to_show = [
                ('precision@10', 'Precision@10'),
                ('recall@10', 'Recall@10'),
                ('f1@10', 'F1@10'),
                ('ndcg@10', 'NDCG@10'),
            ]

            for metric_key, metric_name in metrics_to_show:
                orig_val = 0
                enh_val = 0

                # Find the metric in results
                for metric_type in ['precision', 'recall', 'f1', 'ndcg']:
                    if metric_key in results['original'].get(metric_type, {}):
                        orig_val = results['original'][metric_type][metric_key]['mean']
                        enh_val = results['enhanced'][metric_type][metric_key]['mean']
                        break

                improvement = ((enh_val - orig_val) / orig_val * 100) if orig_val > 0 else 0
                arrow = "↑" if improvement > 0 else "↓" if improvement < 0 else "="

                print(f"{metric_name:20} Original: {orig_val:.4f} | Enhanced: {enh_val:.4f} | {arrow} {abs(improvement):+.1f}%")

            # Additional metrics
            print("\nAdditional Metrics:")
            print("-" * 80)

            for model_name, model_results in [('Original', results['original']), ('Enhanced', results['enhanced'])]:
                print(f"\n{model_name}:")
                print(f"  Hit Rate@10:    {model_results.get('hit_rate', {}).get('hit_rate@10', 0):.4f}")
                print(f"  Coverage:       {model_results.get('coverage', 0):.4f}")
                print(f"  Diversity:      {model_results.get('diversity', {}).get('mean', 0):.4f}")
                print(f"  Novelty:        {model_results.get('novelty', {}).get('mean', 0):.4f}")
                print(f"  MRR:            {model_results.get('mrr', {}).get('mean', 0):.4f}")

        elif 'enhanced' in results:
            print("\nEnhanced Model Results:")
            print("-" * 80)
            enh = results['enhanced']

            print(f"Precision@10:    {enh['precision']['precision@10']['mean']:.4f}")
            print(f"Recall@10:       {enh['recall']['recall@10']['mean']:.4f}")
            print(f"F1@10:           {enh['f1']['f1@10']['mean']:.4f}")
            print(f"NDCG@10:         {enh['ndcg']['ndcg@10']['mean']:.4f}")
            print(f"Hit Rate@10:     {enh.get('hit_rate', {}).get('hit_rate@10', 0):.4f}")
            print(f"Coverage:        {enh.get('coverage', 0):.4f}")
            print(f"Diversity:       {enh.get('diversity', {}).get('mean', 0):.4f}")
            print(f"Novelty:         {enh.get('novelty', {}).get('mean', 0):.4f}")

        # Save detailed report
        if enhanced_model:
            print("\n" + "-" * 80)
            report_file = f"evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            evaluator.generate_report(report_file)
            print(f"[OK] Detailed report saved to: {report_file}")

    except Exception as e:
        print(f"[FAIL] Evaluation failed: {e}")
        import traceback
        traceback.print_exc()


def display_database_stats(db):
    """Display database statistics"""
    print("\n" + "=" * 80)
    print("DATABASE STATISTICS")
    print("=" * 80)

    try:
        stats = db.get_stats()
        print(f"Total Recipes:     {stats.get('total_recipes', 0):,}")
        print(f"Total Ingredients: {stats.get('total_ingredients', 0):,}")
        print(f"Total Tags:        {stats.get('total_tags', 0):,}")

        # Get user interaction stats
        interactions_query = """
            SELECT
                (SELECT COUNT(*) FROM user_favorites) as favorites,
                (SELECT COUNT(*) FROM recipe_ratings) as ratings,
                (SELECT COUNT(*) FROM recipe_comments) as comments,
                (SELECT COUNT(DISTINCT user_id) FROM users) as users
        """
        interactions = db.execute_query(interactions_query, fetch=True)

        if interactions:
            stats_row = interactions[0]
            print(f"\nUser Interactions:")
            print(f"  Total Users:     {stats_row.get('users', 0):,}")
            print(f"  Favorites:       {stats_row.get('favorites', 0):,}")
            print(f"  Ratings:         {stats_row.get('ratings', 0):,}")
            print(f"  Comments:        {stats_row.get('comments', 0):,}")

    except Exception as e:
        print(f"[WARN] Could not retrieve all stats: {e}")


def main():
    """Main training pipeline"""
    print("\n")
    print("=" * 80)
    print(" " * 25 + "ML MODEL TRAINING")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load environment
    env_path = Path(__file__).parent / '.env'
    if not env_path.exists():
        print("[FAIL] .env file not found!")
        print("Please create .env file with database credentials")
        return 1

    load_dotenv(dotenv_path=env_path)

    # Connect to database
    print("Connecting to database...")
    db = Database()

    try:
        db.connect()
        print("[OK] Database connected")
    except Exception as e:
        print(f"[FAIL] Database connection failed: {e}")
        return 1

    # Display stats
    display_database_stats(db)

    # Ask user what to train
    print("\n" + "=" * 80)
    print("TRAINING OPTIONS")
    print("=" * 80)
    print("1. Train Original Model only (fast, basic TF-IDF)")
    print("2. Train Enhanced Model only (recommended, hybrid system)")
    print("3. Train Both Models and Compare (comprehensive)")
    print("4. Clear caches and retrain Enhanced Model")
    print()

    choice = input("Enter your choice (1-4): ").strip()

    original_model = None
    enhanced_model = None
    total_start = time.time()

    if choice == '1':
        print("\n[INFO] Training Original Model...")
        original_model, _ = train_original_model(db)

    elif choice == '2':
        print("\n[INFO] Training Enhanced Model...")
        enhanced_model, _ = train_enhanced_model(db)

    elif choice == '3':
        print("\n[INFO] Training Both Models...")
        original_model, orig_time = train_original_model(db)
        enhanced_model, enh_time = train_enhanced_model(db)

        if original_model and enhanced_model:
            print("\n" + "=" * 80)
            print("TRAINING TIME COMPARISON")
            print("=" * 80)
            print(f"Original Model:  {orig_time:.2f}s")
            print(f"Enhanced Model:  {enh_time:.2f}s")
            print(f"Difference:      {abs(enh_time - orig_time):.2f}s")

    elif choice == '4':
        print("\n[INFO] Clearing caches and retraining...")
        clear_caches()
        enhanced_model, _ = train_enhanced_model(db)

    else:
        print("[FAIL] Invalid choice")
        return 1

    # Evaluate if requested
    if original_model or enhanced_model:
        print("\n" + "=" * 80)
        evaluate_choice = input("\nRun evaluation? (y/n): ").strip().lower()

        if evaluate_choice == 'y':
            evaluate_models(db, original_model, enhanced_model)

    total_time = time.time() - total_start

    # Final summary
    print("\n" + "=" * 80)
    print("TRAINING COMPLETE")
    print("=" * 80)
    print(f"Total time: {total_time:.2f}s")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if enhanced_model:
        print("\n[OK] Enhanced model is ready to use!")
        print("     Restart your Flask app to use the new model")
        print("     Run: python app_v2.py")

    db.disconnect()
    return 0


if __name__ == '__main__':
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Training interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n[FAIL] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
