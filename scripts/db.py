#!/usr/bin/env python3
"""
SQLite database for Maracaibo real estate listings.
Handles storage, deduplication, and queries.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "data" / "listings.db"

def get_db():
    """Get database connection"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database schema"""
    conn = get_db()
    
    # Create tables first (without sector index yet)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            source_id TEXT NOT NULL,
            url TEXT,
            text TEXT,
            author TEXT,
            timestamp TEXT,
            images TEXT,
            likes INTEGER DEFAULT 0,
            price_usd REAL,
            bedrooms INTEGER,
            bathrooms INTEGER,
            sqm REAL,
            property_type TEXT,
            location TEXT,
            status TEXT DEFAULT 'new',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source, source_id)
        );
        
        CREATE TABLE IF NOT EXISTS sent_to_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER NOT NULL,
            group_id TEXT NOT NULL,
            sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(listing_id, group_id),
            FOREIGN KEY (listing_id) REFERENCES listings(id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_listings_status ON listings(status);
        CREATE INDEX IF NOT EXISTS idx_listings_price ON listings(price_usd);
        CREATE INDEX IF NOT EXISTS idx_listings_type ON listings(property_type);
        CREATE INDEX IF NOT EXISTS idx_listings_created ON listings(created_at);
        CREATE INDEX IF NOT EXISTS idx_sent_group ON sent_to_groups(group_id);
    """)
    
    # Migration: add sector column if missing
    try:
        conn.execute("SELECT sector FROM listings LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE listings ADD COLUMN sector TEXT")
        print("Added 'sector' column to listings table")
    
    # Now create sector index (after migration ensures column exists)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_listings_sector ON listings(sector)")
    
    conn.commit()
    conn.close()
    print(f"Database initialized: {DB_PATH}")

def add_listing(listing: dict) -> bool:
    """Add a listing to the database. Returns True if new, False if duplicate."""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO listings (
                source, source_id, url, text, author, timestamp,
                images, likes, price_usd, bedrooms, bathrooms,
                sqm, property_type, location, sector, listing_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            listing.get('source'),
            listing.get('id') or listing.get('source_id'),
            listing.get('url'),
            listing.get('text'),
            listing.get('author'),
            listing.get('timestamp'),
            json.dumps(listing.get('images', [])),
            listing.get('likes', 0),
            listing.get('price_usd'),
            listing.get('bedrooms'),
            listing.get('bathrooms'),
            listing.get('sqm'),
            listing.get('property_type'),
            listing.get('location'),
            listing.get('sector'),
            listing.get('listing_date')
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Duplicate
        return False
    finally:
        conn.close()

def get_listings(
    status: str = None,
    property_type: str = None,
    min_price: float = None,
    max_price: float = None,
    min_bedrooms: int = None,
    limit: int = 50,
    offset: int = 0
) -> list:
    """Query listings with filters"""
    conn = get_db()
    
    query = "SELECT * FROM listings WHERE 1=1"
    params = []
    
    if status:
        query += " AND status = ?"
        params.append(status)
    if property_type:
        query += " AND property_type = ?"
        params.append(property_type)
    if min_price:
        query += " AND price_usd >= ?"
        params.append(min_price)
    if max_price:
        query += " AND price_usd <= ?"
        params.append(max_price)
    if min_bedrooms:
        query += " AND bedrooms >= ?"
        params.append(min_bedrooms)
    
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor = conn.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_new_listings(limit: int = 20) -> list:
    """Get listings with status 'new'"""
    return get_listings(status='new', limit=limit)

def get_unsent_for_group(group_id: str, limit: int = 20) -> list:
    """Get listings that haven't been sent to a specific group yet."""
    conn = get_db()
    cursor = conn.execute("""
        SELECT l.* FROM listings l
        WHERE l.id NOT IN (
            SELECT listing_id FROM sent_to_groups WHERE group_id = ?
        )
        ORDER BY l.created_at DESC
        LIMIT ?
    """, (group_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def mark_sent(listing_ids: list):
    """Mark listings as sent (legacy - updates status field)"""
    if not listing_ids:
        return
    conn = get_db()
    placeholders = ','.join('?' * len(listing_ids))
    conn.execute(
        f"UPDATE listings SET status = 'sent', updated_at = CURRENT_TIMESTAMP WHERE id IN ({placeholders})",
        listing_ids
    )
    conn.commit()
    conn.close()

def mark_sent_to_group(listing_ids: list, group_id: str):
    """Mark listings as sent to a specific group."""
    if not listing_ids:
        return
    conn = get_db()
    for lid in listing_ids:
        try:
            conn.execute(
                "INSERT INTO sent_to_groups (listing_id, group_id) VALUES (?, ?)",
                (lid, group_id)
            )
        except sqlite3.IntegrityError:
            pass  # Already sent to this group
    conn.commit()
    conn.close()

def mark_reviewed(listing_id: int, interested: bool = False):
    """Mark a listing as reviewed"""
    status = 'interested' if interested else 'reviewed'
    conn = get_db()
    conn.execute(
        "UPDATE listings SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (status, listing_id)
    )
    conn.commit()
    conn.close()

def get_stats() -> dict:
    """Get database statistics"""
    conn = get_db()
    stats = {}
    
    stats['total'] = conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0]
    stats['new'] = conn.execute("SELECT COUNT(*) FROM listings WHERE status = 'new'").fetchone()[0]
    stats['sent'] = conn.execute("SELECT COUNT(*) FROM listings WHERE status = 'sent'").fetchone()[0]
    stats['interested'] = conn.execute("SELECT COUNT(*) FROM listings WHERE status = 'interested'").fetchone()[0]
    
    # By type
    cursor = conn.execute("SELECT property_type, COUNT(*) FROM listings GROUP BY property_type")
    stats['by_type'] = dict(cursor.fetchall())
    
    # By source
    cursor = conn.execute("SELECT source, COUNT(*) FROM listings GROUP BY source")
    stats['by_source'] = dict(cursor.fetchall())
    
    conn.close()
    return stats

def format_listing_telegram(listing: dict) -> str:
    """Format a listing for Telegram - compact format with clickable links"""
    emoji = {
        'casa': '🏠', 
        'apartamento': '🏢', 
        'townhouse': '🏘️', 
        'terreno': '🏗️',
        'comercial': '🏪'
    }.get(listing.get('property_type'), '🏠')
    
    # Price
    price = f"${listing['price_usd']:,.0f}" if listing.get('price_usd') else ''
    
    # Location - shorten Maracaibo
    loc = listing.get('location', '')
    if loc:
        loc = loc.replace('Maracaibo - ', '').replace('Maracaibo', 'Mcbo')
        if len(loc) > 25:
            loc = loc[:22] + '...'
    
    # Details compact: 3h|2b|120m²
    details = []
    if listing.get('bedrooms'):
        details.append(f"{int(listing['bedrooms'])}h")
    if listing.get('bathrooms'):
        details.append(f"{int(listing['bathrooms'])}b")
    if listing.get('sqm'):
        details.append(f"{int(listing['sqm'])}m²")
    details_str = '|'.join(details)
    
    # Build line: emoji $price - Location | details → [Ver](url)
    parts = [emoji]
    if price:
        parts.append(price)
    if loc:
        parts.append(f"- {loc}")
    if details_str:
        parts.append(f"| {details_str}")
    
    url = listing.get('url', '')
    if url:
        parts.append(f"→ [Ver]({url})")
    
    return ' '.join(parts)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == 'init':
            init_db()
        elif cmd == 'stats':
            stats = get_stats()
            print(json.dumps(stats, indent=2))
        elif cmd == 'new':
            listings = get_new_listings()
            for l in listings:
                print(format_listing_telegram(l))
                print('---')
        elif cmd == 'all':
            listings = get_listings(limit=100)
            print(json.dumps(listings, indent=2, default=str))
    else:
        print("Usage: python db.py [init|stats|new|all]")
