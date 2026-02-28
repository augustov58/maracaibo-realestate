#!/usr/bin/env python3
"""
Download Instagram images and upload to Supabase Storage.
Replaces expiring CDN URLs with permanent Supabase URLs.
"""

import os
import json
import sqlite3
import hashlib
import requests
from pathlib import Path
from datetime import datetime

try:
    from supabase import create_client
except ImportError:
    import subprocess
    subprocess.run(['pip', 'install', '--user', 'supabase'], check=True)
    from supabase import create_client

SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://blvambokvobhakfabnec.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '')
BUCKET_NAME = 'listing-images'
DB_PATH = Path(__file__).parent.parent / 'data' / 'listings.db'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

def get_image_hash(url):
    """Create a hash from URL for filename."""
    return hashlib.md5(url.encode()).hexdigest()[:12]

def download_image(url):
    """Download image and return bytes."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code == 200 and len(resp.content) > 1000:
            return resp.content
    except Exception as e:
        print(f"  Download error: {e}")
    return None

def upload_to_supabase(supabase, image_bytes, listing_id, image_index):
    """Upload image to Supabase Storage, return public URL."""
    filename = f"{listing_id}/{image_index}.jpg"
    
    try:
        # Check if already exists
        existing = supabase.storage.from_(BUCKET_NAME).list(str(listing_id))
        existing_names = [f['name'] for f in existing] if existing else []
        
        if f"{image_index}.jpg" in existing_names:
            # Already uploaded
            return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{filename}"
        
        # Upload
        result = supabase.storage.from_(BUCKET_NAME).upload(
            filename,
            image_bytes,
            {'content-type': 'image/jpeg'}
        )
        
        return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{filename}"
    except Exception as e:
        if 'Duplicate' in str(e) or 'already exists' in str(e).lower():
            return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{filename}"
        print(f"  Upload error: {e}")
        return None

def process_instagram_listings(limit=50):
    """Process Instagram listings, download and re-upload images."""
    if not SUPABASE_KEY:
        print("Error: SUPABASE_SERVICE_KEY not set")
        return
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Get Instagram listings with CDN images
    cursor = conn.execute('''
        SELECT id, url, images 
        FROM listings 
        WHERE (source = 'instagram' OR url LIKE '%instagram%')
        AND images LIKE '%cdninstagram%'
        ORDER BY created_at DESC
        LIMIT ?
    ''', (limit,))
    
    listings = cursor.fetchall()
    print(f"Found {len(listings)} Instagram listings to process")
    
    processed = 0
    for listing in listings:
        listing_id = listing['id']
        
        try:
            images = json.loads(listing['images']) if listing['images'] else []
        except:
            continue
        
        if not images:
            continue
        
        # Filter to only CDN images
        cdn_images = [img for img in images if 'cdninstagram' in img or 'fbcdn' in img]
        if not cdn_images:
            continue
        
        print(f"\n[{listing_id}] Processing {len(cdn_images)} images...")
        
        new_images = []
        for i, img_url in enumerate(cdn_images[:5]):  # Limit to 5 images per listing
            print(f"  Downloading image {i+1}...")
            img_bytes = download_image(img_url)
            
            if img_bytes:
                new_url = upload_to_supabase(supabase, img_bytes, listing_id, i)
                if new_url:
                    new_images.append(new_url)
                    print(f"  ✓ Uploaded: {new_url[-40:]}")
                else:
                    print(f"  ✗ Upload failed")
            else:
                print(f"  ✗ Download failed (image may have expired)")
        
        if new_images:
            # Update database with new URLs
            conn.execute(
                'UPDATE listings SET images = ? WHERE id = ?',
                (json.dumps(new_images), listing_id)
            )
            conn.commit()
            processed += 1
            print(f"  ✓ Updated with {len(new_images)} permanent images")
    
    print(f"\n✅ Processed {processed} listings")
    conn.close()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=50, help='Max listings to process')
    args = parser.parse_args()
    
    process_instagram_listings(limit=args.limit)
