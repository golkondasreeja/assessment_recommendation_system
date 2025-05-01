import streamlit as st
from recommender import ProductRecommender, load_products_from_csv

# Set page config
st.set_page_config(
    page_title="SHL Product Recommender",
    page_icon="🎯",
    layout="wide"
)

# Add title and description
st.title("🎯 SHL Product Recommender")
st.markdown("""
This app helps you find the most suitable SHL products based on your requirements.
Simply describe what you're looking for in natural language, and we'll recommend the best products for you.
""")

# Load products and initialize recommender
@st.cache_data
def load_recommender():
    products = load_products_from_csv('shl_products.csv')
    return ProductRecommender(products)

recommender = load_recommender()

# Create input form
with st.form("recommendation_form"):
    query = st.text_area(
        "Describe what you're looking for:",
        placeholder="e.g., I need a remote personality test that takes less than 30 minutes",
        help="Be as specific as possible about your requirements"
    )
    
    num_recommendations = st.slider(
        "Number of recommendations:",
        min_value=1,
        max_value=5,
        value=3
    )
    
    submitted = st.form_submit_button("Get Recommendations")

# Display recommendations when form is submitted
if submitted and query:
    st.subheader("Recommended Products")
    
    # Get recommendations
    recommendations = recommender.recommend(query, top_n=num_recommendations)
    
    # Display each recommendation
    for i, product in enumerate(recommendations, 1):
        with st.expander(f"{i}. {product.name}", expanded=True):
            st.markdown(f"**URL:** [{product.url}]({product.url})")
            
            # Add some visual separation
            if i < len(recommendations):
                st.divider()

# Add sidebar with example queries
with st.sidebar:
    st.header("Example Queries")
    st.markdown("Try these example queries:")
    
    examples = [
        "I need a remote personality test that takes less than 30 minutes",
        "Looking for an adaptive cognitive ability test",
        "Show me skills assessment tests with remote testing support",
        "Find tests suitable for IT professionals",
        "Which assessments are best for sales roles"
    ]
    
    for example in examples:
        if st.button(example, key=example):
            st.session_state.query = example
            st.experimental_rerun()

# Add footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Powered by SHL Product Recommender</p>
</div>
""", unsafe_allow_html=True) 