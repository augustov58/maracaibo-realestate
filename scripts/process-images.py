#!/usr/bin/env python3
"""
Image Processor for Mi Casa Venezuela
Downloads images from Instagram/web and uploads to Supabase Storage
"""

import os
import sys
import json
import hashlib
import httpx
from pathlib import Path

# Supabase config
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '')
BUCKET = 'listing-images'

def get_supabase_client():
    """Create Supabase client"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Warning: Supabase credentials not set, skipping image upload")
        return None
    
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def download_image(url: str, timeout: int = 30) -> bytes | None:
    """Download image from URL with proper headers"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.instagram.com/',
    }
    
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            if response.status_code == 200:
                return response.content
            else:
                print(f"  Failed to download {url[:50]}... (status {response.status_code})")
                return None
    except Exception as e:
        print(f"  Error downloading {url[:50]}...: {e}")
        return None

def upload_to_storage(supabase, listing_id: str, image_data: bytes, index: int) -> str | None:
    """Upload image to Supabase Storage"""
    try:
        # Generate filename
        ext = 'jpg'  # Default, could detect from content
        filename = f"listings/{listing_id}/{index}.{ext}"
        
        # Upload to storage
        result = supabase.storage.from_(BUCKET).upload(
            filename,
            image_data,
            file_options={"content-type": "image/jpeg", "upsert": "true"}
        )
        
        # Get public URL
        public_url = supabase.storage.from_(BUCKET).get_public_url(filename)
        return public_url
    except Exception as e:
        print(f"  Error uploading image: {e}")
        return None

def process_listing_images(supabase, listing_id: str, image_urls: list, source: str) -> list:
    """
    Download and upload images for a listing.
    Only processes Instagram images (others don't need proxy).
    """
    if source != 'instagram':
        return image_urls  # Return original URLs for non-Instagram sources
    
    if not supabase:
        return image_urls  # Can't upload without Supabase
    
    stored_urls = []
    for i, url in enumerate(image_urls[:10]):  # Limit to 10 images per listing
        if not url or 'cdninstagram.com' not in url:
            stored_urls.append(url)
            continue
            
        print(f"  Downloading image {i+1}/{len(image_urls[:10])} for listing {listing_id}...")
        image_data = download_image(url)
        
        if image_data:
            stored_url = upload_to_storage(supabase, listing_id, image_data, i)
            if stored_url:
                stored_urls.append(stored_url)
                print(f"    ✓ Uploaded to storage")
            else:
                stored_urls.append(url)  # Fallback to original
        else:
            stored_urls.append(url)  # Fallback to original
    
    return stored_urls

def ensure_bucket_exists(supabase):
    """Create bucket if it doesn't exist"""
    try:
        buckets = supabase.storage.list_buckets()
        bucket_names = [b.name for b in buckets]
        
        if BUCKET not in bucket_names:
            print(f"Creating bucket '{BUCKET}'...")
            supabase.storage.create_bucket(BUCKET, options={"public": True})
            print(f"  ✓ Bucket created")
        else:
            print(f"Bucket '{BUCKET}' exists")
    except Exception as e:
        print(f"Error with bucket: {e}")

def main():
    """Test the image processor"""
    supabase = get_supabase_client()
    if not supabase:
        print("No Supabase credentials, exiting")
        sys.exit(1)
    
    ensure_bucket_exists(supabase)
    
    # Test with a sample Instagram image
    test_urls = [
        "https://scontent-atl3-3.cdninstagram.com/v/t51.82787-15/example.jpg"
    ]
    
    result = process_listing_images(supabase, "test-123", test_urls, "instagram")
    print(f"Result: {result}")

if __name__ == "__main__":
    main()
