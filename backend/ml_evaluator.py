"""
ML Model Evaluation Module
Provides metrics and evaluation tools for the recommendation system
"""
import numpy as np
from sklearn.metrics import ndcg_score, precision_score, recall_score
from typing import List, Dict, Any, Tuple
import pandas as pd
from collections import defaultdict


class RecommenderEvaluator:
    """Evaluate recommendation system performance"""
    
    def __init__(self, recommender, test_data: List[Dict] = None):
        """
        Initialize evaluator
        
        Args:
            recommender: RecipeRecommender instance
            test_data: List of test cases with ground truth
        """
        self.recommender = recommender
        self.test_data = test_data or []
    
    def precision_at_k(self, recommendations: List[int], relevant_items: List[int], k: int = 10) -> float:
        """
        Calculate Precision@K
        
        Args:
            recommendations: List of recommended recipe IDs
            relevant_items: List of relevant recipe IDs (ground truth)
            k: Number of top recommendations to consider
        
        Returns:
            Precision@K score (0-1)
        """
        if not recommendations or not relevant_items:
            return 0.0
        
        top_k = recommendations[:k]
        relevant_set = set(relevant_items)
        hits = sum(1 for item in top_k if item in relevant_set)
        
        return hits / k if k > 0 else 0.0
    
    def recall_at_k(self, recommendations: List[int], relevant_items: List[int], k: int = 10) -> float:
        """
        Calculate Recall@K
        
        Args:
            recommendations: List of recommended recipe IDs
            relevant_items: List of relevant recipe IDs (ground truth)
            k: Number of top recommendations to consider
        
        Returns:
            Recall@K score (0-1)
        """
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
        """
        Calculate Normalized Discounted Cumulative Gain@K
        
        Args:
            recommendations: List of recommended recipe IDs
            relevant_items: List of relevant recipe IDs with optional relevance scores
            k: Number of top recommendations to consider
        
        Returns:
            NDCG@K score (0-1)
        """
        if not recommendations or not relevant_items:
            return 0.0
        
        top_k = recommendations[:k]
        relevant_set = set(relevant_items)
        
        # Create relevance scores (1 for relevant, 0 for not relevant)
        relevance_scores = [1 if item in relevant_set else 0 for item in top_k]
        
        # Ideal DCG (all relevant items at top)
        ideal_scores = sorted(relevance_scores, reverse=True)
        
        if sum(ideal_scores) == 0:
            return 0.0
        
        # Calculate DCG
        dcg = sum((2**rel - 1) / np.log2(idx + 2) for idx, rel in enumerate(relevance_scores))
        idcg = sum((2**rel - 1) / np.log2(idx + 2) for idx, rel in enumerate(ideal_scores))
        
        return dcg / idcg if idcg > 0 else 0.0
    
    def mean_average_precision(self, all_recommendations: List[List[int]], 
                               all_relevant: List[List[int]]) -> float:
        """
        Calculate Mean Average Precision (MAP) across multiple queries
        
        Args:
            all_recommendations: List of recommendation lists
            all_relevant: List of relevant item lists
        
        Returns:
            MAP score (0-1)
        """
        if not all_recommendations or not all_relevant:
            return 0.0
        
        aps = []
        for recommendations, relevant_items in zip(all_recommendations, all_relevant):
            if not relevant_items:
                continue
            
            relevant_set = set(relevant_items)
            hits = 0
            sum_precisions = 0.0
            
            for i, item in enumerate(recommendations):
                if item in relevant_set:
                    hits += 1
                    precision_at_i = hits / (i + 1)
                    sum_precisions += precision_at_i
            
            ap = sum_precisions / len(relevant_set) if relevant_set else 0.0
            aps.append(ap)
        
        return np.mean(aps) if aps else 0.0
    
    def coverage(self, all_recommendations: List[List[int]], 
                 total_items: int) -> float:
        """
        Calculate catalog coverage - percentage of items that get recommended
        
        Args:
            all_recommendations: List of all recommendation lists
            total_items: Total number of items in catalog
        
        Returns:
            Coverage percentage (0-1)
        """
        if not all_recommendations or total_items == 0:
            return 0.0
        
        unique_recommendations = set()
        for recommendations in all_recommendations:
            unique_recommendations.update(recommendations)
        
        return len(unique_recommendations) / total_items
    
    def diversity_score(self, recommendations: List[Dict]) -> float:
        """
        Calculate recommendation diversity based on ingredient and tag variety
        
        Args:
            recommendations: List of recommended recipes with metadata
        
        Returns:
            Diversity score (0-1)
        """
        if not recommendations:
            return 0.0
        
        all_ingredients = set()
        all_tags = set()
        
        for recipe in recommendations:
            all_ingredients.update(recipe.get('ingredients', []))
            all_tags.update(recipe.get('tags', []))
        
        # Average number of unique characteristics per recommendation
        avg_unique = (len(all_ingredients) + len(all_tags)) / len(recommendations)
        
        # Normalize (assume max 20 unique items is very diverse)
        return min(avg_unique / 20.0, 1.0)
    
    def evaluate_test_set(self, k_values: List[int] = [5, 10, 20]) -> Dict[str, Any]:
        """
        Evaluate recommender on test set
        
        Args:
            k_values: List of k values to evaluate
        
        Returns:
            Dictionary of evaluation metrics
        """
        if not self.test_data:
            return {'error': 'No test data available'}
        
        results = {
            'precision': defaultdict(list),
            'recall': defaultdict(list),
            'f1': defaultdict(list),
            'ndcg': defaultdict(list)
        }
        
        all_recommendations = []
        all_relevant = []
        
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
        
        # Calculate averages
        summary = {}
        for metric in ['precision', 'recall', 'f1', 'ndcg']:
            summary[metric] = {}
            for k in k_values:
                values = results[metric][k]
                summary[metric][f'{metric}@{k}'] = {
                    'mean': np.mean(values) if values else 0.0,
                    'std': np.std(values) if values else 0.0,
                    'min': np.min(values) if values else 0.0,
                    'max': np.max(values) if values else 0.0
                }
        
        # Add MAP and coverage
        summary['map'] = self.mean_average_precision(all_recommendations, all_relevant)
        summary['coverage'] = self.coverage(
            all_recommendations,
            len(self.recommender.recipes_df) if self.recommender.recipes_df is not None else 0
        )
        
        return summary
    
    def compare_algorithms(self, algorithms: Dict[str, Any]) -> pd.DataFrame:
        """
        Compare multiple recommendation algorithms
        
        Args:
            algorithms: Dictionary of {name: recommender_instance}
        
        Returns:
            DataFrame with comparison results
        """
        results = []
        
        for name, recommender in algorithms.items():
            evaluator = RecommenderEvaluator(recommender, self.test_data)
            metrics = evaluator.evaluate_test_set(k_values=[10])
            
            results.append({
                'Algorithm': name,
                'Precision@10': metrics['precision']['precision@10']['mean'],
                'Recall@10': metrics['recall']['recall@10']['mean'],
                'F1@10': metrics['f1']['f1@10']['mean'],
                'NDCG@10': metrics['ndcg']['ndcg@10']['mean'],
                'MAP': metrics['map'],
                'Coverage': metrics['coverage']
            })
        
        return pd.DataFrame(results)
    
    def generate_report(self, output_file: str = 'evaluation_report.txt'):
        """Generate comprehensive evaluation report"""
        results = self.evaluate_test_set(k_values=[5, 10, 20])
        
        with open(output_file, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("RECOMMENDATION SYSTEM EVALUATION REPORT\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Test Set Size: {len(self.test_data)} queries\n\n")
            
            for metric_type in ['precision', 'recall', 'f1', 'ndcg']:
                f.write(f"\n{metric_type.upper()} Scores:\n")
                f.write("-" * 40 + "\n")
                for k, values in results[metric_type].items():
                    f.write(f"{k}: {values['mean']:.4f} (±{values['std']:.4f})\n")
            
            f.write(f"\nMean Average Precision (MAP): {results['map']:.4f}\n")
            f.write(f"Catalog Coverage: {results['coverage']:.4f}\n")
            
            f.write("\n" + "=" * 60 + "\n")
        
        print(f"Evaluation report saved to {output_file}")
        return results


def create_test_data_from_existing_recipes(db, num_test_cases: int = 100) -> List[Dict]:
    """
    Create test data from existing recipes for evaluation
    
    Args:
        db: Database instance
        num_test_cases: Number of test cases to generate
    
    Returns:
        List of test cases
    """
    # Get random sample of recipes
    recipes = db.execute_query(
        "SELECT id FROM recipes ORDER BY RAND() LIMIT %s",
        (num_test_cases,),
        fetch=True
    )
    
    test_data = []
    for recipe_row in recipes:
        recipe = db.get_recipe_by_id(recipe_row['id'])
        if not recipe or not recipe.get('ingredients'):
            continue
        
        # Use a subset of ingredients as query
        ingredients = recipe['ingredients']
        num_query_ingredients = max(2, len(ingredients) // 2)
        query_ingredients = ingredients[:num_query_ingredients]
        
        # The original recipe should be in relevant results
        test_data.append({
            'ingredients': query_ingredients,
            'dietary_preference': '',
            'cuisine_type': '',
            'relevant_recipes': [recipe['id']]
        })
    
    return test_data
