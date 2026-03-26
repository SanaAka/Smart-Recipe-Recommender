"""
Enhanced ML Evaluation and Monitoring Module
Provides comprehensive metrics, A/B testing, and real-time monitoring
"""
import numpy as np
import pandas as pd
from sklearn.metrics import ndcg_score
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
import json
from pathlib import Path


class EnhancedRecommenderEvaluator:
    """Advanced evaluation with monitoring and A/B testing"""

    def __init__(self, recommender, db, test_data: List[Dict] = None):
        """
        Initialize evaluator

        Args:
            recommender: RecipeRecommender instance
            db: Database instance
            test_data: List of test cases with ground truth
        """
        self.recommender = recommender
        self.db = db
        self.test_data = test_data or []

        # Monitoring data
        self.metrics_history = []
        self.performance_log = []

    def precision_at_k(self, recommendations: List[int], relevant_items: List[int], k: int = 10) -> float:
        """Calculate Precision@K"""
        if not recommendations or not relevant_items:
            return 0.0

        top_k = recommendations[:k]
        relevant_set = set(relevant_items)
        hits = sum(1 for item in top_k if item in relevant_set)

        return hits / k if k > 0 else 0.0

    def recall_at_k(self, recommendations: List[int], relevant_items: List[int], k: int = 10) -> float:
        """Calculate Recall@K"""
        if not recommendations or not relevant_items:
            return 0.0

        top_k = recommendations[:k]
        relevant_set = set(relevant_items)
        hits = sum(1 for item in top_k if item in relevant_set)

        return hits / len(relevant_set) if relevant_set else 0.0

    def f1_score_at_k(self, recommendations: List[int], relevant_items: List[int], k: int = 10) -> float:
        """Calculate F1@K score"""
        precision = self.precision_at_k(recommendations, relevant_items, k)
        recall = self.recall_at_k(recommendations, relevant_items, k)

        if precision + recall == 0:
            return 0.0

        return 2 * (precision * recall) / (precision + recall)

    def ndcg_at_k(self, recommendations: List[int], relevant_items: List[int], k: int = 10) -> float:
        """Calculate Normalized Discounted Cumulative Gain@K"""
        if not recommendations or not relevant_items:
            return 0.0

        top_k = recommendations[:k]
        relevant_set = set(relevant_items)

        # Create relevance scores
        relevance_scores = [1 if item in relevant_set else 0 for item in top_k]
        ideal_scores = sorted(relevance_scores, reverse=True)

        if sum(ideal_scores) == 0:
            return 0.0

        # Calculate DCG
        dcg = sum((2**rel - 1) / np.log2(idx + 2) for idx, rel in enumerate(relevance_scores))
        idcg = sum((2**rel - 1) / np.log2(idx + 2) for idx, rel in enumerate(ideal_scores))

        return dcg / idcg if idcg > 0 else 0.0

    def mean_reciprocal_rank(self, recommendations: List[int], relevant_items: List[int]) -> float:
        """Calculate Mean Reciprocal Rank (MRR)"""
        if not recommendations or not relevant_items:
            return 0.0

        relevant_set = set(relevant_items)

        for idx, item in enumerate(recommendations):
            if item in relevant_set:
                return 1.0 / (idx + 1)

        return 0.0

    def hit_rate_at_k(self, all_recommendations: List[List[int]],
                       all_relevant: List[List[int]], k: int = 10) -> float:
        """Calculate hit rate - percentage of queries with at least one relevant item in top-k"""
        if not all_recommendations or not all_relevant:
            return 0.0

        hits = 0
        for recommendations, relevant_items in zip(all_recommendations, all_relevant):
            top_k = recommendations[:k]
            relevant_set = set(relevant_items)
            if any(item in relevant_set for item in top_k):
                hits += 1

        return hits / len(all_recommendations)

    def coverage(self, all_recommendations: List[List[int]], total_items: int) -> float:
        """Calculate catalog coverage"""
        if not all_recommendations or total_items == 0:
            return 0.0

        unique_recommendations = set()
        for recommendations in all_recommendations:
            unique_recommendations.update(recommendations)

        return len(unique_recommendations) / total_items

    def diversity_score(self, recommendations: List[Dict]) -> float:
        """Calculate recommendation diversity"""
        if not recommendations:
            return 0.0

        all_ingredients = set()
        all_tags = set()

        for recipe in recommendations:
            all_ingredients.update(recipe.get('ingredients', []))
            all_tags.update(recipe.get('tags', []))

        avg_unique = (len(all_ingredients) + len(all_tags)) / len(recommendations)
        return min(avg_unique / 20.0, 1.0)

    def novelty_score(self, recommendations: List[int]) -> float:
        """Calculate novelty - how unpopular/surprising the recommendations are"""
        try:
            # Get popularity scores
            popularity_query = """
                SELECT recipe_id, COUNT(*) as interaction_count
                FROM (
                    SELECT recipe_id FROM user_favorites
                    UNION ALL
                    SELECT recipe_id FROM recipe_ratings
                ) as interactions
                GROUP BY recipe_id
            """
            popularity_data = self.db.execute_query(popularity_query, fetch=True)

            if not popularity_data:
                return 0.5  # Neutral score

            popularity_map = {row['recipe_id']: row['interaction_count'] for row in popularity_data}
            max_popularity = max(popularity_map.values())

            # Calculate average unpopularity of recommendations
            novelty_scores = []
            for recipe_id in recommendations:
                popularity = popularity_map.get(recipe_id, 0)
                # Invert: less popular = more novel
                novelty = 1.0 - (popularity / max_popularity)
                novelty_scores.append(novelty)

            return np.mean(novelty_scores)

        except Exception as e:
            print(f"Novelty calculation failed: {e}")
            return 0.5

    def evaluate_online_metrics(self, days=7) -> Dict[str, Any]:
        """Evaluate real-world performance metrics from user interactions"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            metrics = {}

            # Click-through rate (CTR) - approximated by views/ratings
            ctr_query = """
                SELECT
                    COUNT(DISTINCT recipe_id) as total_viewed,
                    COUNT(DISTINCT user_id) as total_users
                FROM recipe_ratings
                WHERE created_at >= %s
            """
            ctr_data = self.db.execute_query(ctr_query, (cutoff_date,), fetch=True)
            if ctr_data:
                total_viewed = int(ctr_data[0]['total_viewed'])
                total_users = int(ctr_data[0]['total_users'])
                metrics['avg_recipes_per_user'] = float(
                    total_viewed / max(total_users, 1)
                )

            # Engagement rate (favorites and ratings)
            engagement_query = """
                SELECT
                    COUNT(DISTINCT f.recipe_id) as favorited,
                    COUNT(DISTINCT r.recipe_id) as rated
                FROM recipes rec
                LEFT JOIN user_favorites f ON rec.id = f.recipe_id AND f.created_at >= %s
                LEFT JOIN recipe_ratings r ON rec.id = r.recipe_id AND r.created_at >= %s
            """
            engagement_data = self.db.execute_query(
                engagement_query, (cutoff_date, cutoff_date), fetch=True
            )
            if engagement_data:
                metrics['engagement_rate'] = {
                    'favorite_rate': int(engagement_data[0]['favorited']),
                    'rating_rate': int(engagement_data[0]['rated'])
                }

            # Average rating for recently recommended recipes
            rating_query = """
                SELECT AVG(rating) as avg_rating, COUNT(*) as rating_count
                FROM recipe_ratings
                WHERE created_at >= %s
            """
            rating_data = self.db.execute_query(rating_query, (cutoff_date,), fetch=True)
            if rating_data:
                # Convert Decimal to float for JSON serialization
                avg_rating = rating_data[0]['avg_rating']
                metrics['average_rating'] = float(avg_rating) if avg_rating is not None else 0.0
                metrics['rating_count'] = int(rating_data[0]['rating_count'])

            # User retention (users who return)
            retention_query = """
                SELECT
                    COUNT(DISTINCT user_id) as returning_users
                FROM (
                    SELECT user_id, COUNT(DISTINCT DATE(created_at)) as active_days
                    FROM recipe_ratings
                    WHERE created_at >= %s
                    GROUP BY user_id
                    HAVING active_days > 1
                ) as retention_data
            """
            retention_data = self.db.execute_query(retention_query, (cutoff_date,), fetch=True)
            if retention_data:
                metrics['returning_users'] = int(retention_data[0]['returning_users'])

            metrics['evaluation_period_days'] = days
            metrics['timestamp'] = datetime.now().isoformat()

            return metrics

        except Exception as e:
            print(f"Online metrics evaluation failed: {e}")
            return {'error': str(e)}

    def evaluate_test_set(self, k_values: List[int] = [5, 10, 20]) -> Dict[str, Any]:
        """Comprehensive evaluation on test set"""
        if not self.test_data:
            return {'error': 'No test data available'}

        results = {
            'precision': defaultdict(list),
            'recall': defaultdict(list),
            'f1': defaultdict(list),
            'ndcg': defaultdict(list),
            'mrr': []
        }

        all_recommendations = []
        all_relevant = []
        all_diversity_scores = []
        all_novelty_scores = []

        for test_case in self.test_data:
            ingredients = test_case.get('ingredients', [])
            relevant_recipes = test_case.get('relevant_recipes', [])

            if not ingredients or not relevant_recipes:
                continue

            # Get recommendations
            recommendations = self.recommender.recommend(
                ingredients=ingredients,
                dietary_preference=test_case.get('dietary_preference', ''),
                cuisine_type=test_case.get('cuisine_type', ''),
                limit=max(k_values)
            )

            recommendation_ids = [r['id'] for r in recommendations]
            all_recommendations.append(recommendation_ids)
            all_relevant.append(relevant_recipes)

            # Calculate diversity and novelty
            all_diversity_scores.append(self.diversity_score(recommendations))
            all_novelty_scores.append(self.novelty_score(recommendation_ids))

            # Calculate metrics for each k
            for k in k_values:
                results['precision'][k].append(
                    self.precision_at_k(recommendation_ids, relevant_recipes, k)
                )
                results['recall'][k].append(
                    self.recall_at_k(recommendation_ids, relevant_recipes, k)
                )
                results['f1'][k].append(
                    self.f1_score_at_k(recommendation_ids, relevant_recipes, k)
                )
                results['ndcg'][k].append(
                    self.ndcg_at_k(recommendation_ids, relevant_recipes, k)
                )

            # MRR
            results['mrr'].append(
                self.mean_reciprocal_rank(recommendation_ids, relevant_recipes)
            )

        # Calculate summary statistics
        summary = {
            'test_set_size': len(self.test_data),
            'evaluated_queries': len(all_recommendations)
        }

        for metric in ['precision', 'recall', 'f1', 'ndcg']:
            summary[metric] = {}
            for k in k_values:
                values = results[metric][k]
                summary[metric][f'{metric}@{k}'] = {
                    'mean': float(np.mean(values)) if values else 0.0,
                    'std': float(np.std(values)) if values else 0.0,
                    'min': float(np.min(values)) if values else 0.0,
                    'max': float(np.max(values)) if values else 0.0
                }

        # Add other metrics
        summary['mrr'] = {
            'mean': float(np.mean(results['mrr'])) if results['mrr'] else 0.0,
            'std': float(np.std(results['mrr'])) if results['mrr'] else 0.0
        }

        summary['hit_rate'] = {}
        for k in k_values:
            summary['hit_rate'][f'hit_rate@{k}'] = self.hit_rate_at_k(
                all_recommendations, all_relevant, k
            )

        summary['coverage'] = self.coverage(
            all_recommendations,
            len(self.recommender.recipes_df) if hasattr(self.recommender, 'recipes_df') else 0
        )

        summary['diversity'] = {
            'mean': float(np.mean(all_diversity_scores)) if all_diversity_scores else 0.0,
            'std': float(np.std(all_diversity_scores)) if all_diversity_scores else 0.0
        }

        summary['novelty'] = {
            'mean': float(np.mean(all_novelty_scores)) if all_novelty_scores else 0.0,
            'std': float(np.std(all_novelty_scores)) if all_novelty_scores else 0.0
        }

        summary['timestamp'] = datetime.now().isoformat()

        # Store in history
        self.metrics_history.append(summary)

        return summary

    def monitor_performance(self, recommendation_time: float, num_results: int):
        """Monitor recommendation performance"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'recommendation_time_ms': recommendation_time * 1000,
            'num_results': num_results
        }

        self.performance_log.append(log_entry)

        # Keep only last 1000 entries
        if len(self.performance_log) > 1000:
            self.performance_log = self.performance_log[-1000:]

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.performance_log:
            return {}

        times = [entry['recommendation_time_ms'] for entry in self.performance_log]

        return {
            'avg_response_time_ms': float(np.mean(times)),
            'median_response_time_ms': float(np.median(times)),
            'p95_response_time_ms': float(np.percentile(times, 95)),
            'p99_response_time_ms': float(np.percentile(times, 99)),
            'total_requests': len(self.performance_log)
        }

    def generate_report(self, output_file: str = 'evaluation_report.json'):
        """Generate comprehensive evaluation report"""
        offline_metrics = self.evaluate_test_set(k_values=[5, 10, 20])
        online_metrics = self.evaluate_online_metrics(days=7)
        performance_stats = self.get_performance_stats()

        report = {
            'offline_metrics': offline_metrics,
            'online_metrics': online_metrics,
            'performance_stats': performance_stats,
            'generated_at': datetime.now().isoformat()
        }

        # Save to file
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"Evaluation report saved to {output_file}")
        return report

    def compare_models(self, model_a, model_b, model_a_name="Model A",
                        model_b_name="Model B") -> pd.DataFrame:
        """Compare two recommendation models"""
        results = []

        for model, name in [(model_a, model_a_name), (model_b, model_b_name)]:
            evaluator = EnhancedRecommenderEvaluator(model, self.db, self.test_data)
            metrics = evaluator.evaluate_test_set(k_values=[10])

            results.append({
                'Model': name,
                'Precision@10': metrics['precision']['precision@10']['mean'],
                'Recall@10': metrics['recall']['recall@10']['mean'],
                'F1@10': metrics['f1']['f1@10']['mean'],
                'NDCG@10': metrics['ndcg']['ndcg@10']['mean'],
                'MRR': metrics['mrr']['mean'],
                'Hit Rate@10': metrics['hit_rate']['hit_rate@10'],
                'Coverage': metrics['coverage'],
                'Diversity': metrics['diversity']['mean'],
                'Novelty': metrics['novelty']['mean']
            })

        df = pd.DataFrame(results)

        # Calculate improvement
        if len(results) == 2:
            improvement = {}
            for col in df.columns:
                if col != 'Model':
                    improvement[col] = (
                        (df.loc[1, col] - df.loc[0, col]) / df.loc[0, col] * 100
                        if df.loc[0, col] != 0 else 0
                    )
            improvement['Model'] = 'Improvement %'
            df = pd.concat([df, pd.DataFrame([improvement])], ignore_index=True)

        return df


