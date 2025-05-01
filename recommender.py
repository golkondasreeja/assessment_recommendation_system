import re
import numpy as np
import pandas as pd
from typing import List, Dict, Optional
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer

class Product(BaseModel):
    name: str
    url: str

class ProductRecommender:
    def __init__(self, products: List[Product]):
        self.products = products
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),  # Include bigrams
            max_features=1000
        )
        self.name_vectors = self._create_name_vectors()
        
    def _create_name_vectors(self) -> Dict[str, np.ndarray]:
        """Create TF-IDF vectors for product names and descriptions"""
        # Create enhanced product texts
        product_texts = []
        for product in self.products:
            # Combine name with domain-specific keywords
            text = f"{product.name} {product.name} "  # Give more weight to name
            
            # Add domain-specific keywords based on product name
            if "assessment" in product.name.lower():
                text += "test evaluation exam skills competency remote online "
            elif "360" in product.name:
                text += "feedback review evaluation performance peer manager "
            elif "hackathon" in product.name.lower():
                text += "coding programming technical IT developer engineer "
            elif "product catalog" in product.name.lower():
                text += "browse search find cognitive ability personality behavior skills assessment test adaptive irt "
            
            product_texts.append(text.lower())
        
        # Create TF-IDF vectors
        name_vectors = self.vectorizer.fit_transform(product_texts)
        
        # Convert to dictionary
        return {product.name: vector.toarray()[0] 
                for product, vector in zip(self.products, name_vectors)}
    
    def _parse_query(self, query: str) -> Dict[str, str]:
        """Parse the query string into components"""
        # Default values
        result = {
            'test_type': '',
            'delivery_mode': '',
            'target_audience': '',
            'duration': '',
            'features': set()
        }
        
        query_lower = query.lower()
        
        # Test types
        test_types = {
            'personality': ['personality', 'behavioral', 'behaviour'],
            'cognitive': ['cognitive', 'ability', 'intelligence', 'iq'],
            'skills': ['skill', 'competency', 'assessment'],
            'technical': ['technical', 'coding', 'programming', 'it']
        }
        
        for test_type, keywords in test_types.items():
            if any(keyword in query_lower for keyword in keywords):
                result['test_type'] = test_type
                break
        
        # Delivery mode
        if any(word in query_lower for word in ['remote', 'online', 'virtual', 'web']):
            result['delivery_mode'] = 'remote'
        elif any(word in query_lower for word in ['onsite', 'in-person', 'local']):
            result['delivery_mode'] = 'onsite'
        
        # Target audience
        audiences = {
            'it': ['it', 'developer', 'programmer', 'technical', 'engineer'],
            'professional': ['professional', 'manager', 'leader', 'executive'],
            'general': ['employee', 'candidate', 'individual']
        }
        
        for audience, keywords in audiences.items():
            if any(keyword in query_lower for keyword in keywords):
                result['target_audience'] = audience
                break
        
        # Duration
        duration_match = re.search(r'(\d+)\s*(?:minute|min|hour)s?', query_lower)
        if duration_match:
            result['duration'] = duration_match.group(1)
        
        # Features
        feature_keywords = {
            'adaptive': ['adaptive', 'irt', 'item response'],
            'feedback': ['feedback', '360', 'review'],
            'remote': ['remote', 'online', 'virtual'],
            'technical': ['coding', 'programming', 'technical']
        }
        
        for feature, keywords in feature_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                result['features'].add(feature)
        
        return result
    
    def _calculate_similarity(self, query_vector: np.ndarray, product_vector: np.ndarray) -> float:
        """Calculate cosine similarity between query and product vectors"""
        epsilon = 1e-10
        return np.dot(query_vector, product_vector) / (
            np.linalg.norm(query_vector) * np.linalg.norm(product_vector) + epsilon
        )
    
    def _match_attributes(self, query_components: Dict[str, str], product: Product) -> float:
        """Calculate attribute matching score"""
        score = 0.0
        weights = {
            'test_type': 0.3,
            'delivery_mode': 0.2,
            'target_audience': 0.2,
            'duration': 0.1,
            'features': 0.2
        }
        
        product_name_lower = product.name.lower()
        
        # Test type matching
        if query_components['test_type']:
            if query_components['test_type'] == 'technical' and 'hackathon' in product_name_lower:
                score += weights['test_type']
            elif query_components['test_type'] in ['personality', 'cognitive', 'skills']:
                if 'assessment' in product_name_lower:
                    score += weights['test_type'] * 0.8  # General assessments
                if 'product catalog' in product_name_lower:
                    score += weights['test_type']  # Product catalog is best for specific test types
        
        # Delivery mode matching
        if query_components['delivery_mode'] == 'remote':
            if 'assessment' in product_name_lower:
                score += weights['delivery_mode']
            if 'product catalog' in product_name_lower:
                score += weights['delivery_mode'] * 0.5  # Some catalog items may be remote
        
        # Target audience matching
        if query_components['target_audience']:
            if query_components['target_audience'] == 'it' and 'hackathon' in product_name_lower:
                score += weights['target_audience']
            elif query_components['target_audience'] in ['professional', 'general']:
                if 'assessment' in product_name_lower:
                    score += weights['target_audience']
                if 'product catalog' in product_name_lower:
                    score += weights['target_audience'] * 0.8  # Catalog has role-specific tests
        
        # Feature matching
        if query_components['features']:
            matching_features = 0
            total_features = len(query_components['features'])
            
            for feature in query_components['features']:
                if feature == 'technical' and 'hackathon' in product_name_lower:
                    matching_features += 1
                elif feature == 'feedback' and '360' in product_name_lower:
                    matching_features += 1
                elif feature in ['remote', 'adaptive']:
                    if 'assessment' in product_name_lower:
                        matching_features += 1
                    if 'product catalog' in product_name_lower and feature == 'adaptive':
                        matching_features += 1  # Product catalog specifically mentions adaptive tests
            
            if total_features > 0:
                score += weights['features'] * (matching_features / total_features)
        
        return score
    
    def recommend(self, query: str, top_n: int = 5) -> List[Product]:
        """Recommend products based on query"""
        # Parse query into components
        query_components = self._parse_query(query)
        
        # Create query vector using the same vectorizer
        query_vector = self.vectorizer.transform([query]).toarray()[0]
        
        # Calculate scores for each product
        scores = []
        for product in self.products:
            # Get product vector
            product_vector = self.name_vectors.get(product.name, np.zeros_like(query_vector))
            
            # Calculate similarity scores
            name_similarity = self._calculate_similarity(query_vector, product_vector)
            attribute_score = self._match_attributes(query_components, product)
            
            # Combine scores (weighted average)
            final_score = 0.6 * name_similarity + 0.4 * attribute_score
            scores.append((product, final_score))
        
        # Sort by score and return top N
        scores.sort(key=lambda x: x[1], reverse=True)
        return [product for product, _ in scores[:top_n]]

def load_products_from_csv(csv_path: str) -> List[Product]:
    """Load products from a CSV file"""
    df = pd.read_csv(csv_path)
    products = []
    
    for _, row in df.iterrows():
        product = Product(
            name=row['Name'],
            url=row['URL']
        )
        products.append(product)
    
    return products

def main():
    """Main function for testing the recommender"""
    # Load products
    products = load_products_from_csv('shl_products.csv')
    recommender = ProductRecommender(products)
    
    # Test query
    query = "I need a remote personality test that takes less than 30 minutes"
    print(f"\nQuery: {query}")
    
    # Get recommendations
    recommendations = recommender.recommend(query)
    
    # Print recommendations
    print("\nTop recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec.name}")
        print(f"URL: {rec.url}")

if __name__ == "__main__":
    main() 