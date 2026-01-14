#!/bin/bash
set -e

# Colors for better output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Activate virtual environment
source venv/bin/activate

echo -e "${YELLOW}Running isort to check import sorting...${NC}"
isort . --check-only --diff || { echo -e "${RED}Import sorting issues found. Run './format.sh' to fix${NC}"; exit 1; }

echo -e "${YELLOW}Running black to check code formatting...${NC}"
black . --check || { echo -e "${RED}Code formatting issues found. Run './format.sh' to fix${NC}"; exit 1; }

echo -e "${YELLOW}Running flake8 to check code style...${NC}"
flake8 || { echo -e "${RED}Code style issues found. Please fix them manually${NC}"; exit 1; }

echo -e "${GREEN}All code quality checks passed!${NC}"
