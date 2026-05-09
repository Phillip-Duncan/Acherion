"""Sidebar JavaScript for the Acherion render surface."""

from __future__ import annotations

SIDEBAR_JS = """
        defaultSidebarPaneWidth(frame) {
            if (!frame) return 244;
            const styles = getComputedStyle(frame);
            const width = parseFloat(
                styles.getPropertyValue(
                    '--ach-palette-pane-default-width'
                ) || '244'
            );
            return Number.isFinite(width) ? width : 244;
        },
        sidebarPaneWidth(frame) {
            if (!frame) return 0;
            const styles = getComputedStyle(frame);
            const width = parseFloat(
                styles.getPropertyValue('--ach-palette-pane-width') || '0'
            );
            return Number.isFinite(width)
                ? width : this.defaultSidebarPaneWidth(frame);
        },
        sidebarPaneMinWidth(frame) {
            if (!frame) return 188;
            const styles = getComputedStyle(frame);
            const width = parseFloat(
                styles.getPropertyValue('--ach-palette-pane-min-width') || '188'
            );
            return Number.isFinite(width) ? width : 188;
        },
        sidebarPaneMaxWidth(frame) {
            if (!frame) return 460;
            const min = this.sidebarPaneMinWidth(frame);
            const styles = getComputedStyle(frame);
            const configured = parseFloat(
                styles.getPropertyValue('--ach-palette-pane-max-width') || '460'
            );
            const frameWidth = frame?.clientWidth || window.innerWidth || 0;
            const availableMax = Math.max(
                min,
                frameWidth > 0 ? frameWidth - 260 : configured
            );
            return Math.max(
                min,
                Math.min(
                    Number.isFinite(configured) ? configured : 460,
                    availableMax
                )
            );
        },
        sidebarCollapseThreshold(frame) {
            if (!frame) return 124;
            const styles = getComputedStyle(frame);
            const width = parseFloat(
                styles.getPropertyValue(
                    '--ach-palette-pane-collapse-threshold'
                ) || '124'
            );
            return Number.isFinite(width) ? width : 124;
        },
        syncSidebarState(frame) {
            if (!frame) return;
            const palette = this.palette(frame);
            if (!palette) return;
            const buttons = Array.from(
                palette.querySelectorAll('.ach-activity-button')
            );
            const panes = Array.from(
                palette.querySelectorAll('.ach-sidebar-pane')
            );
            let activeKey = palette.dataset.activeSidebar || '';
            if (!buttons.some(button => button.dataset.sidebarKey === activeKey)) {
                activeKey = buttons[0]?.dataset.sidebarKey || '';
                palette.dataset.activeSidebar = activeKey;
            }
            const paneOpen = this.sidebarPaneWidth(frame) > 0.5;
            palette.dataset.paneOpen = paneOpen ? '1' : '0';
            frame.classList.toggle('ach-sidebar-pane-closed', !paneOpen);
            buttons.forEach(button => {
                const isActive = button.dataset.sidebarKey === activeKey;
                button.classList.toggle('ach-activity-button-active', isActive);
                button.setAttribute(
                    'aria-pressed',
                    isActive ? 'true' : 'false'
                );
            });
            panes.forEach(pane => {
                const isVisible = (
                    paneOpen && pane.dataset.sidebarKey === activeKey
                );
                pane.classList.toggle('ach-sidebar-pane-active', isVisible);
            });
        },
        clampSidebarPaneWidth(frame, widthValue) {
            const min = this.sidebarPaneMinWidth(frame);
            const max = this.sidebarPaneMaxWidth(frame);
            return Math.max(min, Math.min(max, widthValue));
        },
        setSidebarPaneWidth(frame, widthValue, persist = true) {
            if (!frame) return;
            const nextWidth = this.clampSidebarPaneWidth(frame, widthValue);
            frame.style.setProperty(
                '--ach-palette-pane-width',
                `${nextWidth}px`
            );
            if (persist && nextWidth > 0)
                frame.dataset.sidebarExpandedWidth = String(nextWidth);
            this.syncSidebarState(frame);
        },
        closeSidebarPane(frame) {
            if (!frame) return;
            const currentWidth = this.sidebarPaneWidth(frame);
            if (currentWidth > 0) {
                frame.dataset.sidebarExpandedWidth = String(
                    Math.max(this.sidebarPaneMinWidth(frame), currentWidth)
                );
            }
            frame.style.setProperty('--ach-palette-pane-width', '0px');
            this.syncSidebarState(frame);
        },
        openSidebarPane(frame) {
            if (!frame) return;
            const defaultWidth = this.defaultSidebarPaneWidth(frame);
            const storedWidth = parseFloat(
                frame.dataset.sidebarExpandedWidth || String(defaultWidth)
            );
            const nextWidth = Number.isFinite(storedWidth)
                ? storedWidth : defaultWidth;
            this.setSidebarPaneWidth(frame, nextWidth);
        },
        resetSidebarWidth(frame) {
            if (!frame) return;
            const defaultWidth = this.defaultSidebarPaneWidth(frame);
            frame.dataset.sidebarExpandedWidth = String(defaultWidth);
            this.setSidebarPaneWidth(frame, defaultWidth);
        },
        toggleSidebarSection(button) {
            const frame = this.frame(button);
            const palette = this.palette(frame);
            const key = button?.dataset?.sidebarKey || '';
            if (!frame || !palette || !key) return;
            const currentKey = palette.dataset.activeSidebar || '';
            const paneOpen = this.sidebarPaneWidth(frame) > 0.5;
            if (paneOpen && currentKey === key) {
                this.closeSidebarPane(frame);
                return;
            }
            palette.dataset.activeSidebar = key;
            this.openSidebarPane(frame);
        },
        beginSidebarResize(handle, startClientX) {
            const frame = this.frame(handle);
            if (!frame) return;
            this._stopSidebarResize?.();
            const startWidth = this.sidebarPaneWidth(frame);
            document.body?.classList.add('ach-sidebar-resizing');
            const move = (event) => {
                const nextWidth = startWidth + (event.clientX - startClientX);
                if (nextWidth <= this.sidebarCollapseThreshold(frame)) {
                    this.closeSidebarPane(frame);
                    return;
                }
                this.setSidebarPaneWidth(frame, nextWidth);
            };
            const stop = () => {
                window.removeEventListener('pointermove', move);
                window.removeEventListener('pointerup', stop);
                window.removeEventListener('pointercancel', stop);
                document.body?.classList.remove('ach-sidebar-resizing');
                if (this._stopSidebarResize === stop)
                    this._stopSidebarResize = null;
            };
            this._stopSidebarResize = stop;
            window.addEventListener('pointermove', move);
            window.addEventListener('pointerup', stop);
            window.addEventListener('pointercancel', stop);
        },
"""

__all__ = ['SIDEBAR_JS']