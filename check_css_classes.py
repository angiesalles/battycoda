#!/usr/bin/env python
"""
CSS Class Checker

This script scans CSS files to identify defined classes, and HTML/template files
to identify referenced classes. It then compares them to find:
1. CSS classes that are defined but never used
2. CSS classes that are referenced but not defined

Usage:
    python check_css_classes.py

Options:
    --templates-dir: Directory containing templates (default: ./templates)
    --css-dir: Directory containing CSS files (default: ./static/css)
    --ignore-bootstrap: Ignore Bootstrap classes (default: True)
    --ignore-classes: Comma-separated list of classes to ignore
    --ignore-files: Comma-separated list of files to ignore

Example:
    python check_css_classes.py --templates-dir=./templates --css-dir=./static/css --ignore-bootstrap

Requirements:
    - Python 3.6+
    - tinycss2
    - bs4 (BeautifulSoup)
"""

import argparse
import glob
import os
import re
import sys
from collections import defaultdict

import tinycss2
from bs4 import BeautifulSoup

# Common Bootstrap classes to ignore when checking for undefined classes
BOOTSTRAP_CLASSES = {
    # Layout
    "container",
    "container-fluid",
    "row",
    "col",
    "col-1",
    "col-2",
    "col-3",
    "col-4",
    "col-5",
    "col-6",
    "col-7",
    "col-8",
    "col-9",
    "col-10",
    "col-11",
    "col-12",
    "col-sm",
    "col-md",
    "col-lg",
    "col-xl",
    # Flexbox utilities
    "d-flex",
    "flex-row",
    "flex-column",
    "justify-content-start",
    "justify-content-end",
    "justify-content-center",
    "justify-content-between",
    "justify-content-around",
    "align-items-start",
    "align-items-end",
    "align-items-center",
    "align-items-baseline",
    "align-items-stretch",
    # Spacing utilities (margin and padding)
    "m-0",
    "m-1",
    "m-2",
    "m-3",
    "m-4",
    "m-5",
    "mt-0",
    "mt-1",
    "mt-2",
    "mt-3",
    "mt-4",
    "mt-5",
    "mb-0",
    "mb-1",
    "mb-2",
    "mb-3",
    "mb-4",
    "mb-5",
    "ms-0",
    "ms-1",
    "ms-2",
    "ms-3",
    "ms-4",
    "ms-5",
    "me-0",
    "me-1",
    "me-2",
    "me-3",
    "me-4",
    "me-5",
    "p-0",
    "p-1",
    "p-2",
    "p-3",
    "p-4",
    "p-5",
    "pt-0",
    "pt-1",
    "pt-2",
    "pt-3",
    "pt-4",
    "pt-5",
    "pb-0",
    "pb-1",
    "pb-2",
    "pb-3",
    "pb-4",
    "pb-5",
    "ps-0",
    "ps-1",
    "ps-2",
    "ps-3",
    "ps-4",
    "ps-5",
    "pe-0",
    "pe-1",
    "pe-2",
    "pe-3",
    "pe-4",
    "pe-5",
    # Text utilities
    "text-start",
    "text-center",
    "text-end",
    "text-decoration-none",
    "text-lowercase",
    "text-uppercase",
    "text-capitalize",
    "text-primary",
    "text-secondary",
    "text-success",
    "text-danger",
    "text-warning",
    "text-info",
    "text-light",
    "text-dark",
    "text-muted",
    "text-white",
    # Background utilities
    "bg-primary",
    "bg-secondary",
    "bg-success",
    "bg-danger",
    "bg-warning",
    "bg-info",
    "bg-light",
    "bg-dark",
    "bg-white",
    "bg-transparent",
    # Border utilities
    "border",
    "border-top",
    "border-end",
    "border-bottom",
    "border-start",
    "border-0",
    "border-1",
    "border-2",
    "border-3",
    "border-4",
    "border-5",
    "border-primary",
    "border-secondary",
    "border-success",
    "border-danger",
    "border-warning",
    "border-info",
    "border-light",
    "border-dark",
    "border-white",
    # Display utilities
    "d-none",
    "d-inline",
    "d-inline-block",
    "d-block",
    "d-table",
    "d-table-cell",
    "d-table-row",
    "d-inline-flex",
    "d-sm-none",
    "d-md-none",
    "d-lg-none",
    "d-xl-none",
    # Components
    "alert",
    "alert-primary",
    "alert-secondary",
    "alert-success",
    "alert-danger",
    "alert-warning",
    "alert-info",
    "alert-light",
    "alert-dark",
    "badge",
    "btn",
    "btn-primary",
    "btn-secondary",
    "btn-success",
    "btn-danger",
    "btn-warning",
    "btn-info",
    "btn-light",
    "btn-dark",
    "btn-outline-primary",
    "btn-outline-secondary",
    "btn-outline-success",
    "btn-outline-danger",
    "btn-outline-warning",
    "btn-outline-info",
    "btn-outline-light",
    "btn-outline-dark",
    "btn-lg",
    "btn-sm",
    "card",
    "card-body",
    "card-title",
    "card-subtitle",
    "card-text",
    "card-link",
    "card-header",
    "card-footer",
    "card-img-top",
    "card-img-bottom",
    "dropdown",
    "dropdown-toggle",
    "dropdown-menu",
    "dropdown-item",
    "dropdown-divider",
    "form-control",
    "form-select",
    "form-check",
    "form-check-input",
    "form-check-label",
    "input-group",
    "input-group-text",
    "nav",
    "nav-tabs",
    "nav-pills",
    "nav-link",
    "nav-item",
    "navbar",
    "navbar-brand",
    "navbar-nav",
    "navbar-expand",
    "navbar-expand-sm",
    "navbar-expand-md",
    "navbar-expand-lg",
    "navbar-expand-xl",
    "navbar-light",
    "navbar-dark",
    "pagination",
    "progress",
    "spinner-border",
    "spinner-grow",
    "toast",
    "tooltip",
    # Maisonnette custom classes
    "mai-top-header",
    "mai-top-nav",
    "mai-icons-nav",
    "mai-wrapper",
    "mai-content-wrapper",
    "mai-sub-header",
    "mai-mega-menu",
    "mai-scroller",
    "mai-login",
    "mai-splash-screen",
    "angle-down",
}


