---
name: docker-status
description: "Check the Docker environment health"
---

# Docker Status Check

## CasaOS Docker Host
- IP: 192.168.50.19
- SSH: `ssh nerfherder@192.168.50.19`
- Data: `/DATA/AppData/`

## Quick Commands
```bash
# List running containers
docker ps

# Check specific container logs
docker logs -f [container-name]

# Container health
docker inspect --format='{{.State.Health.Status}}' [container]

# Disk usage
docker system df
```

## Key Service Groups

### Recall (memory system)
- recall-api (:8200) — FastAPI
- qdrant (:6333) — Vector search
- neo4j (:7474/:7687) — Graph memory
- redis (:6379) — Sessions/cache
- postgres (:5432) — Audit log, metrics

### Family Hub (Sadie voice AI)
- family-hub-api (:7070) — FastAPI
- speaker-id (:10400) — Voice recognition
- stt-whisper-http (:10300) — Speech-to-text

### Media Stack
- jellyfin, sonarr, radarr, prowlarr
- gluetun (VPN) — routes *arr traffic
- riven (:8180/:3030) — Media automation

## VPN Check
```bash
docker exec gluetun wget -qO- https://ipinfo.io
```
