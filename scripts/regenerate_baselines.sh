#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Rigenera tutti i file baseline per i test di snapshot.
#
# Uso:
#   ./scripts/regenerate_baselines.sh
#
# I file vengono scritti in tests/baselines/*.json.
# Dopo la rigenerazione, verificare le differenze con:
#   git diff tests/baselines/
# ---------------------------------------------------------------------------
set -euo pipefail

cd "$(dirname "$0")/.."

echo "=== Rigenerazione baselines ==="
echo ""

uv run pytest tests/test_baselines.py --update-baselines -v

echo ""
echo "Baselines rigenerati in tests/baselines/"
echo "Verifica le modifiche con: git diff tests/baselines/"
