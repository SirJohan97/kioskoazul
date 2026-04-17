/**
 * admin-shared.js — Kiosko Azul Admin Panel
 * Sidebar toggle logic for mobile navigation.
 * Works with the .admin-hamburger button hardcoded in each page's topbar.
 */

(function () {
  // Inject the dark overlay into the body (once)
  var overlay = document.createElement('div');
  overlay.id = 'sidebar-overlay';
  overlay.className = 'sidebar-overlay';
  document.body.appendChild(overlay);

  // Close when tapping the overlay
  overlay.addEventListener('click', closeSidebar);

  // Close when navigating (any nav-link click)
  document.querySelectorAll('.nav-link').forEach(function(link) {
    link.addEventListener('click', closeSidebar);
  });

  // Global functions — called directly from onclick=""
  window.toggleSidebar = function() {
    var sidebar = document.getElementById('sidebar');
    if (!sidebar) return;
    if (sidebar.classList.contains('open')) {
      closeSidebar();
    } else {
      openSidebar();
    }
  };

  function openSidebar() {
    var sidebar = document.getElementById('sidebar');
    if (sidebar) sidebar.classList.add('open');
    overlay.classList.add('show');
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    var sidebar = document.getElementById('sidebar');
    if (sidebar) sidebar.classList.remove('open');
    overlay.classList.remove('show');
    document.body.style.overflow = '';
  }

  window.closeSidebar = closeSidebar;
  window.openSidebar = openSidebar;
})();
