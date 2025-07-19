# FaithEcho TODO

## Milestone 0 — Project kick‑off
- [x] Agree on branching model (main & develop, feature branches, squash merge)
- [x] Define Conventional Commits policy and PR template
- [x] Enable Dependabot, branch protection rules & CODEOWNERS

## Milestone 1 — Repository & project structure
 - [x] Copy / verify skeleton directories (`/edge`, `/scripts`, `/ui`, etc.)
 - [x] Add `/docs` for diagrams & ADRs
 - [x] Add `.github/workflows` directory
 - [x] Add monorepo tooling: `pre‑commit`, `ruff`
 - [x] Create top‑level `Makefile` or `Taskfile.yml`
 - [x] Configure Poetry or pip‑tools lockfile under `/src/`
 - [x] Initialise internal Python package `faith_echo`

## Milestone 2 — Local development environment
- [x] Create `.devcontainer/` definition for VS Code Remote‑Containers
- [x] Implement skeleton `docker-compose.yml` so `docker compose up --build` starts the stack
- [x] Provide `scripts/dev‑proxy.sh` with mkcert TLS automation
- [x] Update `README.md` with setup / teardown instructions

## Milestone 2.5 — Language service scaffolding
- [ ] Create base classes for STT, translation and TTS
- [ ] Stub implementations using Google Cloud clients
- [ ] Unit tests covering service interfaces

## Milestone 3 — Core pipeline containers
### ingest_ffmpeg
- [ ] Write entrypoint script with retrying RTMP connection
- [ ] Output raw 16 kHz mono PCM to stdout
- [ ] Add unit test using `.wav` fixture and local ffmpeg
### pipeline_worker
- [ ] Scaffold FastAPI service with `/captions` WebSocket
- [ ] Implement async STT streaming client against Google Speech API
- [ ] Integrate Translate & TTS clients with exponential back‑off
- [ ] Add latency tracking & Prometheus metrics
- [ ] Emit per‑language AAC frames to FIFO pipes
### hls_packager
- [ ] Spawn ffmpeg with dual audio FIFO inputs
- [ ] Produce LL‑HLS outputs and implement sliding‑window cleanup
- [ ] Expose `/health` endpoint returning current segment age
### Dockerfiles & tests
- [ ] Write multi‑stage Dockerfiles (non‑root, slim images)
- [ ] Add contract tests with fake GCP API stubs

## Milestone 4 — Shared Python SDK
- [ ] Implement `config.py` using pydantic‑settings
- [ ] Create DTOs in `models.py`
- [ ] Build `gcp_client.py` with auth pooling and retries
- [ ] Publish package to GitHub Packages

## Milestone 5 — Admin interface
- [ ] Guard routes with HTTP Basic & bcrypt hash env var
- [ ] Build admin UI page with live metrics & controls using Streamlit
- [ ] Add credential rotation endpoint `/admin/rotate-gcp`
- [ ] Write Playwright E2E tests for admin flows

## Milestone 6 — Listener Interface
- [ ] Scaffold Streamlit app under `/ui`
- [ ] Implement captions overlay Web Component
- [ ] Add language selector & latency indicator widget
- [ ] Add reconnect/report button
- [ ] Register service worker and offline fallback page
- [ ] Achieve Lighthouse PWA score ≥ 90 mobile

## Milestone 7 — CI: GitHub Workflows
- [ ] Create `ci.yaml` for PR lint & tests
- [ ] Create `build‑push.yaml` for main branch image push to GHCR
- [ ] Create `deploy‑edge.yaml` for release deployment to edge device
- [ ] Create `pages‑docs.yaml` for MkDocs deployment to GitHub Pages
- [ ] Enable caching for pip & Docker layers

## Milestone 8 — Testing strategy
- [ ] Achieve 90% unit test coverage gate in CI
- [ ] Implement Pact contract tests for GCP integrations
- [ ] Integration tests with Docker‑compose & Playwright hitting UI & admin
- [ ] Load tests with Locust (< 50 ms pipeline overhead)

## Milestone 9 — Observability
- [ ] Add `/metrics` Prometheus endpoint to all services
- [ ] Deploy Prometheus & Grafana side‑cars in docker‑compose
- [ ] Commit Grafana dashboard JSON under `/docs`

## Milestone 10 — Security & Privacy hardening
- [ ] Enforce read‑only rootfs & drop Linux capabilities in Docker
- [ ] Provide optional HTTPS with self‑signed TLS certificate
- [ ] Add Trivy & GitHub secret scanning to CI pipeline

## Milestone 11 — Production deployment playbook
- [ ] Document edge pull & rolling restart commands
- [ ] Automate smoke test hitting `/ui/health.json`
- [ ] Add runbook to `/docs/ops/runbook.md`
