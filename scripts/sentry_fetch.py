#!/usr/bin/env python3
"""
Simple script to fetch Sentry issue details.

Usage:
    python scripts/sentry_fetch.py <issue_id>
    python scripts/sentry_fetch.py 7205057298
    python scripts/sentry_fetch.py --list-projects
    python scripts/sentry_fetch.py --list-issues
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

def load_env():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())

def load_admin_token():
    """Load admin token from .sentry-admin-token file (has full access, separate from CI token)."""
    token_path = Path(__file__).parent.parent / ".sentry-admin-token"
    if token_path.exists():
        return token_path.read_text().strip()
    return None

def api_request(url: str, auth_token: str) -> tuple:
    """Make an API request and return (success, data_or_error)."""
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {auth_token}")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req) as response:
            return True, json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        return False, f"HTTP {e.code}: {e.reason}\nURL: {url}\nResponse: {error_body}"

def fetch_issue(issue_id: str, auth_token: str, org_slug: str) -> dict:
    """Fetch issue details from Sentry API."""
    # Try non-org endpoint first (sometimes works better)
    url = f"https://sentry.io/api/0/issues/{issue_id}/"
    success, result = api_request(url, auth_token)
    if success:
        return result

    # Try org-specific endpoint
    url = f"https://sentry.io/api/0/organizations/{org_slug}/issues/{issue_id}/"
    success, result = api_request(url, auth_token)
    if success:
        return result

    print(f"Failed to fetch issue: {result}", file=sys.stderr)
    sys.exit(1)

def fetch_latest_event(issue_id: str, auth_token: str) -> dict:
    """Fetch the latest event for an issue."""
    url = f"https://sentry.io/api/0/issues/{issue_id}/events/latest/"
    success, result = api_request(url, auth_token)
    return result if success else None

def list_projects(auth_token: str, org_slug: str) -> list:
    """List accessible projects."""
    url = f"https://sentry.io/api/0/organizations/{org_slug}/projects/"
    success, result = api_request(url, auth_token)
    if not success:
        print(f"Failed to list projects: {result}", file=sys.stderr)
        return None
    return result

def list_issues(auth_token: str, org_slug: str, project_slug: str) -> list:
    """List recent issues for a project."""
    url = f"https://sentry.io/api/0/projects/{org_slug}/{project_slug}/issues/?query=is:unresolved"
    success, result = api_request(url, auth_token)
    if not success:
        print(f"Failed to list issues: {result}", file=sys.stderr)
        return None
    return result

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/sentry_fetch.py <issue_id>", file=sys.stderr)
        print("       python scripts/sentry_fetch.py --list-projects", file=sys.stderr)
        print("       python scripts/sentry_fetch.py --list-issues", file=sys.stderr)
        sys.exit(1)

    arg = sys.argv[1]

    # Load environment
    load_env()

    # Prefer admin token (full access) over CI token (limited scope)
    auth_token = load_admin_token() or os.environ.get("SENTRY_AUTH_TOKEN")
    org_slug = os.environ.get("SENTRY_ORG", "university-of-illinois-chic-sq")
    project_slug = os.environ.get("SENTRY_PROJECT", "battycoda")

    if not auth_token:
        print("Error: No Sentry token found.", file=sys.stderr)
        print("  Create .sentry-admin-token with your admin token, or", file=sys.stderr)
        print("  set SENTRY_AUTH_TOKEN in .env", file=sys.stderr)
        sys.exit(1)

    print(f"Using org: {org_slug}, project: {project_slug}")

    # Handle --list-projects
    if arg == "--list-projects":
        print("Listing accessible projects...")
        projects = list_projects(auth_token, org_slug)
        if projects:
            print(f"\nFound {len(projects)} projects:")
            for p in projects:
                print(f"  - {p.get('slug')} (id: {p.get('id')})")
        else:
            print("No projects found or no access")
        sys.exit(0)

    # Handle --list-issues
    if arg == "--list-issues":
        print(f"Listing unresolved issues for {project_slug}...")
        issues = list_issues(auth_token, org_slug, project_slug)
        if issues:
            print(f"\nFound {len(issues)} unresolved issues:")
            for i in issues[:20]:  # Show first 20
                print(f"  [{i.get('id')}] {i.get('title')}")
                print(f"      Last seen: {i.get('lastSeen')}, Count: {i.get('count')}")
        else:
            print("No issues found or no access")
        sys.exit(0)

    issue_id = arg
    print(f"Fetching issue {issue_id}...")

    # Fetch issue details
    issue = fetch_issue(issue_id, auth_token, org_slug)

    print("\n" + "="*60)
    print("ISSUE DETAILS")
    print("="*60)
    print(f"Title: {issue.get('title')}")
    print(f"Culprit: {issue.get('culprit')}")
    print(f"Type: {issue.get('type')}")
    print(f"Level: {issue.get('level')}")
    print(f"Status: {issue.get('status')}")
    print(f"First Seen: {issue.get('firstSeen')}")
    print(f"Last Seen: {issue.get('lastSeen')}")
    print(f"Count: {issue.get('count')}")

    if issue.get('metadata'):
        print(f"\nMetadata:")
        for k, v in issue['metadata'].items():
            print(f"  {k}: {v}")

    # Fetch latest event for stack trace
    print("\n" + "="*60)
    print("LATEST EVENT")
    print("="*60)

    event = fetch_latest_event(issue_id, auth_token)
    if event:
        # Print exception info
        if event.get('entries'):
            for entry in event['entries']:
                if entry.get('type') == 'exception':
                    for exc in entry.get('data', {}).get('values', []):
                        print(f"\nException: {exc.get('type')}: {exc.get('value')}")

                        # Print stack trace
                        stacktrace = exc.get('stacktrace', {})
                        frames = stacktrace.get('frames', [])
                        if frames:
                            print("\nStack Trace (most recent last):")
                            for frame in frames[-10:]:  # Last 10 frames
                                filename = frame.get('filename', '?')
                                lineno = frame.get('lineNo', '?')
                                function = frame.get('function', '?')
                                context_line = frame.get('context_line', '').strip()
                                print(f"  {filename}:{lineno} in {function}")
                                if context_line:
                                    print(f"    > {context_line}")

                elif entry.get('type') == 'message':
                    print(f"\nMessage: {entry.get('data', {}).get('formatted')}")

        # Print tags
        if event.get('tags'):
            print("\nTags:")
            for tag in event['tags'][:10]:  # First 10 tags
                print(f"  {tag.get('key')}: {tag.get('value')}")
    else:
        print("Could not fetch latest event details")

if __name__ == "__main__":
    main()
