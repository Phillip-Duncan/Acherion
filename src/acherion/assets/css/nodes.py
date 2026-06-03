"""Node and editor CSS for the Acherion render surface."""

NODE_CSS = """
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
.ach-node-inline-field-bool {
    width: 28px;
}
.ach-node-inline-field-dict {
    width: 144px;
}
.ach-node-inline-preview-summary {
    color: var(--oe-muted);
    font-size: 11px;
    line-height: 20px;
    max-width: 120px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex: 0 1 auto;
}
.ach-node-inline-upload-hidden {
    position: absolute !important;
    width: 0 !important;
    min-width: 0 !important;
    height: 0 !important;
    min-height: 0 !important;
    opacity: 0 !important;
    overflow: hidden !important;
    pointer-events: none !important;
}
.ach-node-inline-upload-trigger {
    flex: 0 0 auto;
    min-width: 22px !important;
    width: 22px !important;
    height: 22px !important;
    min-height: 22px !important;
    padding: 0 !important;
    border-radius: 6px !important;
    background: var(--oe-text) !important;
    color: var(--oe-bg) !important;
}
.ach-node-inline-upload-trigger .q-btn__content {
    gap: 0 !important;
}
.ach-node-inline-upload-trigger .q-icon {
    font-size: 18px !important;
    line-height: 1 !important;
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
"""
