#!/bin/bash

# Run code formatters and linters for BattyCoda

set -e  # Exit immediately if a command exits with a non-zero status.

echo "==== Running Python Code Formatting and Linting ===="
./format.sh
./lint.sh

echo "==== Checking for CSS class issues ===="
# Install CSS linter requirements if needed
pip install -r css_linter_requirements.txt

# Run the CSS class checker
python check_css_classes.py

echo "==== All linting checks completed ===="