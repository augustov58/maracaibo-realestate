#!/usr/bin/env python3
"""
Web scraper for Maracaibo real estate websites.
Uses requests with proper headers to avoid bot detection.
"""

import os
import sys
import json
import re
import time
import hashlib
from datetime import datetime
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing required packages...")
    os.system("pip install --user requests beautifulsoup4 lxml")
    import requests
    from bs4 import BeautifulSoup

# Headers to mimic a real browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    'DNT': '1',
    'Connection': 'keep-alive',
}

# Website configurations
WEBSITES = {
    'regaladogroup': {
        'name': 'Regalado Group',
        'listing_url': 'https://regaladogroup.net/inmuebles/',
        'base_url': 'https://regaladogroup.net',
        'parser': 'parse_regaladogroup',
    },
    'angelpinton': {
        'name': 'Angel Pinton',
        'listing_url': 'https://www.angelpinton.com/inmobiliaria/maracaibo-v/inmuebles/15',
        'base_url': 'https://www.angelpinton.com',
        'parser': 'parse_angelpinton',
    },
    'nexthouse': {
        'name': 'Next House Inmobiliaria',
        'listing_url': 'https://www.nexthouseinmobiliaria.com/inmobiliaria/inmuebles',
        'base_url': 'https://www.nexthouseinmobiliaria.com',
        'parser': 'parse_nexthouse',
    },
    'zuhause': {
        'name': 'Zuhause Bienes Raices',
        'listing_url': 'https://zuhausebienesraices.com/propiedades/',
        'base_url': 'https://zuhausebienesraices.com',
        'parser': 'parse_zuhause',
    },
    'eliterealestate': {
        'name': 'Elite Real Estate',
        'listing_url': 'https://eliterealestateca.com',
        'base_url': 'https://eliterealestateca.com',
        'parser': 'parse_eliterealestate',
    },
}


def fetch_page(url, retries=3):
    """Fetch a page with proper headers and retry logic."""
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            if response.status_code == 200:
                return response.text
            elif response.status_code == 403:
                print(f"  Access denied (403) for {url}")
                time.sleep(5)  # Wait longer before retry
            else:
                print(f"  HTTP {response.status_code} for {url}")
        except requests.RequestException as e:
            print(f"  Request error: {e}")
        
        if attempt < retries - 1:
            time.sleep(2 * (attempt + 1))
    
    return None


def extract_number(text, pattern):
    """Extract a number from text using a regex pattern."""
    if not text:
        return None
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        try:
            num_str = match.group(1)
            # Handle prices with comma thousands separators and decimal point
            # e.g., "18,000.00" -> 18000.00, "1,200,000" -> 1200000
            if ',' in num_str and '.' in num_str:
                # Has both comma and period - comma is thousands, period is decimal
                num_str = num_str.replace(',', '')
            elif ',' in num_str:
                # Only comma - it's a thousands separator
                num_str = num_str.replace(',', '')
            return float(num_str)
        except:
            pass
    return None


def extract_images(card, base_url):
    """Extract image URLs from a card element."""
    images = []
    for img in card.find_all('img'):
        src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
        if src:
            # Skip placeholder/icon images
            if any(x in src.lower() for x in ['placeholder', 'icon', 'logo', 'spinner', 'loading', 'avatar']):
                continue
            # Handle relative URLs
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                src = base_url + src
            elif not src.startswith('http'):
                src = base_url + '/' + src
            images.append(src)
    return images[:10]  # Limit to 10 images


def parse_regaladogroup(html):
    """Parse listings from Regalado Group website."""
    soup = BeautifulSoup(html, 'lxml')
    listings = []
    seen_urls = set()
    base_url = 'https://regaladogroup.net'
    
    # Find all listing cards (okno_R class contains the full card)
    for card in soup.find_all('div', class_='okno_R'):
        # Find the link within this card
        link = card.find('a', href=re.compile(r'/inmuebles/160/view/'))
        if not link:
            continue
        
        href = link.get('href', '')
        if not href or href in seen_urls:
            continue
        seen_urls.add(href)
        
        # Get all text from the card
        text = card.get_text(separator=' ', strip=True)
        
        # Extract images
        images = extract_images(card, base_url)
        
        # Extract data
        url = href if href.startswith('http') else f"{base_url}{href}"
        sqm = extract_number(text, r'(\d+(?:[.,]\d+)?)\s*mts?2')
        bedrooms = extract_number(text, r'Habitaciones:\s*(\d+)')
        # Price format: "130,000.00 $" or "$ 130,000.00"
        price = extract_number(text, r'([\d,]+(?:\.\d+)?)\s*\$') or extract_number(text, r'\$\s*([\d,]+(?:\.\d+)?)')
        
        # Determine property type from URL
        property_type = None
        if 'Apartamento' in href:
            property_type = 'apartamento'
        elif 'Casa' in href or 'TownHouse' in href:
            property_type = 'casa'
        elif 'Townhouse' in href:
            property_type = 'townhouse'
        elif 'Local' in href:
            property_type = 'local'
        elif 'Terreno' in href:
            property_type = 'terreno'
        
        # Determine if rent or sale from text
        listing_type = 'venta'
        if 'alquiler' in text.lower() or 'alquilar' in text.lower():
            listing_type = 'alquiler'
        
        listing = {
            'url': url,
            'source': 'regaladogroup',
            'text': text[:1000],
            'sqm': sqm,
            'bedrooms': bedrooms,
            'price': price,
            'property_type': property_type,
            'listing_type': listing_type,
            'images': images,
        }
        
        listings.append(listing)
    
    return listings


