#!/usr/bin/env python3
"""
SHL Product Catalog Scraper
This script scrapes product information from the SHL product catalog webpage.
It supports both static (requests + BeautifulSoup) and dynamic (Selenium) content.
"""

import csv
import time
import logging
import argparse
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from urllib.parse import urljoin
from dataclasses import dataclass, field
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Browser headers to mimic a real browser request
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}

# Maximum retries for requests
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

@dataclass
class ProductDetails:
    """Detailed product information"""
    features: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)
    specifications: Dict[str, str] = field(default_factory=dict)
    related_products: List[str] = field(default_factory=list)
    remote_testing_support: bool = False
    adaptive_irt_support: bool = False
    duration: str = ""
    test_type: str = ""

@dataclass
class Product:
    """Basic product information"""
    name: str
    description: str
    url: str
    details: Optional[ProductDetails] = None
    
    def to_dict(self) -> Dict[str, str]:
        """Convert product to dictionary format for CSV output"""
        base_dict = {
            'Name': self.name,
            'Description': self.description,
            'URL': self.url
        }
        
        if self.details:
            base_dict.update({
                'Remote Testing Support': 'Yes' if self.details.remote_testing_support else 'No',
                'Adaptive/IRT Support': 'Yes' if self.details.adaptive_irt_support else 'No',
                'Duration': self.details.duration,
                'Test Type': self.details.test_type,
                'Features': '|'.join(self.details.features),
                'Benefits': '|'.join(self.details.benefits),
                'Specifications': '|'.join(f"{k}:{v}" for k, v in self.details.specifications.items())
            })
        
        return base_dict

def scrape_product_details(url: str, driver=None) -> Optional[ProductDetails]:
    """Scrape detailed product information from a product page"""
    try:
        if driver:
            driver.get(url)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
        else:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
        
        details = ProductDetails()
        
        # Extract features and benefits
        feature_sections = soup.find_all(['div', 'section'], class_=lambda x: x and ('feature' in x.lower() or 'benefit' in x.lower()))
        for section in feature_sections:
            items = section.find_all(['li', 'p'])
            text = ' '.join(item.get_text(strip=True) for item in items)
            if 'feature' in section.get('class', [''])[0].lower():
                details.features.append(text)
            else:
                details.benefits.append(text)
        
        # Extract specifications
        spec_sections = soup.find_all(['div', 'section'], class_=lambda x: x and 'spec' in x.lower())
        for section in spec_sections:
            rows = section.find_all(['tr', 'div'], class_=lambda x: x and 'row' in x.lower())
            for row in rows:
                key = row.find(['th', 'strong', 'b'])
                value = row.find(['td', 'span'])
                if key and value:
                    details.specifications[key.get_text(strip=True)] = value.get_text(strip=True)
        
        # Extract remote testing support
        remote_keywords = ['remote', 'online', 'virtual', 'web-based']
        remote_sections = soup.find_all(text=re.compile('|'.join(remote_keywords), re.I))
        details.remote_testing_support = any(
            any(keyword in section.parent.get_text().lower() for keyword in remote_keywords)
            for section in remote_sections
        )
        
        # Extract adaptive/IRT support
        adaptive_keywords = ['adaptive', 'irt', 'item response theory', 'computerized adaptive']
        adaptive_sections = soup.find_all(text=re.compile('|'.join(adaptive_keywords), re.I))
        details.adaptive_irt_support = any(
            any(keyword in section.parent.get_text().lower() for keyword in adaptive_keywords)
            for section in adaptive_sections
        )
        
        # Extract duration
        duration_patterns = [
            r'(\d+)\s*(?:minute|min|hour|hr)s?',
            r'(\d+)\s*(?:minute|min|hour|hr)s?\s*test',
            r'test\s*duration:\s*(\d+)\s*(?:minute|min|hour|hr)s?'
        ]
        for pattern in duration_patterns:
            duration_matches = soup.find_all(text=re.compile(pattern, re.I))
            if duration_matches:
                details.duration = duration_matches[0].strip()
                break
        
        # Extract test type
        test_type_keywords = {
            'personality': ['personality', 'behavioral', 'trait'],
            'cognitive': ['cognitive', 'ability', 'intelligence', 'iq'],
            'skills': ['skill', 'competency', 'knowledge'],
            'situational': ['situational', 'judgment', 'scenario']
        }
        
        for test_type, keywords in test_type_keywords.items():
            if any(
                any(keyword in section.get_text().lower() for keyword in keywords)
                for section in soup.find_all(['div', 'section', 'p'])
            ):
                details.test_type = test_type
                break
        
        return details
    except Exception as e:
        logging.error(f"Error scraping product details from {url}: {str(e)}")
        return None

