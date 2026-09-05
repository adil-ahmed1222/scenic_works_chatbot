#!/usr/bin/env bash
set -euo pipefail

# Used when Render Root Directory is the repo root.
# Native Python services with rootDir=backend should use backend/render-build.sh instead.
cd backend
exec bash render-build.sh
