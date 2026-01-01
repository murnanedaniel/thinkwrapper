#!/bin/bash
# Create all GitHub issues from templates
# Requires: gh CLI (https://cli.github.com/)
#
# Install gh CLI:
#   macOS: brew install gh
#   Linux: See https://github.com/cli/cli/blob/trunk/docs/install_linux.md
#
# Usage: ./scripts/create_all_issues.sh

set -e

echo "🚀 Creating GitHub Issues for ThinkWrapper MVP"
echo "=============================================="
echo ""

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo "❌ Error: gh CLI not found"
    echo ""
    echo "Please install GitHub CLI:"
    echo "  macOS:   brew install gh"
    echo "  Ubuntu:  See https://github.com/cli/cli/blob/trunk/docs/install_linux.md"
    echo ""
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "⚠️  Not authenticated with GitHub"
    echo "Running: gh auth login"
    echo ""
    gh auth login
fi

echo "✅ GitHub CLI ready"
echo ""

# Issue templates directory
ISSUES_DIR=".github/ISSUES"

# Counter
count=0
failed=0

# Create issues from numbered templates
for template in "$ISSUES_DIR"/[0-9]*.md; do
    if [ -f "$template" ]; then
        # Extract title (first line after removing # and **)
        title=$(grep -m1 '^# ' "$template" | sed 's/^# //')

        # Extract labels
        labels=$(grep '^\*\*Labels\*\*:' "$template" | sed 's/.*: `\(.*\)`/\1/')

        echo "Creating: $title"
        echo "  Labels: $labels"

        # Create the issue
        if gh issue create \
            --repo murnanedaniel/thinkwrapper \
            --title "$title" \
            --body-file "$template" \
            --label "$labels"; then
            ((count++))
            echo "  ✅ Created"
        else
            ((failed++))
            echo "  ❌ Failed"
        fi
        echo ""
    fi
done

echo "=============================================="
echo "📊 Summary:"
echo "  ✅ Created: $count issues"
if [ $failed -gt 0 ]; then
    echo "  ❌ Failed:  $failed issues"
fi
echo ""
echo "View issues: https://github.com/murnanedaniel/thinkwrapper/issues"
echo ""
