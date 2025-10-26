#!/bin/bash
# Markdown Documentation Cleanup Script
# Reorganizes and removes outdated documentation files

set -e

echo "🧹 Coffee Roasting Project - Documentation Cleanup"
echo "=================================================="
echo ""

# Create archive directory if it doesn't exist
mkdir -p docs/archive/phase2-mcp-development
mkdir -p docs/archive/session-notes

echo "📦 Moving outdated files to archive..."

# Move Phase 2 completion docs to archive
mv DEMO_MODE.md docs/archive/phase2-mcp-development/ 2>/dev/null || true
mv DEMO_MODE_STATUS.md docs/archive/phase2-mcp-development/ 2>/dev/null || true
mv docs/PHASE2_COMPLETE.md docs/archive/phase2-mcp-development/ 2>/dev/null || true
mv docs/DEMO_MODE_IMPLEMENTATION.md docs/archive/phase2-mcp-development/ 2>/dev/null || true

# Move session/status tracking to archive
mv PROGRESS.md docs/archive/session-notes/ 2>/dev/null || true
mv PROJECT_STATUS.md docs/archive/session-notes/ 2>/dev/null || true
mv SESSION_RESUME.md docs/archive/session-notes/ 2>/dev/null || true

# Move outdated test docs to archive
mv QUICK_TEST.md docs/archive/phase2-mcp-development/ 2>/dev/null || true
mv READY_TO_TEST.md docs/archive/phase2-mcp-development/ 2>/dev/null || true
mv docs/MANUAL_TESTING.md docs/archive/phase2-mcp-development/ 2>/dev/null || true

echo "✅ Files archived"
echo ""

echo "🗑️  Removing redundant backup files..."
rm -f data/backups/20251019_baseline/processed/processing_summary.md
rm -f data/backups/20251019_baseline/splits/split_report.md
echo "✅ Backups cleaned"
echo ""

echo "📝 Creating archive README..."
cat > docs/archive/phase2-mcp-development/README.md << 'EOF'
# Phase 2 MCP Development - Archived Documentation

This directory contains historical documentation from Phase 2 (MCP Server Development), 
completed on October 26, 2025.

## Contents

- **DEMO_MODE*.md** - Demo mode implementation (later removed for production)
- **PHASE2_COMPLETE.md** - Phase 2 completion summary
- **QUICK_TEST.md** / **READY_TO_TEST.md** - Initial testing guides
- **MANUAL_TESTING.md** - Manual testing procedures

## Status

Phase 2 successfully delivered:
- First Crack Detection MCP Server (HTTP+SSE)
- Roaster Control MCP Server (HTTP+SSE)
- Auth0 JWT authentication
- 23/23 tests passing

See main project README for current status.
EOF

cat > docs/archive/session-notes/README.md << 'EOF'
# Session Notes - Archived

Historical session tracking and progress notes from October 2025.

These files tracked day-to-day progress during Phase 2-3 development
and are preserved for historical reference.

See main project README and Phase 3 documentation for current status.
EOF

echo "✅ Archive READMEs created"
echo ""

echo "✨ Cleanup complete!"
echo ""
echo "Summary:"
echo "  - Archived: Phase 2 completion docs → docs/archive/phase2-mcp-development/"
echo "  - Archived: Session notes → docs/archive/session-notes/"
echo "  - Deleted: Backup data summaries"
echo "  - Created: Archive README files"
echo ""
echo "Next: Review and update main README.md"
