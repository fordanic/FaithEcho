# FaithEcho — Software Specification

## Overview

FaithEcho is a real‑time translation service that allows church attendees who do not understand Swedish to follow worship services in English or French. The system captures the Swedish audio feed, converts it to text, translates the transcript, synthesises speech, and streams the translated audio and live captions to listeners’ mobile browsers with an end‑to‑end latency of 1–3 seconds.

### Key Parameters

| Source  | Targets         | Concurrent Listeners | Latency Budget |
| ------- | --------------- | -------------------- | -------------- |
| Swedish | English, French | \~15 smartphones     | 1–3 s          |

---

## Functional Requirements

### Audio Capture

* Capture a mono 16 kHz RTMP stream from the sound desk.
* Automatically reconnect if the RTMP source drops.

### Processing Pipeline

* Perform Swedish speech‑to‑text (STT) using **Google Cloud Speech‑to‑Text**.
* Translate transcripts to English and French with **Google Cloud Translate**.
* Synthesize English and French speech using **Google Cloud Text‑to‑Speech**.
* Maintain ≤ 3 s pipeline latency (95th percentile).

### Audio Delivery

* Produce two continuous Low‑Latency HLS (LL‑HLS) streams (English and French) with 1‑second segments.
* Serve playlists and segments over HTTP(S) from the on‑prem edge server.
* Allow listeners to switch languages seamlessly without restarting the pipeline.

### Listener Web App

* No sign‑in; discoverable at `http://faithecho.local`.
* Provide live captions, language selector, text‑size control, volume/mute, latency indicator, and reconnect/report button.
* Mobile‑first responsive design that works on the latest Chrome, Safari, and Edge browsers.
* Display a warning if latency exceeds 3 seconds.
* Implemented using **Streamlit**.

### Admin Interface

* Password‑protected admin page (`/admin`) secured by a single shared password.
* Implemented using **Streamlit** served by FastAPI.
* Switch operating mode: **Always‑On**, **Manual**, or **Scheduled**.
* Manual **Start** and **Stop** controls.
* Live dashboard showing input‑level meter, end‑to‑end latency, and client counts per language.
* View recent error and event logs (last 24 hours).
* Rotate Google Cloud API credentials.
* *Nice‑to‑have:* Edit the weekly schedule of services.

---

## Non‑Functional Requirements

| Category             | Requirement                                                    |
| -------------------- | -------------------------------------------------------------- |
| Performance          | ≤ 3 s end‑to‑end; 1 s LL‑HLS segment size.                     |
| Scalability          | Support 15 concurrent clients with < 50 ms additional latency. |
| Availability         | ≥ 99 % during scheduled service hours.                         |
| Privacy              | **No recording or storage** of audio or transcripts.           |
| Maintainability      | Docker‑based deployment with CI/CD to the edge server.         |
| Internationalisation | Ready to add more target languages in future.                  |

---

## System Architecture

```text
               +-------------------- Google Cloud APIs --------------------+
               | Speech‑to‑Text | Translate | Text‑to‑Speech (managed)     |
               +-----------------↑-----------↑--------------↑--------------+
                                 |           |              |
                             gRPC/HTTPS  REST/HTTPS     REST/HTTPS
                                 |           |              |
+-------------- Church LAN --------------+   |       +---------------------------+
|                                        |   |       | Listeners (mobile)       |
|  RTMP Source → Edge Server (Docker)    |   |       | • English LL‑HLS         |
|                                        |   |       | • French  LL‑HLS         |
|  • ffmpeg (RTMP → PCM)                 |   +-------►• Captions WebSocket       |
|  • Python pipeline (STT→MT→TTS via APIs)|           +---------------------------+
|  • LL‑HLS packager (ffmpeg)            | 
|  • FastAPI: /ui /captions /admin       |
|  • Nginx: serve HLS + UI               |
+----------------------------------------+
```

---

## Component Design

### Edge Server

* **OS:** Ubuntu 24.04 LTS
* **Runtime:** Docker 24.0 (`docker‑compose.yml`)

  * `ingest_ffmpeg` – Converts RTMP to raw PCM (16‑bit mono, 16 kHz) and pipes it to the pipeline container.
  * `pipeline_worker` – Python 3.21, FastAPI, websockets.

    * **Streaming STT** via Google Cloud Speech API (bidirectional gRPC).
    * **Translate** transcripts with Google Cloud Translate REST calls.
    * **TTS** synthesis requests to Google Cloud Text‑to‑Speech REST (returns base64 AAC).
    * Re‑packs TTS frames into per‑language FIFO pipes.
  * `hls_packager` – ffmpeg packaging the two AAC FIFO inputs into LL‑HLS (1 s segments).
  * `ui_server` – Streamlit app serving the listener interface, `/hls` playlists, and segments.
  * `admin_api` – Part of `pipeline_worker`; exposes `/admin` with basic auth.
* **Resources:** 4 vCPU / 8 GB RAM minimum.

### Google Cloud Integration

* Dedicated Google Cloud project with service‑account credentials (JSON key) mounted as a Docker secret.
* All API calls originate from the edge server; no custom Cloud Run containers are required.
* Quotas: allow ≥ 2 concurrent streaming STT requests and sufficient TTS synth characters per hour.

### Data‑Flow Timing

| Step                                 | Target (ms)  |
| ------------------------------------ | ------------ |
| Audio chunk & upload to STT          | 250          |
| Google Streaming STT partial result  | 400          |
| Translate call                       | 100          |
| TTS synthesis call                   | 600          |
| Edge re‑mux & HLS segment generation | 400          |
| **Total**                            | **≈ 1.75 s** |

---

## Security

* **Edge inbound:** HTTP on port 80 inside LAN; optional HTTPS with a self‑signed certificate.
* **Edge outbound:** HTTPS 443 to `*.googleapis.com`.
* **Admin authentication:** single bcrypt‑hashed password stored in `.env`.
* **API keys:** stored as Docker secrets; rotation via the admin UI.
* **No persistent data** beyond ephemeral logs (< 24 hours).

---

## Deployment & Operations

| Task                            | Tool / Process                                          |
| ------------------------------- | ------------------------------------------------------- |
| Build & push images             | GitHub Actions                                          |
| Deploy to edge server           | `docker compose pull && docker compose up -d` via SSH   |
| Provision Google project & APIs | Terraform or `gcloud` CLI scripts                       |
| Monitoring                      | Prometheus node exporter + Google Cloud Monitoring      |
| Alerting                        | Email if streaming STT drops > 30 s or HLS stalls > 5 s |

---

## Assumptions & Constraints

1. RTMP source provides clean speech (≥ 16 dB SNR).
2. Church LAN provides ≥ 20 Mbps upstream.
3. Listeners use modern browsers (ES2019+).
4. Google Cloud quotas are sufficient (≈ 0.15 USD per listener‑hour at 64 kb s⁻¹ × 2).

---

## Future Enhancements

* Custom STT phrase lists and MT glossaries (biblical terms).
* Additional target languages (e.g., Arabic, Spanish).
* Dark‑mode UI and full accessibility audit.
* Offline/on‑edge STT for unstable internet situations.
* Recording and on‑demand replay (subject to privacy approval).

---

