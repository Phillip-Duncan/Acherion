"""CSS and client-side JavaScript for the visual-logic designer.

Coordinate system: node positions are stored in world-space CSS pixels with
the logical origin hidden inside a much larger stage. The initial pan offsets
the stage so world-space coordinates still appear in their old screen-space
locations. Panning moves the stage via CSS transform.
worldPoint() converts client coords to world-space by subtracting the stage
origin and dividing by scale.
"""

from __future__ import annotations

from acherion.constants import _CANVAS_WORLD_WIDTH, _GRID_SNAP_SIZE


_ACH_CSS: str = """
.ach-workbench {
    --ach-activitybar-width: 52px;
    --ach-palette-pane-default-width: 244px;
    --ach-palette-pane-width: var(--ach-palette-pane-default-width);
    --ach-palette-pane-min-width: 188px;
    --ach-palette-pane-max-width: 460px;
    --ach-palette-pane-collapse-threshold: 124px;
    --ach-sidebar-glass-bg: color-mix(
        in srgb,
        var(--oe-bg) 92%,
        var(--oe-text) 8%
    );
    --ach-sidebar-glass-filter: blur(16px) saturate(112%);
    --ach-sidebar-panel-bg: color-mix(
        in srgb,
        var(--oe-text) 3%,
        transparent
    );
    --ach-sidebar-panel-bg-strong: color-mix(
        in srgb,
        var(--oe-text) 5%,
        transparent
    );
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
    flex: 0 0 72px;
    gap: 16px;
    height: 72px;
    min-height: 72px;
    padding: 10px 14px;
    border-bottom: 1px solid var(--oe-border);
    box-sizing: border-box;
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
    background: color-mix(in srgb, var(--oe-text) 14%, transparent);
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
    background: color-mix(in srgb, var(--oe-bg) 88%, var(--oe-text) 12%);
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
.ach-menubar-menu .q-item:hover,
.ach-menubar-menu .q-item--active {
    background: var(--oe-hover-tint) !important;
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
.ach-node {
    position: absolute;
    width: 360px;
    border: 1px solid var(--oe-border);
    border-radius: 14px;
    overflow: hidden;
    background: var(--oe-bg);
    z-index: 1;
    cursor: grab;
}
.ach-node-dragging { cursor: grabbing; z-index: 3; }
.ach-node-head {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 12px;
    border-bottom: 1px solid var(--oe-border);
    background: var(--ach-sidebar-panel-bg);
}
.ach-node-drag { color: var(--oe-muted); }
.ach-node .q-btn,
.ach-node .q-field,
.ach-node input,
.ach-node textarea,
.ach-node select { cursor: auto; }
.ach-node-body {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 10px 12px 12px;
}
.ach-node-preview {
    display: flex;
    flex-direction: column;
    gap: 4px;
    align-self: stretch;
    margin: 8px -12px 0;
    padding: 8px 12px 0;
    border-top: 1px solid var(--oe-border);
}
.ach-node-preview-title {
    color: var(--oe-muted);
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.ach-node-preview-value {
    color: var(--oe-text);
    font-size: 12px;
    line-height: 1.35;
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    word-break: break-word;
}
.ach-exec-row {
    min-height: 22px;
    padding: 0 2px 2px;
}
.ach-exec-row-spacer {
    width: 14px;
    height: 12px;
    flex: 0 0 auto;
}
.ach-wire-row {
    display: flex;
    align-items: center;
    gap: 8px;
    min-height: 34px;
    padding: 0 2px;
}
.ach-wire-label { font-size: 12px; color: var(--oe-text); }
.ach-wire-row-inline {
    justify-content: space-between;
    gap: 10px;
}
.ach-wire-inline-center {
    flex: 1 1 auto;
    min-width: 0;
    align-items: flex-start;
    justify-content: center;
    gap: 4px;
    text-align: left;
}
.ach-wire-inline-meta {
    align-items: center;
    justify-content: flex-start;
    gap: 6px;
    min-width: 0;
    flex-wrap: wrap;
}
.ach-wire-row-inline .ach-wire-label {
    max-width: 190px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    text-align: left;
}
.ach-wire-row-inline .ach-wire-source {
    max-width: 100%;
    text-align: left;
}
.ach-wire-source {
    color: var(--oe-muted);
    font-size: 11px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 150px;
}
.ach-node-inline-field {
    flex: 0 0 auto;
    margin: 0;
}
.ach-node-inline-field-number {
    width: 112px;
}
.ach-node-inline-field-text {
    width: 112px;
}
.ach-node-inline-field .q-field__bottom,
.ach-node-inline-field .q-field__append,
.ach-node-inline-field .q-field__prepend {
    display: none !important;
}
.ach-node-inline-field .q-field__control {
    min-height: 22px !important;
    background: var(--ach-sidebar-panel-bg-strong) !important;
    border-radius: 6px !important;
}
.ach-node-inline-field.q-field--outlined .q-field__control:before,
.ach-node-inline-field.q-field--outlined .q-field__control:after {
    border-color: var(--oe-border) !important;
}
.ach-node-inline-field .q-field__native,
.ach-node-inline-field input {
    padding: 0 5px !important;
    min-height: 20px !important;
    font-size: 15px !important;
    line-height: 20px !important;
    color: var(--oe-text) !important;
}
.ach-node-inline-field-number .q-field__native,
.ach-node-inline-field-number input {
    appearance: textfield;
    -moz-appearance: textfield;
    text-align: left;
}
.ach-node-inline-field-number input::-webkit-outer-spin-button,
.ach-node-inline-field-number input::-webkit-inner-spin-button {
    -webkit-appearance: none;
    margin: 0;
}
.ach-type-badge {
    --ach-type-colour: var(--oe-muted);
    font-size: 10px;
    font-family: ui-monospace, 'Cascadia Code', monospace;
    padding: 1px 5px;
    border: 1px solid var(--ach-type-colour);
    border-radius: 9999px;
    color: var(--ach-type-colour);
    background: var(--ach-sidebar-panel-bg-strong);
    flex: 0 0 auto;
    white-space: nowrap;
    user-select: none;
}
.ach-pin-incompatible {
    opacity: 0.35;
}
.ach-pin-btn {
    --ach-pin-colour: var(--oe-muted);
    width: 14px;
    height: 14px;
    border-radius: 9999px;
    position: relative;
    flex: 0 0 auto;
    cursor: pointer;
    border: 2px solid color-mix(in srgb, var(--oe-text) 12%, transparent);
    background: transparent;
}
.ach-pin-btn-in { border-color: var(--ach-pin-colour); }
.ach-pin-btn-out { border-color: var(--ach-pin-colour); }
.ach-pin-btn-optional.ach-pin-btn-in {
    border-color: var(--ach-pin-colour);
    border-style: dashed;
}
.ach-pin-btn-filled.ach-pin-btn-in { background: var(--ach-pin-colour); }
.ach-pin-btn-filled.ach-pin-btn-out { background: var(--ach-pin-colour); }
.ach-wire-row-optional { opacity: 0.7; }
.ach-opt-badge {
    font-size: 9px;
    font-family: ui-monospace, 'Cascadia Code', monospace;
    padding: 1px 4px;
    border: 1px dashed var(--oe-muted);
    border-radius: 9999px;
    color: var(--oe-muted);
    flex: 0 0 auto;
    user-select: none;
}
.ach-pin-btn-active {
    box-shadow: 0 0 0 4px rgba(29,155,240,0.20);
    border-color: rgba(29,155,240,0.9);
}
.ach-pin-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 6px 8px;
    border: 1px solid var(--oe-border);
    border-radius: 8px;
    background: var(--ach-sidebar-panel-bg);
    font-size: 12px;
    color: var(--oe-muted);
}
.ach-pin {
    width: 10px;
    height: 10px;
    border-radius: 9999px;
    display: inline-block;
    flex: 0 0 auto;
}
.ach-pin-in { background: var(--oe-yellow); }
.ach-pin-out { background: var(--oe-blue); }
.ach-badge {
    padding: 2px 8px;
    border: 1px solid var(--oe-border);
    border-radius: 9999px;
    color: var(--oe-muted);
    font-size: 11px;
    line-height: 1.4;
}
.ach-empty {
    padding: 18px;
    border: 1px dashed var(--oe-border);
    border-radius: 12px;
    color: var(--oe-muted);
    background: var(--ach-sidebar-panel-bg);
}
.ach-tone-source .ach-node-head { border-left: 4px solid var(--oe-blue); }
.ach-tone-event .ach-node-head { border-left: 4px solid var(--oe-red); }
.ach-tone-pure .ach-node-head { border-left: 4px solid var(--oe-yellow); }
.ach-tone-control .ach-node-head { border-left: 4px solid var(--oe-text); }
.ach-tone-effect .ach-node-head { border-left: 4px solid var(--oe-green); }
.ach-tone-object .ach-node-head { border-left: 4px solid var(--oe-blue); }
.ach-tone-composite .ach-node-head { border-left: 4px solid var(--oe-blue); }
.ach-node-kind-icon-source { color: var(--oe-blue); }
.ach-node-kind-icon-event { color: var(--oe-red); }
.ach-node-kind-icon-pure { color: var(--oe-yellow); }
.ach-node-kind-icon-control { color: var(--oe-text); }
.ach-node-kind-icon-effect { color: var(--oe-green); }
.ach-node-kind-icon-object { color: var(--oe-blue); }
.ach-node-kind-icon-composite { color: var(--oe-blue); }
.ach-function-box {
    z-index: 0;
    border-radius: 20px;
    border: 1px dashed rgba(29,155,240,0.45);
    background: rgba(29,155,240,0.04);
    overflow: visible;
    pointer-events: none;
}
.ach-function-box > * { pointer-events: auto; }
.ach-function-box.ach-node-selected {
    z-index: 0;
    outline-offset: -3px;
}
.ach-function-box-head {
    display: flex;
    align-items: center;
    gap: 12px;
    min-height: 58px;
    padding: 14px 16px;
    border-bottom: 1px dashed rgba(29,155,240,0.24);
    background: rgba(29,155,240,0.10);
}
.ach-function-box-icon {
    color: var(--oe-blue);
    font-size: 18px;
}
.ach-function-box-title {
    max-width: 260px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 14px;
    font-weight: 700;
    color: var(--oe-text);
    line-height: 1.2;
}
.ach-function-box-subtitle {
    font-size: 11px;
    color: var(--oe-muted);
    line-height: 1.3;
}
.ach-function-box-side {
    position: absolute;
    top: 122px;
    bottom: 24px;
    width: 148px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 0 10px;
    overflow: visible;
}
.ach-function-box-side-left { left: 12px; }
.ach-function-box-side-right { right: 12px; }
.ach-function-box-port-card {
    position: relative;
    border: 1px solid rgba(29,155,240,0.18);
    border-radius: 12px;
    background: var(--ach-sidebar-panel-bg-strong);
    padding: 8px 10px;
    min-height: 40px;
    min-width: 0;
    overflow: hidden;
}
.ach-function-box-port-card-in .ach-function-box-port-anchor,
.ach-function-box-port-card-in .ach-function-box-port-anchor-shadow {
    position: absolute;
    left: -19px;
    top: 50%;
    transform: translateY(-50%);
}
.ach-function-box-port-card-out .ach-function-box-port-anchor,
.ach-function-box-port-card-out .ach-function-box-port-anchor-shadow {
    position: absolute;
    right: -19px;
    top: 50%;
    transform: translateY(-50%);
}
.ach-function-box-port-row {
    justify-content: space-between;
    gap: 8px;
    min-width: 0;
}
.ach-function-box-port-row-right .ach-wire-label,
.ach-function-box-port-row-right .ach-wire-source {
    text-align: right;
}
.ach-port-anchor-stack {
    position: relative;
    width: 14px;
    height: 14px;
    flex: 0 0 auto;
}
.ach-port-anchor-stack .ach-pin-anchor {
    position: absolute;
    inset: 0;
}
.ach-port-anchor-shadow {
    opacity: 0;
    pointer-events: none;
}
.ach-function-box-side .ach-wire-row {
    min-height: 24px;
    padding: 0;
}
.ach-function-box-side .ach-wire-label {
    font-size: 11px;
    display: block;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.ach-function-box-side .ach-wire-source {
    display: block;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.ach-function-box-side .ach-type-badge {
    font-size: 9px;
}
.ach-node-editor-scroll {
    flex: 1 1 auto;
    min-height: 0;
    overflow-y: auto;
    padding-right: 8px;
}
.ach-node-editor-scroll > * {
    flex-shrink: 0;
    width: 100%;
}
.ach-node-editor-fields {
    display: flex;
    flex-direction: column;
    gap: 16px;
}
.ach-node-editor-fields > * {
    flex-shrink: 0;
}
.ach-row-child-expansion > .q-expansion-item__container {
    border: 1px solid var(--oe-border);
    border-radius: inherit;
    overflow: hidden;
    transition: box-shadow 0.15s ease, border-color 0.15s ease;
}
.ach-row-child-expansion:hover > .q-expansion-item__container,
.ach-row-child-expansion.q-expansion-item--expanded > .q-expansion-item__container {
    border-color: var(--oe-blue);
    box-shadow: inset 0 0 0 1px var(--oe-blue);
}
.ach-row-child-expansion-header {
    min-height: 0;
    padding: 8px 10px 8px 12px;
    background: transparent !important;
}
.ach-row-child-expansion-header:hover,
.ach-row-child-expansion-header.q-manual-focusable--focused,
.ach-row-child-expansion-header.q-manual-focusable--focused:hover {
    background: transparent !important;
}
.ach-row-child-expansion-header .q-focus-helper {
    opacity: 0 !important;
    background: transparent !important;
}
.ach-row-child-expansion-header .q-item__section--main {
    min-width: 0;
    padding-right: 8px;
}
.ach-row-child-expansion-header .q-item__section--side {
    padding-left: 10px;
    padding-right: 10px;
}
.ach-row-child-expansion-toggle {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    line-height: 1;
    color: var(--oe-text) !important;
    opacity: 1 !important;
}
.ach-row-child-expansion-toggle,
.ach-row-child-expansion-toggle .q-icon {
    font-size: 1.65rem !important;
    line-height: 1 !important;
    color: var(--oe-text) !important;
    opacity: 1 !important;
}
.ach-row-child-expansion-toggle .q-icon {
    width: 1em;
    height: 1em;
}
.ach-row-child-header {
    gap: 6px;
    padding-right: 8px;
}
.ach-row-child-header-action {
    position: relative;
    z-index: 1;
}
.ach-row-child-header-action .q-btn__content {
    position: relative;
    z-index: 1;
}
.ach-row-child-header-delete {
    margin-right: 8px;
}
.ach-editor-field .q-field__control {
    min-height: 48px !important;
}
.ach-editor-field .q-field__native,
.ach-editor-field .q-field__input {
    min-height: 48px !important;
}
.ach-node-editor-card .q-select.ach-editor-field .q-field__control {
    min-height: 40px !important;
}
.ach-node-editor-card .q-select.ach-editor-field .q-field__native,
.ach-node-editor-card .q-select.ach-editor-field .q-field__input {
    min-height: 24px !important;
}
.ach-node-editor-card .q-checkbox__label {
    color: var(--oe-text) !important;
}
.ach-node-selected {
    outline: 2px solid rgba(29,155,240,0.85);
    outline-offset: 2px;
    z-index: 2;
}
.ach-shell-selecting { cursor: crosshair; }
.ach-shell-selecting,
.ach-shell-selecting * { user-select: none; }
.ach-rubber-band {
    position: absolute;
    border: 1.5px dashed rgba(29,155,240,0.7);
    background: rgba(29,155,240,0.05);
    pointer-events: none;
    z-index: 10;
    border-radius: 3px;
    display: none;
}
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
    box-shadow: inset -1px 0 0 color-mix(in srgb, var(--oe-text) 6%, transparent);
    overflow: hidden;
    min-height: 0;
    will-change: width;
    transition: width 0.18s ease, flex-basis 0.18s ease,
        max-width 0.18s ease;
}
.ach-palette-shell::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(
        180deg,
        color-mix(in srgb, var(--oe-text) 4%, transparent) 0%,
        color-mix(in srgb, var(--oe-text) 2%, transparent) 18%,
        color-mix(in srgb, var(--oe-text) 1%, transparent) 100%
    );
    opacity: 1;
    pointer-events: none;
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
    background: var(--oe-hover-tint-subtle);
    border-color: color-mix(in srgb, var(--oe-text) 10%, transparent);
}
.ach-activity-button.q-btn--flat.ach-activity-button-active,
.ach-activity-button.q-btn--flat.ach-activity-button-active .q-icon,
.ach-activity-button-active {
    color: var(--oe-text);
    background: var(--oe-hover-tint);
    border-color: color-mix(in srgb, var(--oe-text) 14%, transparent);
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
    background: var(--ach-sidebar-panel-bg-strong);
}
.ach-palette-list {
    flex: 1 1 auto;
    min-height: 0;
    overflow-y: auto;
    padding: 10px 8px 14px;
    scrollbar-gutter: stable;
    scrollbar-width: thin;
    scrollbar-color: color-mix(in srgb, var(--oe-text) 22%, transparent) transparent;
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
    background: color-mix(in srgb, var(--oe-text) 20%, transparent);
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
    padding: 0 0 10px;
}
.ach-palette-section + .ach-palette-section {
    border-top: 1px solid var(--oe-border);
    padding-top: 12px;
}
.ach-palette-section-title {
    padding: 8px 6px 8px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--oe-muted);
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
    background: var(--oe-hover-tint-subtle);
    border-color: color-mix(in srgb, var(--oe-text) 10%, transparent);
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
    background: color-mix(in srgb, var(--oe-text) 12%, transparent);
    transition: background 0.15s ease;
}
.ach-sidebar-resizer:hover::before,
.ach-sidebar-resizer:active::before {
    background: rgba(29,155,240,0.58);
}
.ach-workbench.ach-sidebar-pane-closed .ach-sidebar-resizer::before {
    width: 2px;
    background: color-mix(in srgb, var(--oe-text) 18%, transparent);
}
.ach-sidebar-resizer-grip {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 4px;
    height: 56px;
    transform: translate(-50%, -50%);
    border-radius: 9999px;
    background: color-mix(in srgb, var(--oe-text) 14%, transparent);
    box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--oe-text) 10%, transparent);
    transition: background 0.15s ease;
}
.ach-sidebar-resizer:hover .ach-sidebar-resizer-grip,
.ach-sidebar-resizer:active .ach-sidebar-resizer-grip {
    background: rgba(29,155,240,0.30);
}
.ach-workbench.ach-sidebar-pane-closed .ach-sidebar-resizer-grip {
    width: 3px;
    height: 88px;
    background: color-mix(in srgb, var(--oe-text) 22%, transparent);
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
""".replace('__CANVAS_STAGE_WIDTH__', str(_CANVAS_WORLD_WIDTH * 2)).replace(
    '__ACH_GRID_SNAP_SIZE__',
    str(_GRID_SNAP_SIZE),
)


