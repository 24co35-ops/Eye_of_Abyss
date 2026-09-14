#!/bin/bash
# Eye of Abyss — Linux Automated Backup Script
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
KEEP_COUNT="${KEEP_COUNT:-7}"
TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S")
STAGING_DIR="${BACKUP_DIR}/eob_backup_${TIMESTAMP}"

mkdir -p "${STAGING_DIR}"
echo "[*] Starting Eye of Abyss Backup at ${TIMESTAMP}"

# 1. PostgreSQL dump
if command -v pg_dump &> /dev/null && [ -n "${DATABASE_URL:-}" ]; then
  echo "[+] Dumping PostgreSQL database..."
  pg_dump "${DATABASE_URL}" > "${STAGING_DIR}/postgres_dump.sql" || true
fi

# 2. SQLite dump if present
for db_file in case_engine.db services/case-engine/case_engine.db; do
  if [ -f "${db_file}" ]; then
    echo "[+] Copying SQLite database ${db_file}..."
    cp "${db_file}" "${STAGING_DIR}/"
  fi
done

# 3. Evidence artifact files
for dir in storage data artifacts services/case-engine/storage; do
  if [ -d "${dir}" ]; then
    echo "[+] Copying storage directory ${dir}..."
    mkdir -p "${STAGING_DIR}/storage_files"
    cp -r "${dir}" "${STAGING_DIR}/storage_files/"
  fi
done

# 4. Tar and gzip
ARCHIVE="${BACKUP_DIR}/eob_backup_${TIMESTAMP}.tar.gz"
tar -czf "${ARCHIVE}" -C "${BACKUP_DIR}" "eob_backup_${TIMESTAMP}"
rm -rf "${STAGING_DIR}"
echo "[✓] Backup created: ${ARCHIVE}"

# 5. Rotate old backups
ls -1t "${BACKUP_DIR}"/eob_backup_*.tar.gz 2>/dev/null | tail -n +$((KEEP_COUNT + 1)) | xargs -r rm -f
echo "[✓] Backup rotation complete (keeping latest ${KEEP_COUNT})."
