import pandas as pd
import numpy as np
from recommender import ProductRecommender, load_products_from_csv
from typing import List, Dict, Set

def load_benchmark_queries(file_path: str = "benchmark_queries.csv") -> pd.DataFrame:
    """Load benchmark queries from CSV file"""
    return pd.read_csv(file_path)

def calculate_recall_at_k(recommended: List[str], expected: Set[str], k: int) -> float:
    """
    Calculate Recall@k for a single query.
    
    Args:
        recommended: List of recommended product names
        expected: Set of expected product names
        k: Number of top recommendations to consider
        
    Returns:
        Recall@k score (between 0 and 1)
    """
    if not recommended or not expected:
        return 0.0
        
    top_k = recommended[:k]
    relevant_in_top_k = sum(1 for product in top_k if product in expected)
    return relevant_in_top_k / len(expected) if expected else 0.0

def calculate_ap_at_k(recommended: List[str], expected: Set[str], k: int) -> float:
    """
    Calculate Average Precision@k for a single query.
    
    Args:
        recommended: List of recommended product names
        expected: Set of expected product names
        k: Number of top recommendations to consider
        
    Returns:
        AP@k score (between 0 and 1)
    """
    if not recommended or not expected:
        return 0.0
        
    top_k = recommended[:k]
    precision_at_k = []
    relevant_count = 0
    
    for i, product in enumerate(top_k, 1):
        if product in expected:
            relevant_count += 1
            precision_at_k.append(relevant_count / i)
    
    return sum(precision_at_k) / len(expected) if expected else 0.0

def evaluate_recommendations():
    """
    Evaluate the recommendation system using benchmark queries.
    """
    # Load products and initialize recommender
    print("\nLoading products and initializing recommender...")
    products = load_products_from_csv('shl_products.csv')
    recommender = ProductRecommender(products)
    print(f"Loaded {len(products)} products")
    
    # Load benchmark queries
    print("\nLoading benchmark queries...")
    benchmark_df = pd.read_csv('benchmark_queries.csv')
    print(f"Loaded {len(benchmark_df)} benchmark queries")
    
    # Initialize metrics
    total_recall = 0.0
    total_ap = 0.0
    num_queries = len(benchmark_df)
    
    print("\nEvaluating recommendation system...")
    print("-" * 80)
    
    # Process each query
    for idx, row in benchmark_df.iterrows():
        query = row['query']
        expected_products = set(row['expected_product_name'].split(','))
        
        # Get recommendations
        print(f"\nQuery {idx + 1}: {query}")
        print(f"Expected products: {', '.join(expected_products)}")
        
        recommendations = recommender.recommend(query, top_n=3)
        if not recommendations:
            print("No recommendations found!")
            continue
            
        recommended_products = [rec.name for rec in recommendations]
        
        # Print detailed recommendations
        print("\nRecommended products:")
        for product in recommended_products:
            match = "✓" if product in expected_products else "✗"
            print(f"{match} {product}")
        
        # Calculate metrics
        recall = calculate_recall_at_k(recommended_products, expected_products, k=3)
        ap = calculate_ap_at_k(recommended_products, expected_products, k=3)
        
        # Update totals
        total_recall += recall
        total_ap += ap
        
        # Print metrics for this query
        print(f"\nMetrics for this query:")
        print(f"Recall@3: {recall:.3f}")
        print(f"AP@3: {ap:.3f}")
        print("-" * 80)
    
    # Calculate and print final metrics
    mean_recall = total_recall / num_queries
    mean_ap = total_ap / num_queries
    
    print("\nFinal Results:")
    print(f"Mean Recall@3: {mean_recall:.3f}")
    print(f"Mean Average Precision@3 (MAP@3): {mean_ap:.3f}")

if __name__ == "__main__":
    evaluate_recommendations() 