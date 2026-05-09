"""Core JavaScript helpers for the Acherion render surface."""

from __future__ import annotations

CORE_JS = """
        queueSync(viewport) {
            if (!viewport) return;
            if (viewport.__oeVlSyncQueued) return;
            viewport.__oeVlSyncQueued = true;
            requestAnimationFrame(() => {
                viewport.__oeVlSyncQueued = false;
                this.syncViewport(viewport);
            });
        },
        stage(viewport) {
            return viewport ? viewport.querySelector('.ach-canvas') : null;
        },
        origin(stage) {
            if (!stage) return {x: 0, y: 0};
            const styles = getComputedStyle(stage);
            const ox = parseFloat(styles.getPropertyValue('--ach-origin-x') || '0');
            const oy = parseFloat(styles.getPropertyValue('--ach-origin-y') || '0');
            return {
                x: Number.isFinite(ox) ? ox : 0,
                y: Number.isFinite(oy) ? oy : 0,
            };
        },
        chrome(viewport) {
            if (!viewport) return {sidebarWidth: 0, pad: 24};
            const styles = getComputedStyle(viewport);
            const sidebarWidth = parseFloat(
                styles.getPropertyValue('--ach-sidebar-width') || '0'
            );
            const pad = parseFloat(
                styles.getPropertyValue('--ach-stage-pad') || '24'
            );
            return {
                sidebarWidth: Number.isFinite(sidebarWidth) ? sidebarWidth : 0,
                pad: Number.isFinite(pad) ? pad : 24,
            };
        },
        frame(element) {
            return element ? element.closest('.ach-workbench') : null;
        },
        contextSubmenu(item) {
            if (!item) return null;
            return Array.from(item.children || []).find(
                child => child.classList?.contains('ach-ctx-submenu')
            ) || null;
        },
        measureWhileHidden(element, measure) {
            if (!element || typeof measure !== 'function') return null;
            const prevDisplay = element.style.display;
            const prevVisibility = element.style.visibility;
            const prevPointerEvents = element.style.pointerEvents;
            element.style.display = 'block';
            element.style.visibility = 'hidden';
            element.style.pointerEvents = 'none';
            const result = measure();
            element.style.display = prevDisplay;
            element.style.visibility = prevVisibility;
            element.style.pointerEvents = prevPointerEvents;
            return result;
        },
        positionContextSubmenus(menu) {
            if (!menu) return;
            const margin = 12;
            const viewportWidth =
                window.innerWidth || document.documentElement.clientWidth || 0;
            const viewportHeight =
                window.innerHeight || document.documentElement.clientHeight || 0;
            menu.querySelectorAll('.ach-ctx-item-has-submenu').forEach(item => {
                const submenu = this.contextSubmenu(item);
                if (!submenu) return;
                const size = this.measureWhileHidden(submenu, () => {
                    const rect = submenu.getBoundingClientRect();
                    return {width: rect.width, height: rect.height};
                });
                if (!size) return;
                const itemRect = item.getBoundingClientRect();
                const desiredAbsoluteLeft = itemRect.left + itemRect.width - 4;
                const maxLeft = Math.max(
                    margin,
                    viewportWidth - size.width - margin
                );
                const absoluteLeft = Math.max(
                    margin,
                    Math.min(maxLeft, desiredAbsoluteLeft)
                );
                const maxTop = Math.max(
                    margin,
                    viewportHeight - size.height - margin
                );
                const absoluteTop = Math.max(
                    margin,
                    Math.min(maxTop, itemRect.top - 10)
                );
                item.style.setProperty(
                    '--ach-ctx-submenu-left',
                    `${absoluteLeft - itemRect.left}px`
                );
                item.style.setProperty(
                    '--ach-ctx-submenu-top',
                    `${absoluteTop - itemRect.top}px`
                );
            });
        },
        positionContextMenu(menu, anchorX, anchorY) {
            if (!menu) return;
            const margin = 12;
            const viewportWidth =
                window.innerWidth || document.documentElement.clientWidth || 0;
            const viewportHeight =
                window.innerHeight || document.documentElement.clientHeight || 0;
            menu.style.left = `${Math.max(margin, anchorX)}px`;
            menu.style.top = `${Math.max(margin, anchorY)}px`;
            const rect = menu.getBoundingClientRect();
            const maxLeft = Math.max(margin, viewportWidth - rect.width - margin);
            const maxTop = Math.max(
                margin,
                viewportHeight - rect.height - margin
            );
            menu.style.left = `${Math.max(margin, Math.min(maxLeft, anchorX))}px`;
            menu.style.top = `${Math.max(margin, Math.min(maxTop, anchorY))}px`;
            this.positionContextSubmenus(menu);
        },
        palette(frame) {
            return frame ? frame.querySelector('.ach-palette-shell') : null;
        },
"""

__all__ = ['CORE_JS']