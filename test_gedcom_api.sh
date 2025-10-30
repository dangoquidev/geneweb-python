#!/bin/bash
# Test script for GEDCOM import API

echo "🧪 Testing GEDCOM Import API..."
echo ""

# Check if server is running
if ! curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "❌ Server is not running on http://localhost:8000"
    echo "   Please start it with: python run_api.py"
    exit 1
fi

echo "✅ Server is running"
echo ""

# Test import
echo "📤 Uploading tests/fixtures/test_family.ged..."
response=$(curl -s -X POST \
  http://localhost:8000/api/import/gedcom \
  -F "file=@tests/fixtures/test_family.ged" \
  -F "database_name=test-family-api" \
  -F "overwrite=true")

echo "📥 Response:"
echo "$response" | python -m json.tool

echo ""

# Check if database was created
if [ -f "data/test-family-api.pickle" ]; then
    echo "✅ Database created: data/test-family-api.pickle"
    ls -lh data/test-family-api.pickle
else
    echo "❌ Database NOT created: data/test-family-api.pickle"
    exit 1
fi

echo ""
echo "🎉 Test completed successfully!"
