"""Palette, context-menu, and status CSS for the Acherion render surface."""

CHROME_CSS = """
/* --- group frames ---------------------------------------------------- */
.ach-group-frame {
    position: absolute;
    border-radius: 18px;
    pointer-events: none;
    z-index: 0;
}
.ach-group-label {
    position: absolute;
    top: -12px;
    left: 16px;
    padding: 4px 10px;
    border-radius: 9999px;
    border: 1px solid currentColor;
    background: var(--oe-bg);
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    pointer-events: none;
    line-height: 1;
    white-space: nowrap;
}
/* --- node context menu ----------------------------------------------- */
.ach-ctx-backdrop {
    position: fixed;
    inset: 0;
    z-index: 9997;
}
.ach-ctx-menu {
    position: fixed;
    z-index: 9999;
    background: color-mix(in srgb, var(--oe-surface) 96%, #000 4%);
    border: 1px solid color-mix(in srgb, var(--oe-border) 78%, transparent);
    border-radius: 14px;
    padding: 10px;
    min-width: 280px;
    box-shadow: var(--oe-menu-shadow);
    overflow: visible;
}
.ach-ctx-search-row {
    padding: 0 0 8px;
}
.ach-ctx-search-field .q-field__control {
    min-height: 40px !important;
    border-radius: 10px !important;
    background: color-mix(in srgb, var(--oe-bg) 70%, transparent);
}
.ach-ctx-search-field .q-field__native,
.ach-ctx-search-field .q-field__input,
.ach-ctx-search-field input {
    color: var(--oe-text) !important;
}
.ach-ctx-selection {
    display: block;
    padding: 0 4px 8px;
    font-size: 12px;
    color: var(--oe-muted);
    font-weight: 600;
    user-select: none;
}
.ach-ctx-section {
    display: block;
    padding: 10px 6px 6px;
    font-size: 11px;
    color: var(--oe-muted);
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    user-select: none;
}
.ach-ctx-item {
    position: relative;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 9px 10px;
    font-size: 14px;
    color: var(--oe-text);
    cursor: pointer;
    white-space: nowrap;
    user-select: none;
    border-radius: 10px;
}
.ach-ctx-item:hover { background: var(--oe-hover-tint); }
.ach-ctx-item-label {
    flex: 1 1 auto;
    min-width: 0;
}
.ach-ctx-item-arrow {
    margin-left: auto;
    color: var(--oe-muted);
}
.ach-ctx-item-disabled {
    color: var(--oe-muted);
    opacity: 0.7;
    cursor: default;
}
.ach-ctx-item-disabled:hover {
    background: transparent;
}
.ach-ctx-item-has-submenu {
    --ach-ctx-submenu-left: calc(100% - 4px);
    --ach-ctx-submenu-top: -10px;
}
.ach-ctx-item-has-submenu:hover > .ach-ctx-submenu,
.ach-ctx-item-has-submenu:focus-within > .ach-ctx-submenu {
    display: block;
}
.ach-ctx-submenu {
    position: absolute;
    top: var(--ach-ctx-submenu-top);
    left: var(--ach-ctx-submenu-left);
    display: none;
    z-index: 10000;
}
.ach-ctx-submenu-panel {
    min-width: 296px;
    max-height: calc(100vh - 24px);
    overflow: auto;
    padding: 10px;
    border-radius: 14px;
    background: color-mix(in srgb, var(--oe-surface) 97%, #000 3%);
    border: 1px solid color-mix(in srgb, var(--oe-border) 78%, transparent);
    box-shadow: var(--oe-menu-shadow);
}
.ach-ctx-empty {
    display: block;
    padding: 12px 8px 4px;
    font-size: 13px;
    color: var(--oe-muted);
}
.ach-ctx-danger { color: var(--oe-red); }
.ach-palette-shell {
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 3;
    display: flex;
    flex-direction: row;
    width: var(--ach-palette-width);
    min-width: 0;
    max-width: var(--ach-palette-width);
    height: 100%;
    max-height: 100%;
    background: var(--ach-sidebar-glass-bg);
    backdrop-filter: var(--ach-sidebar-glass-filter);
    -webkit-backdrop-filter: var(--ach-sidebar-glass-filter);
    overflow: hidden;
    min-height: 0;
    will-change: width;
    transition: width 0.18s ease, flex-basis 0.18s ease,
        max-width 0.18s ease;
}
.ach-workbench-menu-open .ach-palette-shell {
    pointer-events: none;
}
body:has(.q-menu.ach-menubar-menu) .ach-palette-shell {
    pointer-events: none;
}
.ach-workbench-menu-open .ach-sidebar-resizer {
    pointer-events: none;
}
body:has(.q-menu.ach-menubar-menu) .ach-sidebar-resizer {
    pointer-events: none;
}
.ach-activitybar,
.ach-sidebar-pane-frame,
.ach-palette-header,
.ach-sidebar-pane-stack,
.ach-palette-list {
    position: relative;
    z-index: 1;
}
.ach-activitybar {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    justify-content: flex-start;
    flex: 0 0 var(--ach-activitybar-width);
    width: var(--ach-activitybar-width);
    min-width: var(--ach-activitybar-width);
    padding: 12px 8px;
    border-right: 1px solid var(--oe-border);
    background: var(--ach-sidebar-panel-bg);
}
.ach-activity-button.q-btn--flat,
.ach-activity-button.q-btn--flat .q-icon {
    color: var(--oe-muted) !important;
}
.ach-activity-button {
    position: relative;
    width: 36px !important;
    height: 36px !important;
    color: var(--oe-muted);
    background: transparent;
    border: 1px solid transparent;
    transition: background 0.15s ease, border-color 0.15s ease,
        color 0.15s ease;
}
.ach-activity-button.q-btn--flat:hover,
.ach-activity-button.q-btn--flat:hover .q-icon,
.ach-activity-button:hover {
    color: var(--oe-text);
    background: rgba(255,255,255,0.06);
    border-color: rgba(255,255,255,0.08);
}
.ach-activity-button.q-btn--flat.ach-activity-button-active,
.ach-activity-button.q-btn--flat.ach-activity-button-active .q-icon,
.ach-activity-button-active {
    color: var(--oe-text);
    background: rgba(255,255,255,0.07);
    border-color: rgba(255,255,255,0.12);
}
.ach-activity-button-active::before {
    content: '';
    position: absolute;
    left: -9px;
    top: 7px;
    bottom: 7px;
    width: 3px;
    border-radius: 9999px;
    background: var(--oe-blue);
}
.ach-sidebar-pane-frame {
    display: flex;
    flex-direction: column;
    flex: 0 0 var(--ach-palette-pane-width);
    width: var(--ach-palette-pane-width);
    min-width: 0;
    max-width: var(--ach-palette-pane-width);
    min-height: 0;
    overflow: hidden;
    background: transparent;
    will-change: width;
    transition: width 0.18s ease, flex-basis 0.18s ease,
        max-width 0.18s ease;
}
.ach-palette-header {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 16px;
    border-bottom: 1px solid var(--oe-border);
    background: var(--ach-sidebar-panel-bg-strong);
}
.ach-palette-title {
    display: block;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--oe-muted);
}
.ach-palette-subtitle {
    font-size: 12px;
    color: var(--oe-muted);
    line-height: 1.4;
}
.ach-palette-search {
    margin-top: 2px;
}
.ach-sidebar-pane-stack {
    display: flex;
    flex-direction: column;
    flex: 1 1 auto;
    min-height: 0;
}
.ach-sidebar-pane {
    display: none;
    flex-direction: column;
    flex: 1 1 auto;
    min-width: 0;
    min-height: 0;
}
.ach-sidebar-pane-active {
    display: flex;
}
.ach-sidebar-pane-title {
    padding: 10px 16px 8px;
    border-bottom: 1px solid var(--oe-border);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--oe-muted);
    background: rgba(0,0,0,0.22);
}
.ach-palette-list {
    flex: 1 1 auto;
    min-height: 0;
    overflow-y: auto;
    padding: 10px 8px 14px;
    scrollbar-gutter: stable;
    scrollbar-width: thin;
    scrollbar-color: rgba(255,255,255,0.22) transparent;
}
.ach-palette-list::-webkit-scrollbar {
    width: 10px;
}
.ach-palette-list::-webkit-scrollbar-track {
    background: transparent;
}
.ach-palette-list::-webkit-scrollbar-thumb {
    border: 2px solid transparent;
    border-radius: 9999px;
    background: rgba(255,255,255,0.20);
    background-clip: padding-box;
}
.ach-sidebar-pane-body {
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.ach-palette-section {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 0;
}
.ach-palette-section-collapsed {
    padding-bottom: 0;
}
.ach-palette-section + .ach-palette-section {
    border-top: none;
    padding-top: 0;
}
.ach-palette-section-toggle {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    padding: 4px 6px;
    background: transparent;
    color: inherit;
    border: 1px solid transparent;
    border-radius: 10px;
    cursor: pointer;
    transition: background 0.15s ease, border-color 0.15s ease;
}
.ach-palette-section-toggle:hover {
    background: rgba(255,255,255,0.04);
    border-color: rgba(255,255,255,0.08);
}
.ach-palette-section-toggle:focus-visible {
    outline: 2px solid var(--oe-blue);
    outline-offset: 1px;
}
.ach-palette-section-chevron {
    font-size: 16px;
    color: var(--oe-muted);
}
.ach-palette-section-title {
    flex: 1 1 auto;
    min-width: 0;
    padding: 0;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--oe-muted);
}
.ach-palette-section-count {
    flex: 0 0 auto;
    padding: 1px 8px;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 9999px;
    background: rgba(255,255,255,0.03);
    font-size: 10px;
    font-weight: 700;
    line-height: 1.5;
    color: var(--oe-muted);
}
.ach-palette-section-body {
    display: flex;
    flex-direction: column;
    gap: 2px;
}
.ach-sidebar-empty {
    margin-top: 4px;
}
.ach-palette-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 10px 12px;
    cursor: grab;
    border: 1px solid transparent;
    border-radius: 12px;
    transition: background 0.15s ease, border-color 0.15s ease;
    user-select: none;
}
.ach-palette-item:last-child { border-bottom: none; }
.ach-palette-item:hover {
    background: rgba(255,255,255,0.06);
    border-color: rgba(255,255,255,0.08);
}
.ach-palette-item:active { cursor: grabbing; }
.ach-sidebar-resizer {
    position: absolute;
    top: 0;
    bottom: 0;
    left: var(--ach-palette-width);
    z-index: 4;
    width: 12px;
    transform: translateX(-50%);
    cursor: col-resize;
    background: transparent;
    will-change: left;
    transition: width 0.18s ease, left 0.18s ease, opacity 0.15s ease;
}
.ach-workbench.ach-sidebar-pane-closed .ach-sidebar-resizer {
    width: 8px;
    opacity: 1;
    overflow: visible;
    pointer-events: auto;
}
.ach-sidebar-resizer::before {
    content: '';
    position: absolute;
    top: 0;
    bottom: 0;
    left: 50%;
    width: 1px;
    transform: translateX(-50%);
    background: rgba(255,255,255,0.08);
    transition: background 0.15s ease;
}
.ach-sidebar-resizer:hover::before,
.ach-sidebar-resizer:active::before {
    background: rgba(29,155,240,0.58);
}
.ach-workbench.ach-sidebar-pane-closed .ach-sidebar-resizer::before {
    width: 2px;
    background: rgba(255,255,255,0.14);
}
.ach-sidebar-resizer-grip {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 4px;
    height: 56px;
    transform: translate(-50%, -50%);
    border-radius: 9999px;
    background: rgba(255,255,255,0.12);
    box-shadow: inset 0 0 0 1px rgba(255,255,255,0.08);
    transition: background 0.15s ease;
}
.ach-sidebar-resizer:hover .ach-sidebar-resizer-grip,
.ach-sidebar-resizer:active .ach-sidebar-resizer-grip {
    background: rgba(29,155,240,0.30);
}
.ach-workbench.ach-sidebar-pane-closed .ach-sidebar-resizer-grip {
    width: 3px;
    height: 88px;
    background: rgba(255,255,255,0.18);
}
body.ach-sidebar-resizing,
body.ach-sidebar-resizing * {
    cursor: col-resize !important;
    user-select: none !important;
}
body.ach-sidebar-resizing .ach-palette-shell,
body.ach-sidebar-resizing .ach-sidebar-pane-frame,
body.ach-sidebar-resizing .ach-sidebar-resizer {
    transition: none !important;
}
.ach-palette-item-icon {
    font-size: 18px;
    flex: 0 0 auto;
    margin-top: 2px;
}
.ach-palette-item-name {
    font-size: 13px;
    font-weight: 600;
    color: var(--oe-text);
    line-height: 1.3;
}
.ach-palette-item-desc {
    font-size: 11px;
    color: var(--oe-muted);
    line-height: 1.4;
    margin-top: 2px;
}
.ach-palette-item-pill {
    padding: 1px 6px;
    border: 1px solid var(--oe-border);
    border-radius: 9999px;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.06em;
    line-height: 1.5;
}
.ach-palette-item-pill-source {
    color: var(--oe-blue);
    border-color: var(--oe-blue);
}
.ach-palette-item-pill-event {
    color: var(--oe-red);
    border-color: var(--oe-red);
}
.ach-palette-item-pill-pure {
    color: var(--oe-yellow);
    border-color: var(--oe-yellow);
}
.ach-palette-item-pill-control {
    color: var(--oe-text);
    border-color: var(--oe-text);
}
.ach-palette-item-pill-effect {
    color: var(--oe-green);
    border-color: var(--oe-green);
}
.ach-palette-item-pill-object,
.ach-palette-item-pill-composite {
    color: var(--oe-blue);
    border-color: var(--oe-blue);
}
.ach-type-badge-any,
.ach-pin-btn-type-any {
    --ach-type-colour: #b388ff;
    --ach-pin-colour: #b388ff;
}
.ach-type-badge-exec,
.ach-pin-btn-type-exec {
    --ach-type-colour: var(--oe-text);
    --ach-pin-colour: var(--oe-text);
}
.ach-pin-btn-type-exec {
    width: 14px;
    height: 12px;
    border: none;
    border-radius: 0;
    background: var(--ach-pin-colour);
    clip-path: polygon(0 0, 74% 0, 100% 50%, 74% 100%, 0 100%);
    box-shadow: inset 0 0 0 1px rgba(0,0,0,0.18);
}
.ach-pin-btn-type-exec::after {
    content: '';
    position: absolute;
    inset: 2px;
    background: var(--oe-bg);
    clip-path: polygon(0 0, 72% 0, 100% 50%, 72% 100%, 0 100%);
    pointer-events: none;
}
.ach-pin-btn-type-exec.ach-pin-btn-in,
.ach-pin-btn-type-exec.ach-pin-btn-out {
    border: none;
}
.ach-pin-btn-type-exec.ach-pin-btn-optional {
    opacity: 0.6;
}
.ach-pin-btn-type-exec.ach-pin-btn-filled::after {
    display: none;
}
.ach-pin-btn-type-exec.ach-pin-btn-active {
    box-shadow: none;
    filter: drop-shadow(0 0 4px rgba(29,155,240,0.45));
}
.ach-type-badge-bool,
.ach-pin-btn-type-bool {
    --ach-type-colour: var(--oe-red);
    --ach-pin-colour: var(--oe-red);
}
.ach-type-badge-event,
.ach-pin-btn-type-event {
    --ach-type-colour: var(--oe-red);
    --ach-pin-colour: var(--oe-red);
}
.ach-type-badge-number,
.ach-pin-btn-type-number {
    --ach-type-colour: var(--oe-green);
    --ach-pin-colour: var(--oe-green);
}
.ach-type-badge-int,
.ach-pin-btn-type-int {
    --ach-type-colour: #4caf50;
    --ach-pin-colour: #4caf50;
}
.ach-type-badge-dict,
.ach-pin-btn-type-dict {
    --ach-type-colour: #ff9800;
    --ach-pin-colour: #ff9800;
}
.ach-type-badge-text,
.ach-pin-btn-type-text {
    --ach-type-colour: var(--oe-blue);
    --ach-pin-colour: var(--oe-blue);
}
.ach-type-badge-list,
.ach-pin-btn-type-list {
    --ach-type-colour: var(--oe-yellow);
    --ach-pin-colour: var(--oe-yellow);
}
.ach-type-badge-array,
.ach-pin-btn-type-array {
    --ach-type-colour: var(--oe-yellow);
    --ach-pin-colour: var(--oe-yellow);
}
.ach-type-badge-figure,
.ach-pin-btn-type-figure {
    --ach-type-colour: var(--oe-blue);
    --ach-pin-colour: var(--oe-blue);
}
.ach-type-badge-image,
.ach-pin-btn-type-image {
    --ach-type-colour: var(--oe-blue);
    --ach-pin-colour: var(--oe-blue);
}
.ach-type-badge-object,
.ach-pin-btn-type-object {
    --ach-type-colour: var(--oe-blue);
    --ach-pin-colour: var(--oe-blue);
}
.ach-link-path-type-any,
.ach-link-badge-type-any {
    --ach-link-colour: #b388ff;
}
.ach-link-path-type-exec,
.ach-link-badge-type-exec {
    --ach-link-colour: var(--oe-text);
}
.ach-link-path-type-bool,
.ach-link-badge-type-bool {
    --ach-link-colour: var(--oe-red);
}
.ach-link-path-type-event,
.ach-link-badge-type-event {
    --ach-link-colour: var(--oe-red);
}
.ach-link-path-type-number,
.ach-link-badge-type-number {
    --ach-link-colour: var(--oe-green);
}
.ach-link-path-type-int,
.ach-link-badge-type-int {
    --ach-link-colour: #4caf50;
}
.ach-link-path-type-dict,
.ach-link-badge-type-dict {
    --ach-link-colour: #ff9800;
}
.ach-link-path-type-text,
.ach-link-badge-type-text {
    --ach-link-colour: var(--oe-blue);
}
.ach-link-path-type-list,
.ach-link-badge-type-list {
    --ach-link-colour: var(--oe-yellow);
}
.ach-link-path-type-array,
.ach-link-badge-type-array {
    --ach-link-colour: var(--oe-yellow);
}
.ach-link-path-type-figure,
.ach-link-badge-type-figure {
    --ach-link-colour: var(--oe-blue);
}
.ach-link-path-type-image,
.ach-link-badge-type-image {
    --ach-link-colour: var(--oe-blue);
}
.ach-link-path-type-object,
.ach-link-badge-type-object {
    --ach-link-colour: var(--oe-blue);
}
.ach-statusbar {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    justify-content: center;
    gap: 2px;
    flex: 0 1 min(42vw, 440px);
    min-width: 240px;
    max-width: min(42vw, 440px);
}
.ach-statusbar-label {
    flex: 0 0 auto;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--oe-muted);
}
.ach-statusbar-text {
    width: 100%;
    min-width: 0;
    overflow: hidden;
    text-align: right;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    font-size: 12px;
    line-height: 1.35;
    min-height: calc(12px * 1.35 * 2);
    max-height: calc(12px * 1.35 * 2);
    color: var(--oe-text);
}
"""