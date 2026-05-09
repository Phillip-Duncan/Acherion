"""Preference schema and runtime helpers for Acherion workbenches."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, cast, get_args

from nicegui.elements.codemirror.codemirror import SUPPORTED_THEMES


ShortcutGroup = Literal['Selection', 'View']
ShortcutTriggerKind = Literal['keyboard', 'mouse']
ShortcutInteractionKind = Literal['keyboard', 'click', 'drag', 'wheel']

_KEYBOARD_BASE_KEYS: tuple[str, ...] = (
    'Backspace',
    'Delete',
    'Escape',
    'Enter',
    'Space',
    'Tab',
    'ArrowUp',
    'ArrowDown',
    'ArrowLeft',
    'ArrowRight',
    'Home',
    'End',
    'PageUp',
    'PageDown',
)
_KEYBOARD_MODIFIER_COMBINATIONS: tuple[tuple[str, ...], ...] = (
    (),
    ('Ctrl',),
    ('Shift',),
    ('Alt',),
    ('Mod',),
    ('Ctrl', 'Shift'),
    ('Alt', 'Shift'),
    ('Mod', 'Shift'),
)
_MOUSE_MODIFIER_COMBINATIONS: tuple[tuple[str, ...], ...] = (
    (),
    ('Ctrl',),
    ('Shift',),
    ('Alt',),
    ('Mod',),
    ('Ctrl', 'Shift'),
    ('Alt', 'Shift'),
    ('Mod', 'Shift'),
)
_SHORTCUT_TOKEN_ALIASES: dict[str, str] = {
    'CMD': 'META',
    'COMMAND': 'META',
    'ESC': 'ESCAPE',
    'DEL': 'DELETE',
    'SPACEBAR': 'SPACE',
    ' ': 'SPACE',
    'UP': 'ARROWUP',
    'DOWN': 'ARROWDOWN',
    'LEFT': 'ARROWLEFT',
    'RIGHT': 'ARROWRIGHT',
}
_SHORTCUT_MODIFIER_TOKENS: tuple[str, ...] = (
    'CTRL',
    'SHIFT',
    'ALT',
    'META',
    'MOD',
)
_SHORTCUT_MOUSE_INTERACTIONS: tuple[str, ...] = (
    'CLICK',
    'DRAG',
    'WHEEL',
)
_SHORTCUT_MODIFIER_TOKEN_SET = frozenset(_SHORTCUT_MODIFIER_TOKENS)
_SHORTCUT_MOUSE_INTERACTION_SET = frozenset(_SHORTCUT_MOUSE_INTERACTIONS)


@dataclass(frozen=True)
class AcherionShortcutDefinition:
    """Describe one configurable workbench shortcut."""

    identifier: str
    group: ShortcutGroup
    label: str
    description: str
    default_binding: str
    trigger_kind: ShortcutTriggerKind
    interaction_kind: ShortcutInteractionKind


SUPPORTED_CODE_EDITOR_THEMES: tuple[str, ...] = tuple(
    sorted(cast(tuple[str, ...], get_args(SUPPORTED_THEMES)))
)
DEFAULT_CODE_EDITOR_THEME = 'vscodeDark'

SHORTCUT_DEFINITIONS: tuple[AcherionShortcutDefinition, ...] = (
    AcherionShortcutDefinition(
        identifier='delete_selection_primary',
        group='Selection',
        label='Delete selection',
        description='Remove selected nodes or the selected connection.',
        default_binding='Delete',
        trigger_kind='keyboard',
        interaction_kind='keyboard',
    ),
    AcherionShortcutDefinition(
        identifier='clear_selection',
        group='Selection',
        label='Clear selection',
        description='Clear the current node or connection selection.',
        default_binding='Escape',
        trigger_kind='keyboard',
        interaction_kind='keyboard',
    ),
    AcherionShortcutDefinition(
        identifier='toggle_selection',
        group='Selection',
        label='Toggle node selection',
        description='Toggle one node in or out of the current selection.',
        default_binding='Mod+Click',
        trigger_kind='mouse',
        interaction_kind='click',
    ),
    AcherionShortcutDefinition(
        identifier='box_select',
        group='Selection',
        label='Box select',
        description='Start rubber-band selection inside the canvas.',
        default_binding='Mod+Drag',
        trigger_kind='mouse',
        interaction_kind='drag',
    ),
    AcherionShortcutDefinition(
        identifier='box_select_add',
        group='Selection',
        label='Add box selection',
        description='Add a rubber-band selection to the current selection.',
        default_binding='Mod+Shift+Drag',
        trigger_kind='mouse',
        interaction_kind='drag',
    ),
    AcherionShortcutDefinition(
        identifier='zoom_canvas',
        group='View',
        label='Zoom canvas',
        description='Zoom the canvas around the pointer position.',
        default_binding='Ctrl+Wheel',
        trigger_kind='mouse',
        interaction_kind='wheel',
    ),
)

_SHORTCUT_BY_ID = {
    definition.identifier: definition
    for definition in SHORTCUT_DEFINITIONS
}


def is_shortcut_binding_editable(identifier: str) -> bool:
    """Return whether one shortcut identifier supports reassignment."""
    definition = _SHORTCUT_BY_ID.get(str(identifier or '').strip())
    if definition is None:
        return False
    return definition.interaction_kind == 'keyboard'


def default_preferences_dict() -> dict[str, dict[str, str]]:
    """Return default workbench preferences as a plain dictionary."""
    return {
        'appearance': {
            'code_editor_theme': DEFAULT_CODE_EDITOR_THEME,
        },
        'keyboard_shortcuts': {
            definition.identifier: definition.default_binding
            for definition in SHORTCUT_DEFINITIONS
        },
    }


def normalize_preferences_dict(
    preferences: Mapping[str, Any] | None,
) -> dict[str, dict[str, str]]:
    """Normalize arbitrary preference data into the supported shape."""
    normalized = default_preferences_dict()
    raw_preferences = dict(preferences or {})

    appearance = raw_preferences.get('appearance')
    if isinstance(appearance, Mapping):
        raw_theme = str(appearance.get('code_editor_theme') or '').strip()
        if raw_theme in SUPPORTED_CODE_EDITOR_THEMES:
            normalized['appearance']['code_editor_theme'] = raw_theme

    raw_shortcuts = raw_preferences.get('keyboard_shortcuts')
    if isinstance(raw_shortcuts, Mapping):
        for identifier, raw_binding in raw_shortcuts.items():
            shortcut_id = str(identifier or '').strip()
            if shortcut_id not in _SHORTCUT_BY_ID:
                continue
            if not is_shortcut_binding_editable(shortcut_id):
                continue
            clean_binding = str(raw_binding or '').strip()
            if clean_binding and is_supported_shortcut_binding(
                shortcut_id,
                clean_binding,
            ):
                normalized['keyboard_shortcuts'][shortcut_id] = clean_binding

    return normalized


def shortcut_binding_options(identifier: str) -> tuple[str, ...]:
    """Return legacy suggested binding options for one shortcut."""
    definition = _SHORTCUT_BY_ID.get(str(identifier or '').strip())
    if definition is None:
        raise KeyError(identifier)
    if definition.interaction_kind == 'keyboard':
        options: list[str] = []
        for modifiers in _KEYBOARD_MODIFIER_COMBINATIONS:
            for base_key in _KEYBOARD_BASE_KEYS:
                parts = [*modifiers, base_key]
                options.append('+'.join(parts))
        return tuple(options)

    interaction_label = {
        'click': 'Click',
        'drag': 'Drag',
        'wheel': 'Wheel',
    }[definition.interaction_kind]
    return tuple(
        '+'.join((*modifiers, interaction_label))
        if modifiers else interaction_label
        for modifiers in _MOUSE_MODIFIER_COMBINATIONS
    )


def shortcut_client_config() -> dict[str, Any]:
    """Return shared shortcut metadata for the client runtime."""
    return {
        'default_preferences': default_preferences_dict(),
        'token_aliases': dict(_SHORTCUT_TOKEN_ALIASES),
        'modifier_tokens': list(_SHORTCUT_MODIFIER_TOKENS),
        'mouse_interactions': list(_SHORTCUT_MOUSE_INTERACTIONS),
    }


def _normalize_shortcut_token(token: str) -> str:
    """Normalize one shortcut token using the runtime token rules."""
    clean = str(token or '').strip().upper()
    return _SHORTCUT_TOKEN_ALIASES.get(clean, clean)


def _parse_shortcut_binding(binding: str) -> dict[str, str] | None:
    """Parse one shortcut binding using the runtime interaction rules."""
    parts = [
        token.strip()
        for token in str(binding or '').split('+')
        if token.strip()
    ]
    if not parts:
        return None
    tail = _normalize_shortcut_token(parts[-1])
    interaction = 'keyboard'
    if tail in _SHORTCUT_MOUSE_INTERACTION_SET:
        interaction = tail.lower()
    for token in parts[:-1]:
        normalized = _normalize_shortcut_token(token)
        if normalized not in _SHORTCUT_MODIFIER_TOKEN_SET:
            return None
    return {
        'interaction': interaction,
        'key': tail if interaction == 'keyboard' else '',
    }


def is_supported_shortcut_binding(identifier: str, binding: str) -> bool:
    """Return whether one binding is valid for a shortcut interaction."""
    clean_identifier = str(identifier or '').strip()
    clean_binding = str(binding or '').strip()
    if not clean_binding:
        return False
    definition = _SHORTCUT_BY_ID.get(clean_identifier)
    if definition is None:
        return False
    if not is_shortcut_binding_editable(clean_identifier):
        return clean_binding == definition.default_binding
    parsed = _parse_shortcut_binding(clean_binding)
    if parsed is None:
        return False
    return parsed['interaction'] == definition.interaction_kind


class AcherionPreferencesState:
    """Mutable workbench-scoped preference state."""

    def __init__(
        self,
        preferences: Mapping[str, Any] | None = None,
    ) -> None:
        self._preferences = normalize_preferences_dict(preferences)

    @property
    def code_editor_theme(self) -> str:
        """Return the active CodeMirror theme name."""
        return self._preferences['appearance']['code_editor_theme']

    def set_code_editor_theme(self, theme_name: str) -> bool:
        """Store one CodeMirror theme if it is supported."""
        clean_theme = str(theme_name or '').strip()
        if clean_theme not in SUPPORTED_CODE_EDITOR_THEMES:
            return False
        current_theme = self.code_editor_theme
        if current_theme == clean_theme:
            return False
        self._preferences['appearance']['code_editor_theme'] = clean_theme
        return True

    def shortcut_binding(self, identifier: str) -> str:
        """Return the configured binding for one shortcut identifier."""
        clean_identifier = str(identifier or '').strip()
        if clean_identifier in self._preferences['keyboard_shortcuts']:
            return self._preferences['keyboard_shortcuts'][clean_identifier]
        definition = _SHORTCUT_BY_ID.get(clean_identifier)
        if definition is None:
            raise KeyError(clean_identifier)
        return definition.default_binding

    def set_shortcut_binding(self, identifier: str, binding: str) -> bool:
        """Store one shortcut binding when the identifier is supported."""
        clean_identifier = str(identifier or '').strip()
        if clean_identifier not in _SHORTCUT_BY_ID:
            return False
        if not is_shortcut_binding_editable(clean_identifier):
            return False
        clean_binding = str(binding or '').strip()
        if not clean_binding:
            clean_binding = _SHORTCUT_BY_ID[clean_identifier].default_binding
        if not is_supported_shortcut_binding(clean_identifier, clean_binding):
            return False
        current_binding = self.shortcut_binding(clean_identifier)
        if current_binding == clean_binding:
            return False
        self._preferences['keyboard_shortcuts'][clean_identifier] = clean_binding
        return True

    def apply_mapping(self, preferences: Mapping[str, Any] | None) -> bool:
        """Merge one mapping into the current state and report if it changed."""
        next_preferences = normalize_preferences_dict(preferences)
        if next_preferences == self._preferences:
            return False
        self._preferences = next_preferences
        return True

    def to_dict(self) -> dict[str, dict[str, str]]:
        """Return a deep-copyable plain dictionary for persistence."""
        return {
            'appearance': dict(self._preferences['appearance']),
            'keyboard_shortcuts': dict(self._preferences['keyboard_shortcuts']),
        }


__all__ = [
    'AcherionPreferencesState',
    'AcherionShortcutDefinition',
    'DEFAULT_CODE_EDITOR_THEME',
    'is_shortcut_binding_editable',
    'is_supported_shortcut_binding',
    'SHORTCUT_DEFINITIONS',
    'SUPPORTED_CODE_EDITOR_THEMES',
    'default_preferences_dict',
    'normalize_preferences_dict',
    'shortcut_client_config',
]