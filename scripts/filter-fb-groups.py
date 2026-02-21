#!/usr/bin/env python3
"""
Filter Facebook group posts to extract only real estate listings.
Filters out garbage/non-RE posts.
"""

import json
import os
import re
import glob
from datetime import datetime

# Keywords that indicate real estate (Spanish)
RE_KEYWORDS = [
    # Property types
    r'\bcasa\b', r'\bapartamento\b', r'\bapto\b', r'\btownhouse\b', 
    r'\bquinta\b', r'\bparcela\b', r'\bterreno\b', r'\blocal\b',
    r'\bgalpón?\b', r'\boficina\b', r'\bpent.?house\b',
    
    # Actions
    r'\bventa\b', r'\bvendo\b', r'\bse vende\b', r'\ben venta\b',
    r'\balquiler\b', r'\balquilo\b', r'\bse alquila\b',
    
    # Features
    r'\bhabitacion', r'\bbaño', r'\bm2\b', r'\bm²\b', r'\bmetros?\b',
    r'\bestacionamiento', r'\bgarage\b', r'\bpiscina\b',
    
    # Price indicators
    r'\$\s*[\d,.]+', r'\bprecio\b', r'\busd\b', r'\bdólares?\b',
    r'\bbs\.?\b', r'\bbolívares?\b',
    
    # Location
    r'\bmaracaibo\b', r'\bzulia\b', r'\bsector\b', r'\burbanizaci[oó]n\b',
    r'\bav\.?\b', r'\bcalle\b', r'\bzona\b',
]

# Keywords that indicate NOT real estate (garbage)
GARBAGE_KEYWORDS = [
    r'\bempleo\b', r'\btrabajo\b', r'\bvacante\b', r'\bcontratando\b',
    r'\bservicio\b', r'\breparaci[oó]n\b', r'\bplomero\b', r'\belectricista\b',
    r'\bcarro\b', r'\bveh[ií]culo\b', r'\bmoto\b', r'\bcamioneta\b',
    r'\bcelular\b', r'\biphone\b', r'\bsamsung\b', r'\blaptop\b',
    r'\bropa\b', r'\bzapatos\b', r'\bmuebles\b',  # furniture sold separately
    r'\bcomida\b', r'\brestaurante\b', r'\bdelivery\b',
    r'\bmascotas?\b', r'\bperro\b', r'\bgato\b',
    r'\bpréstamo\b', r'\bcrédito\b', r'\bdinero rápido\b',
]

def is_real_estate(text):
    """Check if post is likely a real estate listing."""
    if not text:
        return False
    
    text_lower = text.lower()
    
    # Check for garbage keywords first (disqualify)
    for pattern in GARBAGE_KEYWORDS:
        if re.search(pattern, text_lower):
            return False
    
    # Count RE keyword matches
    re_matches = 0
    for pattern in RE_KEYWORDS:
        if re.search(pattern, text_lower):
            re_matches += 1
    
    # Need at least 3 RE keywords to qualify
    return re_matches >= 3

def extract_price(text):
    """Extract price from text."""
    if not text:
        return None
    
    # Look for USD prices
    usd_match = re.search(r'\$\s*([\d,\.]+)', text)
    if usd_match:
        try:
            price = float(usd_match.group(1).replace(',', '').replace('.', ''))
            # If number is huge, might be formatted with . as thousands
            if price > 10000000:
                price = price / 1000
            return price
        except:
            pass
    
    return None

def extract_property_type(text):
    """Extract property type from text."""
    if not text:
        return None
    
    text_lower = text.lower()
    
    if re.search(r'\bcasa\b', text_lower):
        return 'casa'
    elif re.search(r'\bapartamento\b|\bapto\b', text_lower):
        return 'apartamento'
    elif re.search(r'\btownhouse\b', text_lower):
        return 'townhouse'
    elif re.search(r'\bterreno\b|\bparcela\b', text_lower):
        return 'terreno'
    elif re.search(r'\blocal\b', text_lower):
        return 'local'
    elif re.search(r'\bquinta\b', text_lower):
        return 'quinta'
    
    return None

def extract_bedrooms(text):
    """Extract number of bedrooms."""
    if not text:
        return None
    
    match = re.search(r'(\d+)\s*(?:habitacion|cuarto|dormitorio)', text.lower())
    if match:
        return int(match.group(1))
    return None

def extract_sqm(text):
    """Extract square meters."""
    if not text:
        return None
    
    match = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:m2|m²|mts?2?|metros)', text.lower())
    if match:
        try:
            return float(match.group(1).replace(',', '.'))
        except:
            pass
    return None

def process_fb_group_post(post):
    """Process a single Facebook group post."""
    text = post.get('text') or post.get('message') or ''
    
    if not is_real_estate(text):
        return None
    
    # Extract data
    listing = {
        'source': 'facebook_group',
        'source_id': post.get('postId') or post.get('id'),
        'url': post.get('url') or post.get('postUrl'),
        'text': text[:2000],  # Truncate long posts
        'author': post.get('user', {}).get('name') if isinstance(post.get('user'), dict) else post.get('user'),
        'timestamp': post.get('time') or post.get('timestamp'),
        'images': json.dumps(post.get('media', []) or []),
        'likes': post.get('likes'),
        'price_usd': extract_price(text),
        'bedrooms': extract_bedrooms(text),
        'sqm': extract_sqm(text),
        'property_type': extract_property_type(text),
        'location': 'Maracaibo',  # Default, can be refined
        'status': 'new',
    }
    
    return listing

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, '..', 'data')
    
    # Find all FB group JSON files from today
    today = datetime.now().strftime('%Y%m%d')
    pattern = os.path.join(data_dir, f'fb-group-*-{today}*.json')
    files = glob.glob(pattern)
    
    if not files:
        # Try any recent files
        pattern = os.path.join(data_dir, 'fb-group-*.json')
        files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)[:5]
    
    print(f"Processing {len(files)} files...")
    
    all_listings = []
    
    for filepath in files:
        print(f"  Processing: {os.path.basename(filepath)}")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                posts = json.load(f)
            
            if not isinstance(posts, list):
                posts = [posts]
            
            for post in posts:
                listing = process_fb_group_post(post)
                if listing:
                    all_listings.append(listing)
                    
        except Exception as e:
            print(f"    Error: {e}")
    
    print(f"\nFiltered to {len(all_listings)} real estate listings")
    
    # Save filtered results
    if all_listings:
        output_file = os.path.join(data_dir, f'fb-filtered-{today}.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_listings, f, indent=2, ensure_ascii=False)
        print(f"Saved to: {output_file}")
        
        # Show sample
        print("\nSample listing:")
        print(json.dumps(all_listings[0], indent=2, ensure_ascii=False)[:500])

if __name__ == '__main__':
    main()
