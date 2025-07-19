# FaithEcho

FaithEcho is a real‑time, low‑latency translation service that lets non‑Swedish speakers follow church services in English or French on their smartphones. It listens to the Swedish audio feed, converts speech to text, translates it, synthesises the target speech and captions, and streams them with a 1–3 second end‑to‑end delay.

## Key Capabilities

* Live Swedish → English/French translation (audio + captions) with ≈ 3 s latency.
* Supports \~15 concurrent mobile listeners on the church Wi‑Fi.
* Seamless language switching without restarting the stream.
* No user accounts; just open **[http://faithecho.local](http://faithecho.local)** in a modern mobile browser.
* Privacy‑first: nothing is recorded or stored.

## System at a Glance

```text
RTMP audio → Edge Server (Docker) → Google Cloud APIs → LL‑HLS + WebSocket → Listeners
```

For a full architecture diagram and timing breakdown see **SPECIFICATION.md**.

## Tech Stack

* **Python 3.21** + **FastAPI** pipeline
* **ffmpeg** for ingest & LL‑HLS packaging
* **Google Cloud Speech‑to‑Text**, **Translate**, **Text‑to‑Speech**
* **Docker 24** / **docker‑compose**
* **Nginx** static server & reverse proxy
* SPA frontend written in vanilla TypeScript + Vite

## Repository Layout

```
/docker-compose.yml     – multi‑container orchestration
/admin/                 – admin UI (served by FastAPI)
/edge/ingest_ffmpeg/    – RTMP → PCM converter
/edge/pipeline_worker/  – STT → MT → TTS pipeline
/edge/hls_packager/     – AAC → LL‑HLS packager
/scripts/               – utility scripts (deployment, cleanup, etc.)
/src/                   – shared source code
/ui/                    – listener web‑app (dist served by Nginx)
```

## Quick Start (Development)

> Tested on **Ubuntu 24.04** with Docker 24.x.

1. Clone and enter the repo:

   ```bash
   git clone https://github.com/fordanic/FaithEcho.git
   cd FaithEcho
   ```

2. Copy the example environment file and fill in your details:

   ```bash
   cp .env.example .env
   # Edit .env with GCP project id, service‑account json path, admin password, etc.
   ```

3. Ensure your Google Cloud project has the **Speech‑to‑Text**, **Translate** and **Text‑to‑Speech** APIs enabled and that
   the service account key referenced in `.env` has the necessary IAM roles.

4. Start the stack:

   ```bash
   docker compose up --build
   ```

5. Point the church sound desk’s RTMP output at `rtmp://<edge>:1935/live/source` (default).
   Open **[http://faithecho.local](http://faithecho.local)** on a phone to listen.

Logs are streamed to the console; stop with Ctrl‑C.

## Production Deployment

The edge server runs headless in the church LAN:

```bash
ssh church-edge 'docker compose pull && docker compose up -d'
```

We recommend provisioning the Google Cloud project via Terraform and wiring the CI/CD workflow in `.github/workflows/` to push new images automatically.

## Configuration Reference

| Variable               | Purpose                                    |
| ---------------------- | ------------------------------------------ |
| `GCP_CREDENTIALS_JSON` | Path to mounted service‑account key file   |
| `ADMIN_PASSWORD_HASH`  | bcrypt hash for `/admin` basic auth        |
| `RTMP_SOURCE_URL`      | Input URL for ffmpeg ingest                |
| `HLS_SEGMENT_SECONDS`  | Target LL‑HLS segment length (default 1 s) |
| `TARGET_LANGS`         | Space‑delimited language codes (`en fr`)   |

See `.env.example` for the full list.

## Admin Interface

Navigate to **/admin** (HTTP basic auth) to:

* Start/stop the pipeline or switch **Always‑On / Manual / Scheduled** mode.
* Watch live input levels, latency, and current listener counts.
* View last‑24‑hour logs and rotate GCP API credentials.

## Listener Web‑App

* **Language selector**: English ↔︎ Français in real time
* Live **captions** with adjustable font size
* Latency indicator turns red if > 3 s
* Works on Chrome, Safari, and Edge (mobile & desktop)

## Privacy & Security Principles

* **No recordings** – all audio and transcripts are transient in‑memory data.
* Edge server only exposes HTTP inside LAN; optional HTTPS with a self‑signed certificate.
* Single shared admin password (bcrypt‑hashed) and GCP keys stored as Docker secrets.

## Roadmap

* Custom STT phrase sets for biblical vocabulary
* Additional target languages (Arabic, Spanish, Swahili, …)
* Dark‑mode and accessibility audit
* Optional on‑edge STT for poor internet

## Contributing

We 💜 contributions! Fork the repo, create a feature branch, open a pull request and follow the code‑style guidelines in `CONTRIBUTING.md`.

## License

Distributed under the BSD 2‑Clause License. See `LICENSE` for more information.

## Acknowledgements

* ...
