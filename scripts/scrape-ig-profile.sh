#!/bin/bash
# Scrape Instagram profile for real estate listings
# Usage: ./scrape-ig-profile.sh "username" [maxPosts]

USERNAME="${1}"
MAX_POSTS="${2:-20}"
APIFY_TOKEN="${APIFY_API_KEY:-apify_api_94b6e3psnkOX9PwMenNjdQ2nvAYjFX2adBvx}"

if [ -z "$USERNAME" ]; then
  echo "Usage: $0 <username> [max_posts]"
  exit 1
fi

# Clean username (remove @ if present)
CLEAN_USER="${USERNAME#@}"

echo "Scraping Instagram profile: @$CLEAN_USER (max $MAX_POSTS posts)..."

# Run the Instagram Profile Scraper actor
RESPONSE=$(curl -s -X POST "https://api.apify.com/v2/acts/apify~instagram-profile-scraper/runs?token=$APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"usernames\": [\"$CLEAN_USER\"],
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
TIMEOUT=180
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
  STATUS=$(curl -s "https://api.apify.com/v2/actor-runs/$RUN_ID?token=$APIFY_TOKEN" | jq -r '.data.status')
  
  if [ "$STATUS" == "SUCCEEDED" ]; then
    echo "Run completed!"
    break
  elif [ "$STATUS" == "FAILED" ] || [ "$STATUS" == "ABORTED" ]; then
    echo "Run failed with status: $STATUS"
    exit 1
  fi
  
  echo "Status: $STATUS - waiting... ($ELAPSED/$TIMEOUT sec)"
  sleep 5
  ELAPSED=$((ELAPSED + 5))
done

if [ $ELAPSED -ge $TIMEOUT ]; then
  echo "Timeout"
  exit 1
fi

# Get the dataset ID and fetch results
DATASET_ID=$(curl -s "https://api.apify.com/v2/actor-runs/$RUN_ID?token=$APIFY_TOKEN" | jq -r '.data.defaultDatasetId')

echo "Fetching results from dataset: $DATASET_ID"

# Save results
OUTPUT_DIR="$(dirname "$0")/../data"
mkdir -p "$OUTPUT_DIR"
OUTPUT_FILE="$OUTPUT_DIR/ig-profile-${CLEAN_USER}-$(date +%Y%m%d-%H%M%S).json"

curl -s "https://api.apify.com/v2/datasets/$DATASET_ID/items?token=$APIFY_TOKEN" > "$OUTPUT_FILE"

COUNT=$(jq 'length' "$OUTPUT_FILE" 2>/dev/null || echo "0")
echo "Saved $COUNT posts to: $OUTPUT_FILE"
