"""Theme helpers for standalone and embedded Acherion workbenches."""

from __future__ import annotations

import importlib.resources
import re
from collections.abc import Mapping
from functools import lru_cache


AcherionThemeOverrides = Mapping[str, str]

_THEME_RESOURCE = 'theme.css'

_DEFAULT_THEME_VARIABLES: dict[str, str] = {
    '--oe-bg': '#000000',
    '--oe-panel': '#000000',
    '--oe-border': '#2F3336',
    '--oe-surface': '#000000',
    '--oe-text': '#E7E9EA',
    '--oe-muted': '#71767B',
    '--oe-blue': '#1D9BF0',
    '--oe-green': '#00BA7C',
    '--oe-red': '#F4212E',
    '--oe-yellow': '#FFD400',
    '--oe-hover-tint': 'rgba(255, 255, 255, 0.07)',
    '--oe-hover-tint-subtle': 'rgba(255, 255, 255, 0.03)',
    '--oe-hover-border': 'rgba(255, 255, 255, 0.4)',
    '--oe-input-hover-border': 'rgba(255, 255, 255, 0.4)',
    '--oe-uploader-hover-border': 'rgba(255, 255, 255, 0.35)',
    '--oe-header-bg': 'rgba(0, 0, 0, 0.85)',
    '--oe-dialog-shadow': '0 8px 40px rgba(0, 0, 0, 0.9)',
    '--oe-legend-bgcolor': 'rgba(22, 24, 28, 0.85)',
    '--oe-uploader-header-bg': 'rgba(255, 255, 255, 0.04)',
    '--oe-inverted-bg': '#E7E9EA',
    '--oe-inverted-text': '#0F1419',
    '--oe-color-scheme': 'dark',
    '--oe-menu-shadow': '0 8px 32px rgba(0, 0, 0, 0.85)',
    '--oe-date-indicator-filter': 'brightness(0) invert(1)',
    '--oe-spin-button-filter': 'invert(1)',
    '--ach-sidebar-glass-bg': 'rgba(0,0,0,0.72)',
    '--ach-sidebar-glass-filter': 'blur(16px) saturate(112%)',
    '--ach-sidebar-panel-bg': 'rgba(255,255,255,0.03)',
    '--ach-sidebar-panel-bg-strong': 'rgba(255,255,255,0.04)',
}

_THEME_ALIAS_TO_VARIABLE: dict[str, str] = {
    'bg': '--oe-bg',
    'panel': '--oe-panel',
    'border': '--oe-border',
    'surface': '--oe-surface',
    'text': '--oe-text',
    'muted': '--oe-muted',
    'blue': '--oe-blue',
    'green': '--oe-green',
    'red': '--oe-red',
    'yellow': '--oe-yellow',
    'primary': '--oe-blue',
    'secondary': '--oe-muted',
    'accent': '--oe-blue',
    'positive': '--oe-green',
    'negative': '--oe-red',
    'warning': '--oe-yellow',
    'info': '--oe-blue',
    'hover_tint': '--oe-hover-tint',
    'hover_tint_subtle': '--oe-hover-tint-subtle',
    'hover_border': '--oe-hover-border',
    'input_hover_border': '--oe-input-hover-border',
    'uploader_hover_border': '--oe-uploader-hover-border',
    'header_bg': '--oe-header-bg',
    'dialog_shadow': '--oe-dialog-shadow',
    'legend_bgcolor': '--oe-legend-bgcolor',
    'uploader_header_bg': '--oe-uploader-header-bg',
    'inverted_bg': '--oe-inverted-bg',
    'inverted_text': '--oe-inverted-text',
    'color_scheme': '--oe-color-scheme',
    'menu_shadow': '--oe-menu-shadow',
    'date_indicator_filter': '--oe-date-indicator-filter',
    'spin_button_filter': '--oe-spin-button-filter',
    'sidebar_glass_bg': '--ach-sidebar-glass-bg',
    'sidebar_glass_filter': '--ach-sidebar-glass-filter',
    'sidebar_panel_bg': '--ach-sidebar-panel-bg',
    'sidebar_panel_bg_strong': '--ach-sidebar-panel-bg-strong',
}

_COMMENT_RE = re.compile(r'/\*.*?\*/', flags=re.S)
_RULE_RE = re.compile(r'(?s)([^{}]+)\{([^{}]*)\}')


@lru_cache(maxsize=1)
def _load_default_theme_css() -> str:
    """Return packaged Acherion theme CSS."""
    return importlib.resources.files('acherion').joinpath(
        _THEME_RESOURCE
    ).read_text(encoding='utf-8')


def _resolve_theme_variable_name(key: str) -> str:
    """Normalize one public theme key into a CSS custom-property name."""
    clean_key = str(key or '').strip()
    if not clean_key:
        raise ValueError('Theme override keys must not be empty.')
    if clean_key.startswith('--'):
        return clean_key
    variable_name = _THEME_ALIAS_TO_VARIABLE.get(clean_key)
    if variable_name is None:
        raise ValueError(
            'Unknown theme override key: '
            f'{clean_key!r}. Use a supported alias or a raw CSS variable name.'
        )
    return variable_name


