# DevOps & Infrastructure Skill Pack

## Docker
- Multi-stage builds: builder stage → slim runtime image
- Non-root user in production containers
- `.dockerignore` mirrors `.gitignore` + `node_modules`, `.git`, `*.md`
- Pin base image versions: `node:20.11-alpine`, not `node:latest`
- Health checks: `HEALTHCHECK CMD curl -f http://localhost:3000/health`

## CI/CD
- Pipeline stages: lint → test → build → security-scan → deploy
- Fail fast: lint and unit tests run first (cheapest, fastest)
- Cache dependencies: npm ci with lockfile hash, pip cache, Go module cache
- Deploy: blue-green or canary. Never deploy on Friday
- Rollback: Automated if health check fails within 5 minutes

## Infrastructure as Code
- Terraform: Modules for reusable components. State in S3/GCS with locking
- No inline resources — extract to variables and modules
- `terraform plan` in PR, `terraform apply` only on merge to main
- Tag everything: `environment`, `team`, `cost-center`

## Kubernetes
- Resource limits on every pod: CPU/memory requests AND limits
- Liveness vs readiness probes: liveness restarts, readiness removes from service
- ConfigMaps for config, Secrets for credentials (sealed-secrets or external-secrets)
- Horizontal Pod Autoscaler on CPU/memory. Vertical for right-sizing
- Network policies: deny-all default, allow specific traffic

## Monitoring & Observability
- Three pillars: Metrics (Prometheus), Logs (Loki/ELK), Traces (Jaeger/Tempo)
- Dashboards answer operator questions: "Is it broken? Where? Since when? For whom?"
- Alerts on symptoms (error rate, latency), not causes (CPU usage alone)
- SLOs: Define error budget. Alert when burning too fast, not when exhausted
- Structured logging: JSON, request-id correlation, no PII in logs

## Cloud (AWS / GCP / Azure)
- Least privilege IAM: Specific resources, specific actions, conditions
- Encrypt at rest + in transit. KMS for key management
- VPC: Private subnets for databases, public only for load balancers
- Auto-scaling groups with health checks, not manually sized instances
- Cost: Reserved/committed use for steady state, spot/preemptible for batch
