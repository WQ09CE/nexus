#!/bin/bash

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
DIM='\033[2m'
NC='\033[0m'

PROJECT_ROOT=$(pwd)
SOURCE_DIR=""
GLOBAL_NEXUS_DIR="$HOME/.nexus"
GLOBAL_CLAUDE_DIR="$HOME/.claude"

# ============================================================
# Command Line Options
# ============================================================
CLEAN_MODE=false
UNINSTALL_MODE=false
FORCE_MODE=false

show_help() {
    echo -e "${BLUE}Nexus Installer${NC}"
    echo ""
    echo "Usage: ./install.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help, -h        Show this help message"
    echo "  --clean, -c       Clean old version before installing"
    echo "  --uninstall, -u   Uninstall Nexus (remove installed files)"
    echo "  --force, -f       Skip confirmation prompts"
    echo ""
    echo "Examples:"
    echo "  ./install.sh              Normal install (overwrite)"
    echo "  ./install.sh --clean      Clean old version, then install"
    echo "  ./install.sh --uninstall  Remove Nexus installation"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --clean|-c)
            CLEAN_MODE=true
            shift
            ;;
        --uninstall|-u)
            UNINSTALL_MODE=true
            shift
            ;;
        --force|-f)
            FORCE_MODE=true
            shift
            ;;
        -*)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
        *)
            shift
            ;;
    esac
done

# ============================================================
# Nexus-specific files (only these will be cleaned)
# ============================================================
NEXUS_AGENTS=(
    "eye.md"
    "body.md"
    "mind.md"
)

NEXUS_COMMANDS=(
    "nexus.md"
)

# ============================================================
# Detection and Cleaning Functions
# ============================================================

detect_old_version() {
    if [ -d "$GLOBAL_CLAUDE_DIR/agents" ] && ls "$GLOBAL_CLAUDE_DIR"/agents/eye.md 1>/dev/null 2>&1; then
        return 0
    fi
    return 1
}

show_clean_preview() {
    echo -e "${YELLOW}The following Nexus files will be REMOVED:${NC}"
    echo ""
    echo "  Agents:"
    for agent in "${NEXUS_AGENTS[@]}"; do
        echo "    ~/.claude/agents/$agent"
    done
    echo ""
    echo "  Commands:"
    for cmd in "${NEXUS_COMMANDS[@]}"; do
        echo "    ~/.claude/commands/$cmd"
    done
    echo ""
    echo "  Rules:"
    echo "    ~/.claude/rules/00-nexus*.md"
    echo ""
    echo "  Runtime:"
    echo "    ~/.nexus/runtime/"
    echo ""
}

clean_old_version() {
    echo -e "${BLUE}Cleaning old Nexus installation...${NC}"
    echo ""

    # Clean agents
    if [ -d "$GLOBAL_CLAUDE_DIR/agents" ]; then
        local agent_count=0
        for agent in "${NEXUS_AGENTS[@]}"; do
            if [ -f "$GLOBAL_CLAUDE_DIR/agents/$agent" ]; then
                rm -f "$GLOBAL_CLAUDE_DIR/agents/$agent"
                ((agent_count++))
            fi
        done
        echo -e "  ${GREEN}[ok]${NC} Removed $agent_count Nexus agent files"
    fi

    # Clean rules (nexus-related)
    if [ -d "$GLOBAL_CLAUDE_DIR/rules" ]; then
        rm -f "$GLOBAL_CLAUDE_DIR"/rules/00-nexus*.md 2>/dev/null || true
        echo -e "  ${GREEN}[ok]${NC} Cleaned ~/.claude/rules/00-nexus*.md"
    fi

    # Clean commands
    if [ -d "$GLOBAL_CLAUDE_DIR/commands" ]; then
        local cmd_count=0
        for cmd in "${NEXUS_COMMANDS[@]}"; do
            if [ -f "$GLOBAL_CLAUDE_DIR/commands/$cmd" ]; then
                rm -f "$GLOBAL_CLAUDE_DIR/commands/$cmd"
                ((cmd_count++))
            fi
        done
        echo -e "  ${GREEN}[ok]${NC} Removed $cmd_count Nexus command files"
    fi

    # Clean runtime module
    if [ -d "$GLOBAL_NEXUS_DIR/runtime" ]; then
        rm -rf "$GLOBAL_NEXUS_DIR/runtime" 2>/dev/null || true
        echo -e "  ${GREEN}[ok]${NC} Cleaned ~/.nexus/runtime/"
    fi

    # Clean hooks
    if [ -d "$GLOBAL_NEXUS_DIR/hooks" ]; then
        rm -rf "$GLOBAL_NEXUS_DIR/hooks" 2>/dev/null || true
        echo -e "  ${GREEN}[ok]${NC} Cleaned ~/.nexus/hooks/"
    fi

    echo ""
    echo -e "${GREEN}Old version cleaned.${NC}"
}

do_uninstall() {
    echo -e "${BLUE}Nexus Uninstaller${NC}"
    echo ""

    if ! detect_old_version; then
        echo -e "${YELLOW}No Nexus installation detected.${NC}"
        exit 0
    fi

    show_clean_preview

    if [ "$FORCE_MODE" != true ]; then
        read -p "Continue with uninstall? [y/N] " -r REPLY
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Uninstall cancelled."
            exit 0
        fi
    fi

    clean_old_version

    echo ""
    echo -e "${GREEN}Nexus has been uninstalled.${NC}"
    exit 0
}

# ============================================================
# Handle Uninstall Mode
# ============================================================
if [ "$UNINSTALL_MODE" = true ]; then
    do_uninstall
