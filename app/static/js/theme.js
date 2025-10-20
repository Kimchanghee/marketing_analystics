(function () {
    const storageKey = 'ccc-theme';
    const root = document.documentElement;
    const toggle = () => {
        const current = root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
        const next = current === 'dark' ? 'light' : 'dark';
        applyTheme(next);
    };

    const applyTheme = (theme) => {
        root.setAttribute('data-theme', theme);
        window.localStorage.setItem(storageKey, theme);
        const toggleButton = document.querySelector('[data-theme-toggle]');
        if (!toggleButton) {
            return;
        }
        const labelElement = toggleButton.querySelector('.theme-label');
        const lightLabel = toggleButton.getAttribute('data-light-label');
        const darkLabel = toggleButton.getAttribute('data-dark-label');
        if (labelElement && lightLabel && darkLabel) {
            labelElement.textContent = theme === 'dark' ? darkLabel : lightLabel;
        }
        toggleButton.classList.toggle('is-dark', theme === 'dark');
    };

    document.addEventListener('DOMContentLoaded', () => {
        const toggleButton = document.querySelector('[data-theme-toggle]');
        if (!toggleButton) {
            return;
        }
        toggleButton.addEventListener('click', toggle);
        const storedTheme = window.localStorage.getItem(storageKey);
        if (storedTheme) {
            applyTheme(storedTheme);
        } else {
            applyTheme(root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light');
        }
    });
})();