def normalize_acherion_theme_overrides(
    theme_overrides: AcherionThemeOverrides | None,
) -> dict[str, str]:
    """Return normalized CSS custom-property overrides for Acherion."""
    normalized: dict[str, str] = {}
    for key, value in dict(theme_overrides or {}).items():
        clean_value = str(value or '').strip()
        if not clean_value:
            continue
        normalized[_resolve_theme_variable_name(key)] = clean_value
    return normalized


def acherion_ui_colors(
    theme_overrides: AcherionThemeOverrides | None = None,
) -> dict[str, str]:
    """Return NiceGUI/Quasar color tokens derived from Acherion theme values."""
    theme_values = dict(_DEFAULT_THEME_VARIABLES)
    theme_values.update(normalize_acherion_theme_overrides(theme_overrides))
    return {
        'primary': theme_values['--oe-blue'],
        'secondary': theme_values['--oe-muted'],
        'accent': theme_values['--oe-blue'],
        'positive': theme_values['--oe-green'],
        'negative': theme_values['--oe-red'],
        'warning': theme_values['--oe-yellow'],
        'info': theme_values['--oe-blue'],
    }


def build_acherion_theme_override_css(
    *,
    scope_selector: str,
    theme_overrides: AcherionThemeOverrides | None = None,
) -> str:
    """Build CSS custom-property overrides for one Acherion scope."""
    clean_scope_selector = str(scope_selector or '').strip()
    if not clean_scope_selector:
        raise ValueError('A scope selector is required for theme overrides.')
    normalized = normalize_acherion_theme_overrides(theme_overrides)
    if not normalized:
        return ''
    lines = [f'{clean_scope_selector} {{']
    lines.extend(
        f'    {variable_name}: {value};'
        for variable_name, value in normalized.items()
    )
    lines.append('}')
    return '\n'.join(lines)


def _scope_selector(selector: str, scope_selector: str) -> tuple[str, ...]:
    """Return one CSS selector rewritten to target an Acherion subtree."""
    clean_selector = str(selector or '').strip()
    if not clean_selector:
        return ()
    if clean_selector == ':root':
        return (scope_selector,)
    if clean_selector in {'body', '.q-app', '.q-page', '.nicegui-content'}:
        return (scope_selector,)
    if clean_selector == '*':
        return (scope_selector, f'{scope_selector} *')
    if clean_selector == '*::before':
        return (f'{scope_selector}::before', f'{scope_selector} *::before')
    if clean_selector == '*::after':
        return (f'{scope_selector}::after', f'{scope_selector} *::after')
    return (f'{scope_selector} {clean_selector}',)


@lru_cache(maxsize=64)
def build_scoped_acherion_theme_css(scope_selector: str) -> str:
    """Return the packaged Acherion theme CSS scoped to one container."""
    clean_scope_selector = str(scope_selector or '').strip()
    if not clean_scope_selector:
        raise ValueError('A scope selector is required for scoped theme CSS.')
    if clean_scope_selector == ':root':
        return _load_default_theme_css()

    raw_css = _COMMENT_RE.sub('', _load_default_theme_css())
    scoped_rules: list[str] = []
    for match in _RULE_RE.finditer(raw_css):
        selectors = [
            selector.strip()
            for selector in str(match.group(1) or '').split(',')
            if selector.strip()
        ]
        declarations = str(match.group(2) or '').strip()
        if not selectors or not declarations:
            continue
        scoped_selectors: list[str] = []
        seen_selectors: set[str] = set()
        for selector in selectors:
            for scoped_selector in _scope_selector(selector, clean_scope_selector):
                if scoped_selector in seen_selectors:
                    continue
                seen_selectors.add(scoped_selector)
                scoped_selectors.append(scoped_selector)
        if not scoped_selectors:
            continue
        scoped_rules.append(
            ',\n'.join(scoped_selectors) + ' {\n' + declarations + '\n}'
        )
    return '\n\n'.join(scoped_rules)


def build_embedded_acherion_theme_css(
    *,
    scope_selector: str,
    theme_overrides: AcherionThemeOverrides | None = None,
) -> str:
    """Return fully scoped Acherion theme CSS for one embedded workbench."""
    base_css = build_scoped_acherion_theme_css(scope_selector)
    override_css = build_acherion_theme_override_css(
        scope_selector=scope_selector,
        theme_overrides=theme_overrides,
    )
    if not override_css:
        return base_css
    return base_css + '\n\n' + override_css


__all__ = [
    'AcherionThemeOverrides',
    'acherion_ui_colors',
    'build_acherion_theme_override_css',
    'build_embedded_acherion_theme_css',
    'build_scoped_acherion_theme_css',
    'normalize_acherion_theme_overrides',
]