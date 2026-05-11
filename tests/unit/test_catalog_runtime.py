"""Unit tests for catalog and runtime lookup helpers."""

from __future__ import annotations

import pytest

import acherion.catalog.models as acherion_catalog_models
import acherion.catalog.modules as acherion_catalog_modules
import acherion.catalog.runtime as acherion_catalog_runtime
import acherion.catalog.types as acherion_catalog_types
import acherion.model as acherion_model
import plotly.graph_objects as go

import tests.helpers as test_helpers


pytestmark = pytest.mark.unit


def test_function_catalog_includes_numpy_and_plotly_modules() -> None:
    module_options = acherion_catalog_modules.module_options()

    assert module_options['np'] == 'numpy (np)'
    assert module_options['go'] == 'plotly.graph_objects (go)'
    assert module_options['px'] == 'plotly.express (px)'
    assert module_options['plotly.subplots'] == 'plotly.subplots'

    np_options = acherion_catalog_runtime.func_options('np')
    go_options = acherion_catalog_runtime.func_options('go')
    px_options = acherion_catalog_runtime.func_options('px')
    subplot_options = acherion_catalog_runtime.func_options('plotly.subplots')

    assert 'np.array' in np_options
    assert 'go.Figure' in go_options
    assert 'px.scatter' in px_options
    assert 'plotly.subplots.make_subplots' in subplot_options


def test_list_outputs_resolve_builtin_list_methods_for_call_method() -> None:
    owner = test_helpers.CatalogPinsOwner()
    list_node = acherion_model.AcherionNode(
        node_id='list1',
        kind='make_list',
        params={'arg_count': 2, 'arg_sources': ['', '']},
    )
    owner._graph.nodes.append(list_node)

    assert owner._resolve_instance_class_path('list1') == 'list'
    methods = acherion_catalog_runtime.class_methods('list')
    assert 'append' in methods
    assert methods['append'].startswith('append(')


def test_for_each_items_resolve_class_path_from_typed_list_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fake_catalog_entry(
        path: str,
    ) -> acherion_catalog_models.FuncEntry | None:
        if path == 'pkg.make_widgets':
            return acherion_catalog_models.FuncEntry(
                path='pkg.make_widgets',
                label='make_widgets',
                signature='pkg.make_widgets()',
                min_args=0,
                max_args=0,
                param_names=(),
                param_types=(),
                return_type='list[pkg.Widget]',
                is_class=False,
            )
        if path == 'pkg.Widget':
            return acherion_catalog_models.FuncEntry(
                path='pkg.Widget',
                label='Widget',
                signature='pkg.Widget()',
                min_args=0,
                max_args=0,
                param_names=(),
                param_types=(),
                return_type='pkg.Widget',
                is_class=True,
            )
        return None

    monkeypatch.setattr(
        acherion_catalog_runtime,
        'catalog_entry',
        _fake_catalog_entry,
    )

    owner = test_helpers.CatalogPinsOwner(
        acherion_model.AcherionGraph(
            nodes=[
                acherion_model.AcherionNode(
                    node_id='widgets',
                    kind='call_function',
                    params={
                        'function_path': 'pkg.make_widgets',
                        'module': 'pkg',
                        'arg_count': 0,
                        'arg_sources': [],
                    },
                ),
                acherion_model.AcherionNode(
                    node_id='loop',
                    kind='for_each',
                    params={'list': 'widgets'},
                ),
            ]
        )
    )

    assert owner._resolve_instance_class_path('loop@0') == 'pkg.Widget'
    assert owner._output_pin_specs(owner._graph.nodes[1])[0]['type'] == (
        'pkg.Widget'
    )


def test_runtime_lookup_accepts_direct_dotted_class_paths() -> None:
    figure = go.Figure()
    class_path = f'{type(figure).__module__}.{type(figure).__name__}'

    methods = acherion_catalog_runtime.class_methods(class_path)
    attrs = acherion_catalog_runtime.class_attributes(class_path)

    assert 'update_layout' in methods
    assert 'layout' in attrs


def test_tuple_type_inference_only_specializes_homogeneous_members() -> None:
    assert acherion_catalog_types.annotation_to_tag(tuple[int, int]) == (
        'list[int]'
    )
    assert acherion_catalog_types.annotation_to_tag(tuple[int, str]) == 'list'


def test_for_each_item_type_avoids_self_recursive_source_lookup() -> None:
    owner = test_helpers.CatalogPinsOwner(
        acherion_model.AcherionGraph(
            nodes=[
                acherion_model.AcherionNode(
                    node_id='loop',
                    kind='for_each',
                    params={'list': 'loop@0'},
                ),
            ]
        )
    )

    assert owner._output_pin_specs(owner._graph.nodes[0])[0]['type'] == 'any'


def test_class_attributes_include_declared_fields_without_instantiation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _SyntheticRecord:
        __annotations__ = {
            'title': str,
            '_private_title': str,
        }
        __slots__ = ('title', 'count', '_private_count')

        def __init__(self, title: str, count: int) -> None:
            self.title = title
            self.count = count

        @property
        def summary(self) -> str:
            return f'{self.title}:{self.count}'

        def method(self) -> str:
            return self.summary

    acherion_catalog_runtime.class_attributes.cache_clear()
    monkeypatch.setattr(
        acherion_catalog_runtime,
        '_class_object',
        lambda _class_path: _SyntheticRecord,
    )
    monkeypatch.setattr(
        acherion_catalog_runtime._catalog_modules,
        'path_to_module',
        lambda _class_path: 'user',
    )

    attrs = acherion_catalog_runtime.class_attributes('user.SyntheticRecord')

    assert 'title' in attrs
    assert 'count' in attrs
    assert 'summary' in attrs
    assert 'method' not in attrs
    assert '_private_title' not in attrs
    assert '_private_count' not in attrs


def test_clear_catalog_runtime_caches_resets_attribute_and_method_lookups(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FirstRecord:
        @property
        def alpha(self) -> int:
            return 1

        def ping(self) -> int:
            return 1

    class _SecondRecord:
        @property
        def beta(self) -> int:
            return 2

        def pong(self) -> int:
            return 2

    current_cls = {'value': _FirstRecord}

    acherion_catalog_runtime.class_attributes.cache_clear()
    acherion_catalog_runtime.class_methods.cache_clear()
    acherion_catalog_runtime.method_func_entry.cache_clear()
    monkeypatch.setattr(
        acherion_catalog_runtime,
        '_class_object',
        lambda _class_path: current_cls['value'],
    )

    first_attrs = acherion_catalog_runtime.class_attributes('user.Record')
    first_method = acherion_catalog_runtime.method_func_entry(
        'user.Record',
        'ping',
    )

    assert 'alpha' in first_attrs
    assert first_method is not None
    assert first_method.signature.startswith('user.Record.ping(')

    current_cls['value'] = _SecondRecord
    acherion_catalog_runtime.clear_catalog_runtime_caches()

    second_attrs = acherion_catalog_runtime.class_attributes('user.Record')
    second_method = acherion_catalog_runtime.method_func_entry(
        'user.Record',
        'pong',
    )

    assert 'beta' in second_attrs
    assert 'alpha' not in second_attrs
    assert second_method is not None
    assert second_method.signature.startswith('user.Record.pong(')