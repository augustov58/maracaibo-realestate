#!/bin/bash
# Master script: scrape Instagram, process to DB, notify new listings
# Usage: ./run-scrape.sh [telegram_topic_id]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

# Load API keys from .env if exists
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

TOPIC_ID="${1:-398}"  # Default to the real estate topic
CHAT_ID="-1003777728309"

echo "=== Maracaibo Real Estate Scrape $(date) ==="

# Instagram profiles to scrape (real estate agents)
PROFILES=(
    "necya.eliterealestate"
    "regaladogroup"
    "angelpintoninmobiliaria"
    "nexthouseinmobiliaria"
    "zuhausebienesraices"
)

# Hashtags to search
HASHTAGS=(
    "inmueblesmaracaibo"
    "casasenmaracaibo"
    "apartamentosmaracaibo"
    "ventacasamaracaibo"
    "bienesraicesmaracaibo"
    "ventamaracaibo"
)

# Scrape profiles first (5 posts each)
echo "--- Scraping Instagram Profiles ---"
for profile in "${PROFILES[@]}"; do
    echo "Scraping @$profile..."
    ./scripts/scrape-ig-profile.sh "$profile" 5 2>&1 || echo "Warning: scrape failed for @$profile"
    sleep 3
done

# Scrape hashtags (5 posts each)
echo "--- Scraping Instagram Hashtags ---"
for tag in "${HASHTAGS[@]}"; do
    echo "Scraping #$tag..."
    ./scripts/scrape-ig.sh "#$tag" 5 2>&1 || echo "Warning: scrape failed for #$tag"
    sleep 3
done

# Scrape websites (run once per day, not every scrape cycle)
HOUR=$(date +%H)
if [ "$HOUR" == "08" ]; then
    echo "--- Scraping Real Estate Websites ---"
    python3 ./scripts/scrape-websites.py --output ./data 2>&1 || echo "Warning: website scrape failed"
fi

# Process all JSON files to database
echo "Processing to database..."
python3 ./scripts/process-to-db.py

# Get new listings count
NEW_COUNT=$(python3 -c "
import sys
sys.path.insert(0, './scripts')
from db import get_new_listings
listings = get_new_listings()
print(len(listings))
")

echo "New listings found: $NEW_COUNT"

if [ "$NEW_COUNT" -gt 0 ]; then
    echo "Formatting and outputting new listings..."
    # Output formatted listings for notification
    python3 -c "
import sys
sys.path.insert(0, './scripts')
from db import get_new_listings, format_listing_telegram, mark_sent

listings = get_new_listings(limit=10)
ids = []
for l in listings:
    print('---LISTING---')
    print(format_listing_telegram(l))
    ids.append(l['id'])

# Mark as sent
mark_sent(ids)
"
fi

echo "=== Scrape complete ==="
