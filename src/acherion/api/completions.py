"""Generic Python completion endpoints for standalone Acherion."""

# pyright: reportMissingTypeStubs=false

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

import jedi  # pyright: ignore[reportMissingTypeStubs]
from fastapi import Request
from nicegui import app

logger = logging.getLogger(__name__)

_JEDI_PREFIX = """\
import collections
import logging
import pathlib
import re
import typing

logger = logging.getLogger(__name__)
"""

_PREFIX_LINES: int = len(_JEDI_PREFIX.splitlines())
_CLASS_SEP = "# --- class methods ---"
_JEDI_PROJECT = jedi.Project(path=str(Path(__file__).parent.parent.parent))


def _build_jedi_context(code: str, row: int, col: int) -> tuple[str, int, int]:
    """Wrap editor code in a synthetic Jedi document."""
    normalized_code = str(code or '').replace(_CLASS_SEP, '').strip('\n')
    if not normalized_code.strip():
        normalized_code = 'pass'
    full_code = _JEDI_PREFIX + normalized_code
    jedi_row = _PREFIX_LINES + row + 1
    jedi_col = col
    return full_code, jedi_row, jedi_col


def _parse_body(body: Any) -> tuple[str, int, int] | None:
    """Extract code, row, and column from a request body."""
    if not isinstance(body, dict):
        return None
    try:
        code = str(body.get('code', ''))
        row = max(0, int(body.get('row', 0)))
        col = max(0, int(body.get('col', 0)))
    except (TypeError, ValueError):
        return None
    return code, row, col


@app.post('/api/py-completions')
async def py_completions(request: Request) -> dict[str, Any]:
    """Return Jedi completions for the current editor cursor position."""
    try:
        params = _parse_body(await request.json())
    except Exception:  # Top-level request boundary.
        return {'completions': []}
    if params is None:
        return {'completions': []}
    code, row, col = params
    full_code, jedi_row, jedi_col = _build_jedi_context(code, row, col)

    def _run() -> list[dict[str, str]]:
        script = jedi.Script(full_code, project=_JEDI_PROJECT)
        raw = script.complete(jedi_row, jedi_col)
        return [
            {
                'name': completion.name,
                'type': completion.type or 'variable',
                'description': (
                    completion.description or ''
                ).split('\n')[0][:120],
            }
            for completion in raw[:80]
            if completion.name and not completion.name.startswith('_')
        ]

    try:
        loop = asyncio.get_running_loop()
        return {'completions': await loop.run_in_executor(None, _run)}
    except Exception:  # Top-level execution boundary.
        logger.exception('Jedi completion failed')
        return {'completions': []}


@app.post('/api/py-hover')
async def py_hover(request: Request) -> dict[str, Any]:
    """Return hover documentation for the symbol at the cursor."""
    try:
        params = _parse_body(await request.json())
    except Exception:  # Top-level request boundary.
        return {'docs': ''}
    if params is None:
        return {'docs': ''}
    code, row, col = params
    full_code, jedi_row, jedi_col = _build_jedi_context(code, row, col)

    def _run() -> str:
        script = jedi.Script(full_code, project=_JEDI_PROJECT)
        results = script.help(jedi_row, jedi_col)
        if not results:
            results = script.infer(jedi_row, jedi_col)
        if not results:
            return ''
        result = results[0]
        parts: list[str] = []
        description = getattr(result, 'description', None) or ''
        if description:
            parts.append(description)
        doc_fn = getattr(result, 'docstring', None)
        if callable(doc_fn):
            doc_result = doc_fn()
            doc = doc_result if isinstance(doc_result, str) else str(doc_result or '')
            if doc:
                trimmed = doc[:900]
                if len(doc) > 900:
                    trimmed += '\n...'
                parts.append(trimmed)
        return '\n\n'.join(parts)

    try:
        loop = asyncio.get_running_loop()
        return {'docs': await loop.run_in_executor(None, _run)}
    except Exception:  # Top-level execution boundary.
        logger.exception('Jedi hover failed')
        return {'docs': ''}


@app.post('/api/py-signatures')
async def py_signatures(request: Request) -> dict[str, Any]:
    """Return function signature help for the current cursor position."""
    try:
        params = _parse_body(await request.json())
    except Exception:  # Top-level request boundary.
        return {'signatures': []}
    if params is None:
        return {'signatures': []}
    code, row, col = params
    full_code, jedi_row, jedi_col = _build_jedi_context(code, row, col)

    def _run() -> list[dict[str, Any]]:
        script = jedi.Script(full_code, project=_JEDI_PROJECT)
        signatures = script.get_signatures(jedi_row, jedi_col)
        result: list[dict[str, Any]] = []
        for signature in signatures[:3]:
            param_labels = [parameter.description for parameter in signature.params]
            result.append({
                'label': signature.name + '(' + ', '.join(param_labels) + ')',
                'name': signature.name,
                'params': param_labels,
                'active': signature.index if signature.index is not None else -1,
            })
        return result

    try:
        loop = asyncio.get_running_loop()
        return {'signatures': await loop.run_in_executor(None, _run)}
    except Exception:  # Top-level execution boundary.
        logger.exception('Jedi signatures failed')
        return {'signatures': []}
