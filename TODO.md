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

## Milestone 3 — Language service scaffolding

**Goal:** Provide three independent, containerised micro‑services – **STT**, **Translate**, **TTS** – that expose streaming APIs so they can be composed into the real‑time pipeline or run stand‑alone for testing.

- [ ] Define gRPC / protobuf schema (`AudioChunk`, `TextChunk`, `SpeechChunk`, `LangRequest`, `LangResponse`)
- [ ] Scaffold three FastAPI/gRPC services under `/services/{stt,translate,tts}`
- [ ] **STTService**

  * Accept 16 kHz mono PCM stream (WebSocket or gRPC bidi stream)
  * Forward to Google Cloud Speech‑to‑Text streaming API
  * Return partial & final `TextChunk` messages with timestamps
- [ ] **TranslationService**

  * Accept `TextChunk` stream and target language codes
  * Call Google Cloud Translate; support custom glossary
  * Stream back translated `TextChunk`
- [ ] **TTSService**

  * Accept `TextChunk` stream plus voice parameters
  * Call Google Cloud Text‑to‑Speech; stream back encoded `SpeechChunk` (AAC 64 kb s⁻¹)
- [ ] Provide health, metrics and readiness endpoints for each service
- [ ] Provide individual Dockerfiles and docker‑compose override for running the trio locally
- [ ] Add typed async Python clients in `faith_echo.sdk`
- [ ] Unit tests (pytest + pytest‑asyncio) and contract tests (Pact) for service interfaces (≥ 90 % coverage)
- [ ] CI job `language‑services.yaml` building & testing images

## Milestone 4 — Core pipeline containers

### `ingest_ffmpeg`

- [ ] Write entrypoint script with retrying RTMP connection
- [ ] Output raw 16 kHz mono PCM to stdout
- [ ] Add unit test using `.wav` fixture and local ffmpeg

### `pipeline_orchestrator`

- [ ] Scaffold FastAPI service with `/captions` WebSocket and `/metrics`
- [ ] Consume audio from `ingest_ffmpeg` and fan‑out to STT microservice client
- [ ] Chain STT ➔ Translate ➔ TTS via async streams
- [ ] Maintain rolling latency measurements & Prometheus metrics
- [ ] Gracefully degrade to direct GCP calls if any microservice unavailable
- [ ] Emit per‑language AAC frames to FIFO pipes

### `hls_packager`

- [ ] Spawn ffmpeg with dual audio FIFO inputs
- [ ] Produce LL‑HLS outputs and implement sliding‑window cleanup
- [ ] Expose `/health` endpoint returning current segment age

### Dockerfiles & tests

- [ ] Build non‑root, slim images for each container
- [ ] Add contract tests with fake microservices & GCP stubs

## Milestone 5 — Shared Python SDK

- [ ] Implement `faith_echo.config` using pydantic‑settings
- [ ] Define protobuf messages and pydantic DTO mirroring (`chunk_pb2`, `models.py`)
- [ ] Implement async clients for STT, Translate, TTS microservices
- [ ] Implement `gcp_client.py` with auth pooling and retries
- [ ] Publish package to GitHub Packages; version with SemVer

## Milestone 6 — Admin interface

- [ ] Guard routes with HTTP Basic & bcrypt hash env var
- [ ] Build Streamlit dashboard with live metrics & controls
- [ ] Expose manual **Start/Stop**, mode selector (**Always‑On / Manual / Scheduled**)
- [ ] Add credential rotation endpoint `/admin/rotate-gcp`
- [ ] Implement schedule editor UI (nice‑to‑have)
- [ ] Write Playwright E2E tests for admin flows

## Milestone 7 — Listener Interface

- [ ] Scaffold Streamlit app under `/ui`
- [ ] Implement captions overlay Web Component
- [ ] Add language selector & latency indicator widget
- [ ] Add volume/mute and font‑size controls; dark‑mode toggle
- [ ] Add reconnect/report button
- [ ] Register service worker and offline fallback page
- [ ] Achieve Lighthouse PWA score ≥ 90 mobile

## Milestone 8 — CI: GitHub Workflows

- [ ] `ci.yaml` – lint, unit, contract tests (pull request)
- [ ] `build‑push.yaml` – build images for main & tag, push to GHCR
- [ ] `deploy‑edge.yaml` – gated release deployment to edge device
- [ ] `pages‑docs.yaml` – MkDocs to GitHub Pages
- [ ] Enable caching for poetry & Docker layers
- [ ] Add `language‑services.yaml` for microservice builds

## Milestone 9 — Testing strategy

- [ ] ≥ 90 % unit test coverage gate in CI
- [ ] Contract tests for microservice gRPC interfaces
- [ ] Integration tests with docker‑compose hitting UI & admin
- [ ] Load tests with Locust (< 50 ms pipeline overhead)
- [ ] Chaos tests: simulate STT/Translate/TTS service outages

## Milestone 10 — Observability

- [ ] `/metrics` Prometheus endpoints in all containers incl. microservices
- [ ] Add Prometheus & Grafana side‑cars in docker‑compose
- [ ] Grafana dashboards: latency, segment age, client count
- [ ] Push logs to Loki; Tempo tracing for gRPC calls

## Milestone 11 — Security & Privacy hardening

- [ ] Enforce read‑only rootfs & drop Linux capabilities
- [ ] Optional HTTPS with self‑signed TLS certificate
- [ ] Trivy & GitHub secret scanning in CI
- [ ] Validate input payloads & size limits (defence‑in‑depth)
- [ ] Confirm no audio or transcripts written to disk

## Milestone 12 — Production deployment playbook

- [ ] Document edge pull & rolling restart commands
- [ ] Automate smoke test hitting `/ui/health.json`
- [ ] Add runbook `/docs/ops/runbook.md`
- [ ] Document emergency rollback & credential rotation procedure
