from typing import List, Dict, Optional
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from dataclasses import dataclass
import json

@dataclass
class Product:
    name: str
    description: str
    url: str
    # Default values for optional fields
    remote_testing_support: bool = False
    adaptive_irt_support: bool = False
    duration: Optional[str] = None
    test_type: Optional[str] = None
    features: List[str] = None
    benefits: List[str] = None
    specifications: Dict[str, str] = None
    
    def __post_init__(self):
        # Initialize empty lists/dicts if None
        if self.features is None:
            self.features = []
        if self.benefits is None:
            self.benefits = []
        if self.specifications is None:
            self.specifications = {}

class ProductRecommender:
    def __init__(self, products: List[Product]):
        self.products = products
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            max_features=5000
        )
        self._prepare_data()
    
    def _prepare_data(self):
        """Prepare product data for vectorization"""
        self.product_texts = []
        for product in self.products:
            text = f"{product.name} {product.description} "
            text += " ".join(product.features) + " "
            text += " ".join(product.benefits) + " "
            text += " ".join(product.specifications.values()) + " "
            if product.test_type:
                text += f"test type: {product.test_type} "
            if product.duration:
                text += f"duration: {product.duration} "
            if product.remote_testing_support:
                text += "remote testing supported "
            if product.adaptive_irt_support:
                text += "adaptive testing supported "
            self.product_texts.append(text)
        
        self.tfidf_matrix = self.vectorizer.fit_transform(self.product_texts)
    
    def _extract_requirements(self, query: str) -> Dict:
        """Extract specific requirements from the natural language query"""
        requirements = {
            'remote_testing': False,
            'adaptive_testing': False,
            'test_type': None,
            'max_duration': None,
            'keywords': []
        }
        
        # Check for remote testing requirement
        if re.search(r'remote|online|virtual|web-based', query.lower()):
            requirements['remote_testing'] = True
        
        # Check for adaptive testing requirement
        if re.search(r'adaptive|irt|item response theory', query.lower()):
            requirements['adaptive_testing'] = True
        
        # Extract test type
        test_types = {
            'personality': ['personality', 'behavioral', 'trait'],
            'cognitive': ['cognitive', 'ability', 'intelligence', 'iq'],
            'skills': ['skill', 'competency', 'knowledge'],
            'situational': ['situational', 'judgment', 'scenario']
        }
        for test_type, keywords in test_types.items():
            if any(keyword in query.lower() for keyword in keywords):
                requirements['test_type'] = test_type
                break
        
        # Extract duration requirement
        duration_match = re.search(r'(\d+)\s*(?:minute|min|hour|hr)s?', query.lower())
        if duration_match:
            requirements['max_duration'] = int(duration_match.group(1))
        
        # Extract other keywords
        words = query.lower().split()
        requirements['keywords'] = [word for word in words if len(word) > 3]
        
        return requirements
    
    def _filter_by_requirements(self, requirements: Dict) -> List[int]:
        """Filter products based on specific requirements"""
        valid_indices = []
        
        for i, product in enumerate(self.products):
            if requirements['remote_testing'] and not product.remote_testing_support:
                continue
            if requirements['adaptive_testing'] and not product.adaptive_irt_support:
                continue
            if requirements['test_type'] and product.test_type != requirements['test_type']:
                continue
            if requirements['max_duration']:
                duration_match = re.search(r'(\d+)', product.duration or '')
                if duration_match and int(duration_match.group(1)) > requirements['max_duration']:
                    continue
            valid_indices.append(i)
        
        return valid_indices
    
    def recommend(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Recommend products based on a natural language query
        
        Args:
            query: Natural language query describing requirements
            top_k: Number of recommendations to return
            
        Returns:
            List of dictionaries containing product recommendations with scores
        """
        # Extract requirements from query
        requirements = self._extract_requirements(query)
        
        # Filter products based on requirements
        valid_indices = self._filter_by_requirements(requirements)
        
        if not valid_indices:
            return []
        
        # Vectorize query
        query_vector = self.vectorizer.transform([query])
        
        # Calculate similarity scores for valid products
        valid_matrix = self.tfidf_matrix[valid_indices]
        similarity_scores = cosine_similarity(query_vector, valid_matrix).flatten()
        
        # Get top k recommendations
        top_indices = similarity_scores.argsort()[-top_k:][::-1]
        
        recommendations = []
        for idx in top_indices:
            product_idx = valid_indices[idx]
            product = self.products[product_idx]
            score = float(similarity_scores[idx])
            
            recommendations.append({
                'product': product,
                'score': score,
                'match_details': {
                    'remote_testing_match': requirements['remote_testing'] == product.remote_testing_support,
                    'adaptive_testing_match': requirements['adaptive_testing'] == product.adaptive_irt_support,
                    'test_type_match': requirements['test_type'] == product.test_type,
                    'duration_match': True if not requirements['max_duration'] else (
                        re.search(r'(\d+)', product.duration or '').group(1) <= requirements['max_duration']
                    )
                }
            })
        
        return recommendations

def load_products_from_csv(csv_path: str) -> List[Product]:
    """Load products from a CSV file"""
    df = pd.read_csv(csv_path)
    products = []
    
    for _, row in df.iterrows():
        # Create product with only the available fields
        product = Product(
            name=row['Name'],
            description=row['Description'],
            url=row['URL']
        )
        products.append(product)
    
    return products

def main():
    # Example usage
    products = load_products_from_csv('shl_products.csv')
    recommender = ProductRecommender(products)
    
    # Example queries
    queries = [
        "I need a remote personality test that takes less than 30 minutes",
        "Looking for an adaptive cognitive ability test",
        "Show me skills assessment tests with remote testing support"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        recommendations = recommender.recommend(query)
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec['product'].name}")
            print(f"Score: {rec['score']:.2f}")
            print(f"URL: {rec['product'].url}")
            print("Match Details:")
            for key, value in rec['match_details'].items():
                print(f"  - {key}: {value}")

if __name__ == "__main__":
    main() 