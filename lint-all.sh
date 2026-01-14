#!/bin/bash
set -e

# Colors for better output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Linting Python ===${NC}"
./lint.sh

echo ""
echo -e "${BLUE}=== Linting JavaScript ===${NC}"
npm run lint || { echo -e "${RED}ESLint issues found. Run 'npm run lint:fix' to auto-fix${NC}"; exit 1; }

echo ""
echo -e "${BLUE}=== Checking JS Formatting ===${NC}"
npm run format:check || { echo -e "${RED}Prettier issues found. Run 'npm run format' to fix${NC}"; exit 1; }

echo ""
echo -e "${GREEN}All linting passed!${NC}"
