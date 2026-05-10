"""Viewport JavaScript for the Acherion render surface."""

from __future__ import annotations

VIEWPORT_JS = """
        defaultPan(viewport) {
            const origin = this.origin(this.stage(viewport));
            const chrome = this.chrome(viewport);
            return {
                x: -origin.x + chrome.sidebarWidth + chrome.pad,
                y: -origin.y + chrome.pad,
            };
        },
        ensureViewportState(viewport) {
            if (!viewport) return;
            if (!viewport.dataset.scale) viewport.dataset.scale = '1';
            const pan = this.defaultPan(viewport);
            if (viewport.dataset.panX === undefined || viewport.dataset.panX === '')
                viewport.dataset.panX = String(pan.x);
            if (viewport.dataset.panY === undefined || viewport.dataset.panY === '')
                viewport.dataset.panY = String(pan.y);
        },
        scale(viewport) {
            this.ensureViewportState(viewport);
            const raw = parseFloat(viewport.dataset.scale || '1');
            return Number.isFinite(raw) && raw > 0 ? raw : 1;
        },
        gridBaseSize(viewport) {
            if (!viewport) return __ACH_GRID_SNAP_SIZE__;
            const styles = getComputedStyle(viewport);
            const raw = parseFloat(
                styles.getPropertyValue('--ach-grid-base-size') ||
                '__ACH_GRID_SNAP_SIZE__'
            );
            return Number.isFinite(raw) && raw > 0
                ? raw : __ACH_GRID_SNAP_SIZE__;
        },
        snapValue(viewport, value) {
            const step = this.gridBaseSize(viewport);
            return step > 0 ? Math.round(value / step) * step : value;
        },
        snapPoint(viewport, x, y) {
            return {
                x: this.snapValue(viewport, x),
                y: this.snapValue(viewport, y),
            };
        },
        updateGrid(viewport) {
            this.ensureViewportState(viewport);
            const sc = this.scale(viewport);
            const origin = this.origin(this.stage(viewport));
            const panX = parseFloat(viewport.dataset.panX || '0');
            const panY = parseFloat(viewport.dataset.panY || '0');
            const base = this.gridBaseSize(viewport);
            let size = base * sc;
            while (size < 14) size *= 2;
            const wrap = (value, step) => {
                const result = value % step;
                return result < 0 ? result + step : result;
            };
            viewport.style.setProperty('--ach-grid-size', `${size}px`);
            viewport.style.setProperty(
                '--ach-grid-offset-x',
                `${wrap(panX + origin.x * sc, size)}px`
            );
            viewport.style.setProperty(
                '--ach-grid-offset-y',
                `${wrap(panY + origin.y * sc, size)}px`
            );
        },
        applyViewportTransform(viewport) {
            this.ensureViewportState(viewport);
            this.updateGrid(viewport);
            const stage = this.stage(viewport);
            if (!stage) return;
            const sc = this.scale(viewport);
            const panX = parseFloat(viewport.dataset.panX || '0');
            const panY = parseFloat(viewport.dataset.panY || '0');
            stage.style.transform =
                `translate(${panX}px,${panY}px) scale(${sc})`;
        },
        setScaleAround(viewport, scaleValue, clientX, clientY) {
            if (!viewport) return;
            this.ensureViewportState(viewport);
            const stage = this.stage(viewport);
            if (!stage) return;
            const rect = viewport.getBoundingClientRect();
            const oldScale = this.scale(viewport);
            const nextScale = Math.max(0.08, Math.min(4.0, scaleValue));
            const panX = parseFloat(viewport.dataset.panX || '0');
            const panY = parseFloat(viewport.dataset.panY || '0');
            const worldX = (clientX - rect.left - panX) / oldScale;
            const worldY = (clientY - rect.top - panY) / oldScale;
            viewport.dataset.scale = String(nextScale);
            viewport.dataset.panX = String(
                (clientX - rect.left) - (worldX * nextScale)
            );
            viewport.dataset.panY = String(
                (clientY - rect.top) - (worldY * nextScale)
            );
            this.applyViewportTransform(viewport);
        },
        zoomViewport(viewport, factor) {
            if (!viewport) return;
            const rect = viewport.getBoundingClientRect();
            const scaleValue = this.scale(viewport) * factor;
            this.setScaleAround(
                viewport,
                scaleValue,
                rect.left + (rect.width / 2),
                rect.top + (rect.height / 2)
            );
        },
        resetViewport(viewport) {
            if (!viewport) return;
            const pan = this.defaultPan(viewport);
            viewport.dataset.scale = '1';
            viewport.dataset.panX = String(pan.x);
            viewport.dataset.panY = String(pan.y);
            this.syncViewport(viewport);
        },
        syncViewport(viewport) {
            if (!viewport) return;
            this.applyViewportTransform(viewport);
            const stage = this.stage(viewport);
            if (!stage) return;
            const update = () => this.updateConnections(stage);
            requestAnimationFrame(() => requestAnimationFrame(update));
            setTimeout(update, 0);
            setTimeout(update, 40);
            setTimeout(update, 160);
            if (document.fonts && document.fonts.ready)
                document.fonts.ready.then(update).catch(() => {});
        },
        centerGraph(viewport) {
            if (!viewport) return;
            const stage = this.stage(viewport);
            if (!stage) return;
            const origin = this.origin(stage);
            const chrome = this.chrome(viewport);
            const scaleValue = this.scale(viewport);
            const nodes = Array.from(stage.querySelectorAll('.ach-node'));
            if (!nodes.length) {
                this.resetViewport(viewport);
                return;
            }
            let minX = Infinity;
            let minY = Infinity;
            let maxX = -Infinity;
            let maxY = -Infinity;
            nodes.forEach(node => {
                const left = parseFloat(node.style.left || '0') - origin.x;
                const top = parseFloat(node.style.top || '0') - origin.y;
                minX = Math.min(minX, left);
                minY = Math.min(minY, top);
                maxX = Math.max(maxX, left + node.offsetWidth);
                maxY = Math.max(maxY, top + node.offsetHeight);
            });
            if (!Number.isFinite(minX) || !Number.isFinite(minY)) {
                this.resetViewport(viewport);
                return;
            }
            const availableWidth = Math.max(
                160,
                viewport.clientWidth - chrome.sidebarWidth - (chrome.pad * 2)
            );
            const availableHeight = Math.max(
                120,
                viewport.clientHeight - (chrome.pad * 2)
            );
            const contentWidth = Math.max(1, maxX - minX);
            const contentHeight = Math.max(1, maxY - minY);
            viewport.dataset.panX = String(
                chrome.sidebarWidth
                + chrome.pad
                + ((availableWidth - (contentWidth * scaleValue)) / 2)
                - (minX * scaleValue)
            );
            viewport.dataset.panY = String(
                chrome.pad
                + ((availableHeight - (contentHeight * scaleValue)) / 2)
                - (minY * scaleValue)
            );
            this.syncViewport(viewport);
        },
        toggleFullscreen(target) {
            if (!target) return;
            const exitFallback = () => {
                target.classList.remove('ach-workbench-local-fullscreen');
                document.body?.classList.remove(
                    'ach-workbench-fullscreen-active'
                );
            };
            const enterFallback = () => {
                target.classList.add('ach-workbench-local-fullscreen');
                document.body?.classList.add(
                    'ach-workbench-fullscreen-active'
                );
            };
            if (target.classList.contains('ach-workbench-local-fullscreen')) {
                exitFallback();
                return;
            }
            if (!document.fullscreenEnabled || !target.requestFullscreen) {
                enterFallback();
                return;
            }
            if (document.fullscreenElement === target) {
                document.exitFullscreen().catch(exitFallback);
                return;
            }
            const enter = () => {
                const fallbackTimer = setTimeout(() => {
                    if (document.fullscreenElement !== target)
                        enterFallback();
                }, 180);
                target.requestFullscreen?.().then(() => {
                    clearTimeout(fallbackTimer);
                }).catch(() => {
                    clearTimeout(fallbackTimer);
                    enterFallback();
                });
            };
            if (document.fullscreenElement) {
                document.exitFullscreen().then(enter).catch(enter);
                return;
            }
            enter();
        },
        observeAll(root) {
            (root || document).querySelectorAll('.ach-workbench').forEach(
                frame => this.syncSidebarState(frame)
            );
            (root || document).querySelectorAll('.ach-shell').forEach(
                viewport => this.observeViewport(viewport)
            );
        },
        observeViewport(viewport) {
            if (!viewport) return;
            this.ensureViewportState(viewport);
            if (viewport.__oeVlObserved) {
                this.queueSync(viewport);
                return;
            }
            viewport.__oeVlObserved = true;
            const stage = this.stage(viewport);
            if (!stage) return;
            const queue = () => this.queueSync(viewport);
            const ro = new ResizeObserver(queue);
            ro.observe(viewport);
            ro.observe(stage);
            const mo = new MutationObserver(queue);
            mo.observe(stage, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ['style', 'class'],
            });
            if (window.IntersectionObserver) {
                const io = new IntersectionObserver(
                    (entries) => {
                        if (entries.some(entry => entry.isIntersecting)) queue();
                    },
                    {threshold: [0, 0.01]}
                );
                io.observe(viewport);
                viewport.__oeVlIntersectionObserver = io;
            }
            viewport.__oeVlResizeObserver = ro;
            viewport.__oeVlMutationObserver = mo;
            queue();
        },
"""

__all__ = ['VIEWPORT_JS']