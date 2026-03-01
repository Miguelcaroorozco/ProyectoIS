(() => {
  const STORAGE_KEY = 'unitecnar:sidebar:collapsed';

  function setCollapsed(collapsed) {
    document.body.classList.toggle('sidebar-collapsed', collapsed);
    try {
      localStorage.setItem(STORAGE_KEY, collapsed ? '1' : '0');
    } catch {
      // ignore
    }
  }

  function getCollapsed() {
    try {
      return localStorage.getItem(STORAGE_KEY) === '1';
    } catch {
      return false;
    }
  }

  function init() {
    setCollapsed(getCollapsed());

    document.addEventListener('click', (event) => {
      const target = event.target;
      if (!(target instanceof Element)) return;

      const toggle = target.closest('[data-sidebar-toggle]');
      if (!toggle) return;

      event.preventDefault();
      setCollapsed(!document.body.classList.contains('sidebar-collapsed'));
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
