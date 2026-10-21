#!/usr/bin/env bash
# Scrape harian domain GIS di laptop, lalu commit+push hasilnya ke fork.
# Dipakai karena GitHub Actions di fork dinonaktifkan GitHub dan HiringCafe 403 dari IP ini.
# crontab: 10 6 * * *   → output/scrape.log
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
PY=.venv/bin/python

{
  echo "=== $(date -u '+%F %T UTC') start"
  for src in --indeed-only; do
    "$PY" scrape_jobs.py "$src"
    echo "  $src rc=$?"
  done

  git add -f output/*.json output/*.md output/*.html
  if git diff --cached --quiet; then
    echo "tidak ada perubahan data"
  else
    git commit -q -m "chore: scrape lokal GIS [$(date -u '+%Y-%m-%d %H:%MZ')]"
    { git -c rebase.autoStash=true pull --rebase -X ours origin main && git push; } \
      || echo "push gagal (data lokal tetap terbaru)"
  fi

  "$PY" -c 'import json;d=json.load(open("output/all_jobs.json"));print("all_jobs:",d["updated_at"],len(d["jobs"]),"jobs")'
  echo "=== done"
} >> output/scrape.log 2>&1
