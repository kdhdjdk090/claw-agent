# Backend Skill Pack

## API Design (REST)
- Resources are nouns, not verbs: `/users`, `/orders`, not `/getUsers`
- HTTP methods carry semantics: GET (read), POST (create), PUT (replace), PATCH (update), DELETE (remove)
- Consistent error responses: `{ "error": { "code": "NOT_FOUND", "message": "..." } }`
- Pagination: cursor-based for real-time data, offset for static lists
- Versioning: URL prefix `/v1/` for breaking changes. Header versioning for minor

## Database Patterns
- **Indexing**: Index columns used in WHERE, JOIN, ORDER BY. Composite indexes match query order
- **N+1 Prevention**: Use JOINs, eager loading, or DataLoader batching. Never query inside loops
- **Migrations**: Forward-only, reversible. Never delete columns in the same deploy as code removal
- **Connection Pooling**: Always. PgBouncer for PostgreSQL, HikariCP for Java
- **Transactions**: Wrap multi-step mutations. Use serializable isolation for financial operations

## Authentication & Authorization
- Passwords: bcrypt/argon2, NEVER MD5/SHA1/plaintext
- Sessions: httpOnly, secure, sameSite cookies. Short-lived access tokens + refresh tokens
- JWT: Keep payloads small. Verify signature + expiry on every request
- RBAC/ABAC: Check permissions at the API layer, not deep in business logic
- Rate limiting: Per-user, per-IP, per-endpoint. 429 with Retry-After header

## Node.js / Express / Fastify
- Middleware chain: cors → helmet → rateLimit → auth → validation → handler
- Validation: Zod/Joi/AJV at the handler entry, before business logic
- Error handling: Central error handler middleware. Typed errors with status codes
- Logging: Structured JSON (pino/winston). Request ID on every log line
- Graceful shutdown: Handle SIGTERM, drain connections, close DB pools

## Python / Django / FastAPI
- FastAPI: Pydantic models for request/response. Dependency injection for DB/auth
- Django: Fat models, thin views. Use QuerySet methods, avoid raw SQL
- SQLAlchemy: Declarative models. Use `select()` over legacy Query API
- Async: Use `asyncio` for I/O-bound work. `ProcessPoolExecutor` for CPU-bound

## Microservices (when justified)
- Start monolith. Extract services only at clear bounded context boundaries
- Communication: REST for sync, message queues (RabbitMQ/SQS/NATS) for async
- Circuit breakers: Retry with exponential backoff + jitter. Fail fast on downstream outages
- Service discovery: DNS-based or sidecar proxy (Envoy/Istio)
