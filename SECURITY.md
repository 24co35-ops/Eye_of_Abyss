# Eye of Abyss — Security Policy & Hardening Guide

## 1. Vulnerability Reporting

If you discover a security vulnerability in Eye of Abyss, please report it responsibly:
- **Email**: security@eyeofabyss.local (or create a private GitHub Security Advisory)
- **Response SLA**: Initial triage within 24 hours; critical fix within 72 hours.
- Do not disclose vulnerabilities in public issue trackers until a patch is released.

---

## 2. Hardening Architecture & Defenses Implemented

| Area | Defense Implemented |
|---|---|
| **Secrets & Config** | Strict startup validation rejecting missing, default (`changeme`), or low-entropy secrets. Enforced minimum 16–32 char lengths. Zero hardcoded secrets in codebase. |
| **Authentication** | Password hashing via passlib/bcrypt. Refresh token rotation with JTI tracking and Redis/in-memory token revocation. Cookie flags `HttpOnly`, `SameSite=Strict`, `Secure`. |
| **Authorization** | Strict role hierarchy (`OWNER` > `SUPERVISOR` > `INVESTIGATOR` > `VIEWER`). Case visibility scoped to assigned/created cases for investigators. Only `OWNER` can provision privileged roles. Registration guarded by invite tokens in production. |
| **Network & Isolation** | Docker network segmentation with isolated, internal `db_tier`. Databases (PostgreSQL, Neo4j, Redis, MinIO) do not publish ports to the host. Redis authenticated with `--requirepass`. |
| **Reverse Proxy & TLS** | Production Nginx reverse proxy with TLSv1.2/1.3 termination, HTTP-to-HTTPS redirect, HSTS, CSP, and X-Frame-Options DENY headers. |
| **Abuse Protection** | Sliding-window Redis rate limiter across replicas. 50MB maximum request body size enforced at proxy and ASGI middleware layers. |
| **SSRF Defense** | Outbound webhook dispatcher validates URLs, blocks private, loopback, link-local, and reserved IP ranges, requires HTTPS, and enforces domain allowlisting. |
| **Storage & Uploads** | File extension blocklist, MIME type checks, magic-byte inspection (audio/PDF/images), S3 bucket encryption, public access blocking, and optional ClamAV scanning hook. |
| **Smart Contract** | `EvidenceRegistry.sol` protected by `onlyAuthorized` relayer role, `onlyOwner`, emergency `pause` circuit breaker, and indexed `EvidenceAnchored` event logging. |

---

## 3. Residual Risks & Operational Mitigations

While the platform has been hardened against common application and network attack vectors, operators should manage the following residual operational risks:

### A. Blockchain Private Key Management
- **Risk**: The relayer private key (`PRIVATE_KEY`) in environment variables could be exposed if the host server is compromised.
- **Operational Requirement**: In high-security environments, use a cloud KMS (AWS KMS, GCP Cloud KMS, HashiCorp Vault) or hardware security module (HSM) rather than storing raw private keys in `.env`. Maintain minimal MATIC/ETH balances on relayer wallets.

### B. Machine Learning Compute Exhaustion (DoS)
- **Risk**: Concurrent heavy deepfake audio analysis or GNN graph traversals can consume significant CPU/GPU resources.
- **Operational Requirement**: Microservices run with Docker resource limits (`cpus`, `memory`). For production scale, place Celery workers on dedicated GPU nodes with task queue concurrency caps (`worker_concurrency=4`).

### C. Persistent Storage Encryption at Rest
- **Risk**: Disk theft or unauthorized physical access could expose database volumes.
- **Operational Requirement**: Enable host-level full disk encryption (LUKS / dm-crypt on Linux, BitLocker on Windows) for the host filesystem hosting Docker volumes (`postgres_prod_data`, `neo4j_prod_data`, `minio_prod_data`).

### D. Reverse Proxy TLS Renewal
- **Risk**: Expired TLS certificates lead to service unavailability.
- **Operational Requirement**: Automate certificate renewal using Certbot or Let's Encrypt cron jobs that reload Nginx gracefully (`docker-compose exec nginx nginx -s reload`).

---

## 4. Operational Maintenance & Key Rotation

1. **JWT & Session Secret Rotation**:
   Rotate `JWT_SECRET` and `JWT_REFRESH_SECRET` periodically. Active user sessions will expire smoothly and require re-authentication.
2. **Database Passwords**:
   Rotate `POSTGRES_PASSWORD`, `NEO4J_PASSWORD`, and `REDIS_PASSWORD` during scheduled maintenance windows, updating both the database container and application environment variables simultaneously.
3. **Audit Log Retention**:
   Case state transitions and evidence submissions are logged in the `audit_logs` database table and optionally broadcast to webhooks. Back up database tables regularly using `scripts/backup.py`.