def extract_classes_from_css(css_content):
    """Extract class names from CSS content."""
    # Parse the CSS
    stylesheet = tinycss2.parse_stylesheet(css_content)
    class_names = set()

    for rule in stylesheet:
        if rule.type != "qualified-rule":
            continue

        # Convert the prelude to text and look for class selectors
        prelude_text = tinycss2.serialize(rule.prelude)

        # Extract all class names (patterns like .class-name)
        classes = re.findall(r"\.([a-zA-Z0-9_-]+)", prelude_text)
        class_names.update(classes)

    return class_names


def extract_classes_from_html(html_content):
    """Extract class names from HTML content."""
    soup = BeautifulSoup(html_content, "html.parser")
    class_names = set()

    # Find all elements with class attributes
    for element in soup.find_all(class_=True):
        # Split class attribute by whitespace to get individual classes
        element_classes = element.get("class")
        class_names.update(element_classes)

    return class_names


def extract_classes_from_django_template(template_content):
    """Extract class names from Django template content."""
    class_names = set()

    # Pattern to match class attribute in HTML tags
    class_pattern = r'class=["\']([^"\']*)["\']'

    # Find all class attributes
    for match in re.finditer(class_pattern, template_content):
        # Split by whitespace to get individual classes
        # Skip Django template variable parts like {{ variable }}
        classes = match.group(1).split()
        classes = [c for c in classes if not (c.startswith("{{") or c.startswith("{%"))]
        class_names.update(classes)

    # Look for dynamically generated classes with concatenation
    # For example: class="row {% if condition %}custom-class{% endif %}"
    dyn_class_pattern = r'class=["\'][^"\']*\{\%[^\%]*\%\}[^"\']*["\']'
    for match in re.finditer(dyn_class_pattern, template_content):
        # These are complex cases that need special handling
        print(f"Dynamic class found (can't analyze): {match.group(0)}")

    return class_names