def parse_angelpinton(html):
    """Parse listings from Angel Pinton website."""
    soup = BeautifulSoup(html, 'lxml')
    listings = []
    seen_urls = set()
    base_url = 'https://www.angelpinton.com'
    
    # Find all property cards (article.c49-property-card)
    for card in soup.find_all('article', class_='c49-property-card'):
        # Find the main link in the card
        link = card.find('a', href=re.compile(r'angelpinton\.com/\d+/inmuebles/'))
        if not link:
            continue
        
        href = link.get('href', '')
        if not href or 'maracaibo' not in href.lower():
            continue
        
        # Skip duplicates
        if href in seen_urls:
            continue
        seen_urls.add(href)
        
        text = card.get_text(separator=' ', strip=True)
        
        # Extract images
        images = extract_images(card, base_url)
        
        # Extract data
        url = href if href.startswith('http') else f"{base_url}{href}"
        sqm = extract_number(text, r'(\d+)\s*m²')
        bedrooms = extract_number(text, r'(\d+)\s*dorms?\.?')
        bathrooms = extract_number(text, r'(\d+)\s*bañ')
        price = extract_number(text, r'US\$\s*([\d,]+(?:\.\d+)?)')
        
        # Property type from URL
        property_type = None
        if 'apartamento' in href:
            property_type = 'apartamento'
        elif 'casa' in href:
            property_type = 'casa'
        elif 'townhouse' in href:
            property_type = 'townhouse'
        
        listing = {
            'url': url,
            'source': 'angelpinton',
            'text': text[:1000],
            'sqm': sqm,
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'price': price,
            'property_type': property_type,
            'images': images,
        }
        
        listings.append(listing)
    
    return listings


def parse_nexthouse(html):
    """Parse listings from Next House website."""
    soup = BeautifulSoup(html, 'lxml')
    listings = []
    
    # Find all property links
    for link in soup.find_all('a', href=re.compile(r'/\d+/inmuebles/')):
        href = link.get('href', '')
        if not href:
            continue
        
        # Only include Maracaibo/San Francisco area
        if not any(loc in href.lower() for loc in ['maracaibo', 'san-francisco']):
            continue
        
        container = link.find_parent(['article', 'div'])
        if not container:
            container = link
        
        text = container.get_text(separator=' ', strip=True)
        
        url = href if href.startswith('http') else f"https://www.nexthouseinmobiliaria.com{href}"
        sqm = extract_number(text, r'(\d+(?:[.,]\d+)?)\s*m²')
        bedrooms = extract_number(text, r'(\d+)\s*dorms?\.?')
        bathrooms = extract_number(text, r'(\d+)\s*bañ')
        price = extract_number(text, r'US\$\s*([\d,]+(?:\.\d+)?)')
        
        property_type = None
        if 'apartamento' in href or 'APARTAMENTO' in text:
            property_type = 'apartamento'
        elif 'casa' in href or 'CASA' in text:
            property_type = 'casa'
        elif 'townhouse' in href:
            property_type = 'townhouse'
        
        listing = {
            'url': url,
            'source': 'nexthouse',
            'text': text[:1000],
            'sqm': sqm,
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'price': price,
            'property_type': property_type,
        }
        
        if listing['url'] not in [l['url'] for l in listings]:
            listings.append(listing)
    
    return listings


def parse_zuhause(html):
    """Parse listings from Zuhause website."""
    soup = BeautifulSoup(html, 'lxml')
    listings = []
    
    # Find all property links
    for link in soup.find_all('a', href=re.compile(r'/propiedades/')):
        href = link.get('href', '')
        if not href or href == 'https://zuhausebienesraices.com/propiedades/':
            continue
        
        # Only include Maracaibo area
        if 'maracaibo' not in href.lower():
            continue
        
        container = link.find_parent(['article', 'div'])
        if not container:
            container = link
        
        text = container.get_text(separator=' ', strip=True)
        
        url = href if href.startswith('http') else f"https://zuhausebienesraices.com{href}"
        sqm = extract_number(text, r'(\d+)\s*m²')
        bathrooms = extract_number(text, r'Baños\s*:\s*(\d+)')
        price = extract_number(text, r'\$([\d,]+)')
        
        property_type = None
        if 'apartamento' in href.lower() or 'Apartamentos' in text:
            property_type = 'apartamento'
        elif 'casa' in href.lower() or 'Casas' in text:
            property_type = 'casa'
        elif 'townhouse' in href.lower():
            property_type = 'townhouse'
        
        listing = {
            'url': url,
            'source': 'zuhause',
            'text': text[:1000],
            'sqm': sqm,
            'bathrooms': bathrooms,
            'price': price,
            'property_type': property_type,
        }
        
        if listing['url'] not in [l['url'] for l in listings]:
            listings.append(listing)
    
    return listings


