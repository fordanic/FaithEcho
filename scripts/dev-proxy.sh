#!/usr/bin/env bash
set -euo pipefail

CERT_DIR="$(dirname "$0")/../certs"
DOMAIN="faithecho.local"
mkdir -p "$CERT_DIR"

if ! command -v mkcert >/dev/null 2>&1; then
  echo "mkcert not installed. Please install it from https://github.com/FiloSottile/mkcert" >&2
  exit 1
fi

mkcert -install
mkcert -cert-file "$CERT_DIR/$DOMAIN.pem" -key-file "$CERT_DIR/$DOMAIN-key.pem" "$DOMAIN"

echo "Certificates written to $CERT_DIR"
