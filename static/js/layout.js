(function () {
    'use strict';

  var STORAGE_SIDEBAR = 'starSidebarCollapsed';
  var STORAGE_THEME = 'starThemeDark';

  function initSidebarCollapse() {
    var btn = document.getElementById('sidebarCollapseBtn');
    if (localStorage.getItem(STORAGE_SIDEBAR) === 'true') {
      document.body.classList.add('sidebar-collapsed');
    }
    if (!btn) return;
    btn.addEventListener('click', function () {
      document.body.classList.toggle('sidebar-collapsed');
      localStorage.setItem(
        STORAGE_SIDEBAR,
        document.body.classList.contains('sidebar-collapsed') ? 'true' : 'false'
      );
      var icon = btn.querySelector('i');
      if (icon) {
        icon.className = document.body.classList.contains('sidebar-collapsed')
          ? 'bi bi-layout-sidebar'
          : 'bi bi-layout-sidebar-inset';
      }
    });
    if (document.body.classList.contains('sidebar-collapsed') && btn.querySelector('i')) {
      btn.querySelector('i').className = 'bi bi-layout-sidebar';
    }
  }

  function applyTheme(dark) {
    var root = document.documentElement;
    if (dark) {
      root.setAttribute('data-bs-theme', 'dark');
      document.body.classList.add('theme-dark');
    } else {
      root.removeAttribute('data-bs-theme');
      document.body.classList.remove('theme-dark');
    }
    localStorage.setItem(STORAGE_THEME, dark ? 'true' : 'false');
    syncThemeIcons();
  }

  function syncThemeIcons() {
    var dark = document.body.classList.contains('theme-dark');
    document.querySelectorAll('#darkModeToggle i').forEach(function (icon) {
      icon.className = dark ? 'bi bi-sun' : 'bi bi-moon-stars';
    });
  }

  function initDarkMode() {
    var toggle = document.getElementById('darkModeToggle');
    var dark = localStorage.getItem(STORAGE_THEME) === 'true';
    if (dark) {
      document.documentElement.setAttribute('data-bs-theme', 'dark');
      document.body.classList.add('theme-dark');
    } else {
      document.documentElement.removeAttribute('data-bs-theme');
      document.body.classList.remove('theme-dark');
    }
    syncThemeIcons();
    if (!toggle) return;
    toggle.addEventListener('click', function () {
      applyTheme(!document.body.classList.contains('theme-dark'));
    });
  }

  function initFullscreen() {
    var btn = document.getElementById('fullscreenToggle');
    if (!btn) return;
    btn.addEventListener('click', function () {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(function () {});
      } else {
        document.exitFullscreen();
      }
    });
  }

  function initSettingsLinks() {
    document.querySelectorAll('.sidebar-settings-link, .navbar-settings-link').forEach(function (el) {
      el.addEventListener('click', function (e) {
        e.preventDefault();
      });
    });
  }

  function closeOffcanvasOnNavigate() {
    var offcanvasEl = document.getElementById('mobileSidebar');
    if (!offcanvasEl) return;
    offcanvasEl.querySelectorAll('.sidebar-link, .sidebar-logout-btn').forEach(function (link) {
      link.addEventListener('click', function () {
        var instance = bootstrap.Offcanvas.getInstance(offcanvasEl);
        if (instance) instance.hide();
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initSidebarCollapse();
    initDarkMode();
    initFullscreen();
    initSettingsLinks();
    closeOffcanvasOnNavigate();
  });
})();
