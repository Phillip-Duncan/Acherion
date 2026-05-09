"""Pin and node-card rendering mixin for AcherionDesigner."""

# pyright: reportAttributeAccessIssue=false

from __future__ import annotations

from typing import Any, cast

from nicegui import ui

from acherion.catalog import types as _catalog_types
import acherion.node_behaviors as acherion_node_behaviors
from acherion.model import (
    AcherionNode,
    _node_var_name,
    _template_icon,
    _template_title,
)


def _pin_button_classes(base: str, pin_type: str) -> str:
    """Return CSS classes for a typed pin button."""
    style_tag = _catalog_types.pin_style_tag(pin_type)
    return f'{base} ach-pin-btn-type-{style_tag}'


def _type_badge_classes(pin_type: str) -> str:
    """Return CSS classes for a typed badge label."""
    style_tag = _catalog_types.pin_style_tag(pin_type)
    return f'ach-type-badge ach-type-badge-{style_tag}'


def _is_exec_pin(pin: dict[str, str]) -> bool:
    """Return True when a pin spec represents control flow."""
    return str(pin.get('type') or '') == 'exec'


def _is_unlabeled_exec_pin(pin: dict[str, str]) -> bool:
    """Return True for exec pins that should live on the top row."""
    if not _is_exec_pin(pin):
        return False
    return not str(pin.get('label') or '').strip()


def _pairable_body_pin_key(
    pin: dict[str, str],
) -> tuple[str, str] | None:
    """Return stable match key for inline bidirectional data rows."""
    label = str(pin.get('label') or '').strip()
    pin_type = str(pin.get('type') or 'any').strip() or 'any'
    if not label or pin_type == 'exec':
        return None
    return (label, pin_type)


