# BattyCoda Frontend Development Guide

This guide covers frontend development including the build system, theming, TypeScript, and JavaScript modules.

## Node.js Environment

This project requires Node.js 22.x or later for Vite and frontend tooling.

**Using nvm (recommended):**
```bash
# Install nvm if not already installed
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Install and use correct Node version (reads from .nvmrc)
nvm install
nvm use
```

**Using system package manager:**
```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**Verify installation:**
```bash
node --version  # Should be v22.x.x
npm --version   # Should be v10.x.x
```

The `.npmrc` file enforces strict engine checking.

## Frontend Stack

BattyCoda uses Bootstrap 5.3 with a custom light/dark theme system.

- **Bootstrap**: 5.3.x via CDN
- **Icons**: Font Awesome 6.x via CDN
- **Themes**: Light and Dark modes using CSS custom properties
- **Build**: Vite for JS/CSS bundling

### Migration History
- **Pre-2026**: Bootstrap 4.3.1 + Maisonnette admin theme v1.3.2
- **Jan 2026**: Migrated to Bootstrap 5.3, removed Maisonnette (discontinued)
- **Jan 2026**: Simplified from 7 color themes to light/dark only

## Theme System

Two themes available: `light` (default) and `dark`. Users can toggle via navbar dropdown.

**Theme Files:**
- `static/css/themes/light.css` - Light theme (teal/green accent #20c997)
- `static/css/themes/dark.css` - Dark theme (adjusted colors for dark backgrounds)
- `static/css/themes.css` - Theme switcher dropdown styling

**How it works:**
1. Theme CSS loaded dynamically via `{% vite_theme_css theme_name %}`
2. Body gets class `theme-light` or `theme-dark`
3. Theme-switcher.js handles runtime switching and localStorage persistence
4. User preference saved to database for authenticated users

**Adding theme support to new CSS:**
```css
/* Use CSS variables that change with theme */
.my-component {
  background-color: var(--bc-card-bg);
  border-color: var(--bc-card-border);
  color: var(--bs-body-color);
}

/* Or use theme-specific overrides */
body.theme-dark .my-component {
  /* dark-mode specific styles */
}
```

## Bootstrap 5 Reference

### Common Utility Classes (BS5 naming)
- **Spacing**: `me-*`, `ms-*`, `pe-*`, `ps-*` (margin/padding end/start)
- **Floats**: `float-end`, `float-start`
- **Text**: `text-end`, `text-start`
- **Gaps**: `gap-*`, `row-gap-*`, `column-gap-*`
- **Visibility**: `visually-hidden` (replaces `sr-only`)

### Data Attributes
BS5 uses `data-bs-*` prefix:
```html
data-bs-toggle="dropdown"   <!-- not data-toggle -->
data-bs-dismiss="modal"     <!-- not data-dismiss -->
data-bs-target="#myModal"   <!-- not data-target -->
```

### JavaScript API
BS5 doesn't require jQuery. Access components via:
```javascript
// Modal
const modal = new bootstrap.Modal(document.getElementById('myModal'));
modal.show();

// Tooltip
const tooltipList = [...document.querySelectorAll('[data-bs-toggle="tooltip"]')]
  .map(el => new bootstrap.Tooltip(el));
```

## Vite Build System

BattyCoda uses Vite for JavaScript bundling and development.

### Directory Structure
```
static/
├── js/
│   ├── main.js              # Main entry point
│   ├── types/               # TypeScript type definitions
│   ├── utils/               # Shared utilities
│   ├── player/              # Waveform player module
│   ├── cluster_explorer/    # Clustering visualization
│   ├── cluster_mapping/     # Cluster-to-call mapping
│   ├── file_upload/         # File upload handling
│   ├── segmentation/        # Segmentation module
│   └── test/                # Test setup, fixtures, mocks
├── css/
│   ├── main.css             # CSS entry point
│   └── themes/              # Theme CSS files
└── dist/                    # Built output (gitignored)
```

### Build Commands
```bash
npm run dev           # Start Vite dev server (port 5173)
npm run build         # Build for production
npm run build:watch   # Build with watch mode
npm run preview       # Preview production build
```

### CSS Bundling

CSS is processed through Vite with PostCSS for autoprefixing and minification.

**Entry Points:**
- `static/css/main.css` - Main CSS bundle
- `static/css/themes/light.css` - Light theme
- `static/css/themes/dark.css` - Dark theme

**Key Files:**
- `static/css/app.css` - Minimal core styles
- `postcss.config.js` - PostCSS configuration
- `vite.config.js` - Vite config with CSS entry points
- `battycoda_app/templatetags/vite.py` - Custom template tags

**Template Tags:**
```html
{% load vite %}
{% vite_css 'styles' %}           <!-- Load main CSS bundle -->
{% vite_theme_css 'light' %}      <!-- Load light theme CSS -->
{% vite_theme_css 'dark' %}       <!-- Load dark theme CSS -->
{% vite_theme_urls %}             <!-- Inject theme URL mapping for JS -->
```

### Adding New JavaScript Modules

1. Create module in appropriate directory:
   ```javascript
   // static/js/feature/mymodule.js
   export function myFunction() { ... }
   ```

2. Add entry point in `vite.config.js` if needed:
   ```javascript
   rollupOptions: {
     input: {
       myFeature: resolve(__dirname, 'static/js/feature/index.js'),
     }
   }
   ```

3. Load in Django template:
   ```html
   {% load vite %}
   {% vite_asset 'myFeature.js' %}
   ```

### Accessing Django Data in JavaScript

Use data attributes pattern (not inline scripts):

```html
<!-- In template -->
<div id="app-data"
     data-recording-id="{{ recording.id }}"
     data-api-url="{% url 'api:endpoint' %}"
     style="display: none;">
