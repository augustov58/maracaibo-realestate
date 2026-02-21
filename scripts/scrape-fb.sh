#!/bin/bash
# Scrape Facebook group/page for Maracaibo real estate listings
# Usage: ./scrape-fb.sh "https://facebook.com/groups/..." [maxPosts]

URL="${1}"
MAX_POSTS="${2:-20}"
APIFY_TOKEN="${APIFY_API_KEY:-apify_api_94b6e3psnkOX9PwMenNjdQ2nvAYjFX2adBvx}"

if [ -z "$URL" ]; then
  echo "Usage: $0 <facebook_url> [max_posts]"
  echo "Example: $0 'https://www.facebook.com/groups/123456789' 20"
  exit 1
fi

echo "Scraping Facebook: $URL (max $MAX_POSTS posts)..."

# Run the Facebook Posts Scraper actor
RESPONSE=$(curl -s -X POST "https://api.apify.com/v2/acts/apify~facebook-posts-scraper/runs?token=$APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"startUrls\": [{\"url\": \"$URL\"}],
    \"resultsLimit\": $MAX_POSTS
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
while true; do
  STATUS=$(curl -s "https://api.apify.com/v2/actor-runs/$RUN_ID?token=$APIFY_TOKEN" | jq -r '.data.status')
  
  if [ "$STATUS" == "SUCCEEDED" ]; then
    echo "Run completed!"
    break
  elif [ "$STATUS" == "FAILED" ] || [ "$STATUS" == "ABORTED" ]; then
    echo "Run failed with status: $STATUS"
    exit 1
  fi
  
  echo "Status: $STATUS - waiting..."
  sleep 5
done

# Get the dataset ID and fetch results
DATASET_ID=$(curl -s "https://api.apify.com/v2/actor-runs/$RUN_ID?token=$APIFY_TOKEN" | jq -r '.data.defaultDatasetId')

echo "Fetching results from dataset: $DATASET_ID"

# Save results
OUTPUT_DIR="$(dirname "$0")/../data"
mkdir -p "$OUTPUT_DIR"

# Extract group/page name for filename
NAME=$(echo "$URL" | grep -oP '(?<=/)[^/]+$' | head -1)
OUTPUT_FILE="$OUTPUT_DIR/fb-${NAME:-unknown}-$(date +%Y%m%d-%H%M%S).json"

curl -s "https://api.apify.com/v2/datasets/$DATASET_ID/items?token=$APIFY_TOKEN" > "$OUTPUT_FILE"

COUNT=$(jq 'length' "$OUTPUT_FILE")
echo "Saved $COUNT posts to: $OUTPUT_FILE"
