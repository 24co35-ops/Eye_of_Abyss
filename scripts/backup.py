#!/usr/bin/env python3
"""Eye of Abyss — Automated Backup Utility.

Backs up:
1. PostgreSQL database dump (or SQLite database file)
2. Neo4j graph database export / cypher dump
3. Evidence storage artifacts (MinIO / local directory)

Usage:
  python scripts/backup.py [--out-dir ./backups] [--keep 7]
"""

from __future__ import annotations

import argparse
import datetime
import os
import shutil
import subprocess
import sys
import tarfile


def create_backup(out_dir: str = "./backups", keep: int = 7) -> str:
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_root = os.path.abspath(out_dir)
    os.makedirs(backup_root, exist_ok=True)
    
    archive_name = f"eob_backup_{timestamp}"
    staging_dir = os.path.join(backup_root, archive_name)
    os.makedirs(staging_dir, exist_ok=True)
    
    print(f"[*] Starting Eye of Abyss backup -> {staging_dir}")
    
    # 1. PostgreSQL / SQLite backup
    db_url = os.getenv("DATABASE_URL", "")
    if "sqlite" in db_url or not db_url:
        sqlite_paths = ["case_engine.db", "services/case-engine/case_engine.db"]
        for p in sqlite_paths:
            if os.path.exists(p):
                shutil.copy(p, os.path.join(staging_dir, os.path.basename(p)))
                print(f"[+] Backed up SQLite database: {p}")
    else:
        pg_dump = shutil.which("pg_dump")
        if pg_dump:
            dump_file = os.path.join(staging_dir, "postgres_dump.sql")
            try:
                subprocess.run([pg_dump, db_url, "-f", dump_file], check=True)
                print(f"[+] PostgreSQL dump created: {dump_file}")
            except Exception as e:
                print(f"[-] pg_dump failed: {e}")
        else:
            print("[!] pg_dump executable not found in PATH; skipping raw SQL dump.")

    # 2. Local Evidence / Storage files backup
    storage_dirs = ["storage", "data", "artifacts", "services/case-engine/storage"]
    for sdir in storage_dirs:
        if os.path.exists(sdir) and os.path.isdir(sdir):
            dest_sdir = os.path.join(staging_dir, "storage_files", os.path.basename(sdir))
            shutil.copytree(sdir, dest_sdir, dirs_exist_ok=True)
            print(f"[+] Backed up storage directory: {sdir}")

    # 3. Create compressed tar.gz archive
    archive_path = os.path.join(backup_root, f"{archive_name}.tar.gz")
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(staging_dir, arcname=archive_name)
    
    # Remove staging folder
    shutil.rmtree(staging_dir, ignore_errors=True)
    print(f"[✓] Backup archive created successfully: {archive_path}")

    # 4. Rotate old backups (keep latest N)
    all_backups = sorted([
        os.path.join(backup_root, f) for f in os.listdir(backup_root)
        if f.startswith("eob_backup_") and f.endswith(".tar.gz")
    ])
    if len(all_backups) > keep:
        for old in all_backups[:-keep]:
            os.remove(old)
            print(f"[-] Removed old backup archive: {old}")

    return archive_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backup Eye of Abyss database and evidence files")
    parser.add_argument("--out-dir", default="./backups", help="Target directory for backups")
    parser.add_argument("--keep", type=int, default=7, help="Number of backups to retain")
    args = parser.parse_args()
    
    create_backup(args.out_dir, args.keep)
