#!/bin/bash
# Scrape Facebook groups for Maracaibo real estate listings
# Usage: ./scrape-fb-groups.sh [maxPosts]

set -e

MAX_POSTS="${1:-30}"
APIFY_TOKEN="${APIFY_API_KEY:-apify_api_94b6e3psnkOX9PwMenNjdQ2nvAYjFX2adBvx}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/../data"
mkdir -p "$OUTPUT_DIR"

# Facebook group URL
GROUP_URL="https://www.facebook.com/groups/1099521444366476"
GROUP_ID="1099521444366476"

echo "========================================"
echo "Scraping: $GROUP_URL"
echo "Max posts: $MAX_POSTS"
echo "========================================"

RESPONSE=$(curl -s -X POST "https://api.apify.com/v2/acts/apify~facebook-groups-scraper/runs?token=$APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"startUrls\": [{\"url\": \"$GROUP_URL\"}],
    \"maxPosts\": $MAX_POSTS,
    \"maxPostComments\": 0,
    \"maxReviews\": 0,
    \"proxy\": {
      \"useApifyProxy\": true
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

# Poll for completion
TIMEOUT=300
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
  STATUS=$(curl -s "https://api.apify.com/v2/actor-runs/$RUN_ID?token=$APIFY_TOKEN" | jq -r '.data.status')
  
  if [ "$STATUS" == "SUCCEEDED" ]; then
    echo "Run completed!"
    break
  elif [ "$STATUS" == "FAILED" ] || [ "$STATUS" == "ABORTED" ]; then
    echo "Run failed with status: $STATUS"
    curl -s "https://api.apify.com/v2/actor-runs/$RUN_ID?token=$APIFY_TOKEN" | jq '.data.statusMessage'
    exit 1
  fi
  
  echo "Status: $STATUS - waiting... ($ELAPSED/$TIMEOUT sec)"
  sleep 10
  ELAPSED=$((ELAPSED + 10))
done

if [ $ELAPSED -ge $TIMEOUT ]; then
  echo "Timeout waiting for scrape"
  exit 1
fi

# Get results
DATASET_ID=$(curl -s "https://api.apify.com/v2/actor-runs/$RUN_ID?token=$APIFY_TOKEN" | jq -r '.data.defaultDatasetId')
OUTPUT_FILE="$OUTPUT_DIR/fb-group-${GROUP_ID}-$(date +%Y%m%d-%H%M%S).json"

curl -s "https://api.apify.com/v2/datasets/$DATASET_ID/items?token=$APIFY_TOKEN" > "$OUTPUT_FILE"

COUNT=$(jq 'length' "$OUTPUT_FILE" 2>/dev/null || echo "0")
echo "Saved $COUNT posts to: $OUTPUT_FILE"

# Show sample
if [ "$COUNT" != "0" ] && [ "$COUNT" != "null" ]; then
  echo "Sample post:"
  jq '.[0] | {text: .text[0:200], url: .url}' "$OUTPUT_FILE" 2>/dev/null || true
fi

echo "========================================"
echo "Running filter..."
echo "========================================"

python3 "$SCRIPT_DIR/filter-fb-groups.py"
