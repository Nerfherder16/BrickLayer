#!/bin/bash
# Wait for Neo4j to be ready then run constraints
until cypher-shell -u neo4j -p codevvos "RETURN 1" 2>/dev/null; do sleep 2; done
cypher-shell -u neo4j -p codevvos < /docker-entrypoint-initdb.d/constraints.cypher
