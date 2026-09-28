#!/usr/bin/env bash
# Builds every sandbox image the game needs. Run once, and again whenever
# you pull an update that touches docker/*/Dockerfile.
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is not on PATH. Install Docker Desktop with WSL integration"
  echo "enabled for this distro, or Docker Engine directly inside WSL."
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "docker is installed but not reachable. Start Docker Desktop (or the"
  echo "docker daemon) and re-run this script."
  exit 1
fi

echo "Building sandbox images (first run pulls base images — a few minutes)."
echo

docker build -t breach-linux:latest  ./docker/linux
docker build -t breach-python:latest ./docker/python
docker build -t breach-pwsh:latest   ./docker/pwsh
docker build -t breach-dind:latest   ./docker/dind
docker build -t breach-aws:latest    ./docker/aws

# LocalStack itself is pulled lazily the first time an AWS-domain run starts,
# not built here — it's an upstream image, not one of ours.

echo
echo "All images built. Launch the game with:"
echo "  python3 -m breach"
