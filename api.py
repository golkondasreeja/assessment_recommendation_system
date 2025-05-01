from flask import Flask, request, jsonify
from pydantic import BaseModel, ValidationError
from typing import List, Optional
from recommender import load_products_from_csv, ProductRecommender
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class RecommendationRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5

class ProductResponse(BaseModel):
    name: str
    url: str
    score: float

class RecommendationResponse(BaseModel):
    recommendations: List[ProductResponse]

# Initialize recommender
try:
    logger.info("Initializing recommender...")
    products = load_products_from_csv('shl_products.csv')
    recommender = ProductRecommender(products)
    logger.info(f"Recommender initialized successfully with {len(products)} products!")
except Exception as e:
    logger.error(f"Error initializing recommender: {e}")
    products = []
    recommender = None

@app.route("/")
def root():
    logger.info("Received request to root endpoint")
    return jsonify({"message": "Welcome to SHL Product Recommender API"})

@app.route("/health")
def health_check():
    logger.info("Received request to health endpoint")
    status = "ok" if recommender is not None else "error"
    return jsonify({
        "status": status,
        "recommender_initialized": recommender is not None,
        "num_products": len(products) if products else 0
    })

@app.route("/recommend", methods=["POST"])
def get_recommendations():
    logger.info("Received request to recommend endpoint")
    
    if not recommender:
        logger.error("Recommender not initialized")
        return jsonify({"error": "Recommender not initialized"}), 500
    
    try:
        data = request.get_json()
        if not data:
            logger.warning("No JSON data provided in request")
            return jsonify({"error": "No JSON data provided"}), 400
            
        request_data = RecommendationRequest(**data)
        logger.info(f"Processing recommendation request for query: {request_data.query}")
        
        recommendations = recommender.recommend(request_data.query, top_k=request_data.top_k)
        response_recommendations = [
            ProductResponse(
                name=rec['product'].name,
                url=rec['product'].url,
                score=rec['score']
            )
            for rec in recommendations
        ]
        response = RecommendationResponse(recommendations=response_recommendations)
        logger.info(f"Found {len(response.recommendations)} recommendations")
        return jsonify(response.dict())
    
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({"error": "Invalid request data", "details": str(e)}), 400
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    logger.info("Starting Flask server on port 5000...")
    app.run(host="127.0.0.1", port=5000, debug=True) 