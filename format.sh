#!/bin/bash
set -e

# Colors for better output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Activate virtual environment
source venv/bin/activate

echo -e "${YELLOW}Running ruff linter with auto-fix...${NC}"
ruff check --fix .

echo -e "${YELLOW}Running ruff formatter...${NC}"
ruff format .

echo -e "${GREEN}Code formatting complete!${NC}"
