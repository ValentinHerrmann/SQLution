# Theme Switcher Documentation

This documentation explains how to use the light/dark mode theme switcher implemented for the SQLution application.

## Files Created

### CSS Files
- **`lightmode.css`** - Complete light theme styles with CSS variables
- **`darkmode.css`** - Complete dark theme styles with CSS variables  
- **`theme-switcher.css`** - Theme toggle button styles and transitions

### JavaScript File
- **`theme-switcher.js`** - Theme switching logic and functionality

## Features

### 🌓 Automatic Theme Detection
- Detects user's system preference (light/dark mode)
- Remembers user's manual theme selection
- Applies theme immediately on page load (no flash)

### 🎯 Theme Toggle Button
- Automatically adds toggle button to navbar
- Falls back to floating button if no navbar exists
- Shows current mode and switches to opposite
- Keyboard shortcut: `Ctrl/Cmd + Shift + T`

### 🎨 Comprehensive Styling
- All Bootstrap components styled for both themes
- Custom tooltips, modals, forms, tables
- Smooth transitions between themes
- Proper contrast ratios for accessibility

### 🔄 Dynamic Content Support
- Automatically applies theme to dynamically loaded content
- Works with iframes (like SQL IDE)
- Mutation observer watches for new elements

## Usage

### Automatic Integration
The theme switcher is automatically initialized when the page loads. No additional setup required.

### Manual Control
```javascript
// Toggle between light and dark mode
toggleTheme();

// Set specific theme
setTheme('dark');  // or 'light'

// Get current theme
const currentTheme = getTheme(); // returns 'light' or 'dark'

// Reset to system preference
window.themeSwitcher.resetToSystemTheme();
```

### Events
Listen for theme changes:
```javascript
window.addEventListener('themeChanged', (event) => {
    console.log('Theme changed to:', event.detail.theme);
});
```

## CSS Variable System

### Light Mode Variables
```css
:root {
  --bg-primary: #ffffff;
  --bg-secondary: #f8f9fa;
  --text-primary: #212529;
  --text-secondary: #6c757d;
  --accent-primary: #007bff;
  /* ... more variables */
}
```

### Dark Mode Variables
```css
[data-theme="dark"] {
  --bg-primary: #1a1a1a;
  --bg-secondary: #2d2d2d;
  --text-primary: #ffffff;
  --text-secondary: #b0b0b0;
  --accent-primary: #4dabf7;
  /* ... more variables */
}
```

## Customization

### Adding New Styled Elements
To style new components for both themes:

```css
/* Light mode */
[data-theme="light"] .my-component,
body:not([data-theme]) .my-component {
  background-color: var(--bg-primary);
  color: var(--text-primary);
}

/* Dark mode */
[data-theme="dark"] .my-component {
  background-color: var(--bg-primary);
  color: var(--text-primary);
}
```

### Modifying Colors
Edit the CSS variables in `lightmode.css` and `darkmode.css` to change the color scheme.

### Button Placement
The toggle button is automatically placed in the navbar. To customize:

```javascript
// Remove automatic button creation
const button = document.getElementById('theme-toggle-btn');
if (button) button.remove();

// Create custom button
const customButton = document.createElement('button');
customButton.onclick = toggleTheme;
customButton.innerHTML = 'Toggle Theme';
document.querySelector('.my-location').appendChild(customButton);
```

## Browser Support

- ✅ Chrome/Chromium 76+
- ✅ Firefox 67+
- ✅ Safari 12.1+
- ✅ Edge 79+
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## Accessibility Features

- ✅ Proper contrast ratios for both themes
- ✅ Focus indicators for keyboard navigation
- ✅ Screen reader friendly
- ✅ Respects `prefers-reduced-motion`
- ✅ High contrast mode support
- ✅ Keyboard shortcuts

## Performance

- **Minimal overhead**: ~3KB gzipped for all theme files
- **No flash**: Themes applied before content is visible
- **Cached preferences**: Themes saved in localStorage
- **Smooth transitions**: Hardware-accelerated CSS transitions

## Troubleshooting

### Theme Not Applying
1. Check browser console for JavaScript errors
2. Verify all CSS files are loaded
3. Check if `localStorage` is enabled

### Button Not Appearing
1. Verify navbar exists with class `.navbar-nav`
2. Check if theme-switcher.js is loaded
3. Look for JavaScript errors in console

### Custom Components Not Themed
Add `data-theme` attribute handling to your custom CSS:
```css
[data-theme="light"] .custom-component { /* light styles */ }
[data-theme="dark"] .custom-component { /* dark styles */ }
```

## Integration with Existing Code

The theme switcher is designed to work with existing Bootstrap and custom styles. It uses CSS attribute selectors to apply themes without conflicting with existing classes.

All theme styles are scoped to `[data-theme="light"]` and `[data-theme="dark"]` attributes, ensuring they don't interfere with existing styles.