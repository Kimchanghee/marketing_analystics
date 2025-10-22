(function () {
    const initSlider = (slider) => {
        const viewport = slider.querySelector('[data-slider-viewport]');
        const track = slider.querySelector('[data-slider-track]');
        const prev = slider.querySelector('[data-slider-prev]');
        const next = slider.querySelector('[data-slider-next]');

        if (!viewport || !track) {
            return;
        }

        const items = Array.from(track.querySelectorAll('.slider-item'));

        if (!items.length) {
            return;
        }

        const getGapSize = () => {
            const style = window.getComputedStyle(track);
            const gapValue = style.columnGap || style.gap || '0';
            const parsed = parseFloat(gapValue);
            return Number.isFinite(parsed) ? parsed : 0;
        };

        const getStepSize = () => {
            const gap = getGapSize();
            const itemWidth = items[0].getBoundingClientRect().width;
            return itemWidth + gap;
        };

        let stepSize = getStepSize();

        const updateStepSize = () => {
            stepSize = getStepSize();
        };

        const getMaxScroll = () => Math.max(track.scrollWidth - viewport.clientWidth, 0);

        const scrollByItem = (direction) => {
            const maxScroll = getMaxScroll();
            const current = viewport.scrollLeft;

            if (maxScroll === 0) {
                return;
            }

            const threshold = stepSize / 2;

            if (direction > 0) {
                if (Math.abs(current - maxScroll) <= threshold) {
                    viewport.scrollTo({ left: 0, behavior: 'smooth' });
                } else {
                    const target = Math.min(current + stepSize, maxScroll);
                    viewport.scrollTo({ left: target, behavior: 'smooth' });
                }
            } else {
                if (current <= threshold) {
                    viewport.scrollTo({ left: maxScroll, behavior: 'smooth' });
                } else {
                    const target = Math.max(current - stepSize, 0);
                    viewport.scrollTo({ left: target, behavior: 'smooth' });
                }
            }
        };

        prev?.addEventListener('click', () => {
            scrollByItem(-1);
        });

        next?.addEventListener('click', () => {
            scrollByItem(1);
        });

        window.addEventListener('resize', updateStepSize);
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
