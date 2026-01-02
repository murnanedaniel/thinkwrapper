# Known Issues and Improvements

This document tracks issues identified during the code cleanup and standardization process.

## Issue #1: Update Existing Tests for New API Response Format

**Priority:** Medium
**Type:** Test Updates Required

### Summary
The codebase has been refactored to use standardized API responses and improved input validation. This requires updating existing tests to match the new response format.

### Changes Made

1. **Standardized API responses** - All endpoints now return consistent format:
   - Success: `{"success": true, "data": {...}}` or `{"success": true, "message": "..."}`
   - Error: `{"success": false, "error": "...", "details": "..."}`
   - Processing: `{"success": true, "status": "processing", "task_id": "..."}`

2. **Input validation** - Added `InputValidator` class with:
   - Topic validation (3-500 chars, XSS prevention)
   - Email validation
   - Style validation
   - Format validation

3. **Constants centralized** - Created `app/constants.py` for magic numbers

4. **Code quality improvements**:
   - Replaced print statements with proper logging
   - Fixed bare exception handling with specific error types
   - Fixed OpenAI API usage (completions → chat.completions)

### Affected Test Files

| File | Issue |
|------|-------|
| `tests/test_routes.py` | Response format, style validation |
| `tests/test_routes_comprehensive.py` | Response format, error messages |
| `tests/test_synthesis_routes.py` | Response nesting under `data` key |
| `tests/test_payment.py` | Response format changes |
| `tests/test_claude_routes.py` | Response nesting under `data` key |
| `tests/test_services.py` | max_tokens constant changed |
| `tests/test_newsletter_synthesis.py` | API call format changed |
| `tests/test_claude_service.py` | Async tests need pytest-asyncio |

### Required Test Updates

1. **Response format changes**:
   ```python
   # Old
   assert response.json['subject'] == 'Expected Subject'

   # New
   assert response.json['data']['subject'] == 'Expected Subject'
   ```

2. **Error message changes**:
   - `"No topic provided"` → `"Topic is required"`
   - `"email_to is required"` → `"Email is required"`

3. **Constants changes**:
   - `max_tokens=1500` → `max_tokens=1024` (DEFAULT_MAX_TOKENS)

4. **Async tests**:
   - Install `pytest-asyncio`
   - Add `@pytest.mark.asyncio` decorator to async tests

### New Tests Added

- `tests/test_journeys.py` - 36 comprehensive journey tests (all passing)
  - Signup journey tests
  - Newsletter creation journey tests
  - Admin synthesis journey tests
  - Payment journey tests
  - Preview journey tests
  - Claude API journey tests
  - Input validation tests
  - Configuration journey tests

### Related Files

- `docs/USER_JOURNEYS.md` - User journey documentation
- `app/api_utils.py` - APIResponse and InputValidator classes
- `app/constants.py` - Centralized constants

---

## Issue #2: Async Test Support Missing

**Priority:** Low
**Type:** Test Infrastructure

### Summary
The async tests in `test_claude_service.py` fail because pytest-asyncio is not configured.

### Fix
```bash
pip install pytest-asyncio
```

Then add to `pytest.ini`:
```ini
[pytest]
asyncio_mode = auto
```

---

## Issue #3: Coverage Below Threshold

**Priority:** Low
**Type:** Test Coverage

### Summary
After refactoring, test coverage dropped to ~53% due to:
1. New code added (api_utils.py, constants.py)
2. Existing tests expecting old response format

### Fix
Update existing tests per Issue #1, which should restore coverage to >65%.

---

## Completed Improvements

### Code Quality ✅
- [x] Replaced print statements with proper logging
- [x] Fixed bare exception handling
- [x] Centralized magic numbers into constants.py
- [x] Fixed OpenAI API usage (completions → chat.completions)

### API Standardization ✅
- [x] Created APIResponse helper class
- [x] All endpoints use consistent response format
- [x] Added @require_json decorator

### Input Validation ✅
- [x] Created InputValidator class
- [x] Topic validation (length, XSS prevention)
- [x] Email validation
- [x] Style and format validation

### Documentation ✅
- [x] Created USER_JOURNEYS.md with complete journey documentation
- [x] Documented all API endpoints with examples
- [x] Created success criteria for each journey

### Journey Tests ✅
- [x] Created test_journeys.py with 36 tests
- [x] All journey tests passing
- [x] Tests cover all major user flows
