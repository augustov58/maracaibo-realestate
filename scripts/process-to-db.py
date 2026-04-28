#!/usr/bin/env python3
"""
Process scraped JSON files and add to SQLite database.
Handles deduplication automatically.
"""

import json
import re
from pathlib import Path
from db import init_db, add_listing, get_stats

# Import AI enrichment module
try:
    from ai_enrich import enrich_with_ai, normalize_sector, extract_sector_from_text
    HAS_AI_ENRICH = True
except ImportError:
    HAS_AI_ENRICH = False
    print("Warning: ai_enrich module not available, skipping AI enrichment")

# Keywords that indicate a property listing
PROPERTY_KEYWORDS = [
    'venta', 'vendo', 'se vende', 'en venta',
    'casa', 'apartamento', 'apto', 'townhouse', 'town house',
    'habitaciones', 'habitación', 'hab', 'cuartos',
    'baños', 'baño',
    'metros', 'm2', 'mts',
    'precio', 'negociable', 'usd', 'dolares', '$'
]

# Location keywords by area
LOCATIONS = {
    'Maracaibo': [
        'maracaibo', 'bella vista', 'tierra negra', 'la lago', 'santa lucia',
        'el milagro', 'sabaneta', 'juana de avila', 'virginia',
        'cecilio acosta', 'don bosco', 'la victoria', 'las mercedes',
        'amparo', 'coquivacoa', 'chiquinquira', 'santa fe',
        'la limpia', 'ciudadela', 'pomona', 'lago mar beach',
        'indio mara', 'monte claro', 'monte bello', 'la paragua',
        'los olivos', 'san francisco', 'la coromoto', 'paraiso',
        'delicias', '5 de julio', 'padilla', 'sector', 'av 5 de julio',
        'lago mar beach', 'el rosal', 'la florida', 'los estanques',
        'villa antoañona', 'terrazas del mar', 'antoanona'
    ],
    'Zulia': ['zulia', 'cabimas', 'ciudad ojeda', 'lagunillas', 'santa rita'],
    'Margarita': ['margarita', 'porlamar', 'pampatar', 'costa azul', 'playa el agua', 'maneiro', 'nueva esparta'],
    'Caracas': ['caracas', 'miranda', 'chacao', 'altamira', 'las mercedes caracas'],
    'Valencia': ['valencia', 'carabobo', 'naguanagua'],
    'Venezuela': ['venezuela']  # Fallback
}

# Flat list for basic matching
LOCATION_KEYWORDS = []
for locs in LOCATIONS.values():
    LOCATION_KEYWORDS.extend(locs)

