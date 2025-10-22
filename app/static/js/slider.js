(function () {
    const toPixels = (value, context) => {
        if (!value) {
            return 0;
        }

        const parsed = parseFloat(value);

        if (!Number.isFinite(parsed)) {
            return 0;
        }

        if (value.endsWith('rem')) {
            const rootFontSize = parseFloat(window.getComputedStyle(document.documentElement).fontSize) || 16;
            return parsed * rootFontSize;
        }

        if (value.endsWith('em')) {
            const contextFontSize = context ? parseFloat(window.getComputedStyle(context).fontSize) : 16;
            return parsed * (contextFontSize || 16);
        }

        return parsed;
    };

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
            const gapValue = style.columnGap || style.gap || '0px';
            return toPixels(gapValue, track);
        };

        const getStepSize = () => {
            const gap = getGapSize();
            const itemWidth = items[0].getBoundingClientRect().width;
            return itemWidth + gap;
        };

        const getAllItems = () => Array.from(track.querySelectorAll('.slider-item'));

        const removeClones = () => {
            track.querySelectorAll('.slider-item-clone').forEach((clone) => clone.remove());
        };

        const cloneItem = (item) => {
            const clone = item.cloneNode(true);
            clone.classList.add('slider-item-clone');
            clone.setAttribute('aria-hidden', 'true');
            clone.removeAttribute('id');
            clone.querySelectorAll('[id]').forEach((node) => {
                node.removeAttribute('id');
            });
            clone.querySelectorAll('a, button, input, textarea, select').forEach((interactive) => {
                interactive.setAttribute('tabindex', '-1');
                interactive.setAttribute('aria-hidden', 'true');
            });
            return clone;
        };

        const scrollToIndex = (index, behavior = 'smooth') => {
            const allItems = getAllItems();

            if (!allItems.length) {
                return false;
            }

            const targetIndex = prefixCount + index;
            const target = allItems[targetIndex];

            if (!target) {
                return false;
            }

            const baseOffset = allItems[0].offsetLeft;
            const targetOffset = target.offsetLeft - baseOffset;

            viewport.scrollTo({ left: targetOffset, behavior });
            return true;
        };

        const jumpToIndex = (index) => {
            scrollToIndex(index, 'auto');
        };

        const animationDuration = 450;
        let currentIndex = 0;
        let prefixCount = 0;
        let stepSize = 0;
        let resizeTimer = null;
        let animationTimer = null;
        let isAnimating = false;

        const setupClones = (activeIndex = 0) => {
            window.clearTimeout(animationTimer);
            isAnimating = false;
            removeClones();

            stepSize = getStepSize();

            if (!Number.isFinite(stepSize) || stepSize <= 0) {
                stepSize = items[0].getBoundingClientRect().width;
            }

            const estimatedVisible = Math.max(1, Math.round(viewport.clientWidth / stepSize));
            prefixCount = Math.min(estimatedVisible, items.length);
            const suffixCount = prefixCount;

            const prefixItems = items.slice(-prefixCount).map(cloneItem);
            prefixItems.forEach((clone) => {
                track.insertBefore(clone, track.firstChild);
            });

            const suffixItems = items.slice(0, suffixCount).map(cloneItem);
            suffixItems.forEach((clone) => {
                track.appendChild(clone);
            });

            currentIndex = activeIndex;
            requestAnimationFrame(() => {
                jumpToIndex(currentIndex);
            });
        };

        const handleResize = () => {
            window.clearTimeout(resizeTimer);
            resizeTimer = window.setTimeout(() => {
                const normalizedIndex = ((currentIndex % items.length) + items.length) % items.length;
                setupClones(normalizedIndex);
            }, 150);
        };

        const move = (direction) => {
            if (isAnimating) {
                return;
            }

            isAnimating = true;
            currentIndex += direction;
            const didScroll = scrollToIndex(currentIndex);

            if (!didScroll) {
                currentIndex = ((currentIndex % items.length) + items.length) % items.length;
                isAnimating = false;
                return;
            }

            window.clearTimeout(animationTimer);
            animationTimer = window.setTimeout(() => {
                if (currentIndex >= items.length) {
                    currentIndex = 0;
                    jumpToIndex(currentIndex);
                } else if (currentIndex < 0) {
                    currentIndex = items.length - 1;
                    jumpToIndex(currentIndex);
                }

                isAnimating = false;
            }, animationDuration);
        };

        setupClones(0);

        prev?.addEventListener('click', () => {
            move(-1);
        });

        next?.addEventListener('click', () => {
            move(1);
        });

        window.addEventListener('resize', handleResize);
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