def parse_eliterealestate(html):
    """Parse listings from Elite Real Estate website."""
    soup = BeautifulSoup(html, 'lxml')
    listings = []
    seen_urls = set()
    base_url = 'https://eliterealestateca.com'
    
    # Find all property links (format: /propiedad/xxx/)
    for link in soup.find_all('a', href=re.compile(r'/propiedad/[^/]+/')):
        href = link.get('href', '')
        if not href or href == 'https://eliterealestateca.com/propiedad/':
            continue
        
        # Skip duplicates
        if href in seen_urls:
            continue
        seen_urls.add(href)
        
        # Get container - look for parent article or div with property info
        container = link.find_parent(['article', 'div'])
        if not container:
            container = link
        
        # Extract images
        images = extract_images(container, base_url)
        
        text = container.get_text(separator=' ', strip=True)
        title = link.get_text(strip=True)
        
        url = href if href.startswith('http') else f"https://eliterealestateca.com{href}"
        
        # Extract data from text
        bedrooms = extract_number(text, r'Hab\.?:?\s*(\d+)')
        bathrooms = extract_number(text, r'Baños:?\s*(\d+)')
        
        # Price pattern: $$ 300.000 or $$45.000 or $$1.000.000
        # In this format, dots are thousands separators
        price_match = re.search(r'\$\$?\s*([\d.]+)', text)
        price = None
        if price_match:
            price_str = price_match.group(1).replace('.', '')
            try:
                price = float(price_str)
            except:
                pass
        
        # Determine property type from title/URL
        property_type = None
        title_lower = title.lower()
        if 'apartamento' in title_lower or 'apto' in title_lower:
            property_type = 'apartamento'
        elif 'casa' in title_lower or 'quinta' in title_lower:
            property_type = 'casa'
        elif 'townhouse' in title_lower:
            property_type = 'townhouse'
        elif 'edificio' in title_lower or 'local' in title_lower or 'galpon' in title_lower or 'galpón' in title_lower:
            property_type = 'comercial'
        elif 'terreno' in title_lower:
            property_type = 'terreno'
        
        # Extract location from title (after comma)
        location = None
        if ',' in title:
            location = title.split(',')[-1].strip()
        
        listing = {
            'url': url,
            'source': 'eliterealestate',
            'text': f"{title} - {text[:500]}",
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'price': price,
            'property_type': property_type,
            'location': location,
            'images': images,
        }
        
        listings.append(listing)
    
    return listings


# Mapping of parser names to functions
PARSERS = {
    'parse_regaladogroup': parse_regaladogroup,
    'parse_angelpinton': parse_angelpinton,
    'parse_nexthouse': parse_nexthouse,
    'parse_zuhause': parse_zuhause,
    'parse_eliterealestate': parse_eliterealestate,
}


def scrape_website(site_key):
    """Scrape a single website."""
    config = WEBSITES.get(site_key)
    if not config:
        print(f"Unknown website: {site_key}")
        return []
    
    print(f"Scraping {config['name']}...")
    
    html = fetch_page(config['listing_url'])
    if not html:
        print(f"  Failed to fetch {config['listing_url']}")
        return []
    
    parser = PARSERS.get(config['parser'])
    if not parser:
        print(f"  No parser for {site_key}")
        return []
    
    try:
        listings = parser(html)
        print(f"  Found {len(listings)} listings from {config['name']}")
        return listings
    except Exception as e:
        print(f"  Error parsing {config['name']}: {e}")
        return []


def scrape_all_websites():
    """Scrape all configured websites."""
    all_listings = []
    
    for site_key in WEBSITES:
        listings = scrape_website(site_key)
        all_listings.extend(listings)
        time.sleep(3)  # Rate limiting between sites
    
    return all_listings


def save_results(listings, output_dir):
    """Save results to JSON file."""
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    filename = f"websites-{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(listings, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(listings)} listings to {filepath}")
    return filepath


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape Maracaibo real estate websites')
    parser.add_argument('--site', choices=list(WEBSITES.keys()) + ['all'], default='all',
                       help='Website to scrape (default: all)')
    parser.add_argument('--output', default='./data',
                       help='Output directory (default: ./data)')
    args = parser.parse_args()
    
    os.makedirs(args.output, exist_ok=True)
    
    if args.site == 'all':
        listings = scrape_all_websites()
    else:
        listings = scrape_website(args.site)
    
    if listings:
        save_results(listings, args.output)
    else:
        print("No listings found")
