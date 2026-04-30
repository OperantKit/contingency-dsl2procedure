"""Main compiler: JSON AST (dict) -> MethodSection.

Input is a plain dict conforming to contingency-dsl's schema.
No dependency on a specific parser; any parser that emits conformant
JSON can feed this compiler.

Accepted root node types:
    - Program (single-schedule design; most common case)
    - Experiment (label + body; body is Program or PhaseSequence)
    - Paper (experiments: list[Experiment])
    - PhaseSequence (bare multi-phase, no outer Experiment wrapper)

For Paper inputs, ``compile_method`` returns the *first* experiment's
Method section. ``compile_paper`` returns a list of (label, MethodSection).

Public API:
    compile_method(ast_dict, style="jeab") -> MethodSection
    compile_paper(ast_dict, style="jeab") -> list[tuple[str, MethodSection]]
"""

from __future__ import annotations

from .ast_types import ProgramNode, RootNode
from .model import MethodSection
from .references import Reference, ReferenceCollector
from .sections import render_apparatus, render_procedure, render_subjects
from .style import JEAB, Style, get_style


def compile_method(
    ast: RootNode | dict,
    *,
    style: Style | str = JEAB,
    extra_references: list[Reference] | None = None,
) -> MethodSection:
    """Compile a DSL AST dict into a Method section.

    Args:
        ast: A dict conforming to contingency-dsl's schema. Accepted root
             types: Program, Experiment, Paper, PhaseSequence.
        style: A Style object or a built-in style name ("jeab", "jaba").
        extra_references: Additional user-provided references to include.

    Returns:
        MethodSection with subjects, apparatus, procedure, and references.
    """
    if isinstance(style, str):
        style = get_style(style)

    program, extra_ps = _unwrap_root(ast)
    return _compile_single(
        program, extra_ps, style=style, extra_references=extra_references,
    )


def compile_paper(
    ast: dict,
    *,
    style: Style | str = JEAB,
    extra_references: list[Reference] | None = None,
) -> list[tuple[str, MethodSection]]:
    """Compile a Paper node to (label, MethodSection) tuples, one per Experiment.

    For non-Paper inputs, returns a single-element list with label=\"\".
    """
    if isinstance(style, str):
        style = get_style(style)
    if not isinstance(ast, dict):
        return []
    if ast.get("type") == "Paper":
        paper_shared = ast.get("shared_annotations", []) or []
        out: list[tuple[str, MethodSection]] = []
        for exp in ast.get("experiments", []) or []:
            label = exp.get("label", "")
            body = exp.get("body", {})
            program, extra_ps = _unwrap_root(body)
            # Merge Paper-level shared_annotations into each experiment so
            # that subject/apparatus info stated once at the top applies to
            # every experiment (experiment-level wins on keyword collision).
            if paper_shared and isinstance(program, dict):
                existing = list(program.get("program_annotations", []) or [])
                existing_kws = {
                    a.get("keyword") for a in existing if isinstance(a, dict)
                }
                merged = list(existing)
                for a in paper_shared:
                    if isinstance(a, dict) and a.get("keyword") not in existing_kws:
                        merged.append(a)
                program = {**program, "program_annotations": merged}
            method = _compile_single(
                program, extra_ps, style=style,
                extra_references=extra_references,
            )
            out.append((label, method))
        return out
    # Single-experiment fallback
    program, extra_ps = _unwrap_root(ast)
    method = _compile_single(
        program, extra_ps, style=style, extra_references=extra_references,
    )
    return [(ast.get("label", ""), method)]


# --- Helpers -----------------------------------------------------------------

_SCHEDULE_TYPES: frozenset[str] = frozenset({
    "Atomic", "Special", "Compound", "Modifier", "SecondOrder",
    "AversiveSchedule", "TrialBased", "IdentifierRef",
    "AnnotatedSchedule",
    "AdjustingSchedule", "InterlockingSchedule",
    "MTS",
    # Pre-expansion experiment-layer primitives handled as phase schedules
    "Shaping", "ProgressiveTraining", "PhaseRef",
    # Respondent primitives
    "PairForwardDelay", "PairForwardTrace", "PairSimultaneous", "PairBackward",
    "Extinction", "CSOnly", "USOnly", "Contingency", "TrulyRandom",
    "ExplicitlyUnpaired", "Serial", "ITI", "Differential",
    "ExtensionPrimitive",
})


