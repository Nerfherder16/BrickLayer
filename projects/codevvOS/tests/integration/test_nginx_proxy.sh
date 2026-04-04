#!/usr/bin/env bash
# tests/integration/test_nginx_proxy.sh
# Nginx proxy route smoke tests
#
# Usage: ./tests/integration/test_nginx_proxy.sh [BASE_URL]
# Default BASE_URL: https://localhost
#
# Test coverage:
#   /preview/         — expects 502 when Vite dev server (localhost:5173) is not running
#   /bl-sidecar/health — expects 200 when bl-sidecar container is healthy
#   /neo4j/           — expects 200 (redirect to Neo4j browser) when neo4j container is up

set -euo pipefail

BASE_URL="${1:-https://localhost}"
PASS=0
FAIL=0

check() {
    local description="$1"
    local expected_status="$2"
    local url="$3"

    actual_status=$(curl -sk -o /dev/null -w "%{http_code}" "$url" || echo "000")

    if [ "$actual_status" = "$expected_status" ]; then
        echo "PASS: $description (HTTP $actual_status)"
        PASS=$((PASS + 1))
    else
        echo "FAIL: $description — expected HTTP $expected_status, got HTTP $actual_status"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== Nginx Proxy Route Smoke Tests ==="
echo "Base URL: $BASE_URL"
echo ""

# /preview/ — Vite dev server on localhost:5173
# When the upstream is not running nginx returns 502 Bad Gateway.
# This is the expected state in CI / production (Vite is a dev-only server).
check "/preview/ returns 502 when Vite upstream is absent" "502" "$BASE_URL/preview/"

# /bl-sidecar/health — BrickLayer sidecar REST API
# Uncomment and run manually when the bl-sidecar container is running:
# check "/bl-sidecar/health returns 200" "200" "$BASE_URL/bl-sidecar/health"

# /neo4j/ — Neo4j browser UI
# Uncomment and run manually when the neo4j container is running:
# check "/neo4j/ returns 200" "200" "$BASE_URL/neo4j/"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
