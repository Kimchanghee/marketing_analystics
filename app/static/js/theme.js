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

        // Toggle icon visibility
        const sunIcon = toggleButton.querySelector('.theme-icon-sun');
        const moonIcon = toggleButton.querySelector('.theme-icon-moon');

        if (sunIcon && moonIcon) {
            if (theme === 'dark') {
                sunIcon.style.display = 'none';
                moonIcon.style.display = 'block';
            } else {
                sunIcon.style.display = 'block';
                moonIcon.style.display = 'none';
            }
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
        const currentTheme = storedTheme || root.getAttribute('data-theme') || 'light';
        applyTheme(currentTheme);
    });
})();
