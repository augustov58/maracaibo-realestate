#!/usr/bin/env python3
"""
Full re-migration to Supabase with images.
Deletes all mcv_listings and re-imports from SQLite.
"""

import os
import json
import sqlite3
from pathlib import Path

# Load env
env_file = Path(__file__).parent.parent.parent / 'projects' / 'micasavenezuela' / '.env.local'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

from supabase import create_client

SUPABASE_URL = os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
SUPABASE_KEY = os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')
SQLITE_PATH = Path(__file__).parent.parent / 'data' / 'listings.db'

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Load latest website scrape for images
data_dir = Path(__file__).parent.parent / 'data'
latest_file = sorted(data_dir.glob('websites-*.json'))[-1]
print(f"Loading images from {latest_file.name}")

with open(latest_file) as f:
    website_listings = json.load(f)

# Create URL -> images map
url_to_images = {}
for l in website_listings:
    if l.get('url') and l.get('images'):
        url_to_images[l['url']] = l['images']

print(f"Found {len(url_to_images)} URLs with images")

# Clear existing data
print("\nDeleting existing mcv_listings...")
supabase.table('mcv_listings').delete().neq('id', 0).execute()

# Read from SQLite
print(f"\nReading from {SQLITE_PATH}")
conn = sqlite3.connect(SQLITE_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.execute('SELECT * FROM listings')
listings = [dict(row) for row in cursor.fetchall()]
conn.close()

print(f"Found {len(listings)} listings in SQLite")

# Insert in batches
batch_size = 50
inserted = 0

for i in range(0, len(listings), batch_size):
    batch = listings[i:i+batch_size]
    records = []
    
    for l in batch:
        # Get images from scrape or existing
        images = []
        if l.get('url') and l['url'] in url_to_images:
            images = url_to_images[l['url']]
        elif l.get('images'):
            try:
                images = json.loads(l['images']) if isinstance(l['images'], str) else l['images']
            except:
                images = []
        
        records.append({
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
        })
    
    try:
        result = supabase.table('mcv_listings').insert(records).execute()
        inserted += len(batch)
        print(f"\rInserted: {inserted}/{len(listings)}", end='')
    except Exception as e:
        print(f"\nError: {e}")

print(f"\n\nMigration complete: {inserted} listings")

# Count with images
result = supabase.table('mcv_listings').select('id, images').execute()
with_images = sum(1 for r in result.data if r['images'] and len(r['images']) > 0)
print(f"Listings with images: {with_images}")
