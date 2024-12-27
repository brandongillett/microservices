#!/usr/bin/env bash

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No color (reset)

# Cleanup targets
CLEANUP_TARGETS=(
    "__pycache__"
    "app.egg-info"
    ".pyc"
    ".mypy_cache"
    ".pytest_cache"
    ".coverage"
    "htmlcov"
)

# Function to cleanup a directory
cleanup_directory() {
    local target="$1"
    local root_dir="$2"
    local target_name="$3"

    echo -e "${YELLOW}Cleaning up $target_name...${NC}"

    find "$root_dir" -name "$target" -exec rm -rf {} + 2>/dev/null || echo -e "${RED}Warning: Some $target_name could not be deleted.${NC}"
}

# Main cleanup process
echo -e "${CYAN}Starting cleanup...${NC}"
PROJECT_ROOT=${1:-$(pwd)}

for TARGET in "${CLEANUP_TARGETS[@]}"; do
    echo -e "${CYAN}Processing: $TARGET...${NC}"
    cleanup_directory "$TARGET" "$PROJECT_ROOT" "$TARGET"
done

# Completion message
echo ""
echo -e "${GREEN}--------------------------------${NC}"
echo -e "${GREEN}Cleanup completed successfully!${NC}"
echo -e "${GREEN}--------------------------------${NC}"
