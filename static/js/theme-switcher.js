/**
 * BattyCoda Theme Switcher
 * Allows users to switch between different Maisonnette themes
 * Works for both authenticated and non-authenticated users
 */

document.addEventListener('DOMContentLoaded', function() {
    // Constants
    const LOCAL_STORAGE_THEME_KEY = 'battycoda_theme';
    const mainBody = document.getElementById('main-body');
    
    // Get theme switcher links
    const themeSwitcherLinks = document.querySelectorAll('.theme-switcher-link');
    
    // Check if user is authenticated (look for logout link)
    const isAuthenticated = document.getElementById('logoutLink') !== null;
    
    // If not authenticated, apply theme from localStorage if available
    if (!isAuthenticated) {
        const savedTheme = localStorage.getItem(LOCAL_STORAGE_THEME_KEY);
        if (savedTheme) {
            applyTheme(savedTheme);
            
            // Update active state in dropdown
            themeSwitcherLinks.forEach(link => {
                if (link.dataset.theme === savedTheme) {
                    link.classList.add('active');
                }
            });
        }
    }
    
    // Add click event to each theme switcher link
    themeSwitcherLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Get theme name from data attribute
            const themeName = this.dataset.theme;
            
            if (isAuthenticated) {
                // For authenticated users, update theme preference via Ajax
                updateThemePreference(themeName);
            } else {
                // For non-authenticated users, save theme to localStorage
                localStorage.setItem(LOCAL_STORAGE_THEME_KEY, themeName);
            }
            
            // Apply theme immediately
            applyTheme(themeName);
            
            // Update active state in dropdown
            themeSwitcherLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    /**
     * Update theme preference in user profile via Ajax (for authenticated users)
     */
    function updateThemePreference(themeName) {
        // Get CSRF token from cookie
        const csrftoken = getCookie('csrftoken');
        
        // Send Ajax request to update theme preference
        fetch('/update_theme_preference/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({
                theme: themeName
            })
        })
        .then(response => {
            if (!response.ok) {
                console.error('Failed to update theme preference');
            }
        })
        .catch(error => {
            console.error('Error updating theme preference:', error);
        });
    }
    
    /**
     * Apply theme by adding/removing CSS classes and loading theme CSS
     */
    function applyTheme(themeName) {
        // Remove all theme classes from body
        mainBody.className = mainBody.className
            .replace(/theme-[a-z-]+/g, '')
            .trim();
        
        // Add new theme class to body
        mainBody.classList.add(`theme-${themeName}`);
        
        // Only load theme CSS if it's not the default theme
        if (themeName !== 'default') {
            // Check if theme CSS is already loaded
            const themeId = `theme-css-${themeName}`;
            let themeLink = document.getElementById(themeId);
            
            // If CSS not loaded yet, load it
            if (!themeLink) {
                // Create link element for theme CSS
                themeLink = document.createElement('link');
                themeLink.id = themeId;
                themeLink.rel = 'stylesheet';
                themeLink.href = `/static/css/themes/${themeName}.css`;
                
                // Add to head
                document.head.appendChild(themeLink);
            }
        }
        
        // If switching from another theme to default, remove all theme CSS files
        if (themeName === 'default') {
            // Get all theme CSS link elements
            document.querySelectorAll('link[id^="theme-css-"]').forEach(link => {
                // Remove the link element
                link.parentNode.removeChild(link);
            });
        }
    }
    
    /**
     * Get cookie by name (for CSRF token)
     */
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});