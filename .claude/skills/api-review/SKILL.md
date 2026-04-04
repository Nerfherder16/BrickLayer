---
name: api-review
description: "Review this FastAPI code for security, performance, and best practices"
---

# FastAPI Code Review

## Check For

### 1. Security
- Input validation (Pydantic models, field constraints)
- SQL/Cypher injection (parameterized queries, no f-strings in Cypher)
- Authentication/authorization on every endpoint
- CORS configuration
- Secrets exposure in logs or error responses
- Error messages don't leak internals

### 2. Performance
- N+1 queries
- Missing async/await
- Large response payloads (add pagination)
- Background tasks saturating resources (use semaphores)
- Unbounded list growth (Redis, in-memory)

### 3. Best Practices
- Proper error handling (specific exceptions, not bare except)
- Response models defined (Pydantic)
- Dependency injection for shared resources
- Singleton pattern for store/service initialization
- structlog for logging

### 4. Recall-Specific Patterns
- `scroll_all()` instead of biased semantic search for bulk ops
- `slowapi` rate limiting requires `request: Request` parameter by name
- Qdrant `DatetimeRange` goes in `range=` not `datetime_range=`
- Ollama calls need `think: false` + `format: json` + 180s timeout
- Fire-and-forget for audit writes (never block main ops)

## Response Format
- **CRITICAL**: Security issues
- **WARNING**: Performance/bugs
- **INFO**: Suggestions
