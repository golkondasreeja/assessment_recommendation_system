import streamlit as st
import pandas as pd
from recommender import ProductRecommender, load_products_from_csv
import os

# Set page configuration
st.set_page_config(
    page_title="SHL Product Recommender",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
        margin-bottom: 1rem;
    }
    .product-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .score-badge {
        background-color: #4CAF50;
        color: white;
        padding: 5px 10px;
        border-radius: 20px;
        font-weight: bold;
    }
    .match-detail {
        margin-left: 20px;
        font-size: 0.9rem;
    }
    .match-true {
        color: #4CAF50;
    }
    .match-false {
        color: #F44336;
    }
</style>
""", unsafe_allow_html=True)

# App title and description
st.markdown("<h1 class='main-header'>SHL Product Recommender</h1>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; margin-bottom: 2rem;'>
    Find the perfect SHL assessment product based on your requirements.
</div>
""", unsafe_allow_html=True)

# Sidebar for information and controls
with st.sidebar:
    st.markdown("<h2 class='sub-header'>About</h2>", unsafe_allow_html=True)
    st.markdown("""
    This application helps you find the most suitable SHL assessment products based on your specific requirements.
    
    Simply enter your requirements in natural language, and the system will recommend the best matching products.
    """)
    
    st.markdown("<h2 class='sub-header'>Example Queries</h2>", unsafe_allow_html=True)
    st.markdown("""
    - "I need a remote personality test that takes less than 30 minutes"
    - "Looking for an adaptive cognitive ability test"
    - "Show me skills assessment tests with remote testing support"
    """)
    
    st.markdown("<h2 class='sub-header'>Settings</h2>", unsafe_allow_html=True)
    top_k = st.slider("Number of recommendations", min_value=1, max_value=10, value=5)

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    # Query input
    query = st.text_input("Enter your requirements:", placeholder="e.g., I need a remote personality test that takes less than 30 minutes")
    
    # Search button
    if st.button("Find Recommendations", key="search_button"):
        if query:
            with st.spinner("Finding the best matches for you..."):
                # Load products and create recommender
                products = load_products_from_csv('shl_products.csv')
                recommender = ProductRecommender(products)
                
                # Get recommendations
                recommendations = recommender.recommend(query, top_k=top_k)
                
                # Display results
                if recommendations:
                    st.markdown(f"<h2 class='sub-header'>Found {len(recommendations)} matching products:</h2>", unsafe_allow_html=True)
                    
                    for i, rec in enumerate(recommendations, 1):
                        product = rec['product']
                        score = rec['score']
                        match_details = rec['match_details']
                        
                        # Create product card
                        st.markdown(f"""
                        <div class='product-card'>
                            <h3>{i}. {product.name}</h3>
                            <p><span class='score-badge'>Relevance: {score:.2f}</span></p>
                            <p><strong>Description:</strong> {product.description}</p>
                            <p><strong>URL:</strong> <a href='{product.url}' target='_blank'>{product.url}</a></p>
                            <p><strong>Match Details:</strong></p>
                        """, unsafe_allow_html=True)
                        
                        # Display match details with color coding
                        for key, value in match_details.items():
                            color_class = "match-true" if value else "match-false"
                            display_name = key.replace('_', ' ').title()
                            st.markdown(f"<p class='match-detail {color_class}'>• {display_name}: {'✓' if value else '✗'}</p>", unsafe_allow_html=True)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.warning("No products found matching your requirements. Try a different query.")
        else:
            st.warning("Please enter your requirements.")

with col2:
    # Display product statistics
    st.markdown("<h2 class='sub-header'>Product Statistics</h2>", unsafe_allow_html=True)
    
    try:
        df = pd.read_csv('shl_products.csv')
        st.markdown(f"<p>Total Products: <strong>{len(df)}</strong></p>", unsafe_allow_html=True)
        
        # Display a sample of products
        st.markdown("<h3>Sample Products</h3>", unsafe_allow_html=True)
        for _, row in df.head(3).iterrows():
            st.markdown(f"""
            <div style='background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>
                <p><strong>{row['Name']}</strong></p>
                <p style='font-size: 0.8rem;'>{row['Description'][:100]}...</p>
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error loading product data: {str(e)}")
        st.info("Please run the scraper first to generate product data.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; font-size: 0.8rem; color: #666;'>
    SHL Product Recommender | Powered by Streamlit
</div>
""", unsafe_allow_html=True) 