class _RenderPinsMixin:
    """Pin-row and system-node rendering methods."""

    @staticmethod
    def _inline_default_editor_spec(
        node: AcherionNode,
    ) -> tuple[str, str, Any] | None:
        """Return inline default editor binding for supported nodes."""
        return acherion_node_behaviors.inline_default_editor_spec_for_node(node)

    def _set_inline_default_value(
        self: Any,
        node: AcherionNode,
        *,
        field_name: str,
        input_kind: str,
        value: Any,
        notify: bool = True,
    ) -> None:
        """Persist one inline node default value."""
        if input_kind == 'number':
            if node.kind == 'constant':
                value_type = str(node.params.get('value_type') or 'number').strip()
                if value_type == 'int':
                    try:
                        node.params[field_name] = int(float(value or 0))
                    except (TypeError, ValueError):
                        node.params[field_name] = 0
                else:
                    node.params[field_name] = 0 if value in (None, '') else value
            else:
                node.params[field_name] = 0 if value in (None, '') else value
        else:
            node.params[field_name] = str(value or '')
        if notify:
            self._notify_change()

    def _render_inline_default_editor(self: Any, node: AcherionNode) -> bool:
        """Render compact node-card editor for supported default values."""
        spec = self._inline_default_editor_spec(node)
        if spec is None:
            return False
        input_kind, field_name, current_value = spec
        field_classes = 'ach-node-inline-field'
        if input_kind == 'number':
            field_classes += ' ach-node-inline-field-number'
            step = '1' if (
                node.kind == 'constant'
                and str(node.params.get('value_type') or 'number').strip() == 'int'
            ) else 'any'
            number_field = ui.number(
                value=current_value,
            ).props(
                f'dense outlined hide-bottom-space step={step}'
            ).classes(field_classes)
            number_field.on(
                'update:model-value',
                lambda event, cur=node, name=field_name, kind=input_kind: (
                    self._set_inline_default_value(
                        cur,
                        field_name=name,
                        input_kind=kind,
                        value=getattr(event, 'args', None),
                        notify=False,
                    )
                ),
            )
            number_field.on(
                'blur',
                lambda _event, cur=node, name=field_name, kind=input_kind,
                field=number_field: (
                    self._set_inline_default_value(
                        cur,
                        field_name=name,
                        input_kind=kind,
                        value=field.value,
                    )
                ),
            )
            number_field.on(
                'keydown.enter',
                lambda _event, cur=node, name=field_name, kind=input_kind,
                field=number_field: (
                    self._set_inline_default_value(
                        cur,
                        field_name=name,
                        input_kind=kind,
                        value=field.value,
                    )
                ),
            )
            return True

        text_field = ui.input(
            value=str(current_value or ''),
        ).props('dense outlined hide-bottom-space').classes(
            field_classes + ' ach-node-inline-field-text'
        )
        text_field.on(
            'update:model-value',
            lambda event, cur=node, name=field_name, kind=input_kind: (
                self._set_inline_default_value(
                    cur,
                    field_name=name,
                    input_kind=kind,
                    value=getattr(event, 'args', None),
                    notify=False,
                )
            ),
        )
        text_field.on(
            'blur',
            lambda _event, cur=node, name=field_name, kind=input_kind,
            field=text_field: (
                self._set_inline_default_value(
                    cur,
                    field_name=name,
                    input_kind=kind,
                    value=field.value,
                )
            ),
        )
        text_field.on(
            'keydown.enter',
            lambda _event, cur=node, name=field_name, kind=input_kind,
            field=text_field: (
                self._set_inline_default_value(
                    cur,
                    field_name=name,
                    input_kind=kind,
                    value=field.value,
                )
            ),
        )
        return True

    @staticmethod
    def _pin_literal_input_kind(
        pin_type: str,
        editor_kind: str = '',
    ) -> str | None:
        """Return compact editor kind for one eligible input pin type."""
        if editor_kind in {'number', 'text'}:
            return editor_kind
        if pin_type in {'float', 'int'}:
            return 'number'
        if pin_type == 'str':
            return 'text'
        return None

    @staticmethod
    def _pin_literal_value(
        node: AcherionNode,
        pin_id: str,
    ) -> Any:
        """Return stored literal fallback value for one input pin."""
        raw_literals = node.params.get('pin_literals')
        if not isinstance(raw_literals, dict):
            return None
        return raw_literals.get(pin_id)

    def _set_pin_literal_value(
        self: Any,
        node: AcherionNode,
        *,
        pin_id: str,
        input_kind: str,
        value: Any,
        notify: bool = True,
    ) -> None:
        """Persist one literal fallback value for an input pin."""
        literals = dict(node.params.get('pin_literals') or {})
        if value in (None, ''):
            literals.pop(pin_id, None)
        elif input_kind == 'number':
            literals[pin_id] = value
        else:
            literals[pin_id] = str(value)
        node.params['pin_literals'] = literals
        if notify:
            self._notify_change()

    def _render_input_literal_editor(
        self: Any,
        node: AcherionNode,
        *,
        pin_id: str,
        pin_type: str,
        editor_kind: str,
        source_id: str,
    ) -> bool:
        """Render compact literal editor for one unconnected input pin."""
        if source_id:
            return False
        input_kind = self._pin_literal_input_kind(pin_type, editor_kind)
        if input_kind is None:
            return False
        current_value = self._pin_literal_value(node, pin_id)
        field_classes = 'ach-node-inline-field'
        if input_kind == 'number':
            field_classes += ' ach-node-inline-field-number'
            step = '1' if pin_type == 'int' else 'any'
            number_field = ui.number(
                value=current_value,
            ).props(
                f'dense outlined hide-bottom-space step={step}'
            ).classes(field_classes)
            number_field.on(
                'update:model-value',
                lambda event, cur=node, pid=pin_id, kind=input_kind: (
                    self._set_pin_literal_value(
                        cur,
                        pin_id=pid,
                        input_kind=kind,
                        value=getattr(event, 'args', None),
                        notify=False,
                    )
                ),
            )
            number_field.on(
                'blur',
                lambda _event, cur=node, pid=pin_id, kind=input_kind,
                field=number_field: (
                    self._set_pin_literal_value(
                        cur,
                        pin_id=pid,
                        input_kind=kind,
                        value=field.value,
                    )
                ),
            )
            number_field.on(
                'keydown.enter',
                lambda _event, cur=node, pid=pin_id, kind=input_kind,
                field=number_field: (
                    self._set_pin_literal_value(
                        cur,
                        pin_id=pid,
                        input_kind=kind,
                        value=field.value,
                    )
                ),
            )
            return True

        text_field = ui.input(
            value='' if current_value is None else str(current_value),
        ).props('dense outlined hide-bottom-space').classes(
            field_classes + ' ach-node-inline-field-text'
        )
        text_field.on(
            'update:model-value',
            lambda event, cur=node, pid=pin_id, kind=input_kind: (
                self._set_pin_literal_value(
                    cur,
                    pin_id=pid,
                    input_kind=kind,
                    value=getattr(event, 'args', None),
                    notify=False,
                )
            ),
        )
        text_field.on(
            'blur',
            lambda _event, cur=node, pid=pin_id, kind=input_kind,
            field=text_field: (
                self._set_pin_literal_value(
                    cur,
                    pin_id=pid,
                    input_kind=kind,
                    value=field.value,
                )
            ),
        )
        text_field.on(
            'keydown.enter',
            lambda _event, cur=node, pid=pin_id, kind=input_kind,
            field=text_field: (
                self._set_pin_literal_value(
                    cur,
                    pin_id=pid,
                    input_kind=kind,
                    value=field.value,
                )
            ),
        )
        return True

    def _function_box_entry_source_id(self: Any, node: AcherionNode) -> str:
        if node.kind != 'function_box':
            return ''
        entry_node = cast(
            AcherionNode | None,
            self._function_entry_node(node.node_id),
        )
        if entry_node is None:
            return ''
        return entry_node.node_id

    def _body_input_pins(
        self: Any,
        node: AcherionNode,
    ) -> list[tuple[int, dict[str, str]]]:
        """Return input pin specs that belong in the node body."""
        top_exec = self._top_exec_input_pin(node)
        return [
            (index, pin)
            for index, pin in enumerate(self._input_pin_specs(node))
            if not _is_exec_pin(pin)
            or top_exec is None
            or index != top_exec[0]
        ]

    def _body_output_pins(
        self: Any,
        node: AcherionNode,
    ) -> list[tuple[int, dict[str, str]]]:
        """Return output pin specs that belong in the node body."""
        top_exec = self._top_exec_output_pin(node)
        return [
            (index, pin)
            for index, pin in enumerate(self._output_pin_specs(node))
            if not _is_exec_pin(pin)
            or top_exec is None
            or index != top_exec[0]
        ]

    def _top_exec_input_pin(
        self: Any,
        node: AcherionNode,
    ) -> tuple[int, dict[str, str]] | None:
        """Return the top-row exec-input pin spec, if present."""
        exec_pins = [
            (index, pin)
            for index, pin in enumerate(self._input_pin_specs(node))
            if _is_unlabeled_exec_pin(pin)
        ]
        if len(exec_pins) == 1:
            return exec_pins[0]
        return None

    def _top_exec_output_pin(
        self: Any,
        node: AcherionNode,
    ) -> tuple[int, dict[str, str]] | None:
        """Return the top-row exec-output pin spec, if present."""
        exec_pins = [
            (index, pin)
            for index, pin in enumerate(self._output_pin_specs(node))
            if _is_unlabeled_exec_pin(pin)
        ]
        if len(exec_pins) == 1:
            return exec_pins[0]
        return None

    def _full_output_source_id(
        self: Any,
        node: AcherionNode,
        pin_index: int,
    ) -> str:
        """Return the stored source id for one output pin index."""
        n_outputs = len(self._output_pin_specs(node))
        if n_outputs > 1:
            return f'{node.node_id}@{pin_index}'
        return node.node_id

    def _body_pin_rows(
        self: Any,
        node: AcherionNode,
    ) -> list[
        dict[
            str,
            tuple[int, dict[str, str]] | None,
        ]
    ]:
        """Return ordered body rows, pairing same-label input/output pins."""
        body_inputs = self._body_input_pins(node)
        body_outputs = self._body_output_pins(node)
        output_positions_by_key: dict[tuple[str, str], list[int]] = {}
        for output_position, (_pin_index, pin) in enumerate(body_outputs):
            match_key = _pairable_body_pin_key(pin)
            if match_key is None:
                continue
            output_positions_by_key.setdefault(match_key, []).append(
                output_position
            )

        used_output_positions: set[int] = set()
        rows: list[
            dict[str, tuple[int, dict[str, str]] | None]
        ] = []
        for input_pin in body_inputs:
            matched_output: tuple[int, dict[str, str]] | None = None
            match_key = _pairable_body_pin_key(input_pin[1])
            if match_key is not None:
                output_positions = output_positions_by_key.get(match_key, [])
                if output_positions:
                    output_position = output_positions.pop(0)
                    matched_output = body_outputs[output_position]
                    used_output_positions.add(output_position)
            rows.append({'input': input_pin, 'output': matched_output})

        for output_position, output_pin in enumerate(body_outputs):
            if output_position in used_output_positions:
                continue
            rows.append({'input': None, 'output': output_pin})
        return rows

    def _body_pin_row_count(
        self: Any,
        node: AcherionNode,
    ) -> int:
        """Return rendered body row count after inline pairing."""
        return len(self._body_pin_rows(node))

    def _body_pin_row_index(
        self: Any,
        node: AcherionNode,
        *,
        direction: str,
        pin_index: int,
    ) -> int:
        """Return body row index for one input/output pin."""
        for row_index, row in enumerate(self._body_pin_rows(node)):
            pin_entry = row['input'] if direction == 'in' else row['output']
            if pin_entry is None:
                continue
            if pin_entry[0] == pin_index:
                return row_index
        return 0

    def _render_top_exec_row(
        self: Any,
        node: AcherionNode,
    ) -> None:
        """Render unlabeled exec pins as the top row in the node body."""
        exec_input = self._top_exec_input_pin(node)
        exec_output = self._top_exec_output_pin(node)
        entry_source_id = self._function_box_entry_source_id(node)
        if (
            exec_input is None
            and exec_output is None
            and not entry_source_id
        ):
            return
        with ui.row().classes('ach-wire-row ach-exec-row'):
            with ui.row().classes('items-center gap-2'):
                if exec_input is not None:
                    pin_index, pin = exec_input
                    source_id = self._input_source_id(node, pin['pin_id'])
                    btn_cls = _pin_button_classes(
                        'ach-pin-btn ach-pin-btn-in',
                        'exec',
                    )
                    if source_id:
                        btn_cls += ' ach-pin-btn-filled'
                    ui.element('div').classes(
                        f'{btn_cls} ach-pin-anchor'
                    ).props(
                        f'data-node-id={node.node_id} '
                        'data-pin-direction=in '
                        f'data-pin-index={pin_index}'
                    ).on(
                        'click',
                        lambda _e, cur=node, pid=pin['pin_id']: (
                            self._connect_input_pin(cur, pid)
                        ),
                    )
                else:
                    ui.element('div').classes('ach-exec-row-spacer')

                if entry_source_id:
                    active = self._pending_source_node_id == entry_source_id
                    btn_cls = _pin_button_classes(
                        'ach-pin-btn ach-pin-btn-out',
                        'exec',
                    )
                    if self._has_outgoing_connection(entry_source_id):
                        btn_cls += ' ach-pin-btn-filled'
                    if active:
                        btn_cls += ' ach-pin-btn-active'
                    ui.element('div').classes(
                        f'{btn_cls} ach-pin-anchor'
                    ).props(
                        f'data-node-id={node.node_id} '
                        'data-pin-direction=out '
                        'data-pin-index=entry '
                        'title="Internal entry"'
                    ).on(
                        'click',
                        lambda _e, sid=entry_source_id: self._start_connection(sid),
                    )
            ui.space()
            if exec_output is not None:
                pin_index, _pin = exec_output
                source_id = self._full_output_source_id(node, pin_index)
                active = self._pending_source_node_id == source_id
                btn_cls = _pin_button_classes('ach-pin-btn ach-pin-btn-out', 'exec')
                if self._has_outgoing_connection(source_id):
                    btn_cls += ' ach-pin-btn-filled'
                if active:
                    btn_cls += ' ach-pin-btn-active'
                ui.element('div').classes(
                    f'{btn_cls} ach-pin-anchor'
                ).props(
                    f'data-node-id={node.node_id} '
                    'data-pin-direction=out '
                    f'data-pin-index={pin_index}'
                ).on(
                    'click',
                    lambda _e, sid=source_id: self._start_connection(sid),
                )
            else:
                ui.element('div').classes('ach-exec-row-spacer')

    def _render_input_pin_row(
        self: Any,
        node: AcherionNode,
        *,
        pin_index: int,
        pin_id: str,
        label: str,
        pin_type: str = 'any',
        editor_kind: str = '',
        optional: bool = False,
    ) -> None:
        source_id = self._input_source_id(node, pin_id)
        is_incompatible = False
        if self._pending_source_node_id is not None:
            pending_type = self._pending_output_type()
            if not _catalog_types.types_compatible(pending_type, pin_type):
                is_incompatible = True
        btn_cls = _pin_button_classes('ach-pin-btn ach-pin-btn-in', pin_type)
        if optional:
            btn_cls += ' ach-pin-btn-optional'
        if source_id:
            btn_cls += ' ach-pin-btn-filled'
        row_cls = 'ach-wire-row'
        if is_incompatible:
            row_cls += ' ach-pin-incompatible'
        if optional:
            row_cls += ' ach-wire-row-optional'
        with ui.row().classes(row_cls):
            ui.element('div').classes(
                f'{btn_cls} ach-pin-anchor'
            ).props(
                f'data-node-id={node.node_id} '
                f'data-pin-direction=in '
                f'data-pin-index={pin_index}'
            ).on(
                'click',
                lambda _e, cur=node, pid=pin_id: self._connect_input_pin(cur, pid),
            )
            ui.label(label).classes('ach-wire-label')
            self._render_input_literal_editor(
                node,
                pin_id=pin_id,
                pin_type=pin_type,
                editor_kind=editor_kind,
                source_id=source_id,
            )
            ui.space()

    def _render_output_pin_row(
        self: Any,
        node: AcherionNode,
        *,
        pin_index: int,
        label: str,
        pin_type: str = 'any',
    ) -> None:
        full_src_id = self._full_output_source_id(node, pin_index)
        active = self._pending_source_node_id == full_src_id
        btn_cls = _pin_button_classes('ach-pin-btn ach-pin-btn-out', pin_type)
        if self._has_outgoing_connection(full_src_id):
            btn_cls += ' ach-pin-btn-filled'
        if active:
            btn_cls += ' ach-pin-btn-active'
        with ui.row().classes('ach-wire-row'):
            ui.label(label).classes('ach-wire-label')
            self._render_inline_default_editor(node)
            ui.space()
            ui.element('div').classes(
                f'{btn_cls} ach-pin-anchor'
            ).props(
                f'data-node-id={node.node_id} '
                f'data-pin-direction=out '
                f'data-pin-index={pin_index}'
            ).on(
                'click',
                lambda _e, sid=full_src_id: self._start_connection(sid),
            )

    def _render_inline_pin_row(
        self: Any,
        node: AcherionNode,
        *,
        input_pin_index: int,
        input_pin_id: str,
        output_pin_index: int,
        label: str,
        pin_type: str = 'any',
        editor_kind: str = '',
        optional: bool = False,
    ) -> None:
        """Render one centered row with matching input and output pins."""
        source_id = self._input_source_id(node, input_pin_id)
        is_incompatible = False
        if self._pending_source_node_id is not None:
            pending_type = self._pending_output_type()
            if not _catalog_types.types_compatible(pending_type, pin_type):
                is_incompatible = True

        input_btn_cls = _pin_button_classes(
            'ach-pin-btn ach-pin-btn-in',
            pin_type,
        )
        if optional:
            input_btn_cls += ' ach-pin-btn-optional'
        if source_id:
            input_btn_cls += ' ach-pin-btn-filled'

        full_src_id = self._full_output_source_id(node, output_pin_index)
        active = self._pending_source_node_id == full_src_id
        output_btn_cls = _pin_button_classes(
            'ach-pin-btn ach-pin-btn-out',
            pin_type,
        )
        if self._has_outgoing_connection(full_src_id):
            output_btn_cls += ' ach-pin-btn-filled'
        if active:
            output_btn_cls += ' ach-pin-btn-active'

        row_cls = 'ach-wire-row ach-wire-row-inline'
        if is_incompatible:
            row_cls += ' ach-pin-incompatible'
        if optional:
            row_cls += ' ach-wire-row-optional'

        with ui.row().classes(row_cls):
            ui.element('div').classes(
                f'{input_btn_cls} ach-pin-anchor'
            ).props(
                f'data-node-id={node.node_id} '
                'data-pin-direction=in '
                f'data-pin-index={input_pin_index}'
            ).on(
                'click',
                lambda _e, cur=node, pid=input_pin_id: (
                    self._connect_input_pin(cur, pid)
                ),
            )
            with ui.column().classes('ach-wire-inline-center'):
                with ui.row().classes('ach-wire-inline-meta'):
                    ui.label(label).classes('ach-wire-label')
                    if not self._render_inline_default_editor(node):
                        self._render_input_literal_editor(
                            node,
                            pin_id=input_pin_id,
                            pin_type=pin_type,
                            editor_kind=editor_kind,
                            source_id=source_id,
                        )
            ui.element('div').classes(
                f'{output_btn_cls} ach-pin-anchor'
            ).props(
                f'data-node-id={node.node_id} '
                'data-pin-direction=out '
                f'data-pin-index={output_pin_index}'
            ).on(
                'click',
                lambda _e, sid=full_src_id: self._start_connection(sid),
            )

    def _render_body_pin_rows(
        self: Any,
        node: AcherionNode,
    ) -> None:
        """Render node body rows with inline matching io pairs."""
        for row in self._body_pin_rows(node):
            input_pin = row['input']
            output_pin = row['output']
            if input_pin is not None and output_pin is not None:
                input_index, input_spec = input_pin
                output_index, output_spec = output_pin
                self._render_inline_pin_row(
                    node,
                    input_pin_index=input_index,
                    input_pin_id=input_spec['pin_id'],
                    output_pin_index=output_index,
                    label=input_spec['label'],
                    pin_type=input_spec.get('type', 'any'),
                    editor_kind=input_spec.get('editor_kind', ''),
                    optional=input_spec.get('optional') == 'true',
                )
                continue
            if input_pin is not None:
                input_index, input_spec = input_pin
                self._render_input_pin_row(
                    node,
                    pin_index=input_index,
                    pin_id=input_spec['pin_id'],
                    label=input_spec['label'],
                    pin_type=input_spec.get('type', 'any'),
                    editor_kind=input_spec.get('editor_kind', ''),
                    optional=input_spec.get('optional') == 'true',
                )
                continue
            if output_pin is not None:
                output_index, output_spec = output_pin
                self._render_output_pin_row(
                    node,
                    pin_index=output_index,
                    label=output_spec['label'],
                    pin_type=output_spec.get('type', 'any'),
                )

    def _render_system_source_node(
        self: Any,
        node: AcherionNode,
    ) -> None:
        for index, pin in self._body_output_pins(node):
            self._render_output_pin_row(
                node,
                pin_index=index,
                label=pin['label'],
                pin_type=pin.get('type', 'any'),
            )

    def _render_system_sink_node(
        self: Any,
        node: AcherionNode,
        graph_index: int,  # noqa: ARG002
    ) -> None:
        self._render_body_pin_rows(node)

    def _render_function_box_node(
        self: Any,
        node: AcherionNode,
        graph_index: int,
    ) -> None:
        input_count = len(self._function_box_boundary_input_sources(node.node_id))
        output_count = len(self._function_box_boundary_output_sources(node.node_id))
        internal_nodes = self._visible_function_child_nodes(node.node_id)
        subtitle = (
            f'{_node_var_name(graph_index, node)} - '
            f'{len(internal_nodes)} nodes - '
            f'{input_count} inputs - '
            f'{output_count} outputs'
        )

        with ui.element('div').classes('ach-function-box-head'):
            ui.icon('drag_indicator').classes('ach-node-drag')
            ui.icon(_template_icon(node.kind)).classes('ach-function-box-icon')
            with ui.column().classes('gap-0 min-w-0'):
                ui.label(node.title or _template_title(node.kind)).classes(
                    'ach-function-box-title'
                )
                ui.label(subtitle).classes('ach-function-box-subtitle')
            ui.space()
            ui.button(
                icon='edit',
                on_click=lambda _e, nid=node.node_id: self._open_node_config_dialog(nid),
            ).props('flat dense round')
            ui.button(
                icon='delete',
                color='negative',
                on_click=lambda _e, nid=node.node_id: self._delete_node(nid),
            ).props('flat dense round')

        with ui.element('div').classes('ach-node-body'):
            self._render_top_exec_row(node)
