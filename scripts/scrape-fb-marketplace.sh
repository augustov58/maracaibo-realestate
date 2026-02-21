#!/bin/bash
# Scrape Facebook Marketplace for Maracaibo real estate
# Usage: ./scrape-fb-marketplace.sh [maxListings]

MAX_LISTINGS="${1:-20}"
APIFY_TOKEN="${APIFY_API_KEY:?APIFY_API_KEY not set}"

echo "Scraping Facebook Marketplace for Maracaibo real estate (max $MAX_LISTINGS)..."

# Use the Facebook Marketplace scraper with location URL
# Maracaibo marketplace property rentals/sales URL
MARKETPLACE_URL="https://www.facebook.com/marketplace/maracaibo/propertyrentals"

RESPONSE=$(curl -s -X POST "https://api.apify.com/v2/acts/apify~facebook-marketplace-scraper/runs?token=$APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"startUrls\": [{\"url\": \"$MARKETPLACE_URL\"}],
    \"maxItems\": $MAX_LISTINGS,
    \"proxy\": {
      \"useApifyProxy\": true,
      \"apifyProxyGroups\": [\"RESIDENTIAL\"]
    }
  }")

RUN_ID=$(echo "$RESPONSE" | jq -r '.data.id')

if [ "$RUN_ID" == "null" ] || [ -z "$RUN_ID" ]; then
  echo "Error starting actor run:"
  echo "$RESPONSE" | jq .
  exit 1
fi

echo "Run started: $RUN_ID"
echo "Waiting for completion..."

# Poll for completion (Facebook scrapes take longer)
TIMEOUT=300
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
  STATUS=$(curl -s "https://api.apify.com/v2/actor-runs/$RUN_ID?token=$APIFY_TOKEN" | jq -r '.data.status')
  
  if [ "$STATUS" == "SUCCEEDED" ]; then
    echo "Run completed!"
    break
  elif [ "$STATUS" == "FAILED" ] || [ "$STATUS" == "ABORTED" ]; then
    echo "Run failed with status: $STATUS"
    # Get error details
    curl -s "https://api.apify.com/v2/actor-runs/$RUN_ID?token=$APIFY_TOKEN" | jq '.data.statusMessage'
    exit 1
  fi
  
  echo "Status: $STATUS - waiting... ($ELAPSED/$TIMEOUT sec)"
  sleep 10
  ELAPSED=$((ELAPSED + 10))
done

if [ $ELAPSED -ge $TIMEOUT ]; then
  echo "Timeout waiting for scrape to complete"
  exit 1
fi

# Get the dataset ID and fetch results
DATASET_ID=$(curl -s "https://api.apify.com/v2/actor-runs/$RUN_ID?token=$APIFY_TOKEN" | jq -r '.data.defaultDatasetId')

echo "Fetching results from dataset: $DATASET_ID"

OUTPUT_DIR="$(dirname "$0")/../data"
mkdir -p "$OUTPUT_DIR"
OUTPUT_FILE="$OUTPUT_DIR/fb-marketplace-$(date +%Y%m%d-%H%M%S).json"

curl -s "https://api.apify.com/v2/datasets/$DATASET_ID/items?token=$APIFY_TOKEN" > "$OUTPUT_FILE"

COUNT=$(jq 'length' "$OUTPUT_FILE" 2>/dev/null || echo "0")
echo "Saved $COUNT listings to: $OUTPUT_FILE"

# Show sample if we got results
if [ "$COUNT" -gt 0 ]; then
  echo "Sample listing:"
  jq '.[0]' "$OUTPUT_FILE"
fi