fi

# ============================================================
# Main Installation
# ============================================================
echo -e "${BLUE}Nexus Installer${NC}"
echo ""

# Handle Clean Mode
if [ "$CLEAN_MODE" = true ]; then
    if detect_old_version; then
        show_clean_preview

        if [ "$FORCE_MODE" != true ]; then
            read -p "Clean old version before installing? [y/N] " -r REPLY
            echo ""
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "Clean cancelled. Proceeding with normal install..."
                echo ""
            else
                clean_old_version
                echo ""
            fi
        else
            clean_old_version
            echo ""
        fi
    else
        echo -e "${DIM}No old version detected, skipping clean.${NC}"
        echo ""
    fi
fi

# ============================================================
# 1. Determine source directory
# ============================================================
if [ -d "$PROJECT_ROOT/nexus-dist" ]; then
    SOURCE_DIR="$PROJECT_ROOT/nexus-dist"
else
    echo -e "${RED}Error: nexus-dist directory not found.${NC}"
    echo "Please run this script from the nexus project root."
    exit 1
fi

CLAUDE_DIR="$HOME/.claude"
NEXUS_DIR="$HOME/.nexus"

echo -e "Installing to: ${GREEN}$HOME${NC}"
echo ""

# ============================================================
# 2. Install project files
# ============================================================
echo -e "${BLUE}[1/2] Project Files${NC}"

# Create directory structure
mkdir -p "$CLAUDE_DIR/rules"
mkdir -p "$CLAUDE_DIR/commands"
mkdir -p "$CLAUDE_DIR/agents"
mkdir -p "$NEXUS_DIR/runtime"
mkdir -p "$NEXUS_DIR/hooks"
mkdir -p "$NEXUS_DIR/context"

# Copy core rules
cp "$SOURCE_DIR"/rules/00-nexus-core.md "$CLAUDE_DIR/rules/"
echo -e "  ${GREEN}[ok]${NC} Core rule"

# Copy commands
if [ -d "$SOURCE_DIR/commands" ] && ls "$SOURCE_DIR"/commands/*.md 1>/dev/null 2>&1; then
    cp "$SOURCE_DIR"/commands/*.md "$CLAUDE_DIR/commands/"
    CMD_COUNT=$(find "$SOURCE_DIR/commands" -maxdepth 1 -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
    echo -e "  ${GREEN}[ok]${NC} Commands ($CMD_COUNT files)"
fi

# Copy agents
if [ -d "$SOURCE_DIR/agents" ] && ls "$SOURCE_DIR"/agents/*.md 1>/dev/null 2>&1; then
    cp "$SOURCE_DIR"/agents/*.md "$CLAUDE_DIR/agents/"
    AGENT_COUNT=$(find "$SOURCE_DIR/agents" -maxdepth 1 -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
    echo -e "  ${GREEN}[ok]${NC} Agents ($AGENT_COUNT files)"
fi

echo ""

# ============================================================
# 3. Copy runtime from project root
# ============================================================
echo -e "${BLUE}[2/3] Runtime Components${NC}"

if [ -d "$PROJECT_ROOT/runtime" ] && ls "$PROJECT_ROOT"/runtime/*.py 1>/dev/null 2>&1; then
    find "$PROJECT_ROOT/runtime" -maxdepth 1 -name "*.py" \
        ! -name "test_*.py" ! -name "example_*.py" \
        -exec cp {} "$NEXUS_DIR/runtime/" \;
    RUNTIME_COUNT=$(find "$PROJECT_ROOT/runtime" -maxdepth 1 -name "*.py" \
        ! -name "test_*.py" ! -name "example_*.py" | wc -l | tr -d ' ')
    echo -e "  ${GREEN}[ok]${NC} Runtime ($RUNTIME_COUNT files)"
else
    echo -e "  ${DIM}[skip]${NC} No runtime files found"
fi

echo ""

# ============================================================
# 4. Copy hooks
# ============================================================
echo -e "${BLUE}[3/3] Hooks${NC}"

if [ -d "$SOURCE_DIR/hooks" ] && ls "$SOURCE_DIR"/hooks/*.py 1>/dev/null 2>&1; then
    cp "$SOURCE_DIR"/hooks/*.py "$NEXUS_DIR/hooks/"
    chmod +x "$NEXUS_DIR"/hooks/*.py
    HOOK_COUNT=$(find "$SOURCE_DIR/hooks" -maxdepth 1 -name "*.py" 2>/dev/null | wc -l | tr -d ' ')
    echo -e "  ${GREEN}[ok]${NC} Hooks ($HOOK_COUNT files)"
else
    echo -e "  ${DIM}[skip]${NC} No hooks found"
fi

echo ""

# ============================================================
# Done
# ============================================================
echo -e "${GREEN}Done!${NC}"
echo ""
echo "Installed to:"
echo -e "  ${DIM}$CLAUDE_DIR/rules/${NC}     Core rules (auto-loaded)"
echo -e "  ${DIM}$CLAUDE_DIR/agents/${NC}    Agent definitions"
echo -e "  ${DIM}$CLAUDE_DIR/commands/${NC}  Commands"
echo -e "  ${DIM}$NEXUS_DIR/runtime/${NC}    Runtime"
echo -e "  ${DIM}$NEXUS_DIR/hooks/${NC}      Hooks (PreCompact, etc.)"
echo -e "  ${DIM}$NEXUS_DIR/context/${NC}    Context storage"
echo ""
echo -e "Start Claude Code and say: ${GREEN}/nexus${NC}"
