"""Unit tests for editor configuration controls."""

from __future__ import annotations

import pytest

import acherion.model as acherion_model
import acherion.embed.render.editor as acherion_render_editor

import tests.helpers as test_helpers


pytestmark = pytest.mark.unit


def test_make_dict_editor_arg_count_seeds_key_names() -> None:
    class _StubEditor(acherion_render_editor._RenderEditorMixin):
        pass

    editor = _StubEditor()
    node = acherion_model.AcherionNode(
        node_id='dict1',
        kind='make_dict',
        params={
            'arg_count': 0,
            'arg_sources': [],
            'key_names': [],
        },
    )

    editor._set_editor_arg_count(node, 2)
    editor._set_editor_make_dict_key(node, 1, 'beta')

    assert node.params['arg_count'] == 2
    assert node.params['arg_sources'] == ['', '']
    assert node.params['key_names'] == ['key_1', 'beta']


def test_constant_editor_only_renders_value_type_selector(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {
        'checkbox': 0,
        'input': 0,
        'number': 0,
        'select': 0,
    }

    class _StubUiElement:
        def props(self, _value: object) -> '_StubUiElement':
            return self

        def classes(self, _value: object) -> '_StubUiElement':
            return self

    class _StubEditor(acherion_render_editor._RenderEditorMixin):
        def __init__(self) -> None:
            self._host = None

        def _is_system_sink_node(
            self,
            _node: acherion_model.AcherionNode,
        ) -> bool:
            return False

    def _track_call(name: str):
        def _handler(*args: object, **kwargs: object) -> _StubUiElement:
            del args, kwargs
            calls[name] += 1
            return _StubUiElement()

        return _handler

    monkeypatch.setattr(
        acherion_render_editor,
        'get_acherion_node_definition',
        lambda _kind: None,
    )
    monkeypatch.setattr(
        acherion_render_editor.ui,
        'checkbox',
        _track_call('checkbox'),
    )
    monkeypatch.setattr(
        acherion_render_editor.ui,
        'input',
        _track_call('input'),
    )
    monkeypatch.setattr(
        acherion_render_editor.ui,
        'number',
        _track_call('number'),
    )
    monkeypatch.setattr(
        acherion_render_editor.ui,
        'select',
        _track_call('select'),
    )

    _StubEditor()._render_node_config_fields(
        acherion_model.AcherionNode(
            node_id='constant',
            kind='constant',
            params={
                'value_type': 'dict',
                'dict_value': "{'alpha': 1}",
            },
        )
    )

    assert calls == {
        'checkbox': 0,
        'input': 1,
        'number': 0,
        'select': 1,
    }


def test_make_list_editor_uses_numeric_number_bounds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call = test_helpers.capture_editor_number_call(
        monkeypatch,
        acherion_model.AcherionNode(
            node_id='list',
            kind='make_list',
            params={'arg_count': 3},
        ),
    )

    kwargs = call['kwargs']

    assert kwargs['min'] == 0
    assert isinstance(kwargs['min'], int)
    assert kwargs['step'] == 1
    assert isinstance(kwargs['step'], int)


def test_sequencer_editor_uses_numeric_number_bounds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call = test_helpers.capture_editor_number_call(
        monkeypatch,
        acherion_model.AcherionNode(
            node_id='seq',
            kind='sequencer',
            params={'then_count': 4},
        ),
    )

    kwargs = call['kwargs']

    assert kwargs['min'] == 2
    assert isinstance(kwargs['min'], int)
    assert kwargs['max'] == 8
    assert isinstance(kwargs['max'], int)
    assert kwargs['step'] == 1
    assert isinstance(kwargs['step'], int)


def test_else_if_branch_editor_uses_numeric_number_bounds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call = test_helpers.capture_editor_number_call(
        monkeypatch,
        acherion_model.AcherionNode(
            node_id='branch',
            kind='else_if_branch',
            params={'condition_count': 3},
        ),
    )

    kwargs = call['kwargs']

    assert kwargs['min'] == 1
    assert isinstance(kwargs['min'], int)
    assert 'max' not in kwargs
    assert kwargs['step'] == 1
    assert isinstance(kwargs['step'], int)


def test_else_if_branch_editor_prunes_removed_conditions() -> None:
    class _StubEditor(acherion_render_editor._RenderEditorMixin):
        pass

    editor = _StubEditor()
    node = acherion_model.AcherionNode(
        node_id='branch',
        kind='else_if_branch',
        params={
            'condition_count': 3,
            'condition:0': 'first',
            'condition:1': 'second',
            'condition:2': 'third',
            'condition:12': 'later',
        },
    )

    editor._set_editor_else_if_condition_count(node, 2)

    assert node.params['condition_count'] == 2
    assert node.params['condition:0'] == 'first'
    assert node.params['condition:1'] == 'second'
    assert 'condition:2' not in node.params
    assert 'condition:12' not in node.params


def test_else_if_branch_editor_allows_more_than_eight_conditions() -> None:
    class _StubEditor(acherion_render_editor._RenderEditorMixin):
        pass

    editor = _StubEditor()
    node = acherion_model.AcherionNode(
        node_id='branch',
        kind='else_if_branch',
        params={'condition_count': 2},
    )

    editor._set_editor_else_if_condition_count(node, 12)

    assert node.params['condition_count'] == 12