def _unwrap_root(ast) -> tuple[ProgramNode, dict | None]:
    """Reduce any supported root shape to (ProgramNode, optional PhaseSequence).

    - Program         → (program, None)
    - Experiment      → unwrap(body) — Experiment-level label is ignored here.
    - PhaseSequence   → (synthesized program, phase_sequence)
    - Paper           → unwrap first experiment's body, merging Paper.shared
                        annotations into the program's program_annotations
                        (experiment-level annotations override).
    - Bare schedule   → (synthesized Program wrapping the schedule, None)
    - Anything else   → ({}, None)
    """
    if not isinstance(ast, dict):
        return {}, None
    t = ast.get("type", "")
    if t == "Program":
        return ast, None
    if t == "Experiment":
        return _unwrap_root(ast.get("body", {}))
    if t == "Paper":
        experiments = ast.get("experiments", []) or []
        if experiments:
            program, extra = _unwrap_root(experiments[0].get("body", {}))
            paper_shared = ast.get("shared_annotations", []) or []
            if paper_shared and isinstance(program, dict):
                existing = list(program.get("program_annotations", []) or [])
                existing_kws = {
                    a.get("keyword") for a in existing if isinstance(a, dict)
                }
                merged = list(existing)
                for a in paper_shared:
                    if (
                        isinstance(a, dict)
                        and a.get("keyword") not in existing_kws
                    ):
                        merged.append(a)
                program = dict(program)
                program["program_annotations"] = merged
            return program, extra
        return {}, None
    if t == "PhaseSequence" or "phases" in ast:
        # Synthesize a Program so that subjects/apparatus can read the
        # shared annotations as if they were program-level annotations.
        synthesized: ProgramNode = {
            "type": "Program",
            "program_annotations": ast.get("shared_annotations", []) or [],
            "param_decls": ast.get("shared_param_decls", []) or [],
            "bindings": [],
            "schedule": {},
        }
        return synthesized, ast
    if t in ("Shaping", "ProgressiveTraining"):
        # Pre-expansion experiment-layer nodes: wrap in a single-Phase
        # PhaseSequence so the downstream narrative describes the node
        # rather than silently falling through.
        synthesized_ps: dict = {
            "type": "PhaseSequence",
            "shared_annotations": [],
            "phases": [{
                "type": "Phase",
                "label": ast.get("label", t),
                "schedule": ast,
            }],
        }
        synthesized_prog: ProgramNode = {
            "type": "Program",
            "program_annotations": [],
            "param_decls": [],
            "bindings": [],
            "schedule": {},
        }
        return synthesized_prog, synthesized_ps
    # Bare schedule at root (e.g. t-tau from_ttau fixtures, or callers
    # passing a lone ScheduleExpr). Wrap into a minimal Program so the
    # render pipeline can describe it.
    if t in _SCHEDULE_TYPES:
        synthesized_bare: ProgramNode = {
            "type": "Program",
            "program_annotations": [],
            "param_decls": [],
            "bindings": [],
            "schedule": ast,
        }
        return synthesized_bare, None
    return {}, None


def _compile_single(
    program: ProgramNode,
    phase_sequence: dict | None,
    *,
    style: Style,
    extra_references: list[Reference] | None,
) -> MethodSection:
    refs = ReferenceCollector()
    if extra_references:
        for ref in extra_references:
            refs.add(ref)

    subjects = render_subjects(program, style=style, refs=refs)
    apparatus = render_apparatus(program, style=style, refs=refs)

    if phase_sequence is not None:
        procedure = render_procedure(phase_sequence, style=style, refs=refs)
    else:
        procedure = render_procedure(program, style=style, refs=refs)

    return MethodSection(
        subjects=subjects,
        apparatus=apparatus,
        procedure=procedure,
        references=tuple(refs.sorted_references()),
        style=style,
    )
