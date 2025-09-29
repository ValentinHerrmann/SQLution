/* ===== THEME SWITCHER JAVASCRIPT ===== */

class ThemeSwitcher {
    constructor() {
        this.currentTheme = localStorage.getItem('theme') || 'light';
        this.init();
    }

    init() {
        console.log('ThemeSwitcher init() called'); // Debug log
        
        // Apply saved theme immediately
        this.applyTheme(this.currentTheme);
        
        // Create theme toggle button if it doesn't exist
        this.createToggleButton();
        
        // Listen for theme toggle events
        this.setupEventListeners();
        
        // Listen for system theme changes
        this.setupSystemThemeListener();
        
        // Apply theme to dynamically loaded content
        this.setupMutationObserver();
        
        console.log('ThemeSwitcher init() completed'); // Debug log
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        document.body.setAttribute('data-theme', theme);
        
        // Also apply to any iframes (like SQL IDE)
        const iframes = document.querySelectorAll('iframe');
        iframes.forEach(iframe => {
            try {
                if (iframe.contentDocument) {
                    iframe.contentDocument.documentElement.setAttribute('data-theme', theme);
                    iframe.contentDocument.body.setAttribute('data-theme', theme);
                }
            } catch (e) {
                console.log('Cannot access iframe content:', e);
            }
        });
        
        this.currentTheme = theme;
        localStorage.setItem('theme', theme);

        if (apollon) {
            apollon.setTheming(theme);
        }
        
        // Update toggle button text and icon
        this.updateToggleButton();
        
        // Dispatch custom event for other components
        window.dispatchEvent(new CustomEvent('themeChanged', { 
            detail: { theme: theme } 
        }));
    }

    toggleTheme() {
        console.log('toggleTheme called, current theme:', this.currentTheme); // Debug log
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        console.log('Switching to theme:', newTheme); // Debug log
        this.applyTheme(newTheme);
    }

    createToggleButton() {
        // Check if toggle switch container already exists in the template
        const existingContainer = document.getElementById('theme-toggle-btn');
        if (existingContainer) {
            // Replace existing container with new toggle switch design
            const toggleSwitch = this.createToggleSwitchHTML();
            existingContainer.outerHTML = toggleSwitch;
            console.log('Theme container replaced with toggle switch'); // Debug log
            return;
        }

        console.warn('No theme toggle container found in template'); // Debug log
        
        // Create toggle switch as fallback if not in template
        const toggleSwitchHTML = this.createToggleSwitchHTML();
        
        // Try to add to navbar first
        const navbar = document.querySelector('.navbar-nav .nav-item');
        if (navbar) {
            navbar.insertAdjacentHTML('afterbegin', toggleSwitchHTML);
            console.log('Theme toggle added to navbar as fallback'); // Debug log
        } else {
            // Try to add to any navbar
            const anyNavbar = document.querySelector('.navbar-nav');
            if (anyNavbar) {
                const li = document.createElement('li');
                li.className = 'nav-item d-flex align-items-center';
                li.innerHTML = toggleSwitchHTML;
                anyNavbar.appendChild(li);
                console.log('Theme toggle added to navbar with new li element'); // Debug log
            } else {
                // Last resort: add to body
                document.body.insertAdjacentHTML('beforeend', `
                    <div style="position: fixed; top: 10px; right: 10px; z-index: 9999;">
                        ${toggleSwitchHTML}
                    </div>
                `);
                console.log('Theme toggle added to body as floating element'); // Debug log
            }
        }
    }

    createToggleSwitchHTML() {
        const currentIcon = this.currentTheme === 'light' ? 'fas fa-sun' : 'fas fa-moon';
        
        return `
            <div class="theme-toggle-switch" id="theme-toggle-btn">
                <div class="toggle-track">
                    <div class="toggle-slider">
                        <i class="${currentIcon} toggle-slider-icon"></i>
                    </div>
                </div>
            </div>
        `;
    }



    updateToggleButton() {
        const toggleSwitch = document.getElementById('theme-toggle-btn');
        if (toggleSwitch) {
            const sliderIcon = toggleSwitch.querySelector('.toggle-slider-icon');
            
            if (sliderIcon) {
                // Update icon based on current theme
                if (this.currentTheme === 'light') {
                    sliderIcon.className = 'fas fa-sun toggle-slider-icon';
                } else {
                    sliderIcon.className = 'fas fa-moon toggle-slider-icon';
                }
            }
        }
    }

