"""Unit tests for palette grouping and lightweight UI state."""

from __future__ import annotations

import asyncio

import pytest

import acherion.embed.designer.interactions as acherion_designer_interactions
import acherion.embed.designer.shell as acherion_designer_shell
import acherion.embed.render.nodes as acherion_render_nodes
import acherion.preferences as acherion_preferences
import acherion.registry as acherion_registry


pytestmark = pytest.mark.unit


def test_list_index_definition_keeps_index_and_slice_defaults() -> None:
    definition = acherion_registry.get_acherion_node_definition('list_index')

    assert definition is not None
    assert definition.default_params(node_id='idx1') == {
        'source': '',
        'mode': 'index',
        'index': 0,
        'start': '',
        'stop': '',
        'step': '',
    }


def test_clear_selection_shortcut_clears_selected_nodes() -> None:
    class _StubDesigner(acherion_designer_interactions._DesignerInteractionsMixin):
        def __init__(self) -> None:
            self._selected_node_ids = {'n1', 'n2'}
            self._selected_connection_id = None
            self.refresh_count = 0
            self.hint_updates = 0

        def refresh(self) -> None:
            self.refresh_count += 1

        def _update_hint(self) -> None:
            self.hint_updates += 1

    designer = _StubDesigner()

    class _Event:
        args = {'shortcut_id': 'clear_selection', 'key': 'Escape'}

    designer._handle_canvas_key(_Event())

    assert designer._selected_node_ids == set()
    assert designer.refresh_count == 1
    assert designer.hint_updates == 1


def test_copy_and_paste_shortcuts_use_graph_clipboard() -> None:
    class _StubDesigner(acherion_designer_interactions._DesignerInteractionsMixin):
        def __init__(self) -> None:
            self._selected_node_ids = {'n1'}
            self._selected_connection_id = None
            self.copy_calls = 0
            self.paste_calls = 0
            self.paste_anchor: tuple[int | None, int | None] | None = None
            self.notifications: list[tuple[str, str]] = []

        def _copy_selection_to_clipboard(self) -> tuple[bool, str]:
            self.copy_calls += 1
            return (True, 'Copied 1 node.')

        def _paste_copied_nodes(
            self,
            *,
            anchor_x: int | None = None,
            anchor_y: int | None = None,
        ) -> tuple[bool, str]:
            self.paste_calls += 1
            self.paste_anchor = (anchor_x, anchor_y)
            return (True, 'Pasted 1 node.')

        def _notify_ui(self, message: str, *, type: str = 'info') -> None:
            self.notifications.append((message, type))

    designer = _StubDesigner()

    class _CopyEvent:
        args = {'shortcut_id': 'copy_selection', 'key': 'c'}

    class _PasteEvent:
        args = {
            'shortcut_id': 'paste_selection',
            'key': 'v',
            'anchor_x': 420,
            'anchor_y': 240,
        }

    designer._handle_canvas_key(_CopyEvent())
    designer._handle_canvas_key(_PasteEvent())

    assert designer.copy_calls == 1
    assert designer.paste_calls == 1
    assert designer.paste_anchor == (420, 240)
    assert designer.notifications == [
        ('Copied 1 node.', 'positive'),
        ('Pasted 1 node.', 'positive'),
    ]


def test_selecting_node_refocuses_canvas_shortcuts() -> None:
    class _StubDesigner(acherion_designer_interactions._DesignerInteractionsMixin):
        def __init__(self) -> None:
            self._graph = type('Graph', (), {'nodes': [type('Node', (), {
                'node_id': 'n1',
                'params': {},
            })()]})()
            self._selected_node_ids: set[str] = set()
            self._selected_connection_id = None
            self.focus_calls = 0
            self.change_calls = 0

        def _node_by_id(self, node_id: str) -> Any:
            for node in self._graph.nodes:
                if node.node_id == node_id:
                    return node
            return None

        def _selection_ids_for_node(self, node: Any) -> set[str]:
            return {node.node_id}

        def _notify_change(self) -> None:
            self.change_calls += 1

        def _focus_canvas_shortcuts(self) -> None:
            self.focus_calls += 1

    designer = _StubDesigner()

    class _Event:
        args = {'node_id': 'n1', 'toggle': False}

    designer._toggle_node_selection(_Event())

    assert designer._selected_node_ids == {'n1'}
    assert designer.change_calls == 1
    assert designer.focus_calls == 1


def test_grouping_selection_refocuses_canvas_shortcuts() -> None:
    class _StubDesigner(acherion_designer_interactions._DesignerInteractionsMixin):
        def __init__(self) -> None:
            self._selected_node_ids = {'n1', 'n2'}
            self.focus_calls = 0
            self.dismiss_calls = 0
            self.group_calls: list[tuple[str, set[str]]] = []

        def _ctx_dismiss(self) -> None:
            self.dismiss_calls += 1

        def _add_nodes_to_group(self, name: str, node_ids: set[str]) -> None:
            self.group_calls.append((name, set(node_ids)))

        def _focus_canvas_shortcuts(self) -> None:
            self.focus_calls += 1

    designer = _StubDesigner()

    designer._ctx_add_to_group('Group 1')

    assert designer.dismiss_calls == 1
    assert designer.group_calls == [('Group 1', {'n1', 'n2'})]
    assert designer.focus_calls == 1