# Client helper - coordinates are stored in world-space CSS pixels.
# worldPoint(viewport, clientX, clientY) returns world-space (x, y):
#   x = (clientX - stageRect.left) / scale - originX
#   y = (clientY - stageRect.top) / scale - originY
# Pan state stored in viewport.dataset.{panX, panY, scale}.
# The stage origin is hidden via CSS custom properties on .ach-canvas.
_ACH_CLIENT_JS: str = """
(() => {
    if (window.__oeAcherion) return;
    window.__oeAcherion = {
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
            this.updateConnections(stage);
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
                childList: true, subtree: true,
                attributes: true,
                attributeFilter: ['style', 'class'],
            });
            if (window.IntersectionObserver) {
                const io = new IntersectionObserver(
                    (entries) => {
                        if (entries.some(e => e.isIntersecting)) queue();
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
        findNode(stage, nodeId) {
            return Array.from(stage.querySelectorAll('.ach-node')).find(
                n => n.dataset.nodeId === String(nodeId)
            ) || null;
        },
        findPin(stage, nodeId, direction, pinIndex) {
            return Array.from(stage.querySelectorAll('.ach-pin-anchor')).find(
                p =>
                    p.dataset.nodeId === String(nodeId) &&
                    p.dataset.pinDirection === String(direction) &&
                    p.dataset.pinIndex === String(pinIndex)
            ) || null;
        },
        worldPoint(viewport, clientX, clientY) {
            const stage = this.stage(viewport);
            if (!stage) return {x: 0, y: 0};
            const rect = stage.getBoundingClientRect();
            const sc = this.scale(viewport);
            const origin = this.origin(stage);
            return {
                x: (clientX - rect.left) / sc - origin.x,
                y: (clientY - rect.top) / sc - origin.y,
            };
        },
        pinCenter(stage, nodeId, direction, pinIndex) {
            const viewport = stage.closest('.ach-shell');
            const sc = this.scale(viewport);
            const stageRect = stage.getBoundingClientRect();
            const pin = this.findPin(stage, nodeId, direction, pinIndex);
            if (!pin) return null;
            const rect = pin.getBoundingClientRect();
            return {
                x: (rect.left + rect.width / 2 - stageRect.left) / sc,
                y: (rect.top + rect.height / 2 - stageRect.top) / sc,
            };
        },
        curve(sx, sy, ex, ey) {
            const dist = Math.abs(ex - sx);
            const t = Math.max(96, Math.min(240, dist * 0.55 || 96));
            let c1 = sx + t, c2 = ex - t;
            if (ex < sx) {
                const loop = Math.max(140, Math.min(300,
                    (sx - ex) * 0.7 || 140));
                c1 = sx + loop; c2 = ex - loop;
            }
            return `M ${sx} ${sy} C ${c1} ${sy}, ${c2} ${ey}, ${ex} ${ey}`;
        },
        updateConnections(stage) {
            if (!stage) return;
            stage.querySelectorAll('[data-connection-id]').forEach(path => {
                const src = path.dataset.sourceNodeId || '';
                const tgt = path.dataset.targetNodeId || '';
                const inIdx = parseInt(path.dataset.inputIndex || '0', 10);
                const outIdx = parseInt(path.dataset.outputIndex || '0', 10);
                const s = this.pinCenter(stage, src, 'out', outIdx);
                const e = this.pinCenter(stage, tgt, 'in', inIdx);
                if (!s || !e) return;
                path.setAttribute('d', this.curve(s.x, s.y, e.x, e.y));
            });
        },
        moveNode(stage, nodeId, left, top) {
            const node = this.findNode(stage, nodeId);
            if (!node) return;
            const origin = this.origin(stage);
            node.style.left = `${Math.round(left + origin.x)}px`;
            node.style.top = `${Math.round(top + origin.y)}px`;
            this.updateConnections(stage);
        },
        updateRubberBand(vp, x1, y1, x2, y2) {
            let rb = vp.querySelector('.ach-rubber-band');
            if (!rb) {
                rb = document.createElement('div');
                rb.className = 'ach-rubber-band';
                vp.appendChild(rb);
            }
            const stage = this.stage(vp);
            if (!stage) return;
            const sc = this.scale(vp);
            const origin = this.origin(stage);
            const sr = stage.getBoundingClientRect();
            const vr = vp.getBoundingClientRect();
            const sx = (Math.min(x1, x2) + origin.x) * sc + (sr.left - vr.left);
            const sy = (Math.min(y1, y2) + origin.y) * sc + (sr.top - vr.top);
            rb.style.display = 'block';
            rb.style.left = sx + 'px';
            rb.style.top = sy + 'px';
            rb.style.width = (Math.abs(x2 - x1) * sc) + 'px';
            rb.style.height = (Math.abs(y2 - y1) * sc) + 'px';
        },
        clearRubberBand(vp) {
            const rb = vp.querySelector('.ach-rubber-band');
            if (rb) rb.style.display = 'none';
        },
        nodesInRect(stage, x1, y1, x2, y2) {
            const minX = Math.min(x1, x2), maxX = Math.max(x1, x2);
            const minY = Math.min(y1, y2), maxY = Math.max(y1, y2);
            const origin = this.origin(stage);
            const ids = [];
            stage.querySelectorAll('.ach-node').forEach(n => {
                const nl = parseFloat(n.style.left || '0');
                const nt = parseFloat(n.style.top || '0');
                const cx = nl - origin.x + n.offsetWidth / 2;
                const cy = nt - origin.y + n.offsetHeight / 2;
                if (cx >= minX && cx <= maxX && cy >= minY && cy <= maxY)
                    ids.push(n.dataset.nodeId);
            });
            return ids;
        },
    };

    let observeQueued = false;
    const queueObserveAll = () => {
        if (observeQueued) return;
        observeQueued = true;
        requestAnimationFrame(() => {
            observeQueued = false;
            window.__oeAcherion?.observeAll(document);
        });
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', queueObserveAll, {
            once: true,
        });
    } else {
        queueObserveAll();
    }

    const bodyObserver = new MutationObserver(queueObserveAll);
    const observeBody = () => {
        if (!document.body) {
            requestAnimationFrame(observeBody);
            return;
        }
        bodyObserver.observe(document.body, {
            childList: true,
            subtree: true,
        });
        queueObserveAll();
    };
    observeBody();
})();
""".replace('__ACH_GRID_SNAP_SIZE__', str(_GRID_SNAP_SIZE))
