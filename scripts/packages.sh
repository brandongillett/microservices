#!/usr/bin/env sh

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No color (reset)

# Function to check if package is in pyproject.toml dependencies
is_package_in_dependencies() {
    local package_name="$1"
    if grep -F "$package_name" "pyproject.toml" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to update a package
update_package() {
    local package_name="$1"
    local service_dir="$2"

    service_name=$(basename "$service_dir")
    
    if is_package_in_dependencies "$package_name" "$service_dir"; then
        echo -e "${CYAN}Updating package $package_name in $service_name...${NC}"
        uv remove "$package_name" > /dev/null 2>&1 && uv add "$package_name" > /dev/null 2>&1
    else
        echo -e "${YELLOW}Package $package_name not found in $service_name dependencies. Skipping...${NC}"
    fi
}

# Function to add a package
add_package() {
    local package_name="$1"
    local service_dir="$2"
    service_name=$(basename "$service_dir")
    
    echo -e "${CYAN}Adding package $package_name in $service_name...${NC}"
    uv add "$package_name" > /dev/null 2>&1
}

# Function to process each service
process_services() {
    local action="$1"
    local package_name="$2"

    for service_dir in services/*/; do
        service_name=$(basename "$service_dir")

        cd "$service_dir"
        
        if [ "$action" = "add" ]; then
            add_package "$package_name" "$service_dir"
        elif [ "$action" = "update" ]; then
            update_package "$package_name" "$service_dir"
        fi
        
        cd - > /dev/null 2>&1
    done
}

# Main logic to handle input arguments and actions
if [ $# -lt 2 ]; then
    echo -e "${RED}Usage: $0 <add|update> <package_name>${NC}"
    exit 1
fi

action="$1"
package_name="$2"

if [ "$action" = "add" ] || [ "$action" = "update" ]; then
    process_services "$action" "$package_name"
else
    echo -e "${RED}Invalid action. Please use 'add' or 'update'.${NC}"
    exit 1
fi

# Successful packages message
echo ""
echo -e "${GREEN}--------------------------------${NC}"
echo -e "${GREEN}Packages successfully installed!${NC}"
echo -e "${GREEN}--------------------------------${NC}"