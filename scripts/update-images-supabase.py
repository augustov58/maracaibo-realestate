#!/usr/bin/env python3
"""
Update images in Supabase from latest website scrape.
"""

import os
import json
from pathlib import Path

# Load environment from .env.local in the web project
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

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Missing Supabase credentials")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Load latest website data
data_dir = Path(__file__).parent.parent / 'data'
latest_file = sorted(data_dir.glob('websites-*.json'))[-1]
print(f"Loading from {latest_file.name}")

with open(latest_file) as f:
    listings = json.load(f)

# Update each listing with images
updated = 0
for listing in listings:
    images = listing.get('images', [])
    if not images:
        continue
    
    url = listing.get('url')
    if not url:
        continue
    
    # Find and update in Supabase
    result = supabase.table('mcv_listings').update({
        'images': images
    }).eq('url', url).execute()
    
    if result.data:
        updated += 1
        print(f"✓ Updated: {url[:60]}...")

print(f"\nTotal updated: {updated}")
