#!/usr/bin/env python3
"""
Post carousel of recent listings to Instagram via Postiz.
Usage: python post-carousel.py [--dry-run]
"""

import json
import requests
import sqlite3
import tempfile
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Self-hosted Postiz (localhost:4200)
API_KEY = "7073e9f6b60c01982bace378a2c44b7914a3c9330ab06871fd2e8d068b9ff623"
INSTAGRAM_ID = "cmmpto5rh0001pe9njt0sgpga"
POSTIZ_BASE_URL = "http://localhost:4200/api"
DB_PATH = Path(__file__).parent.parent / "data" / "listings.db"


def get_recent_listings(limit=5, hours=48):
    """Get recent listings not yet posted to Instagram."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    since = (datetime.now() - timedelta(hours=hours)).isoformat()
    
    c.execute('''
        SELECT id, text, property_type, location, bedrooms, bathrooms, sqm, price_usd, author, images, url
        FROM listings 
        WHERE status = 'sent' 
        AND images IS NOT NULL 
        AND images != '[]'
        AND created_at >= ?
        ORDER BY created_at DESC 
        LIMIT ?
    ''', (since, limit))
    
    return [dict(row) for row in c.fetchall()]


def upload_image(img_url):
    """Download and upload image to Postiz."""
    resp = requests.get(img_url, timeout=30)
    if resp.status_code != 200:
        return None
    
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        f.write(resp.content)
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            upload_resp = requests.post(
                f"{POSTIZ_BASE_URL}/public/v1/upload",
                headers={"Authorization": API_KEY},
                files={"file": ("image.jpg", f, "image/jpeg")}
            )
        
        if upload_resp.status_code in [200, 201]:
            data = upload_resp.json()
            return {"id": data["id"], "path": data["path"]}
    finally:
        os.unlink(temp_path)
    
    return None


def build_caption(listings, realtors_map):
    """Build carousel caption with all properties."""
    lines = ["✨ *Propiedades Destacadas del Día* ✨\n"]
    
    for i, listing in enumerate(listings):
        prop_type = (listing['property_type'] or 'Propiedad').title()
        location = listing['location'] or 'Maracaibo'
        beds = listing['bedrooms'] or '?'
        baths = listing['bathrooms'] or '?'
        sqm = f"{listing['sqm']:.0f}" if listing['sqm'] else '?'
        price = f"${listing['price_usd']:,.0f}" if listing['price_usd'] else "Consultar"
        author = listing.get('author', '')
        contact = f"@{author}" if author else ""
        
        lines.append(f"📸 Foto {i+1}: {prop_type} en {location}")
        lines.append(f"🛏️ {beds} hab | 🚿 {baths} baños | 📐 {sqm}m² | 💰 {price}")
        if contact:
            lines.append(f"📞 {contact}")
        lines.append("")
    
    lines.append("🔍 Busca más propiedades en micasavenezuela.com")
    lines.append("")
    lines.append("#maracaibo #bienesraices #venezuela #inmuebles #zulia #casaenventa #apartamento #townhouse #micasavenezuela #inversion #propiedades")
    
    return "\n".join(lines)


def post_carousel(dry_run=False):
    """Create and post carousel to Instagram."""
    print(f"[{datetime.now()}] Starting carousel post...")
    
    # Get listings
    listings = get_recent_listings(limit=5, hours=48)
    
    if len(listings) < 3:
        print(f"Only {len(listings)} listings found. Need at least 3 for carousel.")
        return False
    
    print(f"Found {len(listings)} listings")
    
    # Upload images
    uploaded_images = []
    realtors = set()
    
    for i, listing in enumerate(listings):
        images = json.loads(listing['images'])
        if not images:
            continue
        
        print(f"  {i+1}. Uploading from @{listing['author']}...")
        
        uploaded = upload_image(images[0])
        if uploaded:
            uploaded_images.append(uploaded)
            if listing['author']:
                realtors.add(f"@{listing['author']}")
            print(f"     ✓ Done")
        else:
            print(f"     ✗ Failed")
    
    if len(uploaded_images) < 3:
        print(f"Only {len(uploaded_images)} images uploaded. Need at least 3.")
        return False
    
    # Build caption
    caption = build_caption(listings[:len(uploaded_images)], None)
    
    if dry_run:
        print("\n=== DRY RUN ===")
        print(f"Would post {len(uploaded_images)} images")
        print(f"Caption:\n{caption}")
        return True
    
    # Create post
    post_data = {
        "type": "now",
        "date": datetime.utcnow().isoformat() + "Z",
        "shortLink": False,
        "tags": [],
        "posts": [{
            "integration": {"id": INSTAGRAM_ID},
            "value": [{
                "content": caption,
                "image": uploaded_images
            }],
            "settings": {
                "__type": "instagram",
                "post_type": "post"
            }
        }]
    }
    
    response = requests.post(
        f"{POSTIZ_BASE_URL}/public/v1/posts",
        headers={
            "Authorization": API_KEY,
            "Content-Type": "application/json"
        },
        json=post_data
    )
    
    if response.status_code == 201:
        data = response.json()
        print(f"✅ Posted! ID: {data[0]['postId']}")
        return True
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return False


if __name__ == '__main__':
    dry_run = '--dry-run' in sys.argv
    success = post_carousel(dry_run=dry_run)
    sys.exit(0 if success else 1)
