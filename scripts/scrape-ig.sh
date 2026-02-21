#!/bin/bash
# Scrape Instagram hashtag for Maracaibo real estate listings
# Usage: ./scrape-ig.sh "#ventamaracaibo" [maxPosts]

HASHTAG="${1:-#ventamaracaibo}"
MAX_POSTS="${2:-20}"
APIFY_TOKEN="${APIFY_API_KEY:?APIFY_API_KEY not set}"

# Clean hashtag (remove # for URL)
CLEAN_TAG="${HASHTAG#\#}"

echo "Scraping Instagram hashtag: $HASHTAG (max $MAX_POSTS posts)..."

# Run the Instagram Hashtag Scraper actor
RESPONSE=$(curl -s -X POST "https://api.apify.com/v2/acts/apify~instagram-hashtag-scraper/runs?token=$APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"hashtags\": [\"$CLEAN_TAG\"],
    \"resultsLimit\": $MAX_POSTS,
    \"searchType\": \"hashtag\",
    \"searchLimit\": 1
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
OUTPUT_FILE="$OUTPUT_DIR/ig-${CLEAN_TAG}-$(date +%Y%m%d-%H%M%S).json"

curl -s "https://api.apify.com/v2/datasets/$DATASET_ID/items?token=$APIFY_TOKEN" > "$OUTPUT_FILE"

COUNT=$(jq 'length' "$OUTPUT_FILE")
echo "Saved $COUNT posts to: $OUTPUT_FILE"
