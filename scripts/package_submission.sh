#!/usr/bin/env bash
# ==============================================================================
# StackSense Challenge · Synergy '26 Packaging Script
# Conforms strictly to Section 9.2 & 9.3 of the official problem statement.
#
# Generates:
# dist/StackSense26_<FullName>/
# ├── source/
# │   ├── README.md
# │   ├── .env.example
# │   ├── Dockerfile
# │   ├── docker-compose.yml
# │   ├── pyproject.toml
# │   ├── src/
# │   ├── data/
# │   ├── tests/
# │   └── docs/
# ├── outputs/
# │   ├── P1_output.json ... P6_output.json
# └── Report_<FullName>.pdf
# ==============================================================================

set -euo pipefail

FULL_NAME="${1:-Aman_Kumar}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist"
TARGET_DIR="${DIST_DIR}/StackSense26_${FULL_NAME}"

echo "=== Packaging StackSense Submission for: ${FULL_NAME} ==="

# 1. Clean and initialize target directory
rm -rf "${TARGET_DIR}"
mkdir -p "${TARGET_DIR}/source" "${TARGET_DIR}/outputs"

# 2. Build / copy official Report PDF
if [[ -f "${ROOT_DIR}/Report_${FULL_NAME}.pdf" ]]; then
    echo "-> Copying Report_${FULL_NAME}.pdf..."
    cp "${ROOT_DIR}/Report_${FULL_NAME}.pdf" "${TARGET_DIR}/Report_${FULL_NAME}.pdf"
elif [[ -f "${ROOT_DIR}/Report_Aman_Kumar.pdf" ]]; then
    echo "-> Copying Report_Aman_Kumar.pdf to Report_${FULL_NAME}.pdf..."
    cp "${ROOT_DIR}/Report_Aman_Kumar.pdf" "${TARGET_DIR}/Report_${FULL_NAME}.pdf"
else
    echo "-> Generating Report_${FULL_NAME}.pdf via pandoc..."
    pandoc "${ROOT_DIR}/docs/project-report.md" \
        -o "${TARGET_DIR}/Report_${FULL_NAME}.pdf" \
        --css="${ROOT_DIR}/docs/report-style.css" \
        --pdf-engine=weasyprint
fi

# 3. Copy public outputs (P1_output.json through P6_output.json)
echo "-> Copying public scenario outputs..."
cp "${ROOT_DIR}/outputs"/P*_output.json "${TARGET_DIR}/outputs/"

# 4. Copy clean source tree (excluding caches, venvs, and git)
echo "-> Copying source code..."
rsync -av --exclude '__pycache__' \
          --exclude '*.pyc' \
          --exclude '.venv' \
          --exclude 'venv' \
          --exclude '.git' \
          --exclude '.pytest_cache' \
          --exclude '.DS_Store' \
          --exclude 'dist' \
          --exclude '*.egg-info' \
          --exclude 'Report_*.pdf' \
          "${ROOT_DIR}/" "${TARGET_DIR}/source/"

echo ""
echo "=== Package Structure Created at ${TARGET_DIR} ==="
ls -la "${TARGET_DIR}"
echo ""
ls -la "${TARGET_DIR}/outputs"
echo ""
echo "Total folder size: $(du -sh "${TARGET_DIR}" | cut -f1)"
echo "Ready for Google Drive upload per Section 9.2!"
