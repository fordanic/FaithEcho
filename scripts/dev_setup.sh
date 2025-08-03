#!/usr/bin/env bash
# dev_setup.sh — Bootstrap local dev env using the same steps as GitHub CI
set -euo pipefail
IFS=$'\n\t'

REQUIRED_PYTHON="3.12"

info() { echo -e "\033[1;34m[info]\033[0m $*"; }
warn() { echo -e "\033[1;33m[warn]\033[0m $*"; }
err()  { echo -e "\033[1;31m[error]\033[0m $*" >&2; }

# ────────────────────────── 1. Ensure Python 3.12 ──────────────────────────
if ! command -v python3 >/dev/null 2>&1; then
  err "python3 not found. Install Python ${REQUIRED_PYTHON} first."
  exit 1
fi

PY_VER=$(python3 - <<'PY'
import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")
PY
)

if [[ "$PY_VER" != "$REQUIRED_PYTHON" ]]; then
  err "Python ${REQUIRED_PYTHON} is required (found ${PY_VER})."
  exit 1
fi
info "Python ${PY_VER} detected."

# ────────────────────────── 2. System deps (PortAudio) ─────────────────────
install_portaudio() {
  if [[ "$(uname)" == "Linux" ]]; then
    if command -v apt-get >/dev/null 2>&1; then
      info "Installing PortAudio dev libs via apt…"
      sudo apt-get update -qq
      sudo apt-get install -y -qq portaudio19-dev
    else
      warn "Non‑Debian Linux detected — please ensure PortAudio dev headers are installed."
    fi
  elif [[ "$(uname)" == "Darwin" ]]; then
    if command -v brew >/dev/null 2>&1; then
      info "Ensuring PortAudio via Homebrew…"
      brew list portaudio >/dev/null 2>&1 || brew install portaudio
    else
      warn "Homebrew not found; skipping PortAudio install."
    fi
  else
    warn "Unknown OS; please install PortAudio dev libraries manually."
  fi
}
install_portaudio

# ────────────────────────── 3. Poetry + plugin ─────────────────────────────
if ! command -v poetry >/dev/null 2>&1; then
  info "Installing Poetry + poetry‑plugin‑export…"
  python3 -m pip install --upgrade --quiet pip
  python3 -m pip install --quiet "poetry>=1.8" poetry-plugin-export
else
  if ! poetry self show plugins | grep -q "poetry-plugin-export"; then
    info "Adding poetry‑plugin‑export…"
    poetry self add poetry-plugin-export
  fi
fi

# ────────────────────────── 4. Install dependencies ────────────────────────
info "Installing project dependencies (prod + dev)…"
poetry install --with dev --no-interaction --no-root
if [[ $? -ne 0 ]]; then
  err "Failed to install dependencies. Check your Poetry setup."
  exit 1
fi

info "✓ Development environment is ready."