    setupEventListeners() {
        // Theme toggle switch click - simplified for new compact design
        document.addEventListener('click', (e) => {
            // Check if the clicked element or any parent is the theme toggle switch
            const themeSwitch = e.target.closest('#theme-toggle-btn') || 
                               (e.target.id === 'theme-toggle-btn' ? e.target : null);
            
            if (themeSwitch) {
                e.preventDefault();
                e.stopPropagation();
                console.log('Theme toggle clicked'); // Debug log
                this.toggleTheme();
            }
        });

        // Keyboard shortcut (Ctrl/Cmd + Shift + T)
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'T') {
                e.preventDefault();
                this.toggleTheme();
            }
        });
    }

    setupSystemThemeListener() {
        // Listen for system theme changes
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.addEventListener('change', (e) => {
                // Only auto-switch if user hasn't manually set a preference
                if (!localStorage.getItem('theme-manually-set')) {
                    const newTheme = e.matches ? 'dark' : 'light';
                    this.applyTheme(newTheme);
                }
            });
        }
    }

    setupMutationObserver() {
        // Watch for dynamically added content
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            // Apply theme to new elements
                            this.applyThemeToElement(node);
                        }
                    });
                }
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    applyThemeToElement(element) {
        // Apply theme attributes to new elements
        if (element.tagName && element.setAttribute) {
            element.setAttribute('data-theme', this.currentTheme);
        }
        
        // Apply to child elements
        const children = element.querySelectorAll('*');
        children.forEach(child => {
            if (child.setAttribute) {
                child.setAttribute('data-theme', this.currentTheme);
            }
        });
    }

    // Public method to manually set theme
    setTheme(theme) {
        if (theme === 'light' || theme === 'dark') {
            localStorage.setItem('theme-manually-set', 'true');
            this.applyTheme(theme);
        }
    }

    // Public method to get current theme
    getTheme() {
        return this.currentTheme;
    }

    // Public method to reset to system preference
    resetToSystemTheme() {
        localStorage.removeItem('theme-manually-set');
        localStorage.removeItem('theme');
        
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            this.applyTheme('dark');
        } else {
            this.applyTheme('light');
        }
    }
}

// Auto-initialize theme switcher when DOM is ready
function initThemeSwitcher() {
    console.log('Initializing theme switcher...'); // Debug log
    
    // Apply saved theme immediately, even if container is not found yet
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    document.body.setAttribute('data-theme', savedTheme);
    console.log('Applied saved theme:', savedTheme); // Debug log
    
    const container = document.getElementById('theme-toggle-btn');
    console.log('Theme toggle container found:', container); // Debug log
    
    if (container) {
        window.themeSwitcher = new ThemeSwitcher();
        console.log('Theme switcher initialized successfully'); // Debug log
    } else {
        console.warn('Theme toggle container not found, retrying...'); // Debug log
        // Try multiple times with increasing delays
        let retryCount = 0;
        const maxRetries = 5;
        
        const retryInit = () => {
            retryCount++;
            console.log(`Retry attempt ${retryCount}/${maxRetries}...`); // Debug log
            
            const retryContainer = document.getElementById('theme-toggle-btn');
            if (retryContainer) {
                window.themeSwitcher = new ThemeSwitcher();
                console.log('Theme switcher initialized on retry'); // Debug log
            } else if (retryCount < maxRetries) {
                setTimeout(retryInit, retryCount * 200); // Increasing delay
            } else {
                console.error('Theme toggle container still not found after all retries!'); // Debug log
                // Initialize without UI, at least theme switching will work
                window.themeSwitcher = new ThemeSwitcher();
                console.log('Theme switcher initialized without UI container'); // Debug log
            }
        };
        
        setTimeout(retryInit, 100);
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initThemeSwitcher);
} else {
    // DOM is already loaded, but let's wait a bit for all elements to be ready
    setTimeout(initThemeSwitcher, 100);
}

// Expose theme switcher globally
window.ThemeSwitcher = ThemeSwitcher;

// Helper functions for manual integration
window.toggleTheme = function() {
    if (window.themeSwitcher) {
        window.themeSwitcher.toggleTheme();
    }
};

window.setTheme = function(theme) {
    if (window.themeSwitcher) {
        window.themeSwitcher.setTheme(theme);
    }
};

window.getTheme = function() {
    if (window.themeSwitcher) {
        return window.themeSwitcher.getTheme();
    }
    return 'light';
};

// CSS injection for critical styles (prevents flash of unstyled content)
const criticalCSS = `
    * { transition: none !important; }
    body { visibility: hidden; }
    [data-theme="light"] body, body:not([data-theme]) { visibility: visible; }
    [data-theme="dark"] body { visibility: visible; }
`;

// Inject critical CSS immediately
const style = document.createElement('style');
style.textContent = criticalCSS;
document.head.appendChild(style);

// Remove critical CSS after theme is applied
setTimeout(() => {
    style.remove();
}, 100);