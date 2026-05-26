"""Atomic schedule visitor."""

from __future__ import annotations

from ...ast_types import ScheduleNode
from ...references import ReferenceCollector
from ...style import Style
from ...vocabulary import format_atomic_abbrev, format_atomic_full
from ._common import decorate_leaf


def visit_atomic(
    node: ScheduleNode, *, style: Style,
    refs: ReferenceCollector | None = None, first_mention: bool = True,
) -> str:
    dist = node.get("dist")
    # Defensive fallback: some conformance fixtures encode EXT/CRF as
    # Atomic with dist=EXT/CRF (rather than Special{kind=...}). Route
    # these through the Special framing so the compiler never crashes
    # on a missing domain.
    if dist in ("EXT", "CRF"):
        kind = dist
        if kind == "EXT":
            base = style.framing_extinction
        else:
            base = style.framing_crf
        return decorate_leaf(base, node, style=style)

    name = (
        format_atomic_full(node, style)
        if first_mention
        else format_atomic_abbrev(node, style)
    )
    domain = node.get("domain")
    if refs is not None:
        if dist == "V":
            refs.cite("fleshler_hoffman_1962")
        if domain == "T" and dist in ("V", "F"):
            refs.cite_if_known("zeiler_1968")
        if dist == "R" and domain == "I":
            refs.cite_if_known("millenson_1963")
    base = style.framing_reinforced.format(schedule=name)
    return decorate_leaf(base, node, style=style)
