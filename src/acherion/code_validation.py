"""Generic AST helpers for Acherion code validation."""

from __future__ import annotations

import ast
import builtins as _builtins_mod
from collections import deque
from collections.abc import Sequence

PYTHON_BUILTINS: frozenset[str] = frozenset(dir(_builtins_mod)) | frozenset({
    '__name__',
    '__file__',
    '__doc__',
    '__package__',
    '__spec__',
    '__loader__',
    '__builtins__',
})


class CodeValidationSupport:
    """Composable support object for AST-based code validation."""

    def __init__(
        self,
        *,
        protected_names: frozenset[str],
        preimport_lines: Sequence[str] = (),
        python_builtins: frozenset[str] = PYTHON_BUILTINS,
    ) -> None:
        self.protected_names = frozenset(protected_names)
        self.preimport_lines = tuple(preimport_lines)
        self.python_builtins = frozenset(python_builtins)

    def validate_protected_name_writes(self, code: str) -> None:
        """Reject writes that shadow reserved pre-imported names."""
        if not code.strip():
            return
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return
        visitor = _ProtectedNameWriteVisitor(self.protected_names)
        visitor.visit(tree)
        if visitor.error is not None:
            raise ValueError(visitor.error)

    def build_validation_wrapper(
        self,
        source_code: str,
        *,
        register_test_id: str,
        register_display_name: str,
        class_name: str,
        class_body_lines: Sequence[str] = (),
        trailing_lines: Sequence[str] = (),
        register_category: str = 'Custom',
    ) -> tuple[str, int]:
        """Wrap source inside a lightweight TestBase scaffold."""
        lines_before_source = list(self.preimport_lines)
        if lines_before_source:
            lines_before_source.append('')
        lines_before_source.extend([
            (
                f'@register({register_test_id!r}, {register_display_name!r}, '
                f'category={register_category!r})'
            ),
            f'class {class_name}(TestBase):',
            *class_body_lines,
        ])
        indented_source = [
            f'    {line}' if line else ''
            for line in source_code.splitlines()
        ]
        wrapper_lines = [
            *lines_before_source,
            *indented_source,
            *trailing_lines,
        ]
        return ('\n'.join(wrapper_lines), len(lines_before_source))


def collect_target_names(
    targets: Sequence[ast.expr],
    names: set[str],
) -> None:
    """Recursively extract bound names from assignment target node(s)."""
    for target in targets:
        if isinstance(target, ast.Name):
            names.add(target.id)
        elif isinstance(target, (ast.Tuple, ast.List)):
            collect_target_names(list(target.elts), names)
        elif isinstance(target, ast.Starred):
            collect_target_names([target.value], names)


def collect_defined_names(node: ast.AST, names: set[str]) -> None:
    """Collect all names bound anywhere within a function-like body."""
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
            names.add(child.id)
        elif isinstance(child, ast.arg):
            names.add(child.arg)
        elif isinstance(child, ast.ExceptHandler) and child.name:
            names.add(child.name)
        elif isinstance(child, ast.Global):
            for name in child.names:
                names.add(name)
        elif isinstance(child, ast.Import):
            for alias in child.names:
                names.add(alias.asname or alias.name.split('.')[0])
        elif isinstance(child, ast.ImportFrom):
            for alias in child.names:
                if alias.name != '*':
                    names.add(alias.asname or alias.name)
        elif isinstance(child, ast.NamedExpr):
            collect_target_names([child.target], names)
        elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(child.name)
        elif isinstance(child, ast.ClassDef):
            names.add(child.name)


def walk_excluding_classes(root: ast.AST):
    """Walk an AST node without descending into nested class bodies."""
    queue: deque[ast.AST] = deque(ast.iter_child_nodes(root))
    while queue:
        child = queue.popleft()
        yield child
        if not isinstance(child, ast.ClassDef):
            queue.extend(ast.iter_child_nodes(child))


def find_undefined_load(
    root: ast.AST,
    defined_names: set[str] | frozenset[str],
    *,
    context_label: str,
    line_offset: int = 0,
) -> str | None:
    """Return an undefined-name error for one AST scope when present."""
    for node in walk_excluding_classes(root):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id not in defined_names:
                raw_line = getattr(node, 'lineno', 0)
                adj_line = max(1, raw_line - line_offset) if raw_line else '?'
                return (
                    f"Undefined name '{node.id}' in {context_label} "
                    f'(line {adj_line}).'
                )
    return None


def _target_root_name(node: ast.AST) -> str | None:
    """Return the root name bound or mutated by a target-like AST node."""
    current = node
    while True:
        if isinstance(current, ast.Name):
            return current.id
        if isinstance(current, ast.Attribute):
            current = current.value
            continue
        if isinstance(current, ast.Subscript):
            current = current.value
            continue
        if isinstance(current, ast.Starred):
            current = current.value
            continue
        return None


class _ProtectedNameWriteVisitor(ast.NodeVisitor):
    """AST visitor rejecting writes to reserved pre-imported names."""

    def __init__(self, protected_names: frozenset[str]) -> None:
        self._protected_names = protected_names
        self.error: str | None = None

    def _set_error(self, name: str, node: ast.AST, action: str) -> None:
        if self.error is not None:
            return
        line = getattr(node, 'lineno', 0) or '?'
        self.error = (
            f"Pre-imported name '{name}' is reserved and cannot be "
            f'{action} (line {line}).'
        )

    def _check_name(self, name: str | None, node: ast.AST, action: str) -> None:
        if name in self._protected_names:
            self._set_error(str(name), node, action)

    def _check_target(self, target: ast.AST, action: str) -> None:
        if self.error is not None:
            return
        if isinstance(target, ast.Name):
            self._check_name(target.id, target, action)
            return
        if isinstance(target, (ast.Tuple, ast.List)):
            for element in target.elts:
                self._check_target(element, action)
            return
        if isinstance(target, ast.Starred):
            self._check_target(target.value, action)
            return
        self._check_name(_target_root_name(target), target, action)

    def _check_arguments(self, args: ast.arguments) -> None:
        all_args = [
            *args.posonlyargs,
            *args.args,
            *args.kwonlyargs,
        ]
        if args.vararg is not None:
            all_args.append(args.vararg)
        if args.kwarg is not None:
            all_args.append(args.kwarg)
        for arg in all_args:
            self._check_name(arg.arg, arg, 'used as a parameter name')

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            self._check_target(target, 'reassigned')
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self._check_target(node.target, 'modified')
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._check_target(node.target, 'reassigned')
        self.generic_visit(node)

    def visit_Delete(self, node: ast.Delete) -> None:
        for target in node.targets:
            self._check_target(target, 'deleted')
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self._check_target(node.target, 'used as a loop variable')
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self._check_target(node.target, 'used as a loop variable')
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension) -> None:
        self._check_target(node.target, 'used as a loop variable')
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        for item in node.items:
            if item.optional_vars is not None:
                self._check_target(item.optional_vars, 'used as a context alias')
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        for item in node.items:
            if item.optional_vars is not None:
                self._check_target(item.optional_vars, 'used as a context alias')
        self.generic_visit(node)

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        self._check_target(node.target, 'reassigned')
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_name(node.name, node, 'redefined')
        self._check_arguments(node.args)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_name(node.name, node, 'redefined')
        self._check_arguments(node.args)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._check_name(node.name, node, 'redefined')
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            bound_name = alias.asname or alias.name.split('.')[0]
            self._check_name(bound_name, node, 'used as an import alias')

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            if alias.name == '*':
                continue
            bound_name = alias.asname or alias.name
            self._check_name(bound_name, node, 'used as an import alias')
