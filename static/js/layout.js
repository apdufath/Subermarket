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

  function initDarkMode() {
    var toggle = document.getElementById('darkModeToggle');
    if (localStorage.getItem(STORAGE_THEME) === 'true') {
      document.body.classList.add('theme-dark');
    }
    if (!toggle) return;
    toggle.addEventListener('click', function () {
      document.body.classList.toggle('theme-dark');
      var isDark = document.body.classList.contains('theme-dark');
      localStorage.setItem(STORAGE_THEME, isDark ? 'true' : 'false');
      var icon = toggle.querySelector('i');
      if (icon) {
        icon.className = isDark ? 'bi bi-sun' : 'bi bi-moon-stars';
      }
    });
    var icon = toggle.querySelector('i');
    if (icon && document.body.classList.contains('theme-dark')) {
      icon.className = 'bi bi-sun';
    }
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
