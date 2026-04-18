#!/bin/bash

BASE_URL="${1}" # Scalekit URL
CLIENT_ID="${2}" # Scalekit client ID
CLIENT_SECRET="${3}" # Scalekit secret

if [[ -z "$BASE_URL" || -z "$CLIENT_ID" || -z "$CLIENT_SECRET" ]]; then
  echo "Usage: $0 <base_url> <client_id> <client_secret>"
  exit 1
fi

curl -s -X POST "${BASE_URL}/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}"
