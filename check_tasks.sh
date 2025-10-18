#!/bin/bash

# Get your auth token from the frontend (check localStorage or network tab)
# Replace YOUR_TOKEN_HERE with actual token

TOKEN="${1:-YOUR_TOKEN_HERE}"

echo "Fetching tasks..."
echo ""

curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/integrations/tasks | jq '.'

echo ""
echo "Usage: ./check_tasks.sh YOUR_AUTH_TOKEN"

