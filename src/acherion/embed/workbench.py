"""Embeddable Acherion workbench wrapper around the shared designer."""

from __future__ import annotations

import json
from collections.abc import Mapping
from contextlib import nullcontext
from typing import Any, Callable

from nicegui import ui

from acherion.embed.code_editor import build_python_code_editor
from acherion.embed.designer.component import AcherionDesigner
from acherion.host import AcherionHost
from acherion.theme import (
    build_scoped_acherion_theme_css,
    normalize_acherion_theme_overrides,
)


class AcherionWorkbench:
    """Embeddable and customizable workbench shell for AcherionDesigner.

    Hosts can use the default generated-code pane and validation behavior, or
    inject their own code view and callbacks while still reusing the same
    workbench component structure across applications.
    """

    def __init__(
        self,
        *,
        host: AcherionHost | None = None,
        on_change: Callable[[], None] | None = None,
        on_apply_to_code: Callable[[], None] | None = None,
        on_run_preview: Callable[[], bool] | None = None,
        on_validate: Callable[[], bool] | None = None,
        build_code_view: Callable[[], Any] | None = None,
        on_mode_change: Callable[[str], None] | None = None,
        initial_mode: str = 'graph',
        before_build: Callable[[], None] | None = None,
        container_classes: str = '',
        code_editor_theme: Any = 'vscodeDark',
        code_editor_classes: str = 'w-full h-full oe-code-editor',
        code_editor_style: str = 'height:100%; min-height:0',
        code_transform: Callable[[str], str] | None = None,
        refresh_code_on_change: bool = False,
        refresh_code_after_build: bool = False,
        validate_generated_code: Callable[[str], Any] | None = None,
        apply_to_code_status_message: str | None = None,
        theme_overrides: Mapping[str, str] | None = None,
    ) -> None:
        self._on_change = on_change
        self._on_apply_to_code = on_apply_to_code
        self._on_validate = on_validate
        self._host_build_code_view = build_code_view
        self._before_build = before_build
        self._container_classes = container_classes
        self._code_editor_theme = code_editor_theme
        self._code_editor_classes = code_editor_classes
        self._code_editor_style = code_editor_style
        self._code_transform = code_transform
        self._refresh_code_on_change = refresh_code_on_change
        self._refresh_code_after_build = refresh_code_after_build
        self._validate_generated_code = validate_generated_code
        self._apply_to_code_status_message = apply_to_code_status_message
        self._theme_overrides = (
            dict(theme_overrides)
            if theme_overrides is not None
            else None
        )
        self._theme_css_injected = False
        self._built = False
        self._applied_theme_variable_names: set[str] = set()
        self._code_view: Any = None
        self._designer = AcherionDesigner(
            host=host,
            on_change=self._handle_change,
            on_apply_to_code=self._handle_apply_to_code,
            on_run_preview=on_run_preview,
            on_validate=self._handle_validate,
            build_code_view=self._build_code_view,
            on_mode_change=on_mode_change,
            initial_mode=initial_mode,
        )

    @property
    def designer(self) -> AcherionDesigner:
        """Return the underlying AcherionDesigner instance."""
        return self._designer

    @property
    def code_view(self) -> Any:
        """Return the registered code-view widget, if one exists."""
        return self._code_view

    def set_code_view(self, code_view: Any) -> Any:
        """Register the current code-view widget for refresh operations."""
        self._code_view = code_view
        return code_view

    def set_theme_overrides(
        self,
        theme_overrides: Mapping[str, str] | None,
    ) -> None:
        """Enable, replace, or disable the embedded scoped Acherion theme."""
        self._theme_overrides = (
            dict(theme_overrides)
            if theme_overrides is not None
            else None
        )
        if self._theme_overrides is not None:
            self._ensure_theme_css()
        self._apply_theme_state()

    def clear_theme_overrides(self) -> None:
        """Disable the embedded scoped Acherion theme for this workbench."""
        self.set_theme_overrides(None)

    def build(self) -> None:
        """Render the workbench into the current NiceGUI context."""
        if self._before_build is not None:
            self._before_build()
        if self._theme_overrides is not None:
            self._ensure_theme_css()
        container = (
            ui.element('div').classes(self._container_classes)
            if self._container_classes.strip()
            else nullcontext()
        )
        with container:
            self._designer.build()
        self._built = True
        self._apply_theme_state()
        if self._refresh_code_after_build:
            self.refresh_code_view()

    def generated_user_code(self) -> str:
        """Return the underlying designer's generated user code."""
        return self._designer.generated_user_code()

    def refresh_code_view(self) -> None:
        """Refresh the registered code-view widget from generated code."""
        if self._code_view is None:
            return
        self._set_code_view_value(
            self._transform_display_code(self.generated_user_code())
        )

    def _transform_display_code(self, code: str) -> str:
        """Apply optional host-side display transforms to generated code."""
        if self._code_transform is None:
            return code
        return str(self._code_transform(code))

    def _theme_scope_selector(self) -> str:
        """Return the scoped selector used for the embedded Acherion theme."""
        return f'#{self._designer.frame_dom_id}[data-ach-theme="enabled"]'

    def _ensure_theme_css(self) -> None:
        """Inject the scoped embedded theme stylesheet once."""
        if self._theme_css_injected:
            return
        ui.add_css(build_scoped_acherion_theme_css(self._theme_scope_selector()))
        self._theme_css_injected = True

    def _apply_theme_state(self) -> None:
        """Apply the current runtime theme state to an already-built workbench."""
        if not self._built:
            return
        next_variables = normalize_acherion_theme_overrides(self._theme_overrides)
        remove_names = sorted(
            self._applied_theme_variable_names - set(next_variables)
            if self._theme_overrides is not None
            else self._applied_theme_variable_names
        )
        payload = json.dumps({
            'frameId': self._designer.frame_dom_id,
            'enabled': self._theme_overrides is not None,
            'variables': next_variables,
            'removeNames': remove_names,
        })
        self._designer._run_client_javascript(
            '(() => {'
            f'const payload = {payload};'
            'const frame = document.getElementById(payload.frameId);'
            'if (!frame) return;'
            'if (payload.enabled) {'
            '  frame.setAttribute("data-ach-theme", "enabled");'
            '} else {'
            '  frame.removeAttribute("data-ach-theme");'
            '}'
            'for (const name of payload.removeNames) {'
            '  frame.style.removeProperty(name);'
            '}'
            'for (const [name, value] of Object.entries(payload.variables)) {'
            '  frame.style.setProperty(name, String(value));'
            '}'
            '})();'
        )
        self._applied_theme_variable_names = set(next_variables)

    def _set_code_view_value(self, value: str) -> None:
        """Update the registered code-view widget with one text value."""
        if self._code_view is None:
            return
        setter = getattr(self._code_view, 'set_value', None)
        if callable(setter):
            setter(value)
            return
        if hasattr(self._code_view, 'value'):
            self._code_view.value = value

    def _build_code_view(self) -> None:
        """Build either the host-provided or default generated-code view."""
        if self._host_build_code_view is not None:
            code_view = self._host_build_code_view()
            if code_view is not None:
                self.set_code_view(code_view)
            return
        with ui.element('div').classes(
            'w-full h-full min-w-0 min-h-0 flex flex-1'
        ):
            editor = build_python_code_editor(
                value='',
                theme=self._code_editor_theme,
                classes=self._code_editor_classes,
                style=self._code_editor_style,
            )
        self.set_code_view(editor)

    def _handle_change(self) -> None:
        """Dispatch designer change notifications through the wrapper."""
        if self._refresh_code_on_change:
            self.refresh_code_view()
        if self._on_change is not None:
            self._on_change()

    def _handle_apply_to_code(self) -> None:
        """Dispatch compile/apply requests or fall back to code refresh."""
        if self._on_apply_to_code is not None:
            self._on_apply_to_code()
            return
        self.refresh_code_view()
        if self._apply_to_code_status_message:
            self._designer.set_status_message(
                self._apply_to_code_status_message
            )

    def _handle_validate(self) -> bool:
        """Validate generated code through host callback or default handler."""
        if self._on_validate is not None:
            return self._on_validate()
        if self._validate_generated_code is None:
            self._designer.set_status_message(
                'Generated code validation is not available.',
                negative=True,
            )
            return False
        try:
            self._validate_generated_code(self.generated_user_code())
        except Exception as exc:  # Validation boundary for host feedback.
            self.refresh_code_view()
            self._designer.set_status_message(
                f'Generated code validation failed: {exc}',
                negative=True,
            )
            return False
        self.refresh_code_view()
        self._designer.set_status_message('Generated code validated successfully.')
        return True


__all__ = ['AcherionWorkbench']