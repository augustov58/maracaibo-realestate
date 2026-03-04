#!/usr/bin/env python3
"""
Check active listings for:
- Sold/removed (404 or "vendido" text)
- Price changes (especially drops)
"""

import sys
import re
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from db import get_db, get_listings

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def extract_price(text):
    """Extract USD price from text.
    
    Handles Venezuelan number format where:
    - Dots are thousands separators (e.g., 45.000 = 45000)
    - Commas may be decimal separators
    - Double dollar signs ($$) are common
    """
    patterns = [
        r'\$\$?\s*([\d.,]+)',  # $$ or $ followed by number
        r'US\$\s*([\d.,]+)',
        r'([\d.,]+)\s*(?:usd|USD|dólares|dolares)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                num_str = match.group(1)
                
                # Venezuelan format: dots = thousands, comma = decimal
                if '.' in num_str:
                    parts = num_str.replace(',', '.').split('.')
                    if any(len(p) == 3 for p in parts[1:]):
                        # Dots are thousands separators
                        if ',' in match.group(1):
                            whole = num_str.split(',')[0].replace('.', '')
                            decimal = num_str.split(',')[1]
                            num_str = f"{whole}.{decimal}"
                        else:
                            num_str = num_str.replace('.', '')
                
                num_str = num_str.replace(',', '')
                price = float(num_str)
                if 1000 <= price <= 10000000:  # Reasonable range
                    return price
            except:
                pass
    return None

def check_listing(listing):
    """Check a single listing. Returns (status, new_price, message)"""
    url = listing.get('url', '')
    old_price = listing.get('price_usd')
    
    if not url:
        return None, None, None
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        # Check for 404
        if response.status_code == 404:
            return 'sold', None, 'URL not found (404)'
        
        if response.status_code != 200:
            return None, None, f'HTTP {response.status_code}'
        
        text = response.text.lower()
        
        # Check for sold indicators
        sold_keywords = ['vendido', 'sold', 'no disponible', 'reservado']
        for kw in sold_keywords:
            if kw in text:
                return 'sold', None, f'Marked as "{kw}"'
        
        # Extract current price
        new_price = extract_price(response.text)
        
        if new_price and old_price:
            if new_price < old_price:
                pct = ((old_price - new_price) / old_price) * 100
                return 'price_drop', new_price, f'Price dropped {pct:.0f}% (${old_price:,.0f} → ${new_price:,.0f})'
            elif new_price > old_price:
                return 'price_increase', new_price, f'Price increased (${old_price:,.0f} → ${new_price:,.0f})'
        
        return 'active', new_price, None
        
    except requests.RequestException as e:
        return None, None, f'Request error: {e}'

def update_listing_status(listing_id, status):
    """Update listing status to sold"""
    conn = get_db()
    conn.execute(
        "UPDATE listings SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (status, listing_id)
    )
    conn.commit()
    conn.close()

def update_listing_price(listing_id, old_price, new_price):
    """Update listing price, preserve original, and record in history"""
    conn = get_db()
    
    # Check if original_price is already set
    cur = conn.execute(
        "SELECT original_price FROM listings WHERE id = ?",
        (listing_id,)
    )
    row = cur.fetchone()
    current_original = row[0] if row else None
    
    # If original_price not set, preserve the old price as original
    if not current_original and old_price:
        conn.execute(
            "UPDATE listings SET original_price = ? WHERE id = ?",
            (old_price, listing_id)
        )
    
    # Update current price
    conn.execute(
        "UPDATE listings SET price_usd = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (new_price, listing_id)
    )
    
    # Record in history
    conn.execute(
        "INSERT INTO price_history (listing_id, price_usd) VALUES (?, ?)",
        (listing_id, new_price)
    )
    
    conn.commit()
    conn.close()

def main():
    import argparse
    from datetime import datetime, timedelta
    
    parser = argparse.ArgumentParser(description='Check listings for sold/price changes')
    parser.add_argument('--limit', type=int, default=200, help='Max listings to check')
    parser.add_argument('--days', type=int, default=60, help='Only check listings from last N days')
    parser.add_argument('--dry-run', action='store_true', help='Do not update database')
    args = parser.parse_args()
    
    # Get active listings (not already marked sold)
    listings = get_listings(limit=args.limit)
    
    # Filter to last N days and not sold
    cutoff = (datetime.now() - timedelta(days=args.days)).strftime('%Y-%m-%d')
    active_listings = [
        l for l in listings 
        if l.get('status') != 'sold' 
        and (l.get('listing_date') or l.get('created_at', '')[:10]) >= cutoff
    ]
    
    print(f"Tracking window: {args.days} days (since {cutoff})")
    
    print(f"Checking {len(active_listings)} listings...")
    
    sold = []
    price_drops = []
    price_increases = []
    errors = []
    
    for i, listing in enumerate(active_listings):
        print(f"  [{i+1}/{len(active_listings)}] {listing['url'][:60]}...", end=' ')
        
        status, new_price, message = check_listing(listing)
        
        if status == 'sold':
            print(f"SOLD - {message}")
            sold.append((listing, message))
            if not args.dry_run:
                update_listing_status(listing['id'], 'sold')
                
        elif status == 'price_drop':
            print(f"💰 PRICE DROP - {message}")
            price_drops.append((listing, new_price, message))
            if not args.dry_run:
                update_listing_price(listing['id'], listing.get('price_usd'), new_price)
                
        elif status == 'price_increase':
            print(f"📈 {message}")
            price_increases.append((listing, new_price, message))
            if not args.dry_run:
                update_listing_price(listing['id'], listing.get('price_usd'), new_price)
                
        elif status == 'active':
            print("OK")
            
        else:
            print(f"ERROR - {message}")
            errors.append((listing, message))
    
    # Summary
    print(f"\n=== Summary ===")
    print(f"Sold/Removed: {len(sold)}")
    print(f"Price Drops: {len(price_drops)}")
    print(f"Price Increases: {len(price_increases)}")
    print(f"Errors: {len(errors)}")
    
    # Return data for notification
    return {
        'sold': sold,
        'price_drops': price_drops,
        'price_increases': price_increases,
        'errors': errors
    }

if __name__ == '__main__':
    main()
