# AGENTS.md — FaithEcho

> **Scope**  This file provides *machine‑readable* guidance for autonomous coding agents such as **OpenAI Codex** that operate on the FaithEcho repository. All instructions apply to every file under this directory tree unless a more deeply‑nested `AGENTS.md` overrides them.

If a system/developer chat instruction ever conflicts with this file, assume the explicit prompt wins.

---

## Project Context

FaithEcho is a real‑time Swedish→English/French translation service for church sermons (see `README.md` and `SPECIFICATION.md`). The stack is a **Python 3.12 / FastAPI** audio‑processing pipeline packaged in Docker, plus a **TypeScript + Vite** mobile web‑app, orchestrated with **docker‑compose**. Mission‑critical goals are ≤ 3 s end‑to‑end latency, strong privacy (no recordings), and ease of on‑prem deployment.

### Key Architectural Directories

| Path                     | Purpose                                    |
| ------------------------ | ------------------------------------------ |
| `/edge/ingest_ffmpeg/`   | RTMP → PCM converter container             |
| `/edge/pipeline_worker/` | STT → MT → TTS Python pipeline & Admin API |
| `/edge/hls_packager/`    | Low‑Latency HLS segmenter                  |
| `/ui/`                   | Listener SPA (TypeScript)                  |
| `/scripts/`              | Dev & CI helper scripts                    |
| `/src/`                  | Shared Python library (`faith_echo`)       |
| `/docs/`                 | Diagrams, ADRs, runbooks                   |

---

## Development Environment

* Target Python: **3.12** with full **PEP 484** type hints.
* Package manager: **Poetry**.
* Containerisation: **Docker 24.x**; compose file is `docker-compose.yml`.
* Provide a one‑shot local stack with:

  ```bash
  docker compose up --build
  ```

Agents must *never* push images or attempt remote cloud actions; all builds run locally/offline.

---

## Coding Conventions

### Python

* **Formatting & Import Order**  `ruff format .`  *(black‑style formatter; honours Ruff‑isort rules)*
* **Lint/Style**  `ruff check --fix .`  *(includes isort‑style import sorting and auto‑fixes)*
* **Type‑check**  `mypy src/ tests/` (strict mode).
* **Docstrings**  Use Google style.
* **Concurrency**  Prefer `asyncio`, avoid blocking I/O in pipeline code.

### TypeScript / Frontend

* Format with `prettier --write .` and lint via `eslint .`.
* Use functional components and hooks; avoid external state managers (Redux, Zustand) unless required.
* Any DOM‑manipulating code must remain under `ui/` — never inside pipeline containers.

### Docker

* Multi‑stage builds, final stage must run as non‑root user `1000:1000`.
* Set `ENV PYTHONUNBUFFERED=1` and `CMD ["python", "-m", "pip", "check"]` in image test stages.

---

## Programmatic Checks (MUST PASS)

```
# Full quality gate
pre-commit run --all-files    # hooks: ruff, prettier, eslint
pytest -q                     # Python unit tests
mypy src/ tests/              # Static typing
ruff format --check           # Formatting & import order are correct
ruff check .                  # Linting passes
```

If any check fails, iterate until the pipeline is green **before** opening a PR.

---

## Commit & Pull‑Request Policy

* **Conventional Commits**: `type(scope): subject` — `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.
* PR title = first line of commit subject; body must contain:

  * `What / Why` – concise description.
  * `Testing` – commands run and their outcome.
  * `Screenshots` – for UI changes.
* Keep PRs ≤ 500 LOC where possible; break larger work into logical, reviewable chunks.

PRs that fail CI or exceed LOC limits without prior discussion will be marked **needs‑work**.

---

## Testing Philosophy

* **Unit tests** live next to source (`*_test.py` / `*.spec.ts`).
* **Contract tests** for GCP APIs use local stubs in `tests/gcp_stubs/` – *never* hit real endpoints in CI.
* **Latency tests** in `tests/perf/` assert that the pipeline stays under 3 s P95.
* Minimum coverage gate: **90 %** (Python) & **85 %** (TypeScript). Failing to meet the threshold blocks merge.

---

## Security & Secrets

* Never commit API keys or `.env` files — use Docker secrets.
* Use `python-dotenv` in dev only; production loads secrets via environment.
* For tests, set `GOOGLE_APPLICATION_CREDENTIALS` to `/tmp/fake_gcp.json`.
* All network egress but `*.googleapis.com` must be mocked in tests.

---

## Codex‑specific Guidance

1. **Reading order:** start with `SPECIFICATION.md`, then browse `README.md` and `TODO.md`.
2. **Task suggestions:**
   * `fix(pipeline): add exponential back‑off to Translate requests`
   * `feat(ui): dark‑mode toggle`
   * `test(ingest_ffmpeg): ensure RTMP reconnect logic`
3. **Safe commands:** `pytest`, `ruff`, `bash -c "..."`.
4. **Sandboxing:** assume write access only within repo root; never create sibling directories.
5. **Patch formatting:** include context lines and keep diff noise minimal (no unrelated whitespace churn).

---

### End of File
