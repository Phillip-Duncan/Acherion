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