def test_creating_group_refocuses_canvas_shortcuts() -> None:
    class _StubDesigner(acherion_designer_interactions._DesignerInteractionsMixin):
        def __init__(self) -> None:
            self._selected_node_ids = {'n1', 'n2'}
            self.focus_calls = 0
            self.dismiss_calls = 0
            self.create_calls: list[tuple[str, set[str]]] = []
            self.notifications: list[tuple[str, str]] = []

        def _ctx_dismiss(self) -> None:
            self.dismiss_calls += 1

        def _next_default_group_name(self) -> str:
            return 'Group 1'

        def _create_group(self, name: str, node_ids: set[str]) -> None:
            self.create_calls.append((name, set(node_ids)))

        def _focus_canvas_shortcuts(self) -> None:
            self.focus_calls += 1

        def _notify_ui(self, message: str, *, type: str = 'info') -> None:
            self.notifications.append((message, type))

    designer = _StubDesigner()

    designer._open_new_group_dialog()

    assert designer.dismiss_calls == 1
    assert designer.create_calls == [('Group 1', {'n1', 'n2'})]
    assert designer.focus_calls == 1
    assert designer.notifications == [('Created group Group 1.', 'positive')]


def test_default_preferences_include_copy_and_paste_shortcuts() -> None:
    defaults = acherion_preferences.default_preferences_dict()

    assert defaults['keyboard_shortcuts']['copy_selection'] == 'Ctrl+C'
    assert defaults['keyboard_shortcuts']['paste_selection'] == 'Ctrl+V'


def test_menu_paste_uses_viewport_cursor_anchor() -> None:
    class _StubClient:
        async def run_javascript(
            self,
            _code: str,
            timeout: float = 0.0,
        ) -> dict[str, int]:
            assert timeout == 3.0
            return {'anchor_x': 420, 'anchor_y': 240}

    class _StubDesigner(acherion_designer_shell._DesignerShellMixin):
        def __init__(self) -> None:
            self._client = _StubClient()
            self._viewport_dom_id = 'ach-shell-test'
            self.paste_anchor: tuple[int | None, int | None] | None = None
            self.notifications: list[tuple[str, str]] = []

        def _paste_copied_nodes(
            self,
            *,
            anchor_x: int | None = None,
            anchor_y: int | None = None,
        ) -> tuple[bool, str]:
            self.paste_anchor = (anchor_x, anchor_y)
            return (True, 'Pasted 1 node.')

        def _notify_ui(self, message: str, *, type: str = 'info') -> None:
            self.notifications.append((message, type))

    designer = _StubDesigner()

    asyncio.run(designer._paste_current_selection())

    assert designer.paste_anchor == (420, 240)
    assert designer.notifications == [('Pasted 1 node.', 'positive')]


def test_palette_taxonomy_groups_like_nodes_together() -> None:
    sections = acherion_registry._palette_sections()
    section_map = {
        category: [item.kind for item in items]
        for category, items in sections
    }

    assert list(section_map) == [
        'math',
        'logic',
        'collections',
        'flow',
        'object',
        'composite',
        'visualization',
    ]
    assert section_map['math'] == [
        'op_arithmetic',
        'op_unary',
    ]
    assert section_map['logic'] == [
        'compare',
        'op_logic',
        'op_not',
    ]
    assert section_map['collections'] == [
        'constant',
        'make_list',
        'list_index',
        'list_set',
        'make_dict',
        'dict_get',
        'dict_set',
    ]
    assert section_map['object'] == [
        'call_function',
        'call_method',
        'get_attribute',
        'set_attribute',
    ]
    assert section_map['composite'] == [
        'custom_function',
        'function_box',
    ]
    assert section_map['visualization'] == ['plot_figure']
    assert acherion_registry._template_category_label('dict_get') == (
        'Collections'
    )
    assert acherion_registry._template_category_label('custom_function') == (
        'Functions'
    )
    assert acherion_registry._template_category_label('plot_figure') == (
        'Visualization'
    )


def test_palette_section_expansion_state_respects_search_override() -> None:
    class _StubNodes(acherion_render_nodes._RenderNodesMixin):
        def __init__(self) -> None:
            self._palette_query = ''
            self._palette_collapsed_categories: set[str] = set()

    owner = _StubNodes()

    assert owner._palette_section_expanded('collections') is True

    owner._toggle_palette_category('collections')

    assert owner._palette_section_expanded('collections') is False

    owner._palette_query = 'dict'

    assert owner._palette_section_expanded('collections') is True

    owner._palette_query = ''

    assert owner._palette_section_expanded('collections') is False