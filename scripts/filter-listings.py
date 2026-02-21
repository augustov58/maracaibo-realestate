#!/usr/bin/env python3
"""
Filter Maracaibo real estate listings from scraped data.
Usage: python filter-listings.py [--min-price X] [--max-price Y] [--type casa|apartamento]
"""

import json
import os
import re
import argparse
from pathlib import Path
from datetime import datetime

# Keywords that indicate a property listing
PROPERTY_KEYWORDS = [
    'venta', 'vendo', 'se vende', 'en venta',
    'casa', 'apartamento', 'apto', 'townhouse', 'town house',
    'habitaciones', 'habitación', 'hab', 'cuartos',
    'baños', 'baño',
    'metros', 'm2', 'mts',
    'precio', 'negociable', 'usd', 'dolares', '$'
]

# Location keywords for Maracaibo
LOCATION_KEYWORDS = [
    'maracaibo', 'zulia',
    'bella vista', 'tierra negra', 'la lago', 'santa lucia',
    'el milagro', 'sabaneta', 'juana de avila', 'virginia',
    'cecilio acosta', 'don bosco', 'la victoria', 'las mercedes',
    'amparo', 'coquivacoa', 'chiquinquira', 'santa fe',
    'la limpia', 'ciudadela', 'pomona', 'lago mar beach'
]

def extract_price(text):
    """Extract price from text (USD or VES)"""
    text = text.lower()
    
    # Look for USD amounts
    usd_patterns = [
        r'\$\s*([\d,\.]+)',
        r'([\d,\.]+)\s*(?:usd|dolares|dollars)',
        r'(?:usd|dolares)\s*([\d,\.]+)',
    ]
    
    for pattern in usd_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                price = float(match.group(1).replace(',', '').replace('.', ''))
                # Sanity check - real estate prices
                if 1000 <= price <= 10000000:
                    return price
            except:
                pass
    
    return None

