# GitHub Issues - Feature Development Roadmap

This directory contains templates for GitHub issues that represent the major features needed to bring ThinkWrapper to MVP status. Each issue is designed to be a **parallelizable unit of work** that can be tackled independently.

## Creating Issues from Templates

### Option 1: Manual Creation (Recommended)
1. Go to https://github.com/murnanedaniel/thinkwrapper/issues/new
2. Copy content from the appropriate `.md` file in this directory
3. Paste into issue description
4. Set title and labels as specified in the template
5. Click "Submit new issue"

### Option 2: GitHub CLI
```bash
# Install gh CLI if needed
# brew install gh  # macOS
# See: https://cli.github.com/

# Create issue from template
gh issue create \
  --title "Implement Anthropic Claude API Integration" \
  --body-file .github/ISSUES/01-anthropic-api-integration.md \
  --label "feature,api-integration,ai,high-priority"
```

### Option 3: Bulk Create Script
```bash
#!/bin/bash
# create-all-issues.sh

for file in .github/ISSUES/[0-9]*.md; do
  title=$(grep '^# ' "$file" | head -1 | sed 's/^# //')
  labels=$(grep '^\*\*Labels\*\*:' "$file" | sed 's/.*: `\(.*\)`/\1/')

  gh issue create \
    --title "$title" \
    --body-file "$file" \
    --label "$labels"

  echo "Created issue: $title"
done
```

## Issue Dependency Graph

```
Foundation (Complete) ✅
    ├── config.py
    ├── Flask-Migrate
    ├── Render deployment
    └── Database models

Parallel Development (Ready to Start)
    ├── #01: Anthropic API ─┐
    ├── #02: Brave Search ──┼─→ #03: Newsletter Synthesis
    ├── #04: Google OAuth ──┘
    ├── #05: Paddle Payments (depends on #04)
    ├── #06: Celery Setup (depends on #01, #03)
    └── #07: Comprehensive Testing (depends on all)
```

## Priority Levels

### High Priority (Start First)
1. **#01 - Anthropic API Integration** - Core AI functionality
2. **#02 - Brave Search Integration** - Web research
3. **#04 - Google OAuth** - User authentication
4. **#07 - Comprehensive Testing** - Quality assurance

### Medium Priority (After High Priority)
3. **#03 - Newsletter Synthesis** - Depends on #01 & #02
6. **#06 - Celery Task Queue** - Async processing

### Lower Priority (Polish & Monetization)
5. **#05 - Paddle Payments** - Subscription management

## Development Workflow

1. **Pick an Issue**: Choose from available issues based on dependencies
2. **Create Branch**: `git checkout -b feature/issue-N-short-description`
3. **Implement**: Follow the technical requirements in the issue
4. **Test**: Ensure tests pass and coverage targets met
5. **Format**: Run `black app/ tests/` and `ruff check .`
6. **PR**: Create pull request referencing the issue number
7. **Review**: Get code review and address feedback
8. **Merge**: Merge to main after approval

## Estimated Timeline

| Phase | Duration | Issues |
|-------|----------|--------|
| **Phase 1: Core AI** | 3-4 days | #01, #02, #03 |
| **Phase 2: Auth & Payments** | 4-5 days | #04, #05 |
| **Phase 3: Infrastructure** | 2-3 days | #06 |
| **Phase 4: Testing** | 4-5 days | #07 |
| **Total MVP** | ~14-17 days | All issues |

*Note: Timeline assumes 1-2 developers working in parallel*

## Issue Labels

- `feature` - New feature implementation
- `api-integration` - External API integration
- `ai` - AI/ML related work
- `authentication` - Auth related
- `payments` - Payment processing
- `infrastructure` - Infrastructure/DevOps
- `testing` - Test suite development
- `high-priority` - Critical for MVP
- `medium-priority` - Important but not blocking

## Completion Checklist

Each issue is complete when:
- [ ] All technical requirements implemented
- [ ] Tests written and passing
- [ ] Code coverage targets met
- [ ] Documentation updated
- [ ] Code formatted with Black
- [ ] Linting passes (Ruff)
- [ ] PR approved and merged

## Questions?

For questions about these issues or the development roadmap, please:
1. Open a discussion on GitHub
2. Comment on the relevant issue
3. Reach out to the project maintainers

---

**Last Updated**: 2026-01-01
**Status**: Ready for parallel development