def scrape_static(url: str, max_retries: int = MAX_RETRIES, scrape_details: bool = False) -> List[Product]:
    """Scrape products using requests and BeautifulSoup"""
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting static scraping (attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            
            if 'text/html' not in response.headers.get('Content-Type', ''):
                logger.warning("Response is not HTML, might be blocked or redirected")
                continue
                
            soup = BeautifulSoup(response.text, 'html.parser')
            products = []
            
            # Find all product cards
            product_elements = soup.find_all('div', class_='content-card')
            logger.info(f"Found {len(product_elements)} product elements")
            
            # Set up Selenium driver for detail scraping if needed
            driver = None
            if scrape_details:
                options = webdriver.ChromeOptions()
                options.add_argument('--headless')
                options.add_argument('--disable-gpu')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                driver = webdriver.Chrome(options=options)
            
            for element in product_elements:
                try:
                    # Get product name from title
                    name_elem = element.find('h3', class_='content-card__title')
                    if not name_elem:
                        continue
                    name = name_elem.text.strip()
                    
                    # Get product description from content
                    desc_elem = element.find('div', class_='content-card__content')
                    description = desc_elem.text.strip() if desc_elem else ""
                    
                    # Get product URL from link
                    link_elem = element.find('a', class_='content-card__full-width-link')
                    if not link_elem:
                        continue
                    product_url = urljoin(url, link_elem['href'])
                    
                    # Create product object
                    product = Product(name=name, description=description, url=product_url)
                    
                    # Scrape additional details if requested
                    if scrape_details:
                        logger.info(f"Scraping details for {name}")
                        product.details = scrape_product_details(product_url, driver)
                        time.sleep(RETRY_DELAY)  # Be nice to the server
                    
                    products.append(product)
                    logger.debug(f"Successfully parsed product: {name}")
                except Exception as e:
                    logger.error(f"Error parsing product element: {str(e)}")
                    continue
            
            if driver:
                driver.quit()
                    
            return products
            
        except requests.RequestException as e:
            logger.error(f"Error fetching page (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY)
            continue
            
    logger.error("All static scraping attempts failed")
    return []

def scrape_dynamic(url: str, max_retries: int = MAX_RETRIES, scrape_details: bool = False) -> List[Product]:
    """Scrape products using Selenium for dynamic content"""
    driver = None
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting dynamic scraping (attempt {attempt + 1}/{max_retries})")
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            driver = webdriver.Chrome(options=options)
            
            driver.get(url)
            # Wait for content cards to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "content-card"))
            )
            
            products = []
            # Find all product cards
            product_elements = driver.find_elements(By.CLASS_NAME, "content-card")
            logger.info(f"Found {len(product_elements)} product elements")
            
            for element in product_elements:
                try:
                    # Get product name from title
                    name = element.find_element(By.CLASS_NAME, "content-card__title").text.strip()
                    
                    # Get product description from content
                    desc_elem = element.find_element(By.CLASS_NAME, "content-card__content")
                    description = desc_elem.text.strip() if desc_elem else ""
                    
                    # Get product URL from link
                    link_elem = element.find_element(By.CLASS_NAME, "content-card__full-width-link")
                    product_url = link_elem.get_attribute('href')
                    
                    # Create product object
                    product = Product(name=name, description=description, url=product_url)
                    
                    # Scrape additional details if requested
                    if scrape_details:
                        logger.info(f"Scraping details for {name}")
                        product.details = scrape_product_details(product_url, driver)
                        time.sleep(RETRY_DELAY)  # Be nice to the server
                    
                    products.append(product)
                    logger.debug(f"Successfully parsed product: {name}")
                except (NoSuchElementException, StaleElementReferenceException) as e:
                    logger.error(f"Error parsing product element: {e}")
                    continue
            
            driver.quit()
            return products
            
        except Exception as e:
            logger.error(f"Error in dynamic scraping (attempt {attempt + 1}/{max_retries}): {e}")
            if driver:
                driver.quit()
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY)
            continue
            
    logger.error("All dynamic scraping attempts failed")
    return []

def save_to_csv(products: List[Product], filename: str = "shl_products.csv"):
    """Save products to a CSV file"""
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            header = ['Name', 'Description', 'URL']
            if any(p.details for p in products):
                header.extend(['Remote Testing Support', 'Adaptive/IRT Support', 'Duration', 'Test Type', 'Features', 'Benefits', 'Specifications'])
            writer.writerow(header)
            
            # Write product data
            for product in products:
                row = [product.name, product.description, product.url]
                if product.details:
                    row.extend([
                        'Yes' if product.details.remote_testing_support else 'No',
                        'Yes' if product.details.adaptive_irt_support else 'No',
                        product.details.duration,
                        product.details.test_type,
                        '|'.join(product.details.features),
                        '|'.join(product.details.benefits),
                        '|'.join(f"{k}:{v}" for k, v in product.details.specifications.items())
                    ])
                writer.writerow(row)
                
        logger.info(f"Successfully saved {len(products)} products to {filename}")
    except Exception as e:
        logger.error(f"Error saving to CSV: {e}")
        raise

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Scrape products from SHL website')
    parser.add_argument('--url', default="https://www.shl.com/products/",
                      help='URL to scrape (default: https://www.shl.com/products/)')
    parser.add_argument('--output', default="shl_products.csv",
                      help='Output CSV file (default: shl_products.csv)')
    parser.add_argument('--retries', type=int, default=MAX_RETRIES,
                      help=f'Maximum number of retries (default: {MAX_RETRIES})')
    parser.add_argument('--debug', action='store_true',
                      help='Enable debug logging')
    parser.add_argument('--details', action='store_true',
                      help='Scrape detailed information from individual product pages')
    return parser.parse_args()

def main():
    """Main function to scrape SHL products"""
    args = parse_arguments()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    logger.info(f"Starting to scrape products from {args.url}")
    
    # First try static scraping
    logger.info("Attempting static scraping...")
    products = scrape_static(args.url, args.retries, args.details)
    
    # If no products found, try dynamic scraping
    if not products:
        logger.info("No products found with static scraping. Trying dynamic scraping...")
        products = scrape_dynamic(args.url, args.retries, args.details)
    
    # Save results
    if products:
        logger.info(f"Found {len(products)} products")
        save_to_csv(products, args.output)
        logger.info(f"Products saved to {args.output}")
    else:
        logger.error("No products found. Please check the website structure or try again later.")

if __name__ == "__main__":
    main() 