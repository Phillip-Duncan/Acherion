"""Shared search-input CSS fragments for Acherion asset bundles."""

SEARCH_CSS = """
.ach-pill-search-input .q-field__control {
    min-height: 40px !important;
    border-radius: 9999px !important;
    background: var(--oe-bg) !important;
}
.ach-pill-search-input .q-field__control:before {
    border-radius: 9999px !important;
    border-color: var(--oe-border) !important;
}
.ach-pill-search-input .q-field--focused .q-field__control:before {
    border-radius: 9999px !important;
    border-color: var(--oe-blue) !important;
    border-width: 2px !important;
}
.ach-pill-search-input .q-field__native,
.ach-pill-search-input .q-field__input,
.ach-pill-search-input input {
    color: var(--oe-text) !important;
}
.ach-pill-search-input input::placeholder {
    color: var(--oe-muted) !important;
    opacity: 1;
}
.ach-pill-search-input .q-field__prepend,
.ach-pill-search-input .q-field__label,
.ach-pill-search-icon {
    color: var(--oe-muted) !important;
}
"""

__all__ = ['SEARCH_CSS']