# ADR-002: Authentication and tenant resolution

**Status:** Accepted

## Decisions
- Authentication uses signed JWTs (HS256 in dev; RS256 with OIDC keys in production).
- The algorithm is pinned on decode. "none" and algorithm-confusion tokens are rejected.
- Tenant is taken only from the verified token claim, never from a request header or body.
- Tenant isolation is a FastAPI dependency (`get_principals`), not a middleware. Middleware runs before token verification, so it cannot safely trust the tenant.
- ACL identity (user + groups) is resolved from the database on each request, so revoked group membership takes effect without waiting for token expiry.
- Retrieval queries are always wrapped with `with_acl()`. There is no code path that queries OpenSearch without the filter.
- The dev-token endpoint returns 404 outside `ENVIRONMENT=dev`.

## Consequences
- Each protected request performs one DB lookup for principals. Caching is possible later with a short TTL, but tradeoff is delayed revocation.
- Folder structure originally listed `middleware/tenant.py`. That file is removed in favour of the dependency above.