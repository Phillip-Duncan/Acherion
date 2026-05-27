"""Preferences dialog mixin for AcherionDesigner."""

from __future__ import annotations

import json
from typing import Any

from nicegui import ui

import acherion.preferences as acherion_preferences


class _DesignerPreferencesDialogMixin:
    """Render and manage the preferences dialog."""

    def apply_preferences_state(self: Any) -> None:
        """Sync current preferences into client-side helpers."""
        payload = json.dumps(self._preferences_state.to_dict())
        self._run_client_javascript(
            f'window.__oeAcherion?.setPreferences({payload});'
        )

    def _preferences_dialog_snapshot(
        self: Any,
    ) -> dict[str, dict[str, str]]:
        """Return a detached snapshot of current saved preferences."""
        return self._preferences_state.to_dict()

    def _draft_shortcut_binding(self: Any, identifier: str) -> str:
        """Return one draft shortcut binding."""
        shortcuts = self._preferences_draft.get('keyboard_shortcuts', {})
        clean_identifier = str(identifier or '').strip()
        if clean_identifier in shortcuts:
            return str(shortcuts[clean_identifier] or '').strip()
        return self._preferences_state.shortcut_binding(clean_identifier)

    def _preferences_preview_payload(self: Any) -> dict[str, dict[str, str]]:
        """Return preview payload with draft appearance and saved shortcuts."""
        return {
            'appearance': dict(self._preferences_draft['appearance']),
            'keyboard_shortcuts': dict(
                self._preferences_saved_snapshot['keyboard_shortcuts']
            ),
        }

    def _preview_preferences_draft(self: Any) -> None:
        """Preview only draft appearance changes without persisting."""
        if self._on_preferences_preview is None:
            return
        self._on_preferences_preview(self._preferences_preview_payload())

    def _revert_preferences_preview(self: Any) -> None:
        """Revert unsaved appearance preview back to saved preferences."""
        if self._on_preferences_preview is None:
            return
        self._on_preferences_preview(self._preferences_saved_snapshot)

    def _rerender_preferences_dialog(self: Any) -> None:
        """Refresh preferences dialog body after local draft changes."""
        if (
            self._preferences_nav_container is None
            or self._preferences_content_container is None
        ):
            return
        self._render_preferences_dialog_body()
        capture_id = self._preferences_capture_shortcut_id
        if capture_id:
            self._run_client_javascript(
                '(() => {'
                f'const el = document.getElementById({f"{self._frame_dom_id}-pref-{capture_id}"!r});'
                'if (!el) return;'
                'requestAnimationFrame(() => el.focus());'
                '})();'
            )
            return

    def _cancel_preferences_dialog(self: Any) -> None:
        """Close preferences dialog and revert unsaved preview changes."""
        self._preferences_capture_shortcut_id = None
        self._preferences_commit_on_close = False
        if self._preferences_dialog is not None:
            self._preferences_dialog.close()

    def _handle_preferences_dialog_close(self: Any) -> None:
        """Finalize preferences dialog close for save or cancel flows."""
        self._preferences_capture_shortcut_id = None
        if not self._preferences_commit_on_close:
            self._preferences_draft = {
                'appearance': dict(self._preferences_saved_snapshot['appearance']),
                'keyboard_shortcuts': dict(
                    self._preferences_saved_snapshot['keyboard_shortcuts']
                ),
            }
            self._revert_preferences_preview()
        self._preferences_commit_on_close = False
        self._preferences_dialog = None
        self._preferences_nav_container = None
        self._preferences_content_container = None

    def _save_preferences_dialog(self: Any) -> None:
        """Persist current draft preferences and close the dialog."""
        self._preferences_capture_shortcut_id = None
        self._preferences_saved_snapshot = {
            'appearance': dict(self._preferences_draft['appearance']),
            'keyboard_shortcuts': dict(
                self._preferences_draft['keyboard_shortcuts']
            ),
        }
        if self._on_preferences_change is not None:
            self._on_preferences_change(self._preferences_saved_snapshot)
        self._update_hint()
        self._preferences_commit_on_close = True
        if self._preferences_dialog is not None:
            self._preferences_dialog.close()

    def _reset_preferences_section(self: Any, category: str) -> None:
        """Reset one preferences section back to defaults."""
        defaults = acherion_preferences.default_preferences_dict()
        if category == 'Appearance':
            self._preferences_draft['appearance'] = dict(defaults['appearance'])
            self._preview_preferences_draft()
        elif category == 'Keyboard Shortcuts':
            self._preferences_draft['keyboard_shortcuts'] = dict(
                defaults['keyboard_shortcuts']
            )
        self._preferences_capture_shortcut_id = None
        self._rerender_preferences_dialog()

    def _set_code_editor_theme_draft(
        self: Any,
        theme_name: str,
    ) -> None:
        """Update draft theme and preview it immediately."""
        clean_theme = str(theme_name or '').strip()
        if clean_theme not in acherion_preferences.SUPPORTED_CODE_EDITOR_THEMES:
            return
        current_theme = self._preferences_draft['appearance'].get(
            'code_editor_theme',
            '',
        )
        if current_theme == clean_theme:
            return
        self._preferences_draft['appearance']['code_editor_theme'] = clean_theme
        self._preview_preferences_draft()

    def _set_shortcut_capture_mode(
        self: Any,
        identifier: str | None,
    ) -> None:
        """Toggle shortcut capture mode for one draft binding row."""
        clean_identifier = str(identifier or '').strip() or None
        if clean_identifier is not None and not acherion_preferences.is_shortcut_binding_editable(
            clean_identifier
        ):
            return
        if self._preferences_capture_shortcut_id == clean_identifier:
            self._preferences_capture_shortcut_id = None
        else:
            self._preferences_capture_shortcut_id = clean_identifier
        self._rerender_preferences_dialog()

    def _capture_shortcut_binding(
        self: Any,
        identifier: str,
        binding: str,
    ) -> None:
        """Store one captured shortcut binding in draft state."""
        clean_identifier = str(identifier or '').strip()
        if not acherion_preferences.is_shortcut_binding_editable(
            clean_identifier
        ):
            return
        clean_binding = str(binding or '').strip()
        if not acherion_preferences.is_supported_shortcut_binding(
            clean_identifier,
            clean_binding,
        ):
            return
        current_binding = self._draft_shortcut_binding(clean_identifier)
        if current_binding == clean_binding:
            self._preferences_capture_shortcut_id = None
            self._rerender_preferences_dialog()
            return
        self._preferences_draft['keyboard_shortcuts'][
            clean_identifier
        ] = clean_binding
        self._preferences_capture_shortcut_id = None
        self._rerender_preferences_dialog()

    def _format_shortcut_binding(self: Any, binding: str) -> str:
        """Return one user-facing shortcut label without raw Mod tokens."""
        return str(binding or '').replace('Mod', 'Ctrl/Cmd')

    def _shortcut_display_binding(self: Any, identifier: str) -> str:
        """Return one shortcut binding formatted for human-facing hints."""
        return self._format_shortcut_binding(
            self._preferences_state.shortcut_binding(identifier)
        )

    def _matching_shortcut_definitions(
        self: Any,
    ) -> list[acherion_preferences.AcherionShortcutDefinition]:
        """Return visible shortcut definitions for the current filter text."""
        query = str(self._preferences_search_query or '').strip().casefold()
        definitions = list(acherion_preferences.SHORTCUT_DEFINITIONS)
        if not query:
            return definitions
        return [
            definition
            for definition in definitions
            if query in definition.group.casefold()
            or query in definition.label.casefold()
            or query in definition.description.casefold()
            or query
            in self._draft_shortcut_binding(
                definition.identifier
            ).casefold()
        ]

    def _render_preferences_appearance_panel(self: Any) -> None:
        """Render the appearance settings category."""
        with ui.element('div').classes('ach-preferences-section-head'):
            ui.label('Appearance').classes('ach-preferences-title')
            ui.button(
                'Restore Defaults',
                on_click=lambda: self._reset_preferences_section('Appearance'),
            ).props('flat no-caps').classes('ach-preferences-section-reset')
        with ui.element('div').classes('ach-preferences-card'):
            with ui.element('div').classes('ach-preferences-row'):
                with ui.element('div').classes('ach-preferences-row-meta'):
                    ui.label('Code editor theme').classes(
                        'ach-preferences-field-label'
                    )
                    ui.label(
                        f'{len(acherion_preferences.SUPPORTED_CODE_EDITOR_THEMES)} themes'
                    ).classes('ach-preferences-field-help')
                ui.select(
                    list(acherion_preferences.SUPPORTED_CODE_EDITOR_THEMES),
                    value=self._preferences_draft['appearance']['code_editor_theme'],
                    with_input=True,
                    on_change=lambda event: self._set_code_editor_theme_draft(
                        str(event.value or '')
                    ),
                ).props('outlined dense options-dense').classes(
                    'ach-preferences-theme-select ach-preferences-select'
                )

    def _render_shortcut_capture_box(
        self: Any,
        definition: acherion_preferences.AcherionShortcutDefinition,
    ) -> None:
        """Render capture box for one shortcut binding."""
        is_editable = acherion_preferences.is_shortcut_binding_editable(
            definition.identifier
        )
        is_capturing = (
            is_editable
            and self._preferences_capture_shortcut_id == definition.identifier
        )
        binding_value = self._draft_shortcut_binding(definition.identifier)
        display_value = (
            'Press shortcut'
            if is_capturing
            else self._format_shortcut_binding(binding_value)
        )
        box_id = f'{self._frame_dom_id}-pref-{definition.identifier}'
        classes = 'ach-preferences-capture-box'
        if not is_editable:
            classes += ' ach-preferences-capture-box-readonly'
        if is_capturing:
            classes += ' ach-preferences-capture-box-active'
        capture_box = ui.element('div').classes(classes).props(
            f'tabindex={"0" if is_editable else "-1"} '
            f'id={box_id} '
            f'aria-disabled={"false" if is_editable else "true"}'
        )
        with capture_box:
            ui.label(display_value).classes('ach-preferences-capture-value')
        if is_editable and not is_capturing:
            capture_box.on(
                'click',
                lambda _event, sid=definition.identifier: (
                    self._set_shortcut_capture_mode(sid)
                ),
            )
        if not is_editable:
            capture_box.on(
                'mousedown',
                lambda _event: None,
                js_handler='(e) => { e.preventDefault(); e.stopPropagation(); }',
            )
            capture_box.on(
                'click',
                lambda _event: None,
                js_handler='(e) => { e.preventDefault(); e.stopPropagation(); }',
            )
            return
        capture_box.on(
            'blur',
            lambda _event, sid=definition.identifier: (
                self._set_shortcut_capture_mode(None)
                if self._preferences_capture_shortcut_id == sid
                else None
            ),
        )
        capture_box.on(
            'keydown',
            lambda event, sid=definition.identifier: self._capture_shortcut_binding(
                sid,
                str((event.args or {}).get('binding') or ''),
            ),
            js_handler=(
                '(e) => {'
                'if (!e.currentTarget.classList.contains('
                '"ach-preferences-capture-box-active")) return;'
                f'if ({definition.interaction_kind!r} !== "keyboard") return;'
                'const modifiers = [];'
                'const key = String(e.key || "");'
                'if (["Control","Shift","Alt","Meta"].includes(key)) {'
                'e.preventDefault(); e.stopPropagation(); return;'
                '}'
                'if (e.ctrlKey) modifiers.push("Ctrl");'
                'else if (e.metaKey) modifiers.push("Mod");'
                'if (e.shiftKey) modifiers.push("Shift");'
                'if (e.altKey) modifiers.push("Alt");'
                'const tail = window.__oeAcherion?.normalizeShortcutKey(key) || key;'
                'if (!tail) return;'
                'e.preventDefault(); e.stopPropagation();'
                'emit({binding:[...modifiers, tail].join("+")});'
                '}'
            ),
        )
        capture_box.on(
            'mousedown',
            lambda _event: None,
            js_handler=(
                '(e) => {'
                'if (!e.currentTarget.classList.contains('
                '"ach-preferences-capture-box-active")) return;'
                f'if ({definition.interaction_kind!r} !== "click" && {definition.interaction_kind!r} !== "drag") return;'
                'const el = e.currentTarget;'
                'el.dataset.captureStartX = String(e.clientX);'
                'el.dataset.captureStartY = String(e.clientY);'
                'el.dataset.captureBinding = ['
                'e.ctrlKey ? "Ctrl" : (e.metaKey ? "Mod" : ""),'
                'e.shiftKey ? "Shift" : "",'
                'e.altKey ? "Alt" : ""'
                '].filter(Boolean).join("+");'
                'e.preventDefault(); e.stopPropagation();'
                '}'
            ),
        )
        capture_box.on(
            'mousemove',
            lambda event, sid=definition.identifier: self._capture_shortcut_binding(
                sid,
                str((event.args or {}).get('binding') or ''),
            ),
            js_handler=(
                '(e) => {'
                'if (!e.currentTarget.classList.contains('
                '"ach-preferences-capture-box-active")) return;'
                f'if ({definition.interaction_kind!r} !== "drag") return;'
                'if (!(e.buttons & 1)) return;'
                'const el = e.currentTarget;'
                'const sx = parseFloat(el.dataset.captureStartX || "0");'
                'const sy = parseFloat(el.dataset.captureStartY || "0");'
                'if (Math.hypot(e.clientX - sx, e.clientY - sy) < 8) return;'
                'const prefix = String(el.dataset.captureBinding || "");'
                'e.preventDefault(); e.stopPropagation();'
                'emit({binding: prefix ? `${prefix}+Drag` : "Drag"});'
                '}'
            ),
        )
        capture_box.on(
            'mouseup',
            lambda event, sid=definition.identifier: self._capture_shortcut_binding(
                sid,
                str((event.args or {}).get('binding') or ''),
            ),
            js_handler=(
                '(e) => {'
                'if (!e.currentTarget.classList.contains('
                '"ach-preferences-capture-box-active")) return;'
                f'if ({definition.interaction_kind!r} !== "click") return;'
                'const el = e.currentTarget;'
                'const sx = parseFloat(el.dataset.captureStartX || "0");'
                'const sy = parseFloat(el.dataset.captureStartY || "0");'
                'if (Math.hypot(e.clientX - sx, e.clientY - sy) >= 8) return;'
                'const prefix = String(el.dataset.captureBinding || "");'
                'e.preventDefault(); e.stopPropagation();'
                'emit({binding: prefix ? `${prefix}+Click` : "Click"});'
                '}'
            ),
        )
        capture_box.on(
            'wheel',
            lambda event, sid=definition.identifier: self._capture_shortcut_binding(
                sid,
                str((event.args or {}).get('binding') or ''),
            ),
            js_handler=(
                '(e) => {'
                'if (!e.currentTarget.classList.contains('
                '"ach-preferences-capture-box-active")) return;'
                f'if ({definition.interaction_kind!r} !== "wheel") return;'
                'const modifiers = [];'
                'if (e.ctrlKey) modifiers.push("Ctrl");'
                'else if (e.metaKey) modifiers.push("Mod");'
                'if (e.shiftKey) modifiers.push("Shift");'
                'if (e.altKey) modifiers.push("Alt");'
                'e.preventDefault(); e.stopPropagation();'
                'emit({binding:[...modifiers, "Wheel"].join("+")});'
                '}'
            ),
        )

    def _render_preferences_shortcuts_panel(self: Any) -> None:
        """Render the keyboard-shortcuts settings category."""
        definitions = self._matching_shortcut_definitions()
        with ui.element('div').classes('ach-preferences-section-head'):
            ui.label('Keyboard Shortcuts').classes('ach-preferences-title')
            ui.button(
                'Restore Defaults',
                on_click=lambda: self._reset_preferences_section(
                    'Keyboard Shortcuts'
                ),
            ).props('flat no-caps').classes('ach-preferences-section-reset')
        if not definitions:
            ui.label('No shortcuts match the current filter.').classes(
                'ach-preferences-empty'
            )
            return
        grouped: dict[str, list[acherion_preferences.AcherionShortcutDefinition]] = {}
        group_order: list[str] = []
        for definition in definitions:
            if definition.group not in grouped:
                grouped[definition.group] = []
                group_order.append(definition.group)
            grouped.setdefault(definition.group, []).append(definition)
        for group_name in group_order:
            group_items = grouped.get(group_name) or []
            if not group_items:
                continue
            with ui.element('div').classes('ach-preferences-shortcut-group'):
                ui.label(group_name).classes('ach-preferences-group-title')
                for definition in group_items:
                    with ui.element('div').classes(
                        'ach-preferences-shortcut-row'
                    ):
                        with ui.element('div').classes(
                            'ach-preferences-shortcut-meta'
                        ):
                            ui.label(definition.label).classes(
                                'ach-preferences-shortcut-label'
                            )
                        with ui.element('div').classes(
                            'ach-preferences-shortcut-controls'
                        ):
                            self._render_shortcut_capture_box(definition)

    def _render_preferences_dialog_body(self: Any) -> None:
        """Render or rerender preferences dialog nav and content."""
        if (
            self._preferences_nav_container is None
            or self._preferences_content_container is None
        ):
            return
        categories = (
            ('Appearance', 'palette'),
            ('Keyboard Shortcuts', 'keyboard_command_key'),
        )
        self._preferences_nav_container.clear()
        with self._preferences_nav_container:
            for category_label, icon_name in categories:
                classes = 'ach-preferences-nav-item'
                if category_label == self._preferences_active_category:
                    classes += ' ach-preferences-nav-item-active'
                ui.button(
                    category_label,
                    icon=icon_name,
                    on_click=lambda _event, category=category_label: (
                        setattr(
                            self,
                            '_preferences_active_category',
                            category,
                        ),
                        setattr(
                            self,
                            '_preferences_capture_shortcut_id',
                            None,
                        ),
                        self._render_preferences_dialog_body(),
                    ),
                ).props('flat no-caps align=left').classes(classes)

        self._preferences_content_container.clear()
        with self._preferences_content_container:
            if self._preferences_active_category == 'Appearance':
                self._render_preferences_appearance_panel()
            else:
                self._render_preferences_shortcuts_panel()

    def _open_preferences_dialog(self: Any) -> None:
        """Open the editor preferences dialog."""
        if self._overlay_host_el is None:
            return
        self._preferences_search_query = ''
        self._preferences_active_category = 'Appearance'
        self._preferences_commit_on_close = False
        self._preferences_capture_shortcut_id = None
        self._preferences_saved_snapshot = self._preferences_dialog_snapshot()
        self._preferences_draft = {
            'appearance': dict(self._preferences_saved_snapshot['appearance']),
            'keyboard_shortcuts': dict(
                self._preferences_saved_snapshot['keyboard_shortcuts']
            ),
        }

        with self._overlay_host_el:
            dialog = ui.dialog()
            dialog.on('hide', lambda _event: self._handle_preferences_dialog_close())
            self._preferences_dialog = dialog
            with dialog, ui.card().classes('ach-preferences-dialog-card'):
                with ui.element('div').classes('ach-preferences-dialog-shell'):
                    with ui.element('div').classes('ach-preferences-toolbar'):
                        ui.label('Preferences').classes(
                            'ach-preferences-dialog-title'
                        )
                        ui.button(
                            icon='close',
                            on_click=self._cancel_preferences_dialog,
                        ).props('flat round color=white').classes(
                            'ach-preferences-close'
                        )
                    body_container = ui.element('div').classes(
                        'ach-preferences-dialog-body'
                    )
                    with body_container:
                        with ui.element('div').classes('ach-preferences-body'):
                            with ui.element('div').classes('ach-preferences-sidebar'):
                                self._preferences_nav_container = ui.element(
                                    'div'
                                ).classes('ach-preferences-sidebar-nav')
                            with ui.element('div').classes('ach-preferences-main'):
                                with ui.element('div').classes(
                                    'ach-preferences-search-row'
                                ):
                                    search_input = ui.input(
                                        value=self._preferences_search_query,
                                        placeholder='Search',
                                    ).props('outlined dense clearable').classes(
                                        'w-full ach-pill-search-input '
                                        'ach-preferences-search-input'
                                    ).props(
                                        f'id={self._frame_dom_id}-pref-search'
                                    )
                                    with search_input.add_slot('prepend'):
                                        ui.icon('search').classes(
                                            'ach-pill-search-icon'
                                        )
                                    search_input.on(
                                        'update:model-value',
                                        lambda event: (
                                            setattr(
                                                self,
                                                '_preferences_search_query',
                                                str(event.args or ''),
                                            ),
                                            setattr(
                                                self,
                                                '_preferences_capture_shortcut_id',
                                                None,
                                            ),
                                            self._rerender_preferences_dialog(),
                                        ),
                                    )
                                self._preferences_content_container = ui.element(
                                    'div'
                                ).classes('ach-preferences-content')
                    self._render_preferences_dialog_body()
                    with ui.element('div').classes('ach-preferences-footer'):
                        ui.button(
                            'Cancel',
                            on_click=self._cancel_preferences_dialog,
                        ).props('flat no-caps').classes(
                            'ach-preferences-close-text'
                        )
                        ui.button(
                            'Save',
                            on_click=self._save_preferences_dialog,
                        ).props('unelevated no-caps').classes(
                            'ach-preferences-save'
                        )
        dialog.open()