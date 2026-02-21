#!/bin/bash
# Scrape Instagram for general search terms (not hashtags)
# Usage: ./scrape-search.sh "inmuebles maracaibo" [maxPosts]

SEARCH_TERM="${1:-inmuebles maracaibo}"
MAX_POSTS="${2:-20}"
APIFY_TOKEN="${APIFY_API_KEY:-apify_api_94b6e3psnkOX9PwMenNjdQ2nvAYjFX2adBvx}"

echo "Searching Instagram for: '$SEARCH_TERM' (max $MAX_POSTS posts)..."

# Use the Instagram Scraper actor with search functionality
RESPONSE=$(curl -s -X POST "https://api.apify.com/v2/acts/apify~instagram-scraper/runs?token=$APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"search\": \"$SEARCH_TERM\",
    \"searchType\": \"hashtag\",
    \"searchLimit\": 1,
    \"resultsLimit\": $MAX_POSTS,
    \"addParentData\": false
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

# Save results - clean the search term for filename
CLEAN_TERM=$(echo "$SEARCH_TERM" | tr ' ' '-' | tr -cd '[:alnum:]-')
OUTPUT_DIR="$(dirname "$0")/../data"
mkdir -p "$OUTPUT_DIR"
OUTPUT_FILE="$OUTPUT_DIR/search-${CLEAN_TERM}-$(date +%Y%m%d-%H%M%S).json"

curl -s "https://api.apify.com/v2/datasets/$DATASET_ID/items?token=$APIFY_TOKEN" > "$OUTPUT_FILE"

COUNT=$(jq 'length' "$OUTPUT_FILE")
echo "Saved $COUNT posts to: $OUTPUT_FILE"