def create_test_data_from_user_behavior(db, num_test_cases: int = 200) -> List[Dict]:
    """
    Create test data from actual user behavior (favorites, ratings)

    Args:
        db: Database instance
        num_test_cases: Number of test cases to generate

    Returns:
        List of test cases
    """
    try:
        # Get recipes that users have favorited or rated highly
        query = """
            SELECT
                r.id,
                GROUP_CONCAT(DISTINCT i.name SEPARATOR '|') as ingredients
            FROM recipes r
            JOIN recipe_ingredients ri ON r.id = ri.recipe_id
            JOIN ingredients i ON ri.ingredient_id = i.id
            WHERE r.id IN (
                SELECT recipe_id FROM user_favorites
                UNION
                SELECT recipe_id FROM recipe_ratings WHERE rating >= 4
            )
            GROUP BY r.id
            ORDER BY RAND()
            LIMIT %s
        """

        recipes = db.execute_query(query, (num_test_cases,), fetch=True)

        test_data = []
        for recipe_row in recipes:
            if not recipe_row.get('ingredients'):
                continue

            ingredients = recipe_row['ingredients'].split('|')

            # Use a subset of ingredients as query
            num_query_ingredients = max(2, len(ingredients) // 2)
            query_ingredients = ingredients[:num_query_ingredients]

            # The original recipe should be in relevant results
            test_data.append({
                'ingredients': query_ingredients,
                'dietary_preference': '',
                'cuisine_type': '',
                'relevant_recipes': [recipe_row['id']]
            })

        return test_data

    except Exception as e:
        print(f"Failed to create test data from user behavior: {e}")
        return []
