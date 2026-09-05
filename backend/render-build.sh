#!/usr/bin/env bash
set -euo pipefail

python -m pip install --upgrade pip
python -m pip install --index-url https://download.pytorch.org/whl/cpu torch
python -m pip install -r requirements.txt
python -c "from sentence_transformers import SentenceTransformer; print('sentence_transformers import OK')"
