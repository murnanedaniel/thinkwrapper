# Creating GitHub Issues - Quick Guide

I've prepared 7 comprehensive issue templates for the MVP features. Here are three ways to create them:

## Option 1: Automated Script (Recommended)

If you have GitHub CLI installed:

```bash
# Make sure you're authenticated
gh auth login

# Run the script
./scripts/create_all_issues.sh
```

This will create all 7 issues automatically!

## Option 2: Manual Creation

For each file in `.github/ISSUES/`:

1. Go to https://github.com/murnanedaniel/thinkwrapper/issues/new
2. Open the template file (e.g., `01-anthropic-api-integration.md`)
3. Copy the title (first `# heading`)
4. Copy the entire content into the issue description
5. Add the labels listed under `**Labels**:`
6. Click "Submit new issue"

### Quick Links
- [Create Issue #1: Anthropic API](.github/ISSUES/01-anthropic-api-integration.md)
- [Create Issue #2: Brave Search](.github/ISSUES/02-brave-search-api-integration.md)
- [Create Issue #3: Newsletter Synthesis](.github/ISSUES/03-newsletter-synthesis-service.md)
- [Create Issue #4: Google OAuth](.github/ISSUES/04-google-oauth-authentication.md)
- [Create Issue #5: Paddle Payments](.github/ISSUES/05-paddle-payment-integration.md)
- [Create Issue #6: Celery Setup](.github/ISSUES/06-celery-task-queue-setup.md)
- [Create Issue #7: Testing Suite](.github/ISSUES/07-comprehensive-test-suite.md)

## Option 3: One-liner per Issue

If you have `gh` CLI installed, run these commands:

```bash
# Issue 1: Anthropic API Integration
gh issue create \
  --title "Implement Anthropic Claude API Integration" \
  --body-file .github/ISSUES/01-anthropic-api-integration.md \
  --label "feature,api-integration,ai,high-priority"

# Issue 2: Brave Search API Integration
gh issue create \
  --title "Implement Brave Search API Integration" \
  --body-file .github/ISSUES/02-brave-search-api-integration.md \
  --label "feature,api-integration,search,high-priority"

# Issue 3: Newsletter Synthesis Service
gh issue create \
  --title "Implement Newsletter Synthesis Service" \
  --body-file .github/ISSUES/03-newsletter-synthesis-service.md \
  --label "feature,ai,core-functionality,high-priority"

# Issue 4: Google OAuth Authentication
gh issue create \
  --title "Implement Google OAuth Authentication" \
  --body-file .github/ISSUES/04-google-oauth-authentication.md \
  --label "feature,authentication,security,high-priority"

# Issue 5: Paddle Payment Integration
gh issue create \
  --title "Implement Paddle Payment Integration" \
  --body-file .github/ISSUES/05-paddle-payment-integration.md \
  --label "feature,payments,subscription,medium-priority"

# Issue 6: Celery Task Queue Setup
gh issue create \
  --title "Setup Celery Task Queue for Async Processing" \
  --body-file .github/ISSUES/06-celery-task-queue-setup.md \
  --label "feature,infrastructure,async,high-priority"

# Issue 7: Comprehensive Test Suite
gh issue create \
  --title "Build Comprehensive Test Suite" \
  --body-file .github/ISSUES/07-comprehensive-test-suite.md \
  --label "testing,quality,ci-cd,high-priority"
```

## Installing GitHub CLI

### macOS
```bash
brew install gh
```

### Ubuntu/Debian
```bash
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh
```

### Windows
```powershell
winget install --id GitHub.cli
```

Or download from: https://cli.github.com/

## After Creating Issues

Once the issues are created:

1. **Review them** - Make sure they look good
2. **Assign them** - Assign to yourself or team members
3. **Add to project board** - Create a project board to track progress
4. **Start development** - Pick a high-priority issue and start coding!

## Issue Priority Order

**Start with these (parallel development possible):**
1. #1 Anthropic API Integration
2. #2 Brave Search Integration
3. #4 Google OAuth Authentication

**Then:**
4. #3 Newsletter Synthesis (requires #1 & #2)
5. #6 Celery Setup (requires #1 & #3)

**Finally:**
6. #5 Paddle Payments (requires #4)
7. #7 Comprehensive Testing (ongoing throughout)

---

**Questions?** See `.github/ISSUES/README.md` for more details on the development roadmap.
