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
CLEAR_STATE=false

show_help() {
    echo -e "${BLUE}Nexus Installer${NC}"
    echo ""
    echo "Usage: ./install.sh [OPTIONS] [TARGET_DIR]"
    echo ""
    echo "Options:"
    echo "  --help, -h        Show this help message"
    echo "  --clean, -c       Clean old version before installing"
    echo "  --uninstall, -u   Uninstall Nexus (remove installed files)"
    echo "  --force, -f       Skip confirmation prompts"
    echo "  --clear-state     Also clear runtime state files (with --clean or --uninstall)"
    echo ""
    echo "Examples:"
    echo "  ./install.sh              Normal install (overwrite)"
    echo "  ./install.sh --clean      Clean old version, then install"
    echo "  ./install.sh --uninstall  Remove Nexus installation"
    echo "  ./install.sh /path/to/project  Install to specific directory"
    echo ""
    echo "User data preserved (never deleted):"
    echo "  ~/.nexus/notepads/           User notes"
    echo "  ~/.nexus/plans/              User plans"
    echo "  ~/.nexus/context/sessions/   Session archives"
    echo "  ~/.nexus/context/anchors.md  User anchors"
    echo "  ~/.nexus/anchors/            Anchor files"
    echo "  ~/.claude/settings.json       Claude settings"
    echo "  ~/.claude/settings.local.json Local settings"
}

# Parse command line arguments
TARGET_DIR=""
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
        --clear-state)
            CLEAR_STATE=true
            shift
            ;;
        -*)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
        *)
            TARGET_DIR="$1"
            shift
            ;;
    esac
done

# ============================================================
# Detection and Cleaning Functions
# ============================================================

detect_old_version() {
    # Check for any installed Nexus components
    if [ -f "$GLOBAL_NEXUS_DIR/runtime/cli.py" ] || \
       [ -d "$GLOBAL_CLAUDE_DIR/agents" ] && ls "$GLOBAL_CLAUDE_DIR"/agents/explorer.md 1>/dev/null 2>&1; then
        return 0  # Found old version
    fi
    return 1  # No old version
}

# Nexus-specific files (only these will be cleaned)
NEXUS_AGENTS=(
    "explorer.md"
    "analyst.md"
    "reviewer.md"
    "tester.md"
    "implementer.md"
    "architect.md"
    "planner.md"
)

NEXUS_COMMANDS=(
    "nexus.md"
    "plan.md"
    "reflection.md"
)

