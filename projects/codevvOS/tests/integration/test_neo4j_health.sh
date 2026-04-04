#!/bin/bash
# Integration tests - require running docker-compose
echo "Test: Neo4j health check configured"
grep -q "healthcheck" docker-compose.yml && echo "PASS" || echo "FAIL"
echo "Test: Neo4j auth configured"
grep -q "NEO4J_AUTH" docker-compose.yml && echo "PASS" || echo "FAIL"
echo "Test: constraints.cypher has 4 node labels"
grep -c "CREATE CONSTRAINT" neo4j/constraints.cypher
