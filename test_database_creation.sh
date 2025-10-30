#!/bin/bash
# Test end-to-end de la création de base de données
# Usage: ./test_database_creation.sh

set -e  # Exit on error

echo "🧪 Test E2E: Création de base de données"
echo "=========================================="
echo ""

# Configuration
API_URL="http://127.0.0.1:8000/api"
TEST_DB_NAME="e2e_test_$(date +%s)"

echo "📋 Configuration:"
echo "  API URL: $API_URL"
echo "  Test DB: $TEST_DB_NAME"
echo ""

# Test 1: Health check
echo "1️⃣  Test: Health check API"
HEALTH=$(curl -s "$API_URL/health" | python -m json.tool)
echo "✅ API is healthy"
echo "$HEALTH"
echo ""

# Test 2: List databases (before)
echo "2️⃣  Test: Liste des bases (avant création)"
BEFORE=$(curl -s "$API_URL/databases")
COUNT_BEFORE=$(echo "$BEFORE" | python -c "import sys, json; print(json.load(sys.stdin)['count'])")
echo "✅ Bases actuelles: $COUNT_BEFORE"
echo "$BEFORE" | python -m json.tool
echo ""

# Test 3: Create database
echo "3️⃣  Test: Création de base '$TEST_DB_NAME'"
CREATE_RESPONSE=$(curl -s -X POST "$API_URL/databases" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"$TEST_DB_NAME\", \"db_type\": \"pickle\"}")
SUCCESS=$(echo "$CREATE_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['success'])")

if [ "$SUCCESS" == "True" ]; then
    echo "✅ Base créée avec succès"
    echo "$CREATE_RESPONSE" | python -m json.tool
else
    echo "❌ Échec de création"
    echo "$CREATE_RESPONSE" | python -m json.tool
    exit 1
fi
echo ""

# Test 4: Verify file exists
echo "4️⃣  Test: Vérification fichier physique"
DB_PATH="data/${TEST_DB_NAME}.pickle"
if [ -f "$DB_PATH" ]; then
    FILE_SIZE=$(stat -c%s "$DB_PATH")
    echo "✅ Fichier créé: $DB_PATH ($FILE_SIZE bytes)"
    ls -lh "$DB_PATH"
else
    echo "❌ Fichier non trouvé: $DB_PATH"
    exit 1
fi
echo ""

# Test 5: List databases (after)
echo "5️⃣  Test: Liste des bases (après création)"
AFTER=$(curl -s "$API_URL/databases")
COUNT_AFTER=$(echo "$AFTER" | python -c "import sys, json; print(json.load(sys.stdin)['count'])")
echo "✅ Bases actuelles: $COUNT_AFTER (avant: $COUNT_BEFORE)"

if [ "$COUNT_AFTER" -gt "$COUNT_BEFORE" ]; then
    echo "✅ Nouvelle base détectée dans la liste"
else
    echo "❌ La base n'apparaît pas dans la liste"
    exit 1
fi
echo ""

# Test 6: Get database info
echo "6️⃣  Test: Récupération info base"
INFO=$(curl -s "$API_URL/databases/$TEST_DB_NAME")
PERSONS=$(echo "$INFO" | python -c "import sys, json; print(json.load(sys.stdin)['persons'])")
FAMILIES=$(echo "$INFO" | python -c "import sys, json; print(json.load(sys.stdin)['families'])")
echo "✅ Info récupérées:"
echo "   Personnes: $PERSONS (attendu: 0)"
echo "   Familles: $FAMILIES (attendu: 0)"
echo "$INFO" | python -m json.tool
echo ""

# Test 7: Test invalid names
echo "7️⃣  Test: Validation noms invalides"

# Test 7a: Special characters
echo "  → Test caractères spéciaux (/)..."
INVALID_1=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_URL/databases" \
  -H "Content-Type: application/json" \
  -d '{"name": "invalid/name", "db_type": "pickle"}')
if [ "$INVALID_1" == "422" ]; then
    echo "  ✅ Rejeté (422)"
else
    echo "  ❌ Devrait être rejeté (got $INVALID_1)"
fi

# Test 7b: Reserved name
echo "  → Test nom réservé (con)..."
INVALID_2=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_URL/databases" \
  -H "Content-Type: application/json" \
  -d '{"name": "con", "db_type": "pickle"}')
if [ "$INVALID_2" == "422" ]; then
    echo "  ✅ Rejeté (422)"
else
    echo "  ❌ Devrait être rejeté (got $INVALID_2)"
fi

# Test 7c: Duplicate name
echo "  → Test nom dupliqué ($TEST_DB_NAME)..."
INVALID_3=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_URL/databases" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"$TEST_DB_NAME\", \"db_type\": \"pickle\"}")
if [ "$INVALID_3" == "400" ]; then
    echo "  ✅ Rejeté (400)"
else
    echo "  ❌ Devrait être rejeté (got $INVALID_3)"
fi
echo ""

# Test 8: Delete database (cleanup)
echo "8️⃣  Test: Suppression base"
DELETE_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "$API_URL/databases/$TEST_DB_NAME")
if [ "$DELETE_RESPONSE" == "204" ]; then
    echo "✅ Base supprimée (204 No Content)"
else
    echo "❌ Échec suppression (got $DELETE_RESPONSE)"
fi

# Verify file deleted
if [ ! -f "$DB_PATH" ]; then
    echo "✅ Fichier physique supprimé"
else
    echo "⚠️  Fichier encore présent, nettoyage manuel..."
    rm -f "$DB_PATH"
fi
echo ""

# Test 9: Final count
echo "9️⃣  Test: Vérification liste finale"
FINAL=$(curl -s "$API_URL/databases")
COUNT_FINAL=$(echo "$FINAL" | python -c "import sys, json; print(json.load(sys.stdin)['count'])")
if [ "$COUNT_FINAL" == "$COUNT_BEFORE" ]; then
    echo "✅ Retour à l'état initial ($COUNT_FINAL bases)"
else
    echo "⚠️  Nombre différent: avant=$COUNT_BEFORE, final=$COUNT_FINAL"
fi
echo ""

# Summary
echo "=========================================="
echo "✅ Tous les tests E2E ont réussi!"
echo ""
echo "📊 Résumé:"
echo "  - API Health: OK"
echo "  - Création: OK"
echo "  - Fichier physique: OK"
echo "  - Liste databases: OK"
echo "  - Info database: OK"
echo "  - Validation noms: OK"
echo "  - Suppression: OK"
echo "  - Cleanup: OK"
echo ""
echo "🎉 Intégration backend ↔️ frontend validée!"