</div>
```

```javascript
// In JavaScript
import { getPageData } from './utils/page-data.js';
const { recordingId, apiUrl } = getPageData();
```

### External Dependencies (CDN vs Bundled)

**CDN (External)** - Loaded via CDN in Django templates:
| Library | Version | Reason |
|---------|---------|--------|
| jQuery | 3.3.1 | Deep integration, plugin ecosystem |
| Bootstrap JS | 5.3.3 | Tied to jQuery, used for modals/dropdowns |
| Toastr | latest | Simple toast notifications |
| Select2 | 4.1.0 | jQuery-based select dropdowns |
| Perfect Scrollbar | 1.5.0 | Minimal usage |

**Bundled (npm)** - Tree-shaking via Vite:
| Library | Reason |
|---------|--------|
| D3.js | Heavy usage in cluster visualization |

## Feature Flag System

Each JavaScript feature can be migrated independently using feature flags.

**Configuration (settings.py or .env):**
```python
VITE_ENABLED = True  # Master switch
VITE_FEATURES = {
    'theme_switcher': True,   # Migrated
    'notifications': False,   # Not yet
    # ...
}
```

**Available flags:**
- `VITE_FEATURE_THEME_SWITCHER`
- `VITE_FEATURE_NOTIFICATIONS`
- `VITE_FEATURE_DATETIME_FORMATTER`
- `VITE_FEATURE_FILE_UPLOAD`
- `VITE_FEATURE_CLUSTER_EXPLORER`
- `VITE_FEATURE_CLUSTER_MAPPING`
- `VITE_FEATURE_PLAYER`
- `VITE_FEATURE_TASK_ANNOTATION`
- `VITE_FEATURE_SEGMENTATION`

**Templates check flags:**
```html
{% if not VITE_FEATURES.theme_switcher %}
<script src="{% static 'js/theme-switcher.js' %}"></script>
{% endif %}
```

### Rollback Procedures

**Level 1: Disable Single Feature**
```bash
# In .env:
VITE_FEATURE_THEME_SWITCHER=false
sudo systemctl restart battycoda
```

**Level 2: Disable All Vite**
```bash
VITE_ENABLED=false
sudo systemctl restart battycoda
```

**Level 3: Full Revert**
```bash
git log --oneline  # Find pre-Vite commit
git revert HEAD~n..HEAD
sudo systemctl restart battycoda
```

## TypeScript Support

Vite handles TypeScript compilation automatically.

### Strategy: Gradual Adoption
- **New files**: Write in TypeScript (`.ts` extension)
- **Existing files**: Keep as JavaScript unless refactoring
- **Strictness**: Start permissive, increase over time

### Type Checking
```bash
npm run typecheck        # Check types
npm run typecheck:watch  # Watch mode
```

### Configuration
TypeScript is configured in `tsconfig.json` with permissive settings:
- `strict: false` - Not enforcing strict type checking yet
- `allowJs: true` - Mix JavaScript and TypeScript freely
- `checkJs: false` - Don't type-check JavaScript files
- `noEmit: true` - Vite handles compilation

### Type Definitions
Types are organized in `static/js/types/`:
```
static/js/types/
├── global.d.ts    # Window extensions, jQuery, Bootstrap, Toastr
├── models.d.ts    # Domain model types (Recording, Cluster, etc.)
├── api.d.ts       # API response types
└── index.ts       # Central export point
```

Import types from the central export:
```typescript
import type { Cluster, Recording, ApiResponse } from '@/types';
```

### Writing TypeScript

**New utility module:**
```typescript
// static/js/utils/myutil.ts
import type { Recording } from '@/types';

export function processRecording(recording: Recording): string {
  return `${recording.name} (${recording.duration}s)`;
}
```

### When to Use TypeScript
**Use for:** New utility modules, complex data transformations, API client code
**Keep JS for:** Simple scripts, heavily DOM-dependent code, existing code

### Increasing Strictness
Enable stricter checks in `tsconfig.json` as the team becomes comfortable:
```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true
  }
}
```

## JavaScript Linting

```bash
npm run lint          # Lint JavaScript
npm run lint:fix      # Auto-fix lint issues
npm run format        # Format with Prettier
npm run format:check  # Check formatting
```

ESLint config is in `eslint.config.js` (flat config format).

## Key Files Reference

- `config/settings.py` - VITE_ENABLED, VITE_FEATURES settings
- `battycoda_app/context_processors.py` - vite_features context processor
- `battycoda_app/templatetags/vite.py` - Custom template tags for CSS loading
- `templates/base.html` - Conditional script loading
- `vite.config.js` - Vite configuration
- `tsconfig.json` - TypeScript configuration
- `postcss.config.js` - PostCSS configuration
- `eslint.config.js` - ESLint configuration
