"""Workbench and canvas CSS for the Acherion render surface."""

WORKBENCH_CSS = """
.ach-workbench {
    --ach-activitybar-width: 52px;
    --ach-palette-pane-default-width: 244px;
    --ach-palette-pane-width: var(--ach-palette-pane-default-width);
    --ach-palette-pane-min-width: 188px;
    --ach-palette-pane-max-width: 460px;
    --ach-palette-pane-collapse-threshold: 124px;
    --ach-sidebar-glass-bg: rgba(0,0,0,0.72);
    --ach-sidebar-glass-filter: blur(16px) saturate(112%);
    --ach-sidebar-panel-bg: rgba(255,255,255,0.03);
    --ach-sidebar-panel-bg-strong: rgba(255,255,255,0.04);
    --ach-palette-width: calc(
        var(--ach-activitybar-width) + var(--ach-palette-pane-width)
    );
    position: relative;
    display: flex;
    flex-direction: column;
    width: 100%;
    min-width: 0;
    height: min(78vh, 980px);
    max-height: min(78vh, 980px);
    background: var(--oe-surface);
    overflow: hidden;
}
body.ach-workbench-fullscreen-active {
    overflow: hidden;
}
.ach-workbench-local-fullscreen {
    position: fixed !important;
    inset: 0 !important;
    z-index: 9996 !important;
    height: auto !important;
    max-height: none !important;
    border-radius: 0 !important;
}
.ach-menubar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    min-height: 68px;
    padding: 10px 14px;
    border-bottom: 1px solid var(--oe-border);
    background: var(--oe-surface);
}
.ach-menubar-left {
    display: flex;
    align-items: center;
    gap: 10px;
    flex: 1 1 auto;
    min-width: 0;
}
.ach-menubar-right {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 0 0 auto;
    min-width: 0;
}
.ach-workbench-menu-open .ach-workbench-body,
.ach-workbench-menu-open .ach-workbench-body * {
    pointer-events: none;
}
.ach-workbench-menu-open .ach-menubar {
    pointer-events: auto;
}
body:has(.q-menu.ach-menubar-menu) .ach-workbench-body,
body:has(.q-menu.ach-menubar-menu) .ach-workbench-body * {
    pointer-events: none;
}
body:has(.q-menu.ach-menubar-menu) .ach-menubar {
    pointer-events: auto;
}
.ach-menubar-menus {
    display: flex;
    align-items: center;
    gap: 2px;
    flex: 1 1 auto;
    min-width: 0;
    overflow-x: auto;
}
.ach-menubar-separator {
    flex: 0 0 auto;
    width: 1px;
    height: 18px;
    margin: 0 4px 0 6px;
    background: rgba(255,255,255,0.14);
}
.ach-menu-button.q-btn--flat,
.ach-menu-button.q-btn--flat.text-primary,
.ach-menu-button.q-btn--flat .q-btn__content,
.ach-menu-button.q-btn--flat .q-icon {
    color: var(--oe-text) !important;
}
.ach-menu-button .q-btn__content {
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.01em;
}
.ach-menubar-menu {
    z-index: 48 !important;
    min-width: 188px;
    border: 1px solid var(--oe-border);
    border-radius: 10px;
    background: rgba(0,0,0,0.88);
    backdrop-filter: blur(14px) saturate(112%);
    -webkit-backdrop-filter: blur(14px) saturate(112%);
    overflow: hidden;
}
.q-menu.ach-menubar-menu:not([data-ach-aligned="true"]) {
    opacity: 0 !important;
    visibility: hidden !important;
    pointer-events: none !important;
}
.ach-menubar-menu .q-list {
    min-width: 100%;
    padding: 4px 0;
}
.ach-menubar-menu .q-item {
    min-height: 38px;
    padding: 8px 14px;
    justify-content: flex-start;
    text-align: left;
}
.ach-menubar-menu .q-item__section {
    min-width: 0;
    align-items: flex-start;
    justify-content: flex-start;
    text-align: left;
}
.ach-menubar-menu .q-item__section--main {
    width: 100%;
}
.ach-menubar-menu .q-item .q-focus-helper {
    background: transparent !important;
    opacity: 0 !important;
}
.ach-menubar-menu .q-item:hover,
.ach-menubar-menu .q-item.q-manual-focusable--focused,
.ach-menubar-menu .q-item--active {
    background: var(--oe-blue) !important;
    color: #ffffff !important;
}
.ach-menubar-menu .q-item:hover .q-focus-helper,
.ach-menubar-menu .q-item.q-manual-focusable--focused .q-focus-helper,
.ach-menubar-menu .q-item--active .q-focus-helper {
    background: transparent !important;
    opacity: 0 !important;
}
.ach-menubar-menu .q-item:hover .q-item__label,
.ach-menubar-menu .q-item:hover .q-item__section,
.ach-menubar-menu .q-item:hover .q-icon,
.ach-menubar-menu .q-item.q-manual-focusable--focused .q-item__label,
.ach-menubar-menu .q-item.q-manual-focusable--focused .q-item__section,
.ach-menubar-menu .q-item.q-manual-focusable--focused .q-icon,
.ach-menubar-menu .q-item--active .q-item__label,
.ach-menubar-menu .q-item--active .q-item__section,
.ach-menubar-menu .q-item--active .q-icon {
    color: #ffffff !important;
}
.ach-compile-button {
    min-height: 32px !important;
    padding: 0 12px !important;
    border-radius: 9999px !important;
    background: var(--oe-blue) !important;
    color: #ffffff !important;
    box-shadow: none !important;
    flex: 0 0 auto;
}
.ach-compile-button .q-btn__content {
    gap: 6px;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.01em;
}
.ach-compile-button .q-icon {
    font-size: 16px;
}
.ach-mode-button.q-btn--flat,
.ach-mode-button.q-btn--flat.text-primary,
.ach-mode-button.q-btn--flat .q-btn__content,
.ach-mode-button.q-btn--flat .q-icon {
    color: var(--oe-text) !important;
}
.ach-mode-button {
    min-height: 32px !important;
    padding: 0 12px !important;
    border-radius: 9999px !important;
    color: var(--oe-text) !important;
    border: 1px solid var(--oe-border) !important;
    background: transparent !important;
    box-shadow: none !important;
    flex: 0 0 auto;
}
.ach-mode-button .q-btn__content {
    gap: 6px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.01em;
}
.ach-mode-button .q-icon {
    font-size: 16px;
}
.ach-validate-button.q-btn--flat,
.ach-validate-button.q-btn--flat.text-primary,
.ach-validate-button.q-btn--flat .q-btn__content,
.ach-validate-button.q-btn--flat .q-icon {
    color: var(--oe-text) !important;
}
.ach-validate-button {
    min-height: 32px !important;
    padding: 0 12px !important;
    border-radius: 9999px !important;
    color: var(--oe-text) !important;
    border: 1px solid var(--oe-border) !important;
    background: transparent !important;
    box-shadow: none !important;
    flex: 0 0 auto;
}
.ach-validate-button .q-btn__content {
    gap: 6px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.01em;
}
.ach-validate-button .q-icon {
    font-size: 16px;
}
.ach-workbench-body {
    position: relative;
    display: flex;
    flex: 1 1 auto;
    min-height: 0;
}
.ach-code-pane {
    display: flex;
    flex: 1 1 auto;
    min-width: 0;
    min-height: 0;
    padding: 0;
    overflow: hidden;
}
.ach-code-pane > div {
    display: flex;
    flex: 1 1 auto;
    min-width: 0;
    min-height: 0;
    height: 100%;
}
.ach-code-pane .oe-code-editor {
    flex: 1 1 auto;
    min-width: 0;
    min-height: 0;
    height: 100%;
    border: none !important;
    border-radius: 0 !important;
}
.ach-mode-hidden {
    display: none !important;
}
.ach-workbench-main {
    position: relative;
    display: flex;
    align-items: stretch;
    flex: 1 1 auto;
    min-height: 0;
    width: 100%;
    height: 100%;
}
.ach-shell {
    --ach-grid-base-size: __ACH_GRID_SNAP_SIZE__px;
    --ach-grid-size: var(--ach-grid-base-size);
    --ach-grid-offset-x: 0px;
    --ach-grid-offset-y: 0px;
    --ach-sidebar-width: 0px;
    --ach-stage-pad: 28px;
    position: relative;
    flex: 1 1 auto;
    min-width: 0;
    overflow: hidden;
    width: 100%;
    height: 100%;
    max-height: none;
    border: none;
    border-radius: 0;
    background: transparent;
    touch-action: none;
    cursor: grab;
    overscroll-behavior: contain;
    background-color: transparent;
    background-image:
        linear-gradient(
            color-mix(in srgb, var(--oe-text) 8%, transparent) 1px,
            transparent 1px
        ),
        linear-gradient(
            90deg,
            color-mix(in srgb, var(--oe-text) 8%, transparent) 1px,
            transparent 1px
        );
    background-size:
        var(--ach-grid-size) var(--ach-grid-size),
        var(--ach-grid-size) var(--ach-grid-size);
    background-position:
        var(--ach-grid-offset-x) var(--ach-grid-offset-y),
        var(--ach-grid-offset-x) var(--ach-grid-offset-y);
}
.ach-shell-panning { cursor: grabbing; }
.ach-shell-panning,
.ach-shell-panning * { user-select: none; }
.ach-shell-dragging-node,
.ach-shell-dragging-node * { user-select: none; }
.ach-canvas {
    position: relative;
    min-height: 100%;
    width: max(100%, __CANVAS_STAGE_WIDTH__px);
    transform-origin: 0 0;
    background: transparent;
}
.ach-canvas-dragging {
    outline: none;
}
.ach-links {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    pointer-events: auto;
    z-index: 0;
}
.ach-link-path {
    fill: none;
    stroke: var(--ach-link-colour, rgba(29,155,240,0.78));
    stroke-width: 3;
    stroke-linecap: round;
    pointer-events: none;
}
.ach-link-path-selected {
    stroke-width: 4;
    filter: drop-shadow(0 0 4px color-mix(in srgb, var(--ach-link-colour, var(--oe-blue)) 55%, white));
}
.ach-link-hitbox {
    fill: none;
    stroke: transparent;
    stroke-width: 18;
    pointer-events: stroke;
    cursor: pointer;
}
.ach-link-badge {
    fill: var(--ach-link-colour, var(--oe-blue));
    opacity: 0.92;
}
.ach-link-badge-text {
    fill: #ffffff;
    font-size: 10px;
    font-weight: 700;
    font-family: system-ui, sans-serif;
    pointer-events: none;
}
"""