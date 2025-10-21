(function () {
    const initSlider = (slider) => {
        const viewport = slider.querySelector('[data-slider-viewport]');
        const track = slider.querySelector('[data-slider-track]');
        const prev = slider.querySelector('[data-slider-prev]');
        const next = slider.querySelector('[data-slider-next]');

        if (!viewport || !track) {
            return;
        }

        const scrollByViewport = (direction) => {
            const amount = viewport.clientWidth;
            viewport.scrollBy({ left: amount * direction, behavior: 'smooth' });
        };

        const updateButtons = () => {
            if (!prev && !next) {
                return;
            }

            const maxScroll = track.scrollWidth - viewport.clientWidth;
            const current = viewport.scrollLeft;

            if (prev) {
                prev.disabled = current <= 0;
            }
            if (next) {
                next.disabled = current >= maxScroll - 1;
            }
        };

        prev?.addEventListener('click', () => {
            scrollByViewport(-1);
        });

        next?.addEventListener('click', () => {
            scrollByViewport(1);
        });

        viewport.addEventListener('scroll', updateButtons, { passive: true });
        window.addEventListener('resize', updateButtons);

        updateButtons();
    };

    const onReady = () => {
        const sliders = document.querySelectorAll('[data-slider]');
        sliders.forEach(initSlider);
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', onReady);
    } else {
        onReady();
    }
})();
