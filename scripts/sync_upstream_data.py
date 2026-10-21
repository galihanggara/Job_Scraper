#!/usr/bin/env python3
"""Sinkron data listing terbaru dari upstream (ScottCoffin/Job_Scraper) ke laptop.

Kenapa: GitHub Actions di fork galihanggara/Job_Scraper dinonaktifkan GitHub
("Actions has been disabled for this repository", workflow state disabled_fork;
API tidak bisa mengaktifkan ulang), sedangkan scrape dari IP laptop kena 403
(HiringCafe). Actions upstream tetap jalan tiap hari, jadi data upstream yang
dipakai — digabung pakai _merge_into_all_jobs milik repo ini (dedupe + prune 50 hari).

Dijalankan cron: 30 4 * * *  →  output/sync.log
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def git(*args, check=False):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.exit(f"git {' '.join(args)} gagal: {r.stderr.strip()}")
    return r


def main():
    git("fetch", "--quiet", "upstream", "main")

    paths = [p for p in git("ls-tree", "--name-only", "upstream/main", "output/").stdout.split()
             if p.endswith("_jobs.json")]
    jobs, used = [], 0
    for path in paths:
        try:
            data = json.loads(git("show", f"upstream/main:{path}").stdout)
        except json.JSONDecodeError:
            continue
        batch = data.get("jobs", []) if isinstance(data, dict) else data
        if batch:
            jobs.extend(batch)
            used += 1
    if not jobs:
        sys.exit("tidak ada job di upstream — data lokal tidak diubah")

    sys.path.insert(0, ROOT)
    from scrape_jobs import _merge_into_all_jobs  # noqa: E402

    print(f"upstream: {used}/{len(paths)} sumber, {len(jobs)} job")
    _merge_into_all_jobs(jobs)

    if not git("add", "-f", "output/all_jobs.json").returncode:
        if git("diff", "--cached", "--quiet").returncode != 0:
            git("commit", "-q", "-m", f"chore: sync data upstream")
            r = git("-c", "rebase.autoStash=true", "pull", "--rebase", "-X", "ours", "origin", "main")
            if r.returncode or git("push", "origin", "main").returncode:
                print("push gagal (data lokal tetap terbaru)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