def extract_bedrooms(text):
    """Extract number of bedrooms"""
    text = text.lower()
    patterns = [
        r'(\d+)\s*(?:habitaciones|habitación|hab|cuartos|rooms)',
        r'(\d+)\s*hab',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    return None

def extract_property_type(text):
    """Determine property type"""
    text = text.lower()
    
    if any(kw in text for kw in ['casa', 'house']):
        return 'casa'
    elif any(kw in text for kw in ['apartamento', 'apto', 'apartment']):
        return 'apartamento'
    elif any(kw in text for kw in ['townhouse', 'town house', 'th']):
        return 'townhouse'
    elif any(kw in text for kw in ['terreno', 'land', 'lote']):
        return 'terreno'
    
    return 'unknown'

def is_property_listing(text):
    """Check if text looks like a property listing"""
    text = text.lower()
    
    # Must have at least 2 property keywords
    keyword_count = sum(1 for kw in PROPERTY_KEYWORDS if kw in text)
    if keyword_count < 2:
        return False
    
    # Should mention sale (not rent)
    if any(rent_kw in text for rent_kw in ['alquiler', 'alquilo', 'renta', 'arriendo']):
        if not any(sale_kw in text for sale_kw in ['venta', 'vendo', 'se vende']):
            return False
    
    return True

def is_maracaibo_area(text):
    """Check if listing is in Maracaibo area"""
    text = text.lower()
    return any(loc in text for loc in LOCATION_KEYWORDS)

def process_instagram_post(post):
    """Process an Instagram post"""
    caption = post.get('caption', '') or ''
    
    return {
        'source': 'instagram',
        'id': post.get('id'),
        'url': post.get('url') or f"https://instagram.com/p/{post.get('shortCode', '')}",
        'text': caption,
        'author': post.get('ownerUsername', ''),
        'timestamp': post.get('timestamp'),
        'images': [post.get('displayUrl')] if post.get('displayUrl') else [],
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

def filter_listings(data_dir, min_price=None, max_price=None, property_type=None, bedrooms=None):
    """Filter all scraped data for relevant listings"""
    
    data_path = Path(data_dir)
    all_listings = []
    
    # Process all JSON files in data directory
    for json_file in data_path.glob('*.json'):
        try:
            with open(json_file) as f:
                posts = json.load(f)
        except:
            continue
        
        if not isinstance(posts, list):
            posts = [posts]
        
        for post in posts:
            # Determine source and process accordingly
            if 'shortCode' in post or 'ownerUsername' in post:
                processed = process_instagram_post(post)
            else:
                processed = process_facebook_post(post)
            
            text = processed['text']
            
            # Check if it's a property listing
            if not is_property_listing(text):
                continue
            
            # Check if in Maracaibo area
            if not is_maracaibo_area(text):
                continue
            
            # Extract details
            processed['price_usd'] = extract_price(text)
            processed['bedrooms'] = extract_bedrooms(text)
            processed['property_type'] = extract_property_type(text)
            
            # Apply filters
            if min_price and processed['price_usd'] and processed['price_usd'] < min_price:
                continue
            if max_price and processed['price_usd'] and processed['price_usd'] > max_price:
                continue
            if property_type and processed['property_type'] != property_type:
                continue
            if bedrooms and processed['bedrooms'] and processed['bedrooms'] < bedrooms:
                continue
            
            all_listings.append(processed)
    
    # Sort by timestamp (newest first)
    all_listings.sort(key=lambda x: x.get('timestamp') or '', reverse=True)
    
    return all_listings

def format_listing(listing):
    """Format a listing for display"""
    lines = []
    
    emoji = {'casa': '🏠', 'apartamento': '🏢', 'townhouse': '🏘️', 'terreno': '🏗️'}.get(listing['property_type'], '🏠')
    
    lines.append(f"{emoji} **{listing['property_type'].upper()}**")
    
    if listing['price_usd']:
        lines.append(f"💰 ${listing['price_usd']:,.0f} USD")
    
    if listing['bedrooms']:
        lines.append(f"🛏️ {listing['bedrooms']} habitaciones")
    
    # Truncate text
    text = listing['text'][:200] + '...' if len(listing['text']) > 200 else listing['text']
    lines.append(f"\n{text}")
    
    lines.append(f"\n📍 {listing['source'].upper()} | {listing['author']}")
    lines.append(f"🔗 {listing['url']}")
    
    return '\n'.join(lines)

def main():
    parser = argparse.ArgumentParser(description='Filter Maracaibo real estate listings')
    parser.add_argument('--data-dir', default='data', help='Directory with scraped JSON files')
    parser.add_argument('--min-price', type=float, help='Minimum price in USD')
    parser.add_argument('--max-price', type=float, help='Maximum price in USD')
    parser.add_argument('--type', dest='property_type', choices=['casa', 'apartamento', 'townhouse', 'terreno'])
    parser.add_argument('--bedrooms', type=int, help='Minimum bedrooms')
    parser.add_argument('--output', default='filtered-listings.json', help='Output file')
    parser.add_argument('--format', choices=['json', 'text'], default='text', help='Output format')
    
    args = parser.parse_args()
    
    # Resolve data directory
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / args.data_dir
    
    listings = filter_listings(
        data_dir,
        min_price=args.min_price,
        max_price=args.max_price,
        property_type=args.property_type,
        bedrooms=args.bedrooms
    )
    
    print(f"Found {len(listings)} matching listings\n")
    
    if args.format == 'json':
        output_path = script_dir.parent / args.output
        with open(output_path, 'w') as f:
            json.dump(listings, f, indent=2, ensure_ascii=False)
        print(f"Saved to: {output_path}")
    else:
        for i, listing in enumerate(listings[:20], 1):  # Show top 20
            print(f"--- Listing {i} ---")
            print(format_listing(listing))
            print()

if __name__ == '__main__':
    main()