show_clean_preview() {
    echo -e "${YELLOW}The following Nexus files will be REMOVED:${NC}"
    echo ""
    echo "  Agents (${#NEXUS_AGENTS[@]} files):"
    for agent in "${NEXUS_AGENTS[@]}"; do
        echo "    ~/.claude/agents/$agent"
    done
    echo ""
    echo "  Commands (${#NEXUS_COMMANDS[@]} files):"
    for cmd in "${NEXUS_COMMANDS[@]}"; do
        echo "    ~/.claude/commands/$cmd"
    done
    echo ""
    echo "  Rules:"
    echo "    ~/.claude/rules/00-nexus*.md"
    echo ""
    echo "  Skills:"
    echo "    ~/.claude/skills/protocol/"
    echo "    ~/.claude/skills/reflection/"
    echo "    ~/.claude/skills/parallel/"
    echo ""
    echo "  Modules:"
    echo "    ~/.nexus/hooks/*.py"
    echo "    ~/.nexus/runtime/"
    echo "    ~/.nexus/context/*.py"
    if [ "$CLEAR_STATE" = true ]; then
        echo ""
        echo -e "${RED}  Runtime state files (--clear-state):${NC}"
        echo "    ~/.nexus/state.json"
        echo "    ~/.nexus/taskgraph.json"
        echo "    ~/.nexus/events.jsonl"
        echo "    ~/.nexus/artifacts/"
    fi
    echo ""
    echo -e "${GREEN}The following will be PRESERVED:${NC}"
    echo "  ~/.nexus/notepads/           (user notes)"
    echo "  ~/.nexus/plans/              (user plans)"
    echo "  ~/.nexus/context/sessions/   (session archives)"
    echo "  ~/.nexus/context/anchors.md  (user anchors)"
    echo "  ~/.nexus/anchors/            (anchor files)"
    echo "  ~/.claude/settings.json       (Claude settings)"
    echo "  ~/.claude/settings.local.json (local settings)"
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

    # Clean skills directories
    if [ -d "$GLOBAL_CLAUDE_DIR/skills/protocol" ]; then
        rm -rf "$GLOBAL_CLAUDE_DIR/skills/protocol"
        echo -e "  ${GREEN}[ok]${NC} Cleaned ~/.claude/skills/protocol/"
    fi
    if [ -d "$GLOBAL_CLAUDE_DIR/skills/reflection" ]; then
        rm -rf "$GLOBAL_CLAUDE_DIR/skills/reflection"
        echo -e "  ${GREEN}[ok]${NC} Cleaned ~/.claude/skills/reflection/"
    fi
    if [ -d "$GLOBAL_CLAUDE_DIR/skills/parallel" ]; then
        rm -rf "$GLOBAL_CLAUDE_DIR/skills/parallel"
        echo -e "  ${GREEN}[ok]${NC} Cleaned ~/.claude/skills/parallel/"
    fi

    # Clean hooks
    if [ -d "$GLOBAL_NEXUS_DIR/hooks" ]; then
        rm -f "$GLOBAL_NEXUS_DIR"/hooks/*.py 2>/dev/null || true
        echo -e "  ${GREEN}[ok]${NC} Cleaned ~/.nexus/hooks/*.py"
    fi

    # Clean runtime module
    if [ -d "$GLOBAL_NEXUS_DIR/runtime" ]; then
        rm -rf "$GLOBAL_NEXUS_DIR/runtime" 2>/dev/null || true
        echo -e "  ${GREEN}[ok]${NC} Cleaned ~/.nexus/runtime/"
    fi

    # Clean context modules (preserve user data)
    if [ -d "$GLOBAL_NEXUS_DIR/context" ]; then
        rm -f "$GLOBAL_NEXUS_DIR"/context/*.py 2>/dev/null || true
        # Note: anchors.md and sessions/ are preserved
        echo -e "  ${GREEN}[ok]${NC} Cleaned ~/.nexus/context/ (preserved anchors & sessions)"
    fi

    # Optional: Clear runtime state
    if [ "$CLEAR_STATE" = true ]; then
        echo ""
        echo -e "${YELLOW}Clearing runtime state...${NC}"
        rm -f "$GLOBAL_NEXUS_DIR/state.json" 2>/dev/null || true
        rm -f "$GLOBAL_NEXUS_DIR/taskgraph.json" 2>/dev/null || true
        rm -f "$GLOBAL_NEXUS_DIR/events.jsonl" 2>/dev/null || true
        rm -rf "$GLOBAL_NEXUS_DIR/artifacts/" 2>/dev/null || true
        echo -e "  ${GREEN}[ok]${NC} Cleared runtime state files"
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
    echo ""
    echo "User data preserved in:"
    echo -e "  ${DIM}~/.nexus/notepads/${NC}"
    echo -e "  ${DIM}~/.nexus/plans/${NC}"
    echo -e "  ${DIM}~/.nexus/context/sessions/${NC}"
    echo -e "  ${DIM}~/.nexus/context/anchors.md${NC}"
    echo ""
    echo "To completely remove all data, manually delete:"
    echo -e "  ${DIM}rm -rf ~/.nexus${NC}"
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

# Detect old version and warn (if not already cleaning)
if [ "$CLEAN_MODE" != true ] && detect_old_version; then
    echo -e "${YELLOW}Existing Nexus installation detected.${NC}"
    echo "Use --clean to remove old files before installing."
    echo ""
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

# ============================================================
# 2. Determine target directory
# ============================================================
if [ -z "$TARGET_DIR" ]; then
    echo -e "Installing to user home: ${GREEN}$HOME${NC}"
    TARGET_DIR="$HOME"
fi

CLAUDE_DIR="$TARGET_DIR/.claude"
NEXUS_DIR="$TARGET_DIR/.nexus"

echo ""

# ============================================================
# 3. Install project files
# ============================================================
echo -e "${BLUE}[1/4] Project Files${NC}"

# Create directory structure
mkdir -p "$CLAUDE_DIR/rules"
mkdir -p "$CLAUDE_DIR/commands"
mkdir -p "$CLAUDE_DIR/skills/protocol"
mkdir -p "$CLAUDE_DIR/skills/reflection"
mkdir -p "$CLAUDE_DIR/skills/parallel"
mkdir -p "$CLAUDE_DIR/agents"
mkdir -p "$NEXUS_DIR/notepads"
mkdir -p "$NEXUS_DIR/plans"
mkdir -p "$NEXUS_DIR/context/current"
mkdir -p "$NEXUS_DIR/context/sessions"
mkdir -p "$NEXUS_DIR/hooks"
mkdir -p "$NEXUS_DIR/runtime"

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

# Copy protocol skills
if [ -d "$SOURCE_DIR/protocol" ] && ls "$SOURCE_DIR"/protocol/*.md 1>/dev/null 2>&1; then
    cp "$SOURCE_DIR"/protocol/*.md "$CLAUDE_DIR/skills/protocol/"
    echo -e "  ${GREEN}[ok]${NC} Protocol skills"
fi

# Copy reflection skills
if [ -d "$SOURCE_DIR/reflection" ] && ls "$SOURCE_DIR"/reflection/*.md 1>/dev/null 2>&1; then
    cp "$SOURCE_DIR"/reflection/*.md "$CLAUDE_DIR/skills/reflection/"
    echo -e "  ${GREEN}[ok]${NC} Reflection skills"
fi

# Copy parallel skills
if [ -d "$SOURCE_DIR/parallel" ] && ls "$SOURCE_DIR"/parallel/*.md 1>/dev/null 2>&1; then
    cp "$SOURCE_DIR"/parallel/*.md "$CLAUDE_DIR/skills/parallel/"
    echo -e "  ${GREEN}[ok]${NC} Parallel skills"
fi

# Copy context modules
if [ -d "$SOURCE_DIR/context" ] && ls "$SOURCE_DIR"/context/*.py 1>/dev/null 2>&1; then
    find "$SOURCE_DIR/context" -maxdepth 1 -name "*.py" \
        ! -name "test_*.py" ! -name "example_*.py" ! -name "*_usage.py" \
        -exec cp {} "$NEXUS_DIR/context/" \;
    CTX_COUNT=$(find "$SOURCE_DIR/context" -maxdepth 1 -name "*.py" \
        ! -name "test_*.py" ! -name "example_*.py" ! -name "*_usage.py" | wc -l | tr -d ' ')
    echo -e "  ${GREEN}[ok]${NC} Context modules ($CTX_COUNT files)"
fi

# Copy hooks
if [ -d "$SOURCE_DIR/hooks" ] && ls "$SOURCE_DIR"/hooks/*.py 1>/dev/null 2>&1; then
    find "$SOURCE_DIR/hooks" -maxdepth 1 -name "*.py" \
        ! -name "test_*.py" ! -name "test-*.py" ! -name "example_*.py" \
        -exec cp {} "$NEXUS_DIR/hooks/" \;
    HOOK_COUNT=$(find "$SOURCE_DIR/hooks" -maxdepth 1 -name "*.py" \
        ! -name "test_*.py" ! -name "test-*.py" ! -name "example_*.py" | wc -l | tr -d ' ')
    echo -e "  ${GREEN}[ok]${NC} Hooks ($HOOK_COUNT files)"
fi

# Initialize anchors file
if [ ! -f "$NEXUS_DIR/context/anchors.md" ]; then
    cat > "$NEXUS_DIR/context/anchors.md" << 'EOF'
# Anchors

Global anchors for this project.

## Decision Anchors [D]

*No anchors yet*

## Problem Anchors [P]

*No anchors yet*
EOF
    echo -e "  ${GREEN}[ok]${NC} Initialized anchors.md"
fi

echo ""

# ============================================================
# 4. Copy runtime from project root
# ============================================================
echo -e "${BLUE}[2/4] Runtime Components${NC}"

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
# 5. Register Hooks
# ============================================================
echo -e "${BLUE}[3/4] Hook Registration${NC}"

SETTINGS_FILE="$HOME/.claude/settings.json"

# Check if already registered
ALREADY_REGISTERED=false
if [ -f "$SETTINGS_FILE" ]; then
    if grep -q "reflection-extract.py" "$SETTINGS_FILE" 2>/dev/null; then
        ALREADY_REGISTERED=true
    fi
fi

if [ "$ALREADY_REGISTERED" = true ]; then
    echo -e "  ${GREEN}[ok]${NC} Hooks already registered"
else
    echo "  Nexus uses hooks to extract knowledge before context compaction."
    echo -e "  This requires adding configuration to ${DIM}~/.claude/settings.json${NC}"
    echo ""

    if [ "$FORCE_MODE" != true ]; then
        read -p "  Register hooks? [Y/n] " -n 1 -r REPLY
        echo ""
    else
        REPLY="y"
    fi

    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        mkdir -p "$HOME/.claude"

        if [ ! -f "$SETTINGS_FILE" ]; then
            cat > "$SETTINGS_FILE" << 'EOF'
{
  "hooks": {
    "PreCompact": [
      {
        "matcher": "auto",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.nexus/hooks/reflection-extract.py",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
EOF
            echo -e "  ${GREEN}[ok]${NC} Created ~/.claude/settings.json with hooks"
        else
            if command -v python3 &>/dev/null; then
                python3 << 'PYTHON_SCRIPT'
import json
import os

settings_path = os.path.expanduser("~/.claude/settings.json")

with open(settings_path, "r") as f:
    settings = json.load(f)

new_hook = {
    "matcher": "auto",
    "hooks": [
        {
            "type": "command",
            "command": "python3 ~/.nexus/hooks/reflection-extract.py",
            "timeout": 30
        }
    ]
}

if "hooks" not in settings:
    settings["hooks"] = {}

if "PreCompact" not in settings["hooks"]:
    settings["hooks"]["PreCompact"] = []

is_duplicate = False
for hook_entry in settings["hooks"]["PreCompact"]:
    for hook in hook_entry.get("hooks", []):
        if "reflection-extract.py" in hook.get("command", ""):
            is_duplicate = True
            break

if not is_duplicate:
    settings["hooks"]["PreCompact"].append(new_hook)

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)

print("ok")
PYTHON_SCRIPT
                echo -e "  ${GREEN}[ok]${NC} Updated ~/.claude/settings.json with hooks"
            else
                echo -e "  ${RED}[error]${NC} Python3 not found, cannot merge JSON"
            fi
        fi
    else
        echo -e "  ${DIM}Skipped hook registration${NC}"
    fi
fi

echo ""

# ============================================================
# 6. Permissions
# ============================================================
echo -e "${BLUE}[4/4] Permissions${NC}"

PERM_CLAUDE_READ="Read(path:${CLAUDE_DIR}/**)"
PERM_NEXUS_READ="Read(path:${NEXUS_DIR}/**)"
PERM_NEXUS_WRITE="Write(path:${NEXUS_DIR}/**)"

if [ "$FORCE_MODE" = true ]; then
    ADD_PERMS="y"
else
    echo ""
    echo "Add file permissions to Claude settings?"
    echo -e "  ${DIM}$PERM_CLAUDE_READ${NC}"
    echo -e "  ${DIM}$PERM_NEXUS_READ${NC}"
    echo -e "  ${DIM}$PERM_NEXUS_WRITE${NC}"
    echo ""
    read -p "Add permissions to ~/.claude/settings.json? [Y/n] " -n 1 -r ADD_PERMS
    echo ""
fi

if [[ ! $ADD_PERMS =~ ^[Nn]$ ]]; then
    mkdir -p "$HOME/.claude"
    if command -v python3 &>/dev/null; then
        CLAUDE_DIR_ENV="$CLAUDE_DIR" NEXUS_DIR_ENV="$NEXUS_DIR" python3 << 'PYTHON_SCRIPT'
import json
import os

settings_path = os.path.expanduser("~/.claude/settings.json")
claude_dir = os.environ.get("CLAUDE_DIR_ENV", "")
nexus_dir = os.environ.get("NEXUS_DIR_ENV", "")

allow_entries = [
    f"Read(path:{claude_dir}/**)",
    f"Read(path:{nexus_dir}/**)",
    f"Write(path:{nexus_dir}/**)",
]

if os.path.exists(settings_path):
    with open(settings_path, "r", encoding="utf-8") as f:
        settings = json.load(f)
else:
    settings = {}

permissions = settings.setdefault("permissions", {})
allow = permissions.setdefault("allow", [])

for entry in allow_entries:
    if entry and entry not in allow:
        allow.append(entry)

if "defaultMode" not in permissions:
    permissions["defaultMode"] = "default"

with open(settings_path, "w", encoding="utf-8") as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)

print("ok")
PYTHON_SCRIPT
        echo -e "  ${GREEN}[ok]${NC} Updated ~/.claude/settings.json permissions"
    else
        echo -e "  ${RED}[error]${NC} Python3 not found, cannot merge permissions"
    fi
else
    echo -e "  ${DIM}Skipped permission update${NC}"
fi

# ============================================================
# Done
# ============================================================
echo ""
echo -e "${GREEN}Done!${NC}"
echo ""
echo "Installed to:"
echo -e "  ${DIM}$CLAUDE_DIR/rules/${NC}     Core rules (auto-loaded)"
echo -e "  ${DIM}$CLAUDE_DIR/agents/${NC}    Agent definitions"
echo -e "  ${DIM}$CLAUDE_DIR/commands/${NC}  Commands"
echo -e "  ${DIM}$CLAUDE_DIR/skills/${NC}    Protocol, reflection, parallel"
echo -e "  ${DIM}$NEXUS_DIR/${NC}            Work data"
echo -e "  ${DIM}~/.nexus/hooks/${NC}        Global hooks"
echo -e "  ${DIM}~/.nexus/runtime/${NC}      Runtime CLI"
echo ""
echo -e "Start Claude Code and say: ${GREEN}/nexus${NC}"
