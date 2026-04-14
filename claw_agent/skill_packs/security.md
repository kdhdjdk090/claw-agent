# Security Skill Pack

## OWASP Top 10 Defense
1. **Injection**: Parameterized queries. NEVER string-concatenate user input into SQL/commands
2. **Broken Auth**: MFA, account lockout, secure session management, constant-time comparison
3. **Sensitive Data Exposure**: Encrypt PII at rest + transit. Minimize collection. Audit access
4. **XXE**: Disable external entity processing in XML parsers
5. **Broken Access Control**: Check permissions server-side on every request. Deny by default
6. **Security Misconfiguration**: Remove default credentials, disable debug endpoints in prod
7. **XSS**: Output encoding. CSP headers. sanitize-html for user content
8. **Insecure Deserialization**: Validate schema before deserialization. No pickle from untrusted sources
9. **Known Vulnerabilities**: `npm audit`, `pip-audit`, Dependabot/Renovate. Patch within SLA
10. **Insufficient Logging**: Log auth events, access failures, input validation failures. Correlate with request IDs

## Secrets Management
- NEVER commit secrets. Use `.env` locally, vault in production
- Rotate secrets regularly. Automate rotation where possible
- HashiCorp Vault / AWS Secrets Manager / GCP Secret Manager for production
- Scan for leaked secrets: `gitleaks`, `trufflehog`, GitHub secret scanning
- Environment-specific secrets: dev/staging/prod with different credentials

## Application Security
- Input validation at every boundary: API, file upload, URL parameters, headers
- Output encoding context-aware: HTML, URL, JavaScript, CSS contexts differ
- CORS: Explicit allowlist, never `Access-Control-Allow-Origin: *` with credentials
- CSRF: SameSite cookies + CSRF tokens for state-changing requests
- Rate limiting: Authentication endpoints, password reset, API endpoints

## Cryptography
- Hashing: bcrypt/argon2id for passwords. SHA-256 for integrity. NEVER MD5/SHA1
- Encryption: AES-256-GCM for symmetric. RSA-2048+ or Ed25519 for asymmetric
- TLS 1.3 minimum. HSTS with long max-age. Certificate pinning for mobile
- Random: `crypto.randomBytes` / `secrets.token_urlsafe`. NEVER `Math.random()` for security

## Threat Modeling
- STRIDE: Spoofing, Tampering, Repudiation, Information Disclosure, DoS, Elevation
- Trust boundaries: Where does trusted become untrusted? Map every crossing
- Attack surface: Minimize exposed endpoints, ports, protocols
- Defense in depth: Multiple layers. No single point of failure in security
