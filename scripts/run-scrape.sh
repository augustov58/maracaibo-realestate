#!/bin/bash
# Master script: scrape Instagram, process to DB, notify new listings
# Usage: ./run-scrape.sh [telegram_topic_id]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

# Setup logging
LOG_DIR="./logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/scraper-$(date +%Y%m%d).log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Load API keys from .env if exists
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

TOPIC_ID="${1:-398}"  # Default to the real estate topic
CHAT_ID="-1003777728309"

log "=== Maracaibo Real Estate Scrape START ==="

# Instagram profiles to scrape (real estate agents)
PROFILES=(
    "necya.eliterealestate"
    "regaladogroup"
    "angelpintoninmobiliaria"
    "nexthouseinmobiliaria"
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
log "--- Scraping Instagram Profiles ---"
for profile in "${PROFILES[@]}"; do
    log "Scraping @$profile..."
    ./scripts/scrape-ig-profile.sh "$profile" 5 2>&1 | tee -a "$LOG_FILE" || log "Warning: scrape failed for @$profile"
    sleep 3
done

# Scrape hashtags (5 posts each)
log "--- Scraping Instagram Hashtags ---"
for tag in "${HASHTAGS[@]}"; do
    log "Scraping #$tag..."
    ./scripts/scrape-ig.sh "#$tag" 5 2>&1 | tee -a "$LOG_FILE" || log "Warning: scrape failed for #$tag"
    sleep 3
done

# Scrape websites (runs every cycle - 3x daily)
log "--- Scraping Real Estate Websites ---"
python3 ./scripts/scrape-websites.py --output ./data --fetch-details --max-details 100 2>&1 | tee -a "$LOG_FILE"
if [ ${PIPESTATUS[0]} -ne 0 ]; then
    log "ERROR: Website scrape failed with exit code ${PIPESTATUS[0]}"
else
    log "Website scrape completed successfully"
fi

# Process all JSON files to database
log "Processing to database..."
python3 ./scripts/process-to-db.py 2>&1 | tee -a "$LOG_FILE"

# Process Instagram images - download and upload to Supabase Storage
log "Processing Instagram images..."
if [ -n "$SUPABASE_SERVICE_KEY" ]; then
    python3 ./scripts/process-instagram-images.py --limit 20 2>&1 | tee -a "$LOG_FILE" || log "Warning: image processing failed"
else
    log "Skipping image processing (SUPABASE_SERVICE_KEY not set)"
fi

# Get new listings count
NEW_COUNT=$(python3 -c "
import sys
sys.path.insert(0, './scripts')
from db import get_new_listings
listings = get_new_listings()
print(len(listings))
")

log "New listings found: $NEW_COUNT"

if [ "$NEW_COUNT" -gt 0 ]; then
    log "Formatting and outputting new listings..."
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

log "=== Scrape complete ==="
