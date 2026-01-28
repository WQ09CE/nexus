#!/bin/bash
#
# Nexus Local CI Check - Run before creating PR
#
# This script mirrors the GitHub Actions CI workflow to catch issues
# before pushing. Prevents the "local passes, CI fails" problem.
#
# Usage:
#   ./scripts/ci-check.sh          # Run all checks
#   ./scripts/ci-check.sh --quick  # Skip slow tests
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

QUICK_MODE=false
if [ "$1" = "--quick" ]; then
    QUICK_MODE=true
fi

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo ""
echo -e "${BLUE}=================================================================${NC}"
echo -e "${BLUE}  Nexus Local CI Check${NC}"
echo -e "${BLUE}=================================================================${NC}"
echo ""

# Track failures
FAILED=0

# Step 1: Shell Lint
echo -e "${YELLOW}[1/4] Shell Lint (shellcheck)${NC}"
if command -v shellcheck &> /dev/null; then
    if [ -f "install.sh" ]; then
        if shellcheck install.sh; then
            echo -e "  ${GREEN}[PASS]${NC} install.sh"
        else
            echo -e "  ${RED}[FAIL]${NC} install.sh"
            FAILED=1
        fi
    else
        echo -e "  ${YELLOW}[SKIP]${NC} install.sh not found"
    fi
else
    echo -e "  ${YELLOW}[SKIP]${NC} shellcheck not installed"
    echo "         Install with: brew install shellcheck (macOS) or apt install shellcheck (Linux)"
fi
echo ""

# Step 2: Python Syntax Check
echo -e "${YELLOW}[2/4] Python Syntax Check${NC}"
SYNTAX_ERRORS=0
while IFS= read -r -d '' py_file; do
    if ! python3 -m py_compile "$py_file" 2>/dev/null; then
        echo -e "  ${RED}[FAIL]${NC} $py_file"
        SYNTAX_ERRORS=1
    fi
done < <(find . -name "*.py" -not -path "./.git/*" -not -path "./__pycache__/*" -not -path "./.pytest_cache/*" -print0)

if [ $SYNTAX_ERRORS -eq 0 ]; then
    echo -e "  ${GREEN}[PASS]${NC} All Python files have valid syntax"
else
    echo -e "  ${RED}[FAIL]${NC} Some Python files have syntax errors"
    FAILED=1
fi
echo ""

# Step 3: Pytest
echo -e "${YELLOW}[3/4] Python Tests (pytest)${NC}"

# Try to activate conda if available (for pytest)
CONDA_PATHS=(
    "/opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh"
    "$HOME/miniconda3/etc/profile.d/conda.sh"
    "$HOME/anaconda3/etc/profile.d/conda.sh"
)

for CONDA_SH in "${CONDA_PATHS[@]}"; do
    if [ -f "$CONDA_SH" ]; then
        # shellcheck source=/dev/null
        source "$CONDA_SH"
        conda activate base 2>/dev/null || true
        break
    fi
done

# Find pytest
if command -v pytest &> /dev/null; then
    PYTEST_CMD="pytest"
elif python3 -c "import pytest" 2>/dev/null; then
    PYTEST_CMD="python3 -m pytest"
else
    echo -e "  ${YELLOW}[SKIP]${NC} pytest not found"
    echo "         Install with: pip install pytest"
    PYTEST_CMD=""
fi

if [ -n "$PYTEST_CMD" ]; then
    if [ -d "tests" ] && [ -n "$(find tests -name 'test_*.py' 2>/dev/null)" ]; then
        if $PYTEST_CMD tests/ -v --tb=short; then
            echo -e "  ${GREEN}[PASS]${NC} All tests passed"
        else
            echo -e "  ${RED}[FAIL]${NC} Tests failed"
            FAILED=1
        fi
    else
        echo -e "  ${YELLOW}[SKIP]${NC} No test files found"
    fi
fi
echo ""

# Step 4: Installation Test (optional in quick mode)
echo -e "${YELLOW}[4/4] Installation Test${NC}"
if [ "$QUICK_MODE" = true ]; then
    echo -e "  ${YELLOW}[SKIP]${NC} --quick mode"
elif [ ! -f "install.sh" ]; then
    echo -e "  ${YELLOW}[SKIP]${NC} install.sh not found"
else
    TEMP_DIR=$(mktemp -d)
    if bash install.sh "$TEMP_DIR" <<< "n" > /dev/null 2>&1; then
        # Verify key files
        if [ -f "$TEMP_DIR/.claude/rules/00-nexus-core.md" ] && \
           [ -d "$TEMP_DIR/.nexus/runtime" ]; then
            echo -e "  ${GREEN}[PASS]${NC} Installation test passed"
        else
            echo -e "  ${YELLOW}[WARN]${NC} Installation completed but some files missing"
        fi
    else
        echo -e "  ${RED}[FAIL]${NC} Installation script failed"
        FAILED=1
    fi
    rm -rf "$TEMP_DIR"
fi
echo ""

# Summary
echo -e "${BLUE}=================================================================${NC}"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}  All checks passed! Safe to create PR.${NC}"
else
    echo -e "${RED}  Some checks failed. Fix before creating PR.${NC}"
fi
echo -e "${BLUE}=================================================================${NC}"
echo ""

exit $FAILED
