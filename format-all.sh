#!/bin/bash
set -e

# Colors for better output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Formatting Python ===${NC}"
./format.sh

echo ""
echo -e "${BLUE}=== Formatting JavaScript ===${NC}"
echo -e "${YELLOW}Running ESLint with auto-fix...${NC}"
npm run lint:fix || true

echo -e "${YELLOW}Running Prettier...${NC}"
npm run format

echo ""
echo -e "${GREEN}All formatting complete!${NC}"
