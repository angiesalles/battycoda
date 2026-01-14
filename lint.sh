#!/bin/bash
set -e

# Colors for better output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Activate virtual environment
source venv/bin/activate

echo -e "${YELLOW}Running ruff linter...${NC}"
ruff check . || { echo -e "${RED}Linting issues found. Run './format.sh' to auto-fix${NC}"; exit 1; }

echo -e "${YELLOW}Running ruff formatter check...${NC}"
ruff format --check . || { echo -e "${RED}Formatting issues found. Run './format.sh' to fix${NC}"; exit 1; }

echo -e "${GREEN}All code quality checks passed!${NC}"
