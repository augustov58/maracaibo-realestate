#!/usr/bin/env python3
"""
Refresh images for existing listings by fetching from detail pages.
Useful when the scraper has been improved to get better quality images.
"""

import sqlite3
import json
import re
import time
import argparse
from pathlib import Path

try:
    import requests
except ImportError:
    import os
    os.system("pip install --user requests")
    import requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

DB_PATH = Path(__file__).parent.parent / 'data' / 'listings.db'


def fetch_regalado_images(url):
    """Fetch all full-size images from a Regalado property page."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            return None
        html = resp.text
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None
    
    images = []
    seen = set()
    
    # Extract all photo URLs from HTML and convert to full-size
    for match in re.finditer(r'photos/([A-F0-9-]+_[^"\'>\s]+)\.(jpg|png|jpeg)', html, re.I):
        path = match.group(1)
        ext = match.group(2)
        # Remove size suffix to get full-size image
        clean_path = re.sub(r'_\d+_\d+_2_$', '', path)
        full_url = f'https://regaladogroup.net/components/com_realestatemanager/photos/{clean_path}.{ext}'
        if full_url not in seen:
            seen.add(full_url)
            images.append(full_url)
    
    return images


def refresh_images(source='regaladogroup', limit=None, min_images=5):
    """Refresh images for listings that have fewer than min_images."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Get listings that need image refresh
    query = '''
        SELECT id, url, images 
        FROM listings 
        WHERE source = ?
        ORDER BY id DESC
    '''
    if limit:
        query += f' LIMIT {limit}'
    
    cursor = conn.execute(query, (source,))
    listings = cursor.fetchall()
    
    print(f"Found {len(listings)} {source} listings to check")
    
    updated = 0
    skipped = 0
    
    for listing in listings:
        current_images = json.loads(listing['images']) if listing['images'] else []
        
        # Skip if already has enough images
        if len(current_images) >= min_images:
            skipped += 1
            continue
        
        print(f"\n[{listing['id']}] Current: {len(current_images)} images")
        print(f"  URL: {listing['url'][:80]}...")
        
        # Fetch new images based on source
        if source == 'regaladogroup':
            new_images = fetch_regalado_images(listing['url'])
        else:
            print(f"  Skipping: no image fetcher for source '{source}'")
            continue
        
        if new_images is None:
            print(f"  Failed to fetch images")
            continue
        
        if len(new_images) <= len(current_images):
            print(f"  No improvement ({len(new_images)} vs {len(current_images)})")
            continue
        
        # Update the listing
        conn.execute('''
            UPDATE listings 
            SET images = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (json.dumps(new_images), listing['id']))
        conn.commit()
        
        print(f"  ✓ Updated: {len(current_images)} → {len(new_images)} images")
        updated += 1
        
        # Rate limiting
        time.sleep(1)
    
    print(f"\n=== Summary ===")
    print(f"Checked: {len(listings)}")
    print(f"Updated: {updated}")
    print(f"Skipped (already had {min_images}+ images): {skipped}")
    
    return updated


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Refresh images for existing listings')
    parser.add_argument('--source', default='regaladogroup', help='Source to refresh (default: regaladogroup)')
    parser.add_argument('--limit', type=int, help='Max listings to process')
    parser.add_argument('--min-images', type=int, default=5, help='Skip listings with at least this many images (default: 5)')
    args = parser.parse_args()
    
    refresh_images(source=args.source, limit=args.limit, min_images=args.min_images)
