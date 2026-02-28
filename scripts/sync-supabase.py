#!/usr/bin/env python3
"""
Sync new listings from SQLite to Supabase.
Run this after scraping to update the web dashboard.
"""

import os
import json
import sqlite3
from pathlib import Path

try:
    from supabase import create_client
except ImportError:
    import subprocess
    subprocess.run(['pip', 'install', '--user', 'supabase'], check=True)
    from supabase import create_client

# Load environment
env_file = Path(__file__).parent.parent.parent / 'projects' / 'micasavenezuela' / '.env.local'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ.setdefault(key, value)

SUPABASE_URL = os.environ.get('SUPABASE_URL') or os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_KEY') or os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
    print("Set them as environment variables or in .env.local")
    exit(1)

DB_PATH = Path(__file__).parent.parent / 'data' / 'listings.db'

def sync_to_supabase():
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Get existing URLs in Supabase
    result = supabase.table('mcv_listings').select('url').execute()
    existing_urls = {r['url'] for r in result.data if r['url']}
    print(f"Existing in Supabase: {len(existing_urls)}")
    
    # Get all listings from SQLite
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute('SELECT * FROM listings')
    all_listings = [dict(row) for row in cursor.fetchall()]
    print(f"Total in SQLite: {len(all_listings)}")
    
    # Find new listings
    new_listings = [l for l in all_listings if l.get('url') and l['url'] not in existing_urls]
    print(f"New to sync: {len(new_listings)}")
    
    if not new_listings:
        print("Nothing to sync")
        return 0
    
    # Insert new listings
    inserted = 0
    errors = 0
    
    for l in new_listings:
        images = []
        if l.get('images'):
            try:
                images = json.loads(l['images']) if isinstance(l['images'], str) else l['images']
            except:
                images = []
        
        record = {
            'source': l['source'],
            'source_id': l['source_id'],
            'url': l.get('url'),
            'text': l.get('text'),
            'author': l.get('author'),
            'timestamp': l.get('timestamp'),
            'images': images,
            'likes': l.get('likes', 0),
            'price_usd': l.get('price_usd'),
            'bedrooms': l.get('bedrooms'),
            'bathrooms': l.get('bathrooms'),
            'sqm': l.get('sqm'),
            'property_type': l.get('property_type'),
            'location': l.get('location'),
            'status': l.get('status', 'new'),
            'listing_date': l.get('listing_date'),
            'original_price': l.get('original_price'),
        }
        
        try:
            supabase.table('mcv_listings').insert(record).execute()
            inserted += 1
        except Exception as e:
            errors += 1
            if 'duplicate' not in str(e).lower():
                print(f"Error inserting: {e}")
    
    print(f"✅ Synced: {inserted} new listings")
    if errors:
        print(f"⚠️ Errors: {errors}")
    
    return inserted

if __name__ == '__main__':
    sync_to_supabase()
