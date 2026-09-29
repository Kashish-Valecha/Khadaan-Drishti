#!/bin/sh
set -eu

# A fresh SIH demo deployment needs its curated, synthetic catalogue once.
# A mounted production database is deliberately left untouched on future starts.
if [ ! -f /app/backend/khadaan_drishti.db ]; then
  python scripts/seed.py
fi

exec "$@"