def main():
    parser = argparse.ArgumentParser(description="Check CSS class usage in HTML/template files.")
    parser.add_argument("--templates-dir", default="./templates", help="Directory containing templates")
    parser.add_argument("--css-dir", default="./static/css", help="Directory containing CSS files")
    parser.add_argument("--ignore-bootstrap", action="store_true", help="Ignore Bootstrap classes")
    parser.add_argument("--ignore-classes", default="", help="Comma-separated list of classes to ignore")
    parser.add_argument("--ignore-files", default="", help="Comma-separated list of files to ignore")
    args = parser.parse_args()

    # Create sets for defined and used classes
    defined_classes = set()
    used_classes = set()

    # Track where classes are defined (for reporting)
    class_sources = defaultdict(list)

    # Create a set of classes to ignore
    ignored_classes = set()
    if args.ignore_bootstrap:
        ignored_classes.update(BOOTSTRAP_CLASSES)
    if args.ignore_classes:
        ignored_classes.update([c.strip() for c in args.ignore_classes.split(",")])

    # Process CSS files
    css_files = glob.glob(os.path.join(args.css_dir, "**", "*.css"), recursive=True)
    for css_file in css_files:
        if any(ignore in css_file for ignore in args.ignore_files.split(",")):
            continue

        with open(css_file, "r", encoding="utf-8") as f:
            css_content = f.read()

        file_classes = extract_classes_from_css(css_content)

        # Update global set and track source
        for class_name in file_classes:
            defined_classes.add(class_name)
            class_sources[class_name].append(css_file)

    # Process template files
    template_files = []
    for ext in [".html", ".htm", ".django"]:
        template_files.extend(glob.glob(os.path.join(args.templates_dir, "**", f"*{ext}"), recursive=True))

    for template_file in template_files:
        if any(ignore in template_file for ignore in args.ignore_files.split(",")):
            continue

        with open(template_file, "r", encoding="utf-8") as f:
            template_content = f.read()

        # Use the appropriate extractor based on file extension
        if template_file.endswith((".html", ".htm", ".django")):
            file_classes = extract_classes_from_django_template(template_content)
        else:
            file_classes = extract_classes_from_html(template_content)

        used_classes.update(file_classes)

    # Find unused and undefined classes
    unused_classes = defined_classes - used_classes
    undefined_classes = used_classes - defined_classes - ignored_classes

    # Print results
    print("\n===== CSS CLASS ANALYSIS RESULTS =====\n")

    if not undefined_classes and not unused_classes:
        print("✅ All CSS classes are correctly defined and used!\n")
        return 0

    # Undefined classes
    if undefined_classes:
        print(f"⚠️  Found {len(undefined_classes)} undefined CSS classes:\n")
        for class_name in sorted(undefined_classes):
            print(f"  - {class_name}")
        print("\nThese classes are used in templates but not defined in any CSS file.\n")

    # Unused classes
    if unused_classes:
        print(f"ℹ️  Found {len(unused_classes)} unused CSS classes:\n")
        for class_name in sorted(unused_classes):
            sources = ", ".join(os.path.relpath(src) for src in class_sources[class_name][:3])
            if len(class_sources[class_name]) > 3:
                sources += f", and {len(class_sources[class_name]) - 3} more"
            print(f"  - {class_name} (defined in {sources})")
        print("\nThese classes are defined in CSS but not used in any template.\n")

    return 1 if undefined_classes else 0


if __name__ == "__main__":
    sys.exit(main())
