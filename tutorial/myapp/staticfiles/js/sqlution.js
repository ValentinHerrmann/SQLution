/*
  sqlution.js — aggregator module

  Importing this single file in a template (as a module) behaves like including
  all scripts from the `staticfiles/js/` directory.

  Usage in template:
    <script type="module" src="{% static 'js/sqlution.js' %}"></script>

*/

// Import all JS modules from this directory
// These will execute in order and load their dependencies
import './dev-server-banner.js';
import './theme-switcher.js';
import './dialogs.js';
import './sql_ide.js';
