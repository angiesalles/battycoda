/**
 * Theme Switcher Module
 *
 * Allows users to switch between different Maisonnette themes.
 * Works for both authenticated and non-authenticated users.
 */

const LOCAL_STORAGE_THEME_KEY = 'battycoda_theme';

/**
 * Get a cookie value by name
 * @param {string} name - Cookie name
 * @returns {string|null} Cookie value or null
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === name + '=') {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Update theme preference on server for authenticated users
 * @param {string} themeName - Theme name to save
 */
function updateThemePreference(themeName) {
    const csrftoken = getCookie('csrftoken');

    fetch('/update_theme_preference/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({ theme: themeName }),
    })
        .then((response) => {
            if (!response.ok) {
                console.error('Failed to update theme preference');
            }
        })
        .catch((error) => {
            console.error('Error updating theme preference:', error);
        });
}

/**
 * Apply a theme by adding/removing CSS classes and loading theme CSS
 * @param {string} themeName - Theme name to apply
 */
export function applyTheme(themeName) {
    const mainBody = document.getElementById('main-body');
    if (!mainBody) return;

    // Remove all theme classes from body
    mainBody.className = mainBody.className.replace(/theme-[a-z-]+/g, '').trim();

    // Add new theme class to body
    mainBody.classList.add(`theme-${themeName}`);

    // Only load theme CSS if it's not the default theme
    if (themeName !== 'default') {
        const themeId = `theme-css-${themeName}`;
        let themeLink = document.getElementById(themeId);

        if (!themeLink) {
            themeLink = document.createElement('link');
            themeLink.id = themeId;
            themeLink.rel = 'stylesheet';
            themeLink.href = `/static/css/themes/${themeName}.css`;
            document.head.appendChild(themeLink);
        }
    }

    // If switching to default, remove all theme CSS files
    if (themeName === 'default') {
        document.querySelectorAll('link[id^="theme-css-"]').forEach((link) => {
            link.parentNode.removeChild(link);
        });
    }
}

/**
 * Initialize the theme switcher
 */
export function initialize() {
    const mainBody = document.getElementById('main-body');
    const themeSwitcherLinks = document.querySelectorAll('.theme-switcher-link');

    if (!mainBody) return;

    // Check if user is authenticated
    const isAuthenticated = document.getElementById('logoutLink') !== null;

    // If not authenticated, apply theme from localStorage
    if (!isAuthenticated) {
        const savedTheme = localStorage.getItem(LOCAL_STORAGE_THEME_KEY);
        if (savedTheme) {
            applyTheme(savedTheme);

            // Update active state in dropdown
            themeSwitcherLinks.forEach((link) => {
                if (link.dataset.theme === savedTheme) {
                    link.classList.add('active');
                }
            });
        }
    }

    // Add click event to each theme switcher link
    themeSwitcherLinks.forEach((link) => {
        link.addEventListener('click', function (e) {
            e.preventDefault();

            const themeName = this.dataset.theme;

            if (isAuthenticated) {
                updateThemePreference(themeName);
            } else {
                localStorage.setItem(LOCAL_STORAGE_THEME_KEY, themeName);
            }

            applyTheme(themeName);

            // Update active state in dropdown
            themeSwitcherLinks.forEach((l) => l.classList.remove('active'));
            this.classList.add('active');
        });
    });
}

// Auto-initialize on DOMContentLoaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize);
} else {
    initialize();
}

// Expose globally for potential external use
window.applyTheme = applyTheme;