def extract_price(text):
    """Extract price from text (USD).
    
    Handles Venezuelan number format where:
    - Dots are thousands separators (e.g., 45.000 = 45000)
    - Commas may be decimal separators (e.g., 45.000,50)
    - Double dollar signs ($$) are common
    """
    text = text.lower()
    
    patterns = [
        r'\$\$?\s*([\d.,]+)',  # $$ or $ followed by number
        r'([\d.,]+)\s*(?:usd|dólares|dolares|dollars)',
        r'(?:usd|dólares|dolares)\s*([\d.,]+)',
        r'precio[:\s]*([\d.,]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                num_str = match.group(1)
                
                # Venezuelan format: dots = thousands, comma = decimal
                # E.g., "1.500.000" or "45.000" or "300.000,50"
                if '.' in num_str:
                    parts = num_str.replace(',', '.').split('.')
                    # If any middle/last part has 3 digits, dots are thousands separators
                    if any(len(p) == 3 for p in parts[1:]):
                        # Remove all dots (thousands separators)
                        # Keep last comma as decimal if present
                        if ',' in match.group(1):
                            # Has decimal: "45.000,50" → "45000.50"
                            whole = num_str.split(',')[0].replace('.', '')
                            decimal = num_str.split(',')[1] if ',' in num_str else ''
                            num_str = f"{whole}.{decimal}" if decimal else whole
                        else:
                            num_str = num_str.replace('.', '')
                
                # Also remove commas if used as thousands separator (US format)
                num_str = num_str.replace(',', '')
                
                price = float(num_str)
                if 5000 <= price <= 10000000:  # Reasonable real estate range
                    return price
            except:
                pass
    return None

def extract_bedrooms(text):
    """Extract number of bedrooms"""
    text = text.lower()
    patterns = [
        r'(\d+)\s*(?:habitaciones|habitación|hab\b|cuartos)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            num = int(match.group(1))
            if 1 <= num <= 20:
                return num
    return None

def extract_bathrooms(text):
    """Extract number of bathrooms"""
    text = text.lower()
    patterns = [
        r'(\d+)\s*(?:baños|baño)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            num = int(match.group(1))
            if 1 <= num <= 15:
                return num
    return None

def extract_sqm(text):
    """Extract square meters"""
    text = text.lower()
    patterns = [
        r'(\d+)\s*(?:m2|mts2|metros|m²)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            num = float(match.group(1))
            if 20 <= num <= 10000:
                return num
    return None

def extract_property_type(text):
    """Determine property type"""
    text = text.lower()
    
    if any(kw in text for kw in ['townhouse', 'town house', 'th']):
        return 'townhouse'
    elif any(kw in text for kw in ['apartamento', 'apto', 'apartment']):
        return 'apartamento'
    elif any(kw in text for kw in ['casa', 'house', 'vivienda']):
        return 'casa'
    elif any(kw in text for kw in ['terreno', 'land', 'lote', 'parcela']):
        return 'terreno'
    elif any(kw in text for kw in ['local', 'comercial', 'oficina']):
        return 'comercial'
    
    return None

def extract_location(text):
    """Extract location from text - returns city/area classification"""
    text_lower = text.lower()
    
    # Remove hashtags for location detection (they're misleading)
    text_clean = re.sub(r'#\w+', '', text_lower)
    
    # Check locations in priority order (most specific first)
    priority_order = ['Margarita', 'Caracas', 'Valencia', 'Zulia', 'Maracaibo', 'Venezuela']
    
    city = None
    specific = None
    
    for area in priority_order:
        keywords = LOCATIONS.get(area, [])
        for kw in keywords:
            if kw in text_clean:
                city = area
                # Try to get specific sector/neighborhood (keep it short)
                specific = kw.title()
                pattern = rf'(?:sector|urb\.?|urbanización)\s+([A-Za-záéíóúñÁÉÍÓÚÑ\s]+)'
                match = re.search(pattern, text_clean, re.IGNORECASE)
                if match:
                    sector = match.group(1).strip().title()[:30]
                    if sector and sector.lower() != kw:
                        specific = sector
                break
        if city:
            break
    
    # If nothing found in clean text, check original (including hashtags) as fallback
    if not city:
        for area in priority_order:
            keywords = LOCATIONS.get(area, [])
            if any(kw in text_lower for kw in keywords):
                city = area
                break
    
    # Combine into readable format
    if city and specific and city.lower() != specific.lower():
        return f"{city} - {specific}"
    elif city:
        return city
    elif specific:
        return specific
    
    return None

def is_property_listing(text):
    """Check if text looks like a property listing"""
    text = text.lower()
    
    keyword_count = sum(1 for kw in PROPERTY_KEYWORDS if kw in text)
    if keyword_count < 2:
        return False
    
    # Skip rentals
    if any(rent_kw in text for rent_kw in ['alquiler', 'alquilo', 'se alquila', 'arriendo']):
        if not any(sale_kw in text for sale_kw in ['venta', 'vendo', 'se vende']):
            return False
    
    return True

def is_venezuela_listing(text, source=None):
    """Check if listing is in Venezuela (we accept all locations now)"""
    # Elite Real Estate is a Maracaibo-based agency - accept all their listings
    if source in ['eliterealestate', 'regaladogroup', 'angelpinton', 'nexthouse', 'zuhause']:
        return True
    text = text.lower()
    # Accept any Venezuelan location
    return any(loc in text for loc in LOCATION_KEYWORDS)

def process_instagram_post(post):
    """Process an Instagram post"""
    caption = post.get('caption', '') or ''
    timestamp = post.get('timestamp')
    
    # Extract listing_date from timestamp (ISO format or Unix timestamp)
    listing_date = None
    if timestamp:
        try:
            if isinstance(timestamp, str):
                # ISO format: 2026-02-20T15:30:00.000Z
                listing_date = timestamp[:10]  # Just the date part
            elif isinstance(timestamp, (int, float)):
                # Unix timestamp
                from datetime import datetime
                listing_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        except:
            pass
    
    return {
        'source': 'instagram',
        'id': post.get('id') or post.get('shortCode'),
        'url': post.get('url') or f"https://instagram.com/p/{post.get('shortCode', '')}",
        'text': caption,
        'author': post.get('ownerUsername', ''),
        'timestamp': timestamp,
        'listing_date': listing_date,
        'images': post.get('images') or ([post.get('displayUrl')] if post.get('displayUrl') else []),
        'likes': post.get('likesCount', 0),
    }

def process_facebook_post(post):
    """Process a Facebook post"""
    text = post.get('text', '') or post.get('message', '') or ''
    
    return {
        'source': 'facebook',
        'id': post.get('postId') or post.get('id'),
        'url': post.get('url') or post.get('postUrl'),
        'text': text,
        'author': post.get('pageName') or post.get('userName', ''),
        'timestamp': post.get('time') or post.get('timestamp'),
        'images': post.get('images', []) or post.get('media', []),
        'likes': post.get('likes', 0),
    }

def process_website_listing(listing):
    """Process a website scrape listing"""
    from datetime import datetime
    
    text = listing.get('text', '') or listing.get('title', '') or ''
    url = listing.get('url', '')
    source_site = listing.get('source', 'website')
    
    # Generate a unique ID from URL
    import hashlib
    source_id = hashlib.md5(url.encode()).hexdigest()[:16] if url else None
    
    # Use today's date as listing_date for websites (first seen date)
    listing_date = datetime.now().strftime('%Y-%m-%d')
    
    return {
        'source': source_site,
        'id': source_id,
        'listing_date': listing_date,
        'url': url,
        'text': text,
        'author': source_site,
        'timestamp': None,
        'images': listing.get('images', []),
        'likes': 0,
        # Pre-extracted data from scraper
        'price_usd': listing.get('price'),
        'bedrooms': listing.get('bedrooms'),
        'bathrooms': listing.get('bathrooms'),
        'sqm': listing.get('sqm'),
    }

def process_file(json_path: Path) -> tuple:
    """Process a JSON file and add listings to DB. Returns (added, skipped) counts."""
    added = 0
    skipped = 0
    
    try:
        with open(json_path) as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {json_path}: {e}")
        return 0, 0
    
    if not isinstance(data, list):
        data = [data]
    
    # Handle Instagram profile scrapes (posts nested under latestPosts)
    posts = []
    for item in data:
        if 'latestPosts' in item and isinstance(item.get('latestPosts'), list):
            # This is a profile scrape - extract latestPosts
            for post in item['latestPosts']:
                post['ownerUsername'] = item.get('username', '')
                posts.append(post)
        else:
            posts.append(item)
    
    for post in posts:
        # Determine source and process
        if 'shortCode' in post or 'ownerUsername' in post:
            processed = process_instagram_post(post)
        elif post.get('source') in ['regaladogroup', 'angelpinton', 'nexthouse', 'zuhause', 'eliterealestate', 'website']:
            processed = process_website_listing(post)
        else:
            processed = process_facebook_post(post)
        
        text = processed.get('text', '')
        url = processed.get('url', '')
        
        # Filter out old Instagram posts (shortCode starting with 'C' = 2024 or earlier)
        if url and 'instagram.com/p/C' in url:
            skipped += 1
            continue
        
        # Filter
        if not is_property_listing(text):
            skipped += 1
            continue
        
        if not is_venezuela_listing(text, source=processed.get('source')):
            skipped += 1
            continue
        
        # Extract details (use pre-extracted data if available, otherwise extract from text)
        processed['price_usd'] = processed.get('price_usd') or extract_price(text)
        processed['bedrooms'] = processed.get('bedrooms') or extract_bedrooms(text)
        processed['bathrooms'] = processed.get('bathrooms') or extract_bathrooms(text)
        processed['sqm'] = processed.get('sqm') or extract_sqm(text)
        processed['property_type'] = processed.get('property_type') or extract_property_type(text)
        processed['location'] = processed.get('location') or extract_location(text)
        
        # AI enrichment: extract sector and clean description
        if HAS_AI_ENRICH:
            processed = enrich_with_ai(processed)
            # Update text with cleaned description if available
            if processed.get('description_clean'):
                processed['text'] = processed['description_clean']
        
        # Skip Instagram posts with no useful listing data (likely agent promos)
        if processed.get('source') == 'instagram':
            has_data = processed.get('price_usd') or processed.get('bedrooms') or processed.get('sqm')
            if not has_data:
                skipped += 1
                continue
        
        # Add to database
        if add_listing(processed):
            added += 1
        else:
            skipped += 1  # Duplicate
    
    return added, skipped

def main():
    import sys
    
    # Initialize database
    init_db()
    
    # Find data directory
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / 'data'
    
    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}")
        sys.exit(1)
    
    total_added = 0
    total_skipped = 0
    
    # Process all JSON files
    for json_file in sorted(data_dir.glob('*.json')):
        print(f"Processing: {json_file.name}...", end=' ')
        added, skipped = process_file(json_file)
        print(f"added {added}, skipped {skipped}")
        total_added += added
        total_skipped += skipped
    
    print(f"\n=== Summary ===")
    print(f"Total added: {total_added}")
    print(f"Total skipped: {total_skipped}")
    
    # Show stats
    stats = get_stats()
    print(f"\n=== Database Stats ===")
    print(f"Total listings: {stats['total']}")
    print(f"New: {stats['new']}")
    print(f"By type: {stats['by_type']}")
    print(f"By source: {stats['by_source']}")

if __name__ == '__main__':
    main()
