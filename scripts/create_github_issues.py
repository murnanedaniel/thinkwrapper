#!/usr/bin/env python3
"""Create GitHub issues from template files using GitHub API."""
import os
import json
import subprocess
import sys

# Get GitHub credentials from git
def get_github_token():
    """Extract GitHub token from git credentials."""
    try:
        # Try to get from git credential helper
        result = subprocess.run(
            ['git', 'config', '--get', 'credential.helper'],
            capture_output=True,
            text=True
        )

        # For this environment, we'll use the git remote URL to authenticate
        remote_url = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            capture_output=True,
            text=True
        ).stdout.strip()

        print(f"Remote URL: {remote_url}")

        # Extract token from URL if present
        if '@' in remote_url and 'local_proxy' in remote_url:
            # This is using the local proxy authentication
            return "PROXY_AUTH"

        return None
    except Exception as e:
        print(f"Error getting token: {e}")
        return None

def parse_issue_template(filepath):
    """Parse issue template file."""
    with open(filepath, 'r') as f:
        content = f.read()

    # Extract title (first # heading)
    lines = content.split('\n')
    title = None
    labels = []
    body_lines = []

    for i, line in enumerate(lines):
        if line.startswith('# ') and title is None:
            title = line[2:].strip()
        elif line.startswith('**Labels**:'):
            # Extract labels
            label_text = line.split(':', 1)[1].strip()
            labels = [l.strip().strip('`') for l in label_text.split(',')]
        else:
            # Skip the title and labels line from body
            if i > 0 and '**Labels**' not in line:
                body_lines.append(line)

    body = '\n'.join(body_lines).strip()

    return {
        'title': title,
        'body': body,
        'labels': labels
    }

def create_issue_via_api(owner, repo, issue_data, token=None):
    """Create issue using GitHub API."""
    import requests

    url = f"https://api.github.com/repos/{owner}/{repo}/issues"

    headers = {
        'Accept': 'application/vnd.github.v3+json',
    }

    if token and token != "PROXY_AUTH":
        headers['Authorization'] = f'token {token}'

    payload = {
        'title': issue_data['title'],
        'body': issue_data['body'],
        'labels': issue_data['labels']
    }

    print(f"\nCreating issue: {issue_data['title']}")
    print(f"Labels: {', '.join(issue_data['labels'])}")

    try:
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 201:
            issue = response.json()
            print(f"✅ Created: {issue['html_url']}")
            return issue
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    """Main function."""
    # Get repository info
    owner = "murnanedaniel"
    repo = "thinkwrapper"

    # Get GitHub token
    token = get_github_token()

    # Get issue template files
    issues_dir = ".github/ISSUES"
    template_files = sorted([
        f for f in os.listdir(issues_dir)
        if f.endswith('.md') and f[0].isdigit()
    ])

    print(f"Found {len(template_files)} issue templates")
    print(f"Repository: {owner}/{repo}")
    print("=" * 60)

    created_issues = []

    for template_file in template_files:
        filepath = os.path.join(issues_dir, template_file)
        issue_data = parse_issue_template(filepath)

        # Create issue
        issue = create_issue_via_api(owner, repo, issue_data, token)
        if issue:
            created_issues.append(issue)

    print("\n" + "=" * 60)
    print(f"✅ Created {len(created_issues)} issues successfully!")
    print("\nIssue URLs:")
    for issue in created_issues:
        print(f"  - {issue['html_url']}")

if __name__ == '__main__':
    main()
