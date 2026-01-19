# BattyCoda Testing Guide

This guide covers all testing approaches: Python/Django tests, JavaScript unit tests, and end-to-end tests.

## Python Tests (Django)

### Running Tests
```bash
source venv/bin/activate

# Run all tests
python manage.py test

# Run specific test class
python manage.py test battycoda_app.tests.TestClassName

# Run specific test method
python manage.py test battycoda_app.tests.TestClassName.test_method_name

# Run specific test modules
python manage.py test battycoda_app.tests.test_clustering  # Project-level clustering tests
python manage.py test battycoda_app.tests.test_models      # Model tests
python manage.py test battycoda_app.tests.test_views_auth  # Auth view tests
```

### Test File Location
Tests are in `battycoda_app/tests/`:
```
battycoda_app/tests/
├── __init__.py
├── test_models.py
├── test_views_auth.py
├── test_clustering.py
└── ...
```

### Python Linting
```bash
./lint.sh         # Check code quality
./format.sh       # Auto-format with black and isort
```

## JavaScript Unit Tests (Vitest)

Unit tests use Vitest with jsdom for DOM testing.

### Running Tests
```bash
npm test            # Run tests in watch mode
npm run test:run    # Run tests once
npm run test:coverage  # Run with coverage
npm run test:ui     # Open Vitest UI
```

### Test File Location
Place `.test.js` files next to the module they test:
```
static/js/
├── utils/
│   ├── page-data.js
│   └── page-data.test.js    # Tests for page-data.js
├── player/
│   ├── data_manager.js
│   └── data_manager.test.js
```

### Test Setup Files
`static/js/test/` contains:
- `setup.js` - Global test configuration
- `fixtures/` - Test data fixtures
- `mocks/` - Mock implementations

### Writing Tests
```javascript
import { describe, it, expect, vi } from 'vitest';
import { myFunction } from './mymodule.js';

describe('myFunction', () => {
  it('should return expected value', () => {
    expect(myFunction(input)).toBe(expected);
  });
});
```

## E2E Tests (Playwright)

End-to-end tests for full user workflows.

### Running Tests
```bash
npm run e2e           # Run E2E tests
npm run e2e:headed    # Run with browser visible
npm run e2e:ui        # Open Playwright UI
npm run e2e:report    # View test report
npm run e2e:chromium  # Run specific browser
```

### Test File Location
```
tests/e2e/
├── global-setup.js          # Database setup before tests
├── global-teardown.js       # Cleanup after tests
├── fixtures/                # Test data and state
├── helpers/                 # Shared test utilities
│   ├── auth.js              # Login helpers
│   └── theme.js             # Theme switching helpers
└── specs/                   # Test files
    ├── smoke.spec.js        # Basic smoke tests
    ├── auth.spec.js         # Authentication tests
    ├── visual.spec.js       # Visual regression tests
    └── ...
```

Note: Playwright config is at `playwright.config.js` in project root.

### Writing E2E Tests
```javascript
import { test, expect } from '@playwright/test';
import { login } from '../helpers/auth.js';

test('user can view dashboard', async ({ page }) => {
  await login(page, 'test@example.com', 'password');
  await page.goto('/dashboard/');
  await expect(page.locator('h1')).toContainText('Dashboard');
});
```

### Test Database Setup

E2E tests use a separate test database (`battycoda_test`).

**Initial Setup (one-time):**
```bash
sudo -u postgres psql -c "CREATE DATABASE battycoda_test OWNER battycoda;"
```

**Database Management:**
```bash
npm run e2e:setup-db   # Set up test database with initial data
npm run e2e:reset-db   # Reset test database (clears all data)
```

**Environment Variable:**
- `DJANGO_TEST_MODE=true` - Set automatically by E2E test scripts

## Visual Regression Testing

Visual regression tests capture screenshots and compare against baselines.

### Running Visual Tests
```bash
# Run visual regression tests
npx playwright test tests/e2e/specs/visual.spec.js

# Update baselines after intentional UI changes
npx playwright test tests/e2e/specs/visual.spec.js --update-snapshots
```

### Baseline Location
`tests/e2e/specs/visual.spec.js-snapshots/`

### Pages Covered
- Login page (light + dark themes)
- Registration page (light + dark themes)
- Home/Dashboard (light + dark themes)
- Recordings list (light + dark themes)
- Projects list (light + dark themes)
- Clustering dashboard (light + dark themes)
- Create clustering run (light + dark themes)

### Theme Testing Helpers
```javascript
import { setTheme, applyTheme } from '../helpers/theme.js';

// Set theme before navigation (via localStorage)
await setTheme(page, 'dark');
await page.goto('/some-page/');

// Apply theme after page is loaded
await applyTheme(page, 'dark');
```

### When to Update Baselines
- After intentional CSS/styling changes
- After layout changes
- After component redesigns
- **Never** commit baseline updates without reviewing the diffs

### Adding New Visual Tests
1. Add test to `tests/e2e/specs/visual.spec.js`
2. Run with `--update-snapshots` to create baseline
3. Commit the new baseline PNG files

## Testing Checklist (New Features)

Before enabling a feature in production:
- [ ] Python unit tests pass
- [ ] JavaScript unit tests pass
- [ ] E2E tests pass for this feature
- [ ] Manual testing on staging
- [ ] Performance comparison (bundle size, load time)
- [ ] No console errors
- [ ] All browsers tested
