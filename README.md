# SHL Product Scraper and Recommender

This application scrapes product data from the SHL website and provides intelligent recommendations based on natural language queries.

## Features

- **Web Scraping**: Extracts product information from the SHL product catalog
- **Natural Language Processing**: Understands user requirements in plain English
- **Intelligent Recommendations**: Ranks products based on relevance to user queries
- **User-Friendly Interface**: Streamlit web application for easy interaction

## Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Step 1: Scrape Product Data

Run the scraper to collect product data from the SHL website:

```
python shl_scraper.py
```

This will create a `shl_products.csv` file containing the scraped product information.

### Step 2: Launch the Recommender Application

Start the Streamlit application:

```
streamlit run app.py
```

This will open a web browser with the recommender interface.

### Step 3: Find Product Recommendations

1. Enter your requirements in the search box (e.g., "I need a remote personality test that takes less than 30 minutes")
2. Click "Find Recommendations"
3. View the recommended products with their relevance scores and match details

## Example Queries

- "I need a remote personality test that takes less than 30 minutes"
- "Looking for an adaptive cognitive ability test"
- "Show me skills assessment tests with remote testing support"

## Project Structure

- `shl_scraper.py`: Web scraper for collecting product data
- `recommender.py`: Recommendation engine using natural language processing
- `app.py`: Streamlit web application interface
- `requirements.txt`: Python dependencies
- `shl_products.csv`: Scraped product data

## Requirements

- Python 3.8+
- Dependencies listed in requirements.txt

## License

[MIT License](LICENSE) 