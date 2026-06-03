"""Pin and node-card rendering mixin for AcherionDesigner."""

# pyright: reportAttributeAccessIssue=false

from __future__ import annotations

import ast
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


def _event_bool_arg(args: Any, key: str) -> bool:
    """Return bool event arg when present."""
    if not isinstance(args, dict):
        return False
    value = cast(dict[str, object], args).get(key)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {'1', 'true', 'yes', 'on'}
    return bool(value)


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
        refresh: bool = True,
    ) -> None:
        """Persist one inline node default value."""
        if input_kind == 'bool':
            node.params[field_name] = bool(value)
        elif input_kind == 'dict':
            clean_value = str(value or '{}').strip()
            node.params[field_name] = clean_value or '{}'
        elif input_kind == 'number':
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
            if refresh:
                self._notify_change()
            else:
                self._notify_change_without_refresh()

    def _mark_pending_inline_local_change(self: Any) -> None:
        self._pending_inline_local_change = True

    def _flush_pending_inline_local_change(
        self: Any,
        event: Any,
    ) -> None:
        if _event_bool_arg(getattr(event, 'args', None), 'keep_pending'):
            return
        if not bool(getattr(self, '_pending_inline_local_change', False)):
            return
        self._notify_change_without_refresh()

    def _render_inline_default_editor(self: Any, node: AcherionNode) -> bool:
        """Render compact node-card editor for supported default values."""
        if acherion_node_behaviors.render_inline_controls_for_node(self, node):
            return True
        spec = self._inline_default_editor_spec(node)
        if spec is None:
            return False
        input_kind, field_name, current_value = spec
        field_classes = 'ach-node-inline-field'
        if input_kind == 'bool':
            ui.checkbox(
                value=bool(current_value),
                on_change=lambda e, cur=node: self._set_inline_default_value(
                    cur,
                    field_name=field_name,
                    input_kind='bool',
                    value=bool(getattr(e, 'value', False)),
                ),
            ).props('dense').classes(
                'ach-node-inline-field ach-node-inline-field-bool'
            )
            return True

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

            def _stage_number_value(event: Any) -> None:
                self._set_inline_default_value(
                    node,
                    field_name=field_name,
                    input_kind=input_kind,
                    value=getattr(event, 'args', None),
                    notify=False,
                )
                self._mark_pending_inline_local_change()

            def _commit_number_value(event: Any) -> None:
                self._set_inline_default_value(
                    node,
                    field_name=field_name,
                    input_kind=input_kind,
                    value=number_field.value,
                    notify=False,
                )
                self._flush_pending_inline_local_change(event)

            number_field.on(
                'update:model-value',
                _stage_number_value,
            )
            number_field.on(
                'blur',
                _commit_number_value,
                js_handler=(
                    '(e) => emit({'
                    'keep_pending: !!('
                    'e.relatedTarget && '
                    'e.relatedTarget.closest(".ach-node-inline-field")'
                    ')'
                    '})'
                ),
            )
            number_field.on('keydown.enter', _commit_number_value)
            return True

        if input_kind == 'dict':
            field_classes += ' ach-node-inline-field-dict'
            current_text = str(current_value or '{}').strip() or '{}'
        else:
            field_classes += ' ach-node-inline-field-text'
            current_text = str(current_value or '')
        text_field = ui.input(
            value=current_text,
        ).props('dense outlined hide-bottom-space').classes(
            field_classes
        )

        def _stage_text_value(event: Any) -> None:
            self._set_inline_default_value(
                node,
                field_name=field_name,
                input_kind=input_kind,
                value=getattr(event, 'args', None),
                notify=False,
            )
            self._mark_pending_inline_local_change()

        def _commit_text_value(event: Any) -> None:
            self._set_inline_default_value(
                node,
                field_name=field_name,
                input_kind=input_kind,
                value=text_field.value,
                notify=False,
            )
            self._flush_pending_inline_local_change(event)

        text_field.on('update:model-value', _stage_text_value)
        text_field.on(
            'blur',
            _commit_text_value,
            js_handler=(
                '(e) => emit({'
                'keep_pending: !!('
                'e.relatedTarget && '
                'e.relatedTarget.closest(".ach-node-inline-field")'
                ')'
                '})'
            ),
        )
        text_field.on('keydown.enter', _commit_text_value)
        return True

    @staticmethod
    def _pin_literal_input_kind(
        pin_type: str,
        editor_kind: str = '',
    ) -> str | None:
        """Return compact editor kind for one eligible input pin type."""
        if editor_kind in {'bool', 'dict', 'number', 'text'}:
            return editor_kind
        if pin_type == 'bool':
            return 'bool'
        if pin_type == 'dict':
            return 'dict'
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

    @staticmethod
    def _coerce_pin_literal_value(
        value: Any,
        *,
        input_kind: str,
        pin_type: str,
    ) -> Any:
        """Normalize one literal input value using the pin's declared type."""
        if input_kind == 'bool':
            if isinstance(value, str):
                return value.strip().lower() in {'1', 'true', 'yes', 'on'}
            return bool(value)
        if input_kind == 'dict':
            raw_value = str(value or '{}').strip() or '{}'
            try:
                parsed_value = ast.literal_eval(raw_value)
            except (SyntaxError, ValueError):
                return {}
            return parsed_value if isinstance(parsed_value, dict) else {}
        if input_kind != 'number':
            return str(value)
        if pin_type == 'int':
            try:
                return int(float(value))
            except (TypeError, ValueError):
                return None
        if pin_type == 'float':
            try:
                return float(value)
            except (TypeError, ValueError):
                return None
        return value

    def _set_pin_literal_value(
        self: Any,
        node: AcherionNode,
        *,
        pin_id: str,
        input_kind: str,
        pin_type: str,
        value: Any,
        notify: bool = True,
        refresh: bool = True,
    ) -> None:
        """Persist one literal fallback value for an input pin."""
        literals = dict(node.params.get('pin_literals') or {})
        coerced_value = self._coerce_pin_literal_value(
            value,
            input_kind=input_kind,
            pin_type=pin_type,
        )
        if coerced_value in (None, ''):
            literals.pop(pin_id, None)
        else:
            literals[pin_id] = coerced_value
        node.params['pin_literals'] = literals
        if notify:
            if refresh:
                self._notify_change()
            else:
                self._notify_change_without_refresh()

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
        if input_kind == 'bool':
            ui.checkbox(
                value=bool(current_value),
                on_change=lambda e, cur=node, pid=pin_id, ptype=pin_type: (
                    self._set_pin_literal_value(
                        cur,
                        pin_id=pid,
                        input_kind='bool',
                        pin_type=ptype,
                        value=bool(getattr(e, 'value', False)),
                    )
                ),
            ).props('dense').classes(
                'ach-node-inline-field ach-node-inline-field-bool'
            )
            return True

        field_classes = 'ach-node-inline-field'
        if input_kind == 'number':
            field_classes += ' ach-node-inline-field-number'
            step = '1' if pin_type == 'int' else 'any'
            number_field = ui.number(
                value=current_value,
            ).props(
                f'dense outlined hide-bottom-space step={step}'
            ).classes(field_classes)

            def _stage_literal_number(event: Any) -> None:
                self._set_pin_literal_value(
                    node,
                    pin_id=pin_id,
                    input_kind=input_kind,
                    pin_type=pin_type,
                    value=getattr(event, 'args', None),
                    notify=False,
                )
                self._mark_pending_inline_local_change()

            def _commit_literal_number(event: Any) -> None:
                self._set_pin_literal_value(
                    node,
                    pin_id=pin_id,
                    input_kind=input_kind,
                    pin_type=pin_type,
                    value=number_field.value,
                    notify=False,
                )
                self._flush_pending_inline_local_change(event)

            number_field.on(
                'update:model-value',
                _stage_literal_number,
            )
            number_field.on(
                'blur',
                _commit_literal_number,
                js_handler=(
                    '(e) => emit({'
                    'keep_pending: !!('
                    'e.relatedTarget && '
                    'e.relatedTarget.closest(".ach-node-inline-field")'
                    ')'
                    '})'
                ),
            )
            number_field.on('keydown.enter', _commit_literal_number)
            return True

        if input_kind == 'dict':
            field_classes += ' ach-node-inline-field-dict'
            if current_value is None:
                current_text = '{}'
            elif isinstance(current_value, str):
                current_text = current_value.strip() or '{}'
            else:
                current_text = repr(current_value)
        else:
            field_classes += ' ach-node-inline-field-text'
            current_text = '' if current_value is None else str(current_value)
        text_field = ui.input(
            value=current_text,
        ).props('dense outlined hide-bottom-space').classes(
            field_classes
        )

        def _stage_literal_text(event: Any) -> None:
            self._set_pin_literal_value(
                node,
                pin_id=pin_id,
                input_kind=input_kind,
                pin_type=pin_type,
                value=getattr(event, 'args', None),
                notify=False,
            )
            self._mark_pending_inline_local_change()

        def _commit_literal_text(event: Any) -> None:
            self._set_pin_literal_value(
                node,
                pin_id=pin_id,
                input_kind=input_kind,
                pin_type=pin_type,
                value=text_field.value,
                notify=False,
            )
            self._flush_pending_inline_local_change(event)

        text_field.on(
            'update:model-value',
            _stage_literal_text,
        )
        text_field.on(
            'blur',
            _commit_literal_text,
            js_handler=(
                '(e) => emit({'
                'keep_pending: !!('
                'e.relatedTarget && '
                'e.relatedTarget.closest(".ach-node-inline-field")'
                ')'
                '})'
            ),
        )
        text_field.on('keydown.enter', _commit_literal_text)
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
        return f'{node.node_id}@{pin_index}'

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
        if node.kind == 'else_if_branch':
            return len(self._body_input_pins(node))
        if node.kind == 'for_each':
            data_outputs = [
                pin for _index, pin in self._body_output_pins(node)
                if not _is_exec_pin(pin)
            ]
            return 1 + len(data_outputs)
        if node.kind == 'sequencer':
            exec_outputs = [
                pin for _index, pin in self._body_output_pins(node)
                if _is_exec_pin(pin)
            ]
            return max(0, len(exec_outputs) - 1)
        return len(self._body_pin_rows(node))

    def _body_pin_row_index(
        self: Any,
        node: AcherionNode,
        *,
        direction: str,
        pin_index: int,
    ) -> int:
        """Return body row index for one input/output pin."""
        if node.kind == 'else_if_branch':
            if direction == 'out':
                return max(0, pin_index - 1)
            condition_indexes = [
                index for index, _pin in self._body_input_pins(node)
            ]
            if pin_index in condition_indexes:
                return condition_indexes.index(pin_index)
            return 0
        if node.kind == 'for_each':
            if direction == 'out':
                output_specs = self._output_pin_specs(node)
                if pin_index < len(output_specs):
                    pin_id = str(output_specs[pin_index].get('pin_id') or '')
                    if pin_id == 'completed':
                        return 0
                    data_indexes = [
                        index for index, pin in enumerate(output_specs)
                        if not _is_exec_pin(pin)
                    ]
                    if pin_index in data_indexes:
                        return data_indexes.index(pin_index) + 1
                return 0
            input_indexes = [
                index for index, _pin in self._body_input_pins(node)
            ]
            if pin_index in input_indexes:
                return input_indexes.index(pin_index)
            return 0
        if node.kind == 'sequencer':
            if direction == 'out':
                exec_indexes = [
                    index for index, pin in enumerate(self._output_pin_specs(node))
                    if _is_exec_pin(pin)
                ]
                if pin_index in exec_indexes:
                    return max(0, exec_indexes.index(pin_index) - 1)
            return 0
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

    def _render_shifted_exec_output_pin(
        self: Any,
        node: AcherionNode,
        *,
        pin_index: int,
        label: str,
    ) -> None:
        """Render one labeled exec output at the right edge of a shifted row."""
        full_src_id = self._full_output_source_id(node, pin_index)
        active = self._pending_source_node_id == full_src_id
        btn_cls = _pin_button_classes('ach-pin-btn ach-pin-btn-out', 'exec')
        if self._has_outgoing_connection(full_src_id):
            btn_cls += ' ach-pin-btn-filled'
        if active:
            btn_cls += ' ach-pin-btn-active'
        ui.label(label).classes('ach-wire-label')
        ui.element('div').classes(
            f'{btn_cls} ach-pin-anchor'
        ).props(
            f'data-node-id={node.node_id} '
            'data-pin-direction=out '
            f'data-pin-index={pin_index}'
        ).on(
            'click',
            lambda _e, sid=full_src_id: self._start_connection(sid),
        )

    def _render_shifted_exec_output_row(
        self: Any,
        node: AcherionNode,
        output_pin: tuple[int, dict[str, str]] | None,
    ) -> None:
        """Render a right-justified shifted exec output row."""
        with ui.row().classes('ach-wire-row ach-exec-row'):
            ui.space()
            if output_pin is not None:
                output_index, output_spec = output_pin
                self._render_shifted_exec_output_pin(
                    node,
                    pin_index=output_index,
                    label=output_spec['label'],
                )
            else:
                ui.element('div').classes('ach-exec-row-spacer')

    def _render_shifted_exec_top_row(
        self: Any,
        node: AcherionNode,
        output_pin: tuple[int, dict[str, str]] | None,
    ) -> None:
        """Render the exec input and first shifted exec output on the top row."""
        exec_input = self._top_exec_input_pin(node)
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
            ui.space()
            if output_pin is not None:
                output_index, output_spec = output_pin
                self._render_shifted_exec_output_pin(
                    node,
                    pin_index=output_index,
                    label=output_spec['label'],
                )
            else:
                ui.element('div').classes('ach-exec-row-spacer')

    def _render_input_with_shifted_exec_output_row(
        self: Any,
        node: AcherionNode,
        *,
        input_pin: tuple[int, dict[str, str]],
        output_pin: tuple[int, dict[str, str]] | None,
    ) -> None:
        """Render one input with a shifted exec output on the same row."""
        input_index, input_spec = input_pin
        pin_id = input_spec['pin_id']
        pin_type = input_spec.get('type', 'any')
        optional = input_spec.get('optional') == 'true'
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
                'data-pin-direction=in '
                f'data-pin-index={input_index}'
            ).on(
                'click',
                lambda _e, cur=node, pid=pin_id: (
                    self._connect_input_pin(cur, pid)
                ),
            )
            ui.label(input_spec['label']).classes('ach-wire-label')
            self._render_input_literal_editor(
                node,
                pin_id=pin_id,
                pin_type=pin_type,
                editor_kind=input_spec.get('editor_kind', ''),
                source_id=source_id,
            )
            ui.space()
            if output_pin is not None:
                output_index, output_spec = output_pin
                self._render_shifted_exec_output_pin(
                    node,
                    pin_index=output_index,
                    label=output_spec['label'],
                )
            else:
                ui.element('div').classes('ach-exec-row-spacer')

    def _render_else_if_branch_node(
        self: Any,
        node: AcherionNode,
    ) -> None:
        """Render an else-if branch with exec outputs shifted up one row."""
        condition_inputs = self._body_input_pins(node)
        exec_outputs = self._body_output_pins(node)
        self._render_shifted_exec_top_row(
            node,
            exec_outputs[0] if exec_outputs else None,
        )
        for index, input_pin in enumerate(condition_inputs):
            output_index = index + 1
            self._render_input_with_shifted_exec_output_row(
                node,
                input_pin=input_pin,
                output_pin=(
                    exec_outputs[output_index]
                    if output_index < len(exec_outputs)
                    else None
                ),
            )

    def _render_for_each_node(
        self: Any,
        node: AcherionNode,
    ) -> None:
        """Render For Each with exec outputs shifted to the first two rows."""
        input_pins = {
            pin.get('pin_id'): (index, pin)
            for index, pin in self._body_input_pins(node)
        }
        output_pins = {
            pin.get('pin_id'): (index, pin)
            for index, pin in enumerate(self._output_pin_specs(node))
        }
        self._render_shifted_exec_top_row(
            node,
            output_pins.get('loop_body'),
        )
        list_input = input_pins.get('list')
        if list_input is not None:
            self._render_input_with_shifted_exec_output_row(
                node,
                input_pin=list_input,
                output_pin=output_pins.get('completed'),
            )
        else:
            self._render_shifted_exec_output_row(
                node,
                output_pins.get('completed'),
            )
        for output_index, output_spec in enumerate(self._output_pin_specs(node)):
            if _is_exec_pin(output_spec):
                continue
            self._render_output_pin_row(
                node,
                pin_index=output_index,
                label=output_spec['label'],
                pin_type=output_spec.get('type', 'any'),
            )

    def _render_sequencer_node(
        self: Any,
        node: AcherionNode,
    ) -> None:
        """Render Sequencer with Then outputs shifted up and right-aligned."""
        exec_outputs = [
            (index, pin)
            for index, pin in enumerate(self._output_pin_specs(node))
            if _is_exec_pin(pin)
        ]
        self._render_shifted_exec_top_row(
            node,
            exec_outputs[0] if exec_outputs else None,
        )
        for output_pin in exec_outputs[1:]:
            self._render_shifted_exec_output_row(node, output_pin)

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
