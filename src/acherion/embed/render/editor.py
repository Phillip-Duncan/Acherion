"""Node editor rendering mixin for AcherionDesigner."""

# pyright: reportAttributeAccessIssue=false

from __future__ import annotations

import ast
import copy
import os
import tempfile
from typing import Any, Callable

from nicegui import events, ui

import acherion.embed.code_editor as acherion_code_editor
from acherion.catalog import plotly as _catalog_plotly
from acherion.catalog import runtime as _catalog_runtime
import acherion.node_behaviors as acherion_node_behaviors
from acherion.model import (
    AcherionNode,
    _template_title,
)
from acherion.preview import (
    preview_value_plotly_payload,
    preview_value_summary,
    preview_value_type_tag,
)
from acherion.registry import (
    get_acherion_node_definition,
)


class _RenderEditorMixin:
    """Node editor helper and dialog rendering methods."""

    @staticmethod
    def _custom_function_data_summary(data: dict[str, Any]) -> str:
        """Return short summary of inferred custom-function pin types."""
        param_names = [
            str(value)
            for value in list(data.get('param_names') or [])
        ]
        param_types = [
            str(value or 'any')
            for value in list(data.get('param_types') or [])
        ]
        min_args = int(data.get('min_args') or 0)
        input_bits = []
        for index, name in enumerate(param_names):
            type_tag = param_types[index] if index < len(param_types) else 'any'
            optional = ' optional' if index >= min_args else ''
            input_bits.append(f'{name}: {type_tag}{optional}')
        inputs_summary = ', '.join(input_bits) if input_bits else 'none'
        output_type = str(data.get('return_type') or '').strip()
        if output_type:
            return f'Inputs: {inputs_summary} | Output: {output_type}'
        return f'Inputs: {inputs_summary}'

    @staticmethod
    def _valid_dict_literal(value: Any) -> bool:
        """Return True when value is blank or parses as a Python dict literal."""
        raw = str(value or '').strip()
        if not raw:
            return True
        try:
            parsed = ast.literal_eval(raw)
        except (SyntaxError, ValueError):
            return False
        return isinstance(parsed, dict)

    def _validate_editor_node(self: Any, node: AcherionNode) -> bool:
        """Return True when the staged node is valid enough to save."""
        if node.kind == 'constant' and str(node.params.get('value_type') or '') == 'dict':
            raw = str(node.params.get('dict_value') or '').strip()
            if not self._valid_dict_literal(raw):
                self._notify_ui(
                    'Dict constants must be valid Python dict literals before saving.',
                    type='negative',
                )
                return False
        return True

    @staticmethod
    def _apply_editor_change(
        change: Callable[[], None],
        refresh_editor: Callable[[], None] | None,
        *,
        refresh_editor_after: bool = False,
    ) -> None:
        change()
        if refresh_editor_after and refresh_editor is not None:
            refresh_editor()

    def _clone_editor_node(self: Any, node: AcherionNode) -> AcherionNode:
        """Return a detached copy used by the staged node editor."""
        return AcherionNode(
            node_id=node.node_id,
            kind=node.kind,
            title=node.title,
            params=copy.deepcopy(node.params),
        )

    def _set_editor_param(
        self: Any,
        node: AcherionNode,
        key: str,
        value: Any,
    ) -> None:
        """Mutate draft node params without persisting to the graph."""
        node.params[key] = value
        if node.kind == 'function_box' and key == 'function_name':
            node.params['function_name'] = self._sanitize_identifier(
                str(value or ''),
                f'function_{node.node_id}',
            )

    def _set_editor_title(
        self: Any,
        node: AcherionNode,
        value: Any,
    ) -> None:
        """Mutate draft node title without persisting to the graph."""
        node.title = str(value or '')

    @staticmethod
    def _default_make_dict_key_name(index: int) -> str:
        """Return fallback key label for one make_dict input."""
        return f'key_{index + 1}'

    def _set_editor_arg_count(
        self: Any,
        node: AcherionNode,
        value: Any,
    ) -> None:
        """Mutate draft arg_count and arg_sources without persisting."""
        lower_bound = (
            0
            if node.kind in {
                'call_function',
                'custom_function',
                'make_list',
                'make_dict',
            }
            else 1
        )
        arg_count = max(lower_bound, int(value or 0))
        if node.kind not in {'make_list', 'make_dict'}:
            arg_count = min(8, arg_count)
        arg_sources = list(node.params.get('arg_sources') or [])
        while len(arg_sources) < arg_count:
            arg_sources.append('')
        node.params['arg_sources'] = arg_sources[:arg_count]
        node.params['arg_count'] = arg_count
        if node.kind == 'make_dict':
            key_names = list(node.params.get('key_names') or [])
            while len(key_names) < arg_count:
                key_names.append(
                    self._default_make_dict_key_name(len(key_names))
                )
            node.params['key_names'] = key_names[:arg_count]

    def _set_editor_make_dict_key(
        self: Any,
        node: AcherionNode,
        index: int,
        value: Any,
    ) -> None:
        """Mutate one make_dict key name without persisting."""
        key_names = list(node.params.get('key_names') or [])
        while len(key_names) <= index:
            key_names.append(
                self._default_make_dict_key_name(len(key_names))
            )
        clean_key = str(value or '').strip()
        key_names[index] = clean_key or self._default_make_dict_key_name(index)
        node.params['key_names'] = key_names

    def _set_editor_then_count(
        self: Any,
        node: AcherionNode,
        value: Any,
    ) -> None:
        """Mutate draft sequencer branch count without persisting."""
        then_count = max(2, int(value or 0))
        node.params['then_count'] = min(8, then_count)

    def _set_editor_catalog_function(
        self: Any,
        node: AcherionNode,
        path: str,
    ) -> None:
        """Set draft function_path from catalog selection."""
        entry = self._function_entry(path)
        node.params['function_path'] = path
        node.params['module'] = self._function_path_to_module(path)
        self._set_editor_arg_count(node, entry.min_args if entry else 1)

    def _set_editor_catalog_module(
        self: Any,
        node: AcherionNode,
        module_key: str,
    ) -> None:
        """Switch draft catalog module and clear stale callable state."""
        current_path = str(node.params.get('function_path') or '')
        if current_path not in self._function_options(module_key):
            node.params['function_path'] = ''
            node.params['arg_count'] = 1
            node.params['arg_sources'] = ['']
        node.params['module'] = module_key

    def _set_editor_method_name(
        self: Any,
        node: AcherionNode,
        method_name: str,
        class_path: str,
    ) -> None:
        """Set draft method_name and seed arg_sources from signature."""
        node.params['method_name'] = method_name
        entry = (
            _catalog_runtime.method_func_entry(class_path, method_name)
            if class_path else None
        )
        if entry:
            arg_sources = list(node.params.get('arg_sources') or [])
            while len(arg_sources) < entry.min_args:
                arg_sources.append('')
            node.params['arg_sources'] = arg_sources

    def _commit_editor_node(
        self: Any,
        node_id: str,
        draft_node: AcherionNode,
    ) -> bool:
        """Commit staged node editor changes into the live graph."""
        node = self._node_by_id(node_id)
        if node is None:
            self._notify_ui('Node no longer exists.', type='warning')
            return False
        if not self._validate_editor_node(draft_node):
            return False
        node.title = draft_node.title
        node.params = dict(draft_node.params)
        if node.kind == 'function_box':
            node.params['function_name'] = self._sanitize_identifier(
                str(node.params.get('function_name') or ''),
                str(node.title or f'function_{node.node_id}'),
            )
        if node.kind == 'custom_function':
            self._ensure_custom_function_entry(node)
            self._cleanup_custom_function_entries()
        self._notify_change()
        return True

    def _commit_custom_function_node(
        self: Any,
        node_id: str,
        source_code: str,
    ) -> bool:
        """Commit custom function source into graph.user_functions and node."""
        node = self._node_by_id(node_id)
        if node is None:
            self._notify_ui('Node no longer exists.', type='warning')
            return False
        current_path = str(node.params.get('function_path') or '').strip()
        new_path, data, error = self._prepare_custom_function_data(
            node_id=node_id,
            current_path=current_path,
            source_code=source_code,
        )
        if new_path is None or data is None:
            self._notify_ui(error or 'Custom function is invalid.', type='negative')
            return False
        if current_path and current_path != new_path:
            self._graph.user_functions.pop(current_path, None)
        self._graph.user_functions[new_path] = data
        max_args = int(data.get('max_args') or 0)
        arg_sources = list(node.params.get('arg_sources') or [])
        while len(arg_sources) < max_args:
            arg_sources.append('')
        node.params['function_path'] = new_path
        node.params['module'] = 'user'
        node.params['arg_count'] = max_args
        node.params['arg_sources'] = arg_sources[:max_args]
        node.title = str(data.get('label') or node.title)
        self._cleanup_custom_function_entries()
        self._notify_change()
        return True

    def _open_custom_function_dialog(self: Any, node_id: str) -> None:
        """Open compact code editor for one custom function node."""
        node = self._node_by_id(node_id)
        if node is None or self._overlay_host_el is None:
            return
        self._ensure_custom_function_entry(node)
        data = dict(
            (self._graph.user_functions or {}).get(
                str(node.params.get('function_path') or '').strip()
            )
            or {}
        )
        draft_source = {
            'value': str(data.get('source_code') or '')
            or self._default_custom_function_source(
                str(node.params.get('function_path') or 'user.custom_function')
                .split('.', 1)[1]
            )
        }
        validation_state = {
            'validated_source': draft_source['value'] if data else None,
        }
        with self._overlay_host_el:
            dlg = ui.dialog()
            with dlg, ui.card().classes('ach-node-editor-card').style(
                'background:#000000; border:1px solid #2f3336;'
                ' border-radius:12px; padding:20px; min-width:560px;'
                ' max-width:820px; width:min(820px, calc(100vw - 48px));'
            ):
                ui.label('Custom Function').classes('text-base font-bold oe-text')
                ui.label(
                    'Define exactly one function like def my_func(value):'
                ).classes('text-xs oe-muted')
                ui.label(
                    'Optional positional params become input pins. Return value '
                    'feeds the node output.'
                ).classes('text-xs oe-muted')

                status_label = ui.label(
                    'Validate before saving changes.'
                    if not data else
                    'Current saved code is valid. Re-validate after edits.'
                ).classes('text-xs oe-muted')
                summary_label = ui.label(
                    self._custom_function_data_summary(data)
                    if data else ''
                ).classes('text-xs oe-muted font-mono')

                def _set_validation_feedback(
                    message: str,
                    *,
                    negative: bool,
                    summary: str = '',
                ) -> None:
                    status_label.text = message
                    status_label.classes(
                        remove='oe-muted text-positive text-negative',
                    )
                    if negative:
                        status_label.classes(add='text-negative')
                    else:
                        status_label.classes(add='text-positive')
                    summary_label.text = summary

                def _invalidate_validation() -> None:
                    validation_state['validated_source'] = None
                    status_label.text = 'Code changed. Validate before saving.'
                    status_label.classes(
                        remove='text-positive text-negative',
                    )
                    status_label.classes(add='oe-muted')
                    summary_label.text = ''
                    save_button.props(add='disable')

                def _validate() -> bool:
                    current_node = self._node_by_id(node_id)
                    if current_node is None:
                        _set_validation_feedback(
                            'Node no longer exists.',
                            negative=True,
                        )
                        save_button.props(add='disable')
                        return False
                    current_path = str(
                        current_node.params.get('function_path') or ''
                    ).strip()
                    _path, validated_data, error = (
                        self._prepare_custom_function_data(
                            node_id=node_id,
                            current_path=current_path,
                            source_code=draft_source['value'],
                        )
                    )
                    if validated_data is None:
                        validation_state['validated_source'] = None
                        _set_validation_feedback(
                            error or 'Custom function is invalid.',
                            negative=True,
                        )
                        save_button.props(add='disable')
                        return False
                    validation_state['validated_source'] = draft_source['value']
                    _set_validation_feedback(
                        'Custom function is valid.',
                        negative=False,
                        summary=self._custom_function_data_summary(
                            validated_data
                        ),
                    )
                    save_button.props(remove='disable')
                    return True

                def _on_editor_change(e: Any) -> None:
                    draft_source['value'] = str(e.value or '')
                    _invalidate_validation()

                editor = acherion_code_editor.build_python_code_editor(
                    value=draft_source['value'],
                    theme=self._preferences_state.code_editor_theme,
                    on_change=_on_editor_change,
                    classes='w-full oe-code-editor',
                    style='height:min(48vh, 420px); min-height:260px',
                )
                with ui.row().classes('justify-end gap-2 w-full pt-3'):
                    ui.button('Close', on_click=dlg.close).props('flat')
                    ui.button('Validate', on_click=_validate).props('flat')

                    def _save() -> None:
                        if validation_state['validated_source'] != draft_source['value']:
                            if not _validate():
                                return
                        if self._commit_custom_function_node(
                            node_id,
                            draft_source['value'],
                        ):
                            dlg.close()

                    save_button = ui.button(
                        'Save',
                        on_click=_save,
                    ).classes('oe-btn-primary')
                    if validation_state['validated_source'] != draft_source['value']:
                        save_button.props(add='disable')
        dlg.open()

    @staticmethod
    def _preview_binding_for_node(
        node: AcherionNode,
    ) -> acherion_node_behaviors.AcherionPreviewBinding | None:
        """Return transient preview binding for one source-like node."""
        return acherion_node_behaviors.preview_binding_for_node(node)

    def _preview_bound_value(
        self: Any,
        scope: str,
        key: str,
    ) -> Any:
        """Return one transient bound preview value."""
        clean_key = str(key or '').strip()
        if not clean_key:
            return None
        scope_values = self._preview_bindings.get(str(scope or '').strip(), {})
        return scope_values.get(clean_key)

    def _set_preview_bound_value(
        self: Any,
        scope: str,
        key: str,
        value: Any,
    ) -> None:
        """Persist one transient bound preview value and invalidate results."""
        self.set_preview_binding_value(scope, key, value)

    def _clear_preview_bound_value(
        self: Any,
        scope: str,
        key: str,
    ) -> None:
        """Remove one transient bound preview value."""
        self.clear_preview_binding_value(scope, key)

    @staticmethod
    def _preview_accept_filters(file_filter: str) -> str:
        """Return upload accept filters derived from one glob string."""
        parts = [
            part.strip()
            for part in str(file_filter or '').split(',')
            if part.strip().startswith('*.')
        ]
        if not parts:
            return ''
        return ','.join('.' + part[2:] for part in parts)

    @staticmethod
    def _preview_literal_text(value: Any) -> str:
        """Return readable literal text for one collection preview value."""
        if value in (None, ''):
            return '[]'
        return repr(value)

    def _node_preview_source_value(self: Any, node: AcherionNode) -> Any:
        """Return latest preview output value for one node, when present."""
        output_specs = self._output_pin_specs(node)
        if not output_specs:
            return None
        output_count = len(output_specs)
        for index, spec in enumerate(output_specs):
            if str(spec.get('type') or '') == 'exec':
                continue
            source_id = (
                f'{node.node_id}@{index}'
                if output_count > 1 else node.node_id
            )
            if source_id in self._preview_reference_values:
                return self._preview_reference_values.get(source_id)
            if index == 0 and node.node_id in self._preview_reference_values:
                return self._preview_reference_values.get(node.node_id)
        return None

    def _node_preview_reference_value(self: Any, node: AcherionNode) -> Any:
        """Return latest preview value for one host-defined node reference."""
        reference = acherion_node_behaviors.preview_result_reference_for_node(node)
        if not reference:
            return None
        if reference not in self._preview_reference_values:
            return None
        entry = self._preview_reference_values.get(reference)
        if isinstance(entry, dict) and 'value' in entry:
            return entry.get('value')
        return entry

    def _node_preview_result_value(self: Any, node: AcherionNode) -> Any:
        """Return best preview value visible for one node."""
        source_value = self._node_preview_source_value(node)
        if source_value is not None:
            return source_value
        return self._node_preview_reference_value(node)

    def _node_preview_summary(self: Any, node: AcherionNode) -> str:
        """Return compact preview summary text for one node."""
        value = self._node_preview_result_value(node)
        if value is None:
            return ''
        return f'Preview: {preview_value_summary(value)}'

    def _render_preview_visual(
        self: Any,
        value: Any,
        *,
        compact: bool,
    ) -> bool:
        """Render one visual preview when the runtime value supports it."""
        plotly_payload = preview_value_plotly_payload(value)
        if plotly_payload is None:
            return False
        height = '180px' if compact else '260px'
        ui.plotly(plotly_payload).classes('w-full ach-node-preview-plot').style(
            f'height:{height};'
        )
        return True

    def _render_node_preview_card(self: Any, node: AcherionNode) -> None:
        """Render one result-only preview block under a node body."""
        value = self._node_preview_result_value(node)
        if value is None:
            return
        with ui.column().classes('ach-node-preview'):
            ui.label('Preview').classes('ach-node-preview-title')
            if not self._render_preview_visual(value, compact=True):
                ui.label(
                    preview_value_summary(value)
                ).classes('ach-node-preview-value')

    def _set_preview_literal_value(
        self: Any,
        scope: str,
        key: str,
        raw_text: str,
    ) -> None:
        """Parse one Python literal preview value and store it."""
        text = str(raw_text or '').strip()
        if not text:
            self._clear_preview_bound_value(scope, key)
            return
        try:
            parsed = ast.literal_eval(text)
        except (SyntaxError, ValueError):
            self._notify_ui(
                'Preview collections must be valid Python literals.',
                type='warning',
            )
            return
        if isinstance(parsed, tuple):
            parsed = list(parsed)
        self._set_preview_bound_value(scope, key, parsed)

    def _render_preview_file_input(
        self: Any,
        *,
        scope: str,
        key: str,
        component_kind: str,
        file_filter: str,
    ) -> None:
        """Render transient preview upload controls for file-like inputs."""
        allow_multiple = component_kind in {'file_picker', 'file_picker_multi'}
        current_value = self._preview_bound_value(scope, key)
        current_paths = (
            list(current_value)
            if isinstance(current_value, list)
            else ([str(current_value)] if current_value else [])
        )
        if current_paths:
            ui.label(
                'Loaded preview files: ' + ', '.join(current_paths[:3])
                + (' ...' if len(current_paths) > 3 else '')
            ).classes('text-xs oe-muted font-mono')
        else:
            ui.label(
                'No preview file loaded yet.'
            ).classes('text-xs oe-muted')

        async def _handle_upload(
            event: events.MultiUploadEventArguments,
        ) -> None:
            temp_dir = tempfile.mkdtemp(prefix='acherion_preview_')
            uploaded_paths: list[str] = []
            for uploaded_file in event.files:
                file_name = os.path.basename(uploaded_file.name) or 'preview'
                file_path = os.path.join(temp_dir, file_name)
                content = await uploaded_file.read()
                with open(file_path, 'wb') as handle:
                    handle.write(content)
                uploaded_paths.append(file_path)
            if not uploaded_paths:
                return
            value: Any = uploaded_paths if allow_multiple else uploaded_paths[0]
            self._set_preview_bound_value(scope, key, value)
            self._notify_ui(
                f'Loaded {len(uploaded_paths)} preview file(s).',
                type='positive',
            )

        upload = ui.upload(
            label='Load Preview File' + ('s' if allow_multiple else ''),
            multiple=allow_multiple,
            auto_upload=True,
            on_multi_upload=_handle_upload,
        ).props('dense hide-upload-btn')
        accept_filters = self._preview_accept_filters(file_filter)
        if accept_filters:
            upload.props(f'accept="{accept_filters}"')
        upload.classes('w-full')

    def _render_node_preview_panel(self: Any, node: AcherionNode) -> None:
        """Render transient preview controls and latest preview results."""
        binding = self._preview_binding_for_node(node)
        preview_value = self._node_preview_result_value(node)
        if binding is None and preview_value is None:
            return
        ui.separator().classes('w-full my-2')
        ui.label('Preview').classes('text-sm font-semibold oe-text')
        ui.label(
            'Transient only. Preview values and results do not persist to '
            'generated code.'
        ).classes('text-xs oe-muted')

        if binding is not None:
            scope = binding.scope
            key = binding.key
            current_value = self._preview_bound_value(scope, key)
            scope_label = (
                str(scope or '').replace('_', ' ').strip().title() or 'Preview'
            )
            ui.label(
                f'{scope_label} key: {key}'
            ).classes('text-xs oe-muted font-mono')
            if binding.input_kind == 'number':
                ui.number(
                    'Preview value',
                    value=current_value,
                    on_change=lambda e, sc=scope, sk=key: (
                        self._clear_preview_bound_value(sc, sk)
                        if e.value in (None, '')
                        else self._set_preview_bound_value(sc, sk, e.value)
                    ),
                ).props('outlined dense').classes('w-full ach-editor-field')
            elif binding.input_kind == 'file':
                self._render_preview_file_input(
                    scope=scope,
                    key=key,
                    component_kind='file_picker_multi'
                    if binding.allow_multiple else 'file_picker',
                    file_filter=binding.file_filter,
                )
            elif binding.input_kind == 'collection':
                ui.textarea(
                    'Preview literal',
                    value=self._preview_literal_text(current_value),
                    on_change=lambda e, sc=scope, sk=key: (
                        self._set_preview_literal_value(
                            sc,
                            sk,
                            str(e.value or ''),
                        )
                    ),
                ).props('outlined').classes('w-full ach-editor-field')
            else:
                ui.input(
                    'Preview value',
                    value='' if current_value is None else str(current_value),
                    on_change=lambda e, sc=scope, sk=key: (
                        self._clear_preview_bound_value(sc, sk)
                        if str(e.value or '') == ''
                        else self._set_preview_bound_value(
                            sc,
                            sk,
                            str(e.value),
                        )
                    ),
                ).props('outlined dense').classes('w-full ach-editor-field')
            with ui.row().classes('items-center gap-2 w-full justify-end'):
                ui.button(
                    'Clear Preview',
                    on_click=lambda sc=scope, sk=key: (
                        self._clear_preview_bound_value(sc, sk)
                    ),
                ).props('flat dense')
                ui.button(
                    'Run Preview',
                    on_click=self._run_preview_current,
                ).props('flat dense')
            if current_value not in (None, '', []):
                ui.label(
                    f'Preview type: {preview_value_type_tag(current_value) or "any"}'
                ).classes('text-xs oe-muted font-mono')

        if preview_value is not None:
            if self._render_preview_visual(preview_value, compact=False):
                ui.label(
                    self._node_preview_summary(node)
                ).classes('text-xs oe-muted font-mono')
            else:
                ui.label(
                    self._node_preview_summary(node)
                ).classes('text-xs oe-text font-mono')
        else:
            ui.label(
                'Run Preview to inspect the current runtime value for this node.'
            ).classes('text-xs oe-muted')

    def _open_node_config_dialog(self: Any, node_id: str) -> None:
        node = self._node_by_id(node_id)
        if node is None:
            return
        if node.kind == 'function_entry':
            return
        if node.kind == 'custom_function':
            self._open_custom_function_dialog(node_id)
            return
        if self._is_system_node(node):
            return
        if self._overlay_host_el is None:
            return
        draft_node = self._clone_editor_node(node)
        with self._overlay_host_el:
            dlg = ui.dialog()
            with dlg, ui.card().classes('ach-node-editor-card gap-0').style(
                'background:#000000; border:1px solid #2f3336;'
                ' border-radius:12px; padding:20px; min-width:420px;'
                ' max-width:560px; width:min(560px, calc(100vw - 48px));'
                ' max-height:90vh; display:flex; flex-direction:column;'
                ' overflow:hidden;'
            ):
                with ui.column().classes('w-full gap-0 ach-node-editor-scroll'):

                    @ui.refreshable
                    def _render_editor() -> None:
                        live_node = self._node_by_id(node_id)
                        if live_node is None:
                            ui.label('Node no longer exists.').classes(
                                'text-xs oe-muted'
                            )
                            return
                        ui.label(
                            f'Edit {draft_node.title or _template_title(draft_node.kind)}'
                        ).classes('text-base font-bold oe-text')
                        with ui.column().classes('w-full ach-node-editor-fields pt-2'):
                            self._render_node_config_fields(
                                draft_node,
                                refresh_editor=_render_editor.refresh,
                            )

                    _render_editor()
                with ui.row().classes('justify-end gap-2 w-full pt-3 shrink-0'):
                    ui.button('Close', on_click=dlg.close).props('flat')

                    def _save() -> None:
                        if self._commit_editor_node(node_id, draft_node):
                            dlg.close()

                    ui.button('Save', on_click=_save).classes('oe-btn-primary')
        dlg.open()

    def _render_node_config_fields(
        self: Any,
        node: AcherionNode,
        refresh_editor: Callable[[], None] | None = None,
    ) -> None:
        def _apply_change(
            change: Callable[[], None],
            *,
            refresh_after: bool = False,
        ) -> None:
            self._apply_editor_change(
                change,
                refresh_editor,
                refresh_editor_after=refresh_after,
            )

        if self._is_system_sink_node(node):
            if self._host is not None and bool(
                self._host.render_system_sink_config_fields(
                    self,
                    node,
                    refresh_editor=refresh_editor,
                    apply_change=_apply_change,
                )
            ):
                return
            return

        ui.input(
            'Node title',
            value=node.title,
            on_change=lambda e, cur=node: _apply_change(
                lambda: self._set_editor_title(cur, e.value),
            ),
        ).props('outlined dense').classes('w-full ach-editor-field')

        definition = get_acherion_node_definition(node.kind)
        if definition is not None and definition.render_config_fields(
            self,
            node,
            refresh_editor=refresh_editor,
            apply_change=_apply_change,
        ):
            return

        if node.kind == 'function_box':
            ui.input(
                'Python function name',
                value=str(node.params.get('function_name') or ''),
                on_change=lambda e, cur=node: _apply_change(
                    lambda: self._set_editor_param(
                        cur,
                        'function_name',
                        str(e.value or ''),
                    ),
                ),
            ).props('outlined dense').classes('w-full ach-editor-field')
            ui.label(
                (
                    f'{len(self._function_box_boundary_input_sources(node.node_id))} '
                    'inferred inputs - '
                    f'{len(self._function_box_boundary_output_sources(node.node_id))} '
                    'inferred outputs'
                )
            ).classes('text-xs oe-muted')
            ui.label(
                'Connect outside nodes directly to nodes inside the box. '
                'External-to-inner wires become function parameters, and '
                'inner-to-external wires become function outputs.'
            ).classes('text-xs oe-muted')
            ui.label(
                'Execution inside the box starts only from the compact entry '
                'pin beside exec-in. Disconnected exec chains do not run.'
            ).classes('text-xs oe-muted')
            return

        if self._host is not None and bool(
            self._host.render_node_config_fields(
                self,
                node,
                refresh_editor=refresh_editor,
                apply_change=_apply_change,
            )
        ):
            return

        if node.kind == 'constant':
            value_type = str(node.params.get('value_type') or 'number')
            ui.select(
                {
                    'number': 'Number',
                    'int': 'Integer',
                    'bool': 'Boolean',
                    'text': 'Text',
                    'dict': 'Dict',
                },
                label='Value type',
                value=value_type,
                on_change=lambda e, cur=node: _apply_change(
                    lambda: self._set_editor_param(
                        cur,
                        'value_type',
                        str(e.value or 'number'),
                    ),
                    refresh_after=True,
                ),
            ).props('outlined dense').classes('w-full ach-editor-field')
            if value_type == 'text':
                ui.input(
                    'Text value',
                    value=str(node.params.get('text_value') or ''),
                    on_change=lambda e, cur=node: _apply_change(
                        lambda: self._set_editor_param(
                            cur,
                            'text_value',
                            str(e.value or ''),
                        ),
                    ),
                ).props('outlined').classes('w-full ach-editor-field')
            elif value_type == 'bool':
                ui.checkbox(
                    'Boolean value',
                    value=bool(node.params.get('bool_value', False)),
                    on_change=lambda e, cur=node: _apply_change(
                        lambda: self._set_editor_param(
                            cur,
                            'bool_value',
                            bool(e.value),
                        ),
                    ),
                )
            elif value_type == 'int':
                ui.number(
                    'Integer value',
                    value=int(node.params.get('number_value') or 0),
                    format='%d',
                    on_change=lambda e, cur=node: _apply_change(
                        lambda: self._set_editor_param(
                            cur,
                            'number_value',
                            e.value,
                        ),
                    ),
                ).props('outlined step=1').classes('w-full ach-editor-field')
            elif value_type == 'dict':
                ui.input(
                    'Dict literal',
                    value=str(node.params.get('dict_value') or '{}'),
                    validation={
                        'Must be a Python dict literal': self._valid_dict_literal,
                    },
                    on_change=lambda e, cur=node: _apply_change(
                        lambda: self._set_editor_param(
                            cur,
                            'dict_value',
                            str(e.value or '{}'),
                        ),
                    ),
                ).props('outlined').classes('w-full ach-editor-field')
                ui.label('Enter a Python dict literal, e.g. {"key": 1}').classes(
                    'text-xs oe-muted'
                )
            else:
                ui.number(
                    'Number value',
                    value=float(node.params.get('number_value') or 0.0),
                    on_change=lambda e, cur=node: _apply_change(
                        lambda: self._set_editor_param(
                            cur,
                            'number_value',
                            e.value,
                        ),
                    ),
                ).props('outlined').classes('w-full ach-editor-field')
            return

        if node.kind == 'call_function':
            current_path = str(node.params.get('function_path') or '')
            current_module = str(node.params.get('module') or '')
            module_options = self._function_module_options()
            if not current_module and current_path:
                current_module = self._function_path_to_module(current_path)
            if current_module not in module_options:
                current_module = ''
            ui.select(
                module_options,
                label='Module',
                value=current_module or None,
                on_change=lambda e, cur=node: _apply_change(
                    lambda: self._set_editor_catalog_module(
                        cur,
                        str(e.value or ''),
                    ),
                    refresh_after=True,
                ),
            ).props('outlined dense').classes('w-full ach-editor-field')
            if current_module:
                opts = self._function_options(current_module)
                ui.select(
                    opts,
                    label='Callable',
                    value=current_path if current_path in opts else None,
                    with_input=True,
                    on_change=lambda e, cur=node: _apply_change(
                        lambda: self._set_editor_catalog_function(
                            cur,
                            str(e.value or ''),
                        ),
                        refresh_after=True,
                    ),
                ).props('outlined dense').classes('w-full ach-editor-field')
            entry = self._function_entry(current_path)
            if entry:
                optional_count = (
                    (entry.max_args - entry.min_args)
                    if entry.max_args is not None
                    else None
                )
                if optional_count is None:
                    opt_label = ' + unlimited optional'
                elif optional_count > 0:
                    opt_label = f' + {optional_count} optional'
                else:
                    opt_label = ''
                role_label = (
                    f'constructs object ({entry.min_args} required{opt_label})'
                    if entry.is_class
                    else f'{entry.min_args} required{opt_label}'
                )
                ui.label(f'{entry.signature}  ({role_label})').classes(
                    'text-xs oe-muted font-mono'
                )
            return

        if node.kind == 'call_method':
            instance_source = self._input_source_id(node, 'instance')
            class_path = self._resolve_instance_class_path(instance_source)
            method_name = str(node.params.get('method_name') or '')
            if class_path:
                opts = _catalog_runtime.class_methods(class_path)
                ui.select(
                    opts,
                    label='Method',
                    value=method_name if method_name in opts else None,
                    with_input=True,
                    on_change=lambda e, cur=node, cp=class_path: _apply_change(
                        lambda: self._set_editor_method_name(
                            cur,
                            str(e.value or ''),
                            cp,
                        ),
                        refresh_after=True,
                    ),
                ).props('outlined').classes('w-full ach-editor-field')
                if method_name:
                    entry = _catalog_runtime.method_func_entry(class_path, method_name)
                    if entry:
                        optional_count = (
                            (entry.max_args - entry.min_args)
                            if entry.max_args is not None
                            else None
                        )
                        if optional_count is None:
                            opt_label = ' + unlimited optional'
                        elif optional_count > 0:
                            opt_label = f' + {optional_count} optional'
                        else:
                            opt_label = ''
                        ui.label(
                            f'{entry.signature}  ({entry.min_args} required{opt_label})'
                        ).classes('text-xs oe-muted font-mono')
            else:
                ui.label(
                    'Connect instance pin to enable method selection.'
                ).classes('text-xs oe-muted')
                if method_name:
                    ui.label(method_name).classes('text-xs oe-muted font-mono')
            return

        if node.kind in {'get_attribute', 'set_attribute'}:
            instance_source = self._input_source_id(node, 'instance')
            class_path = self._resolve_instance_class_path(instance_source)
            attr_name = str(node.params.get('attribute_name') or '')
            if class_path:
                opts = _catalog_runtime.class_attributes(class_path)
                ui.select(
                    opts,
                    label='Attribute',
                    value=attr_name if attr_name in opts else None,
                    with_input=True,
                    on_change=lambda e, cur=node: _apply_change(
                        lambda: self._set_editor_param(
                            cur,
                            'attribute_name',
                            str(e.value or ''),
                        ),
                    ),
                ).props('outlined').classes('w-full ach-editor-field')
            else:
                ui.label(
                    'Connect instance pin to enable attribute selection.'
                ).classes('text-xs oe-muted')
                if attr_name:
                    ui.label(attr_name).classes('text-xs oe-muted font-mono')
            return

        if node.kind == 'for_each':
            ui.label(
                'Connect list pin. Downstream nodes wired to item/index form '
                'the loop body.'
            ).classes('text-xs oe-muted')
            return

        if node.kind == 'collect':
            ui.label(
                'Appends value each iteration. Output list is available after '
                'the loop.'
            ).classes('text-xs oe-muted')
            return

        if node.kind == 'compare':
            ui.select(
                {'>': '>', '>=': '>=', '<': '<', '<=': '<=', '==': '==', '!=': '!='},
                label='Operator',
                value=str(node.params.get('operator') or '>'),
                on_change=lambda e, cur=node: _apply_change(
                    lambda: self._set_editor_param(
                        cur,
                        'operator',
                        str(e.value or '>'),
                    ),
                ),
            ).props('outlined dense').classes('w-full ach-editor-field')
            return

        if node.kind == 'branch_value':
            ui.label(
                'Outputs the If True value when condition is truthy, else If '
                'False.'
            ).classes('text-xs oe-muted')
            return

        if node.kind == 'branch_route':
            ui.label(
                'If True output = True when condition is truthy. If False = '
                'True when falsy.'
            ).classes('text-xs oe-muted')
            return

        if node.kind == 'op_arithmetic':
            ui.select(
                {
                    '+': 'Add (+)',
                    '-': 'Subtract (-)',
                    '*': 'Multiply (*)',
                    '/': 'Divide (/)',
                    '//': 'Floor div (//)',
                    '%': 'Modulo (%)',
                    '**': 'Power (**)',
                },
                label='Operator',
                value=str(node.params.get('operator') or '+'),
                on_change=lambda e, cur=node: _apply_change(
                    lambda: self._set_editor_param(
                        cur,
                        'operator',
                        str(e.value or '+'),
                    ),
                ),
            ).props('outlined dense').classes('w-full ach-editor-field')
            return

        if node.kind == 'op_unary':
            ui.select(
                {
                    'abs': 'abs(x)',
                    'negate': '-x (negate)',
                    'round': 'round(x)',
                    'int': 'int(x)',
                    'float': 'float(x)',
                    'bool': 'bool(x)',
                    'math.ceil': 'math.ceil(x)',
                    'math.floor': 'math.floor(x)',
                    'math.sqrt': 'math.sqrt(x)',
                    'math.log': 'math.log(x)',
                    'math.exp': 'math.exp(x)',
                },
                label='Function',
                value=str(node.params.get('function') or 'abs'),
                on_change=lambda e, cur=node: _apply_change(
                    lambda: self._set_editor_param(
                        cur,
                        'function',
                        str(e.value or 'abs'),
                    ),
                ),
            ).props('outlined dense').classes('w-full ach-editor-field')
            return

        if node.kind == 'op_logic':
            ui.select(
                {'and': 'AND', 'or': 'OR'},
                label='Operator',
                value=str(node.params.get('operator') or 'and'),
                on_change=lambda e, cur=node: _apply_change(
                    lambda: self._set_editor_param(
                        cur,
                        'operator',
                        str(e.value or 'and'),
                    ),
                ),
            ).props('outlined dense').classes('w-full ach-editor-field')
            return

        if node.kind == 'op_not':
            ui.label('Outputs not bool(value).').classes('text-xs oe-muted')
            return

        if node.kind == 'make_list':
            ui.number(
                label='Item count',
                value=int(node.params.get('arg_count', 0) or 0),
                min=0,
                step=1,
                format='%d',
                on_change=lambda e, cur=node: _apply_change(
                    lambda: self._set_editor_arg_count(cur, e.value),
                ),
            ).props('outlined dense').classes('w-full ach-editor-field')
            return

        if node.kind == 'make_dict':
            entry_count = int(node.params.get('arg_count', 0) or 0)
            ui.number(
                label='Entry count',
                value=entry_count,
                min=0,
                step=1,
                format='%d',
                on_change=lambda e, cur=node: _apply_change(
                    lambda: self._set_editor_arg_count(cur, e.value),
                    refresh_after=True,
                ),
            ).props('outlined dense').classes('w-full ach-editor-field')
            if entry_count <= 0:
                ui.label(
                    'Increase entry count to add key/value pairs.'
                ).classes('text-xs oe-muted')
                return
            ui.label(
                'Each key names the matching input pin in the output dict.'
            ).classes('text-xs oe-muted')
            key_names = list(node.params.get('key_names') or [])
            for index in range(entry_count):
                default_key = self._default_make_dict_key_name(index)
                current_key = str(
                    key_names[index] if index < len(key_names) else default_key
                ).strip() or default_key
                ui.input(
                    f'Key {index + 1}',
                    value=current_key,
                    on_change=lambda e, cur=node, idx=index: _apply_change(
                        lambda: self._set_editor_make_dict_key(
                            cur,
                            idx,
                            e.value,
                        ),
                    ),
                ).props('outlined dense').classes('w-full ach-editor-field')
            ui.label(
                'Duplicate keys follow normal Python dict rules; later entries win.'
            ).classes('text-xs oe-muted')
            return

        if node.kind == 'sequencer':
            ui.number(
                label='Step count',
                value=int(node.params.get('then_count', 2) or 2),
                min=2,
                max=8,
                step=1,
                format='%d',
                on_change=lambda e, cur=node: _apply_change(
                    lambda: self._set_editor_then_count(cur, e.value),
                    refresh_after=True,
                ),
            ).props('outlined dense').classes(
                'w-full ach-editor-field'
            )
            ui.label(
                'Each Then output runs in order. Every exec output accepts one downstream path.'
            ).classes('text-xs oe-muted')
            return

        if node.kind in {'list_index', 'list_set'}:
            mode = str(node.params.get('mode') or 'index').strip()
            node_label = (
                'Get List Value(s)'
                if node.kind == 'list_index'
                else 'Set List Value(s)'
            )

            def _bound_display(key: str) -> str:
                raw_value = node.params.get(key)
                if raw_value in (None, ''):
                    return ''
                text: str = str(raw_value).strip()
                if not text:
                    return ''
                try:
                    return str(int(text))
                except (TypeError, ValueError):
                    return ''

            def _set_bound(key: str, raw_value: Any) -> None:
                text: str = str(raw_value or '').strip()
                if not text:
                    self._set_editor_param(node, key, '')
                    return
                try:
                    parsed = int(text)
                except (TypeError, ValueError):
                    return
                if key == 'step' and parsed == 0:
                    self._set_editor_param(node, key, '')
                    return
                self._set_editor_param(node, key, parsed)

            ui.select(
                {'index': 'Single index', 'slice': 'Slice / step'},
                label='Mode',
                value=mode,
                on_change=lambda e, cur=node: _apply_change(
                    lambda: self._set_editor_param(
                        cur,
                        'mode',
                        str(e.value or 'index'),
                    ),
                    refresh_after=True,
                ),
            ).props('outlined dense').classes('w-full ach-editor-field')
            if mode == 'slice':
                ui.input(
                    'Start (optional)',
                    value=_bound_display('start'),
                    on_change=lambda e, key='start': _apply_change(
                        lambda: _set_bound(key, e.value),
                    ),
                ).props('outlined dense type=number').classes('w-full ach-editor-field')
                ui.input(
                    'Stop (optional)',
                    value=_bound_display('stop'),
                    on_change=lambda e, key='stop': _apply_change(
                        lambda: _set_bound(key, e.value),
                    ),
                ).props('outlined dense type=number').classes('w-full ach-editor-field')
                ui.input(
                    'Step (optional, non-zero)',
                    value=_bound_display('step'),
                    on_change=lambda e, key='step': _apply_change(
                        lambda: _set_bound(key, e.value),
                    ),
                ).props('outlined dense type=number').classes('w-full ach-editor-field')
                ui.label(
                    (
                        'Uses Python slice semantics: '
                        'source[start:stop:step].'
                        if node.kind == 'list_index'
                        else 'Uses Python slice assignment semantics: '
                        'result[start:stop:step] = value. Connect an '
                        'iterable replacement when updating list slices.'
                    )
                ).classes('text-xs oe-muted')
            else:
                ui.number(
                    'Index (0-based)',
                    value=int(node.params.get('index', 0) or 0),
                    format='%d',
                    on_change=lambda e, cur=node: _apply_change(
                        lambda: self._set_editor_param(
                            cur,
                            'index',
                            int(e.value or 0),
                        ),
                    ),
                ).props('outlined dense step=1').classes('w-full ach-editor-field')
                if node.kind == 'list_set':
                    ui.label(
                        'Returns a copied list or ndarray with one item updated.'
                    ).classes('text-xs oe-muted')
            ui.label(
                f'{node_label} works with lists and ndarrays.'
            ).classes('text-xs oe-muted')
            return

        if node.kind == 'plot_figure':
            figure_type = str(node.params.get('figure_type') or 'scatter')
            ui.select(
                _catalog_plotly.trace_options(),
                label='Trace type',
                value=figure_type,
                on_change=lambda e, cur=node: _apply_change(
                    lambda: self._set_editor_param(
                        cur,
                        'figure_type',
                        str(e.value or 'scatter'),
                    ),
                    refresh_after=True,
                ),
            ).props('outlined dense').classes('w-full ach-editor-field')
            te = _catalog_plotly.trace_entry(figure_type)
            if te:
                ui.label(f'{te.go_class}(...)').classes(
                    'text-xs oe-accent-blue font-mono'
                )
            ui.input(
                'Figure title (optional)',
                value=str(node.params.get('figure_title') or ''),
                on_change=lambda e, cur=node: _apply_change(
                    lambda: self._set_editor_param(
                        cur,
                        'figure_title',
                        str(e.value or ''),
                    ),
                ),
            ).props('outlined').classes('w-full ach-editor-field')
            return

