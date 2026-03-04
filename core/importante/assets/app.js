(() => {
  const STORAGE_KEY = 'unitecnar:sidebar:collapsed';
  const THEME_KEY = 'unitecnar:theme';

  let currentTheme = 'light';

  function getSavedTheme() {
    try {
      const value = localStorage.getItem(THEME_KEY);
      if (value === 'dark' || value === 'light') return value;
      return null;
    } catch {
      return null;
    }
  }

  function getDefaultTheme() {
    try {
      return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light';
    } catch {
      return 'light';
    }
  }

  function saveTheme(theme) {
    try {
      localStorage.setItem(THEME_KEY, theme);
    } catch {
      // ignore
    }
  }

  function applyThemeToUI(theme) {
    document.body.classList.toggle('theme-dark', theme === 'dark');

    document.querySelectorAll('[data-theme-toggle]').forEach((toggle) => {
      if (toggle instanceof HTMLInputElement && toggle.type === 'checkbox') {
        toggle.checked = theme === 'dark';
      }

      if (toggle instanceof HTMLButtonElement) {
        toggle.setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false');
        toggle.title = theme === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro';
      }
    });
  }

  function setTheme(theme) {
    currentTheme = theme;
    saveTheme(theme);
    applyThemeToUI(theme);
  }

  function toggleTheme() {
    setTheme(currentTheme === 'dark' ? 'light' : 'dark');
  }

  function applyPhotoToUI(dataUrl) {
    const avatars = document.querySelectorAll('.avatar');
    avatars.forEach((avatar) => {
      if (!(avatar instanceof HTMLElement)) return;

      if (dataUrl) {
        avatar.style.backgroundImage = `url(${dataUrl})`;
        avatar.classList.add('has-photo');
      } else {
        avatar.style.backgroundImage = '';
        avatar.classList.remove('has-photo');
      }
    });

    const photoPreview = document.querySelector('[data-profile-photo-preview]');
    if (photoPreview instanceof HTMLImageElement) {
      if (dataUrl) {
        photoPreview.src = dataUrl;
        photoPreview.style.display = '';
      } else {
        photoPreview.removeAttribute('src');
        photoPreview.style.display = 'none';
      }
    }
  }

  function applyAvatarFromServer() {
    const avatars = document.querySelectorAll('.avatar[data-avatar-url]');
    avatars.forEach((avatar) => {
      if (!(avatar instanceof HTMLElement)) return;
      const url = avatar.getAttribute('data-avatar-url');
      if (url) {
        avatar.style.backgroundImage = `url(${url})`;
        avatar.classList.add('has-photo');
      } else {
        avatar.style.backgroundImage = '';
        avatar.classList.remove('has-photo');
      }
    });
  }

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
    const theme = getSavedTheme() ?? getDefaultTheme();
    currentTheme = theme;
    applyThemeToUI(theme);

    setCollapsed(getCollapsed());

    // Foto de perfil por usuario: viene del backend en data-avatar-url
    applyAvatarFromServer();

    // Limpieza de versiones anteriores (cuando se guardaba en localStorage y se compartía entre cuentas)
    try {
      localStorage.removeItem('unitecnar:profile:photo');
    } catch {
      // ignore
    }

    // Toggle de tema (puede ser botón o checkbox, y pueden existir varios)
    document.querySelectorAll('[data-theme-toggle]').forEach((toggle) => {
      if (toggle instanceof HTMLInputElement && toggle.type === 'checkbox') {
        toggle.addEventListener('change', () => {
          setTheme(toggle.checked ? 'dark' : 'light');
        });
        return;
      }

      if (toggle instanceof HTMLButtonElement) {
        toggle.addEventListener('click', (event) => {
          event.preventDefault();
          toggleTheme();
        });
      }
    });

    // Configuración: selección de foto (si existe en la página)
    const photoInput = document.querySelector('[data-profile-photo-input]');
    if (photoInput instanceof HTMLInputElement) {
      photoInput.addEventListener('change', () => {
        const file = photoInput.files && photoInput.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = () => {
          const dataUrl = typeof reader.result === 'string' ? reader.result : null;
          if (!dataUrl) return;
          applyPhotoToUI(dataUrl);
        };
        reader.readAsDataURL(file);
      });
    }

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
