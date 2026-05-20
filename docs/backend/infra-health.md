# Infrastructure Health Endpoint

DeepFlow exposes `GET /api/v1/health` as an infrastructure-only endpoint for
container health checks, load balancers, and reverse proxy routing.

This endpoint intentionally stays outside `docs/api/openapi.yaml`, whose scope
is the product API contract consumed by frontend and module clients. The health
endpoint still uses the `/api/v1` prefix so nginx and other gateway rules can
proxy backend traffic consistently.

When the database is reachable, the endpoint returns HTTP 200 with the standard
response envelope. When the database check fails, it returns HTTP 503 with the
same response envelope and `data.db` set to `disconnected`.
