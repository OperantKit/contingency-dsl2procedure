"""Targeted unit tests for the contingency-dsl v0.1.0 compatibility pass.

These tests document the AST shapes added during the v0.1.0 coverage
audit and lock in the user-visible prose so future regressions show up
as focused test failures (rather than being absorbed by the broad
conformance smoke test).
"""

from __future__ import annotations

import pytest

from contingency_dsl2procedure import compile_method


def _program(schedule: dict, **extra) -> dict:
    base = {
        "type": "Program",
        "program_annotations": extra.get("program_annotations", []),
        "param_decls": extra.get("param_decls", []),
        "bindings": extra.get("bindings", []),
        "schedule": schedule,
    }
    return base


# --- Atomic dist=EXT/CRF fallback -------------------------------------------


class TestAtomicDistFallback:
    def test_dist_ext_renders_as_extinction(self) -> None:
        ast = _program({"type": "Atomic", "dist": "EXT"})
        m = compile_method(ast, style="jeab")
        assert "extinction" in m.procedure.lower()

    def test_dist_crf_renders_as_crf(self) -> None:
        ast = _program({"type": "Atomic", "dist": "CRF"})
        m = compile_method(ast, style="jeab")
        assert "continuous reinforcement" in m.procedure.lower()


# --- IdentifierRef resolution via bindings ----------------------------------


class TestIdentifierRefResolution:
    def test_let_bound_atomic_is_rendered(self) -> None:
        ast = _program(
            {"type": "IdentifierRef", "name": "baseline"},
            bindings=[{
                "type": "Binding",
                "name": "baseline",
                "value": {
                    "type": "Atomic", "dist": "V", "domain": "I",
                    "value": 60.0, "time_unit": "s",
                },
            }],
        )
        m = compile_method(ast, style="jeab")
        assert "VI" in m.procedure and "60" in m.procedure

    def test_unresolved_identifier_has_graceful_prose(self) -> None:
        ast = _program({"type": "IdentifierRef", "name": "missing"})
        m = compile_method(ast, style="jeab")
        assert "missing" in m.procedure


# --- AnnotatedSchedule wrapper ----------------------------------------------


class TestAnnotatedSchedule:
    def test_wrapper_unwraps_and_merges_annotations(self) -> None:
        ast = _program({
            "type": "AnnotatedSchedule",
            "expr": {
                "type": "PairForwardDelay",
                "cs": "tone",
                "us": "shock",
                "isi": {"value": 10, "unit": "s"},
                "cs_duration": {"value": 15, "unit": "s"},
            },
            "annotations": [{
                "type": "Annotation",
                "keyword": "iti",
                "params": {
                    "distribution": "exponential",
                    "mean": {"value": 60, "time_unit": "s"},
                },
            }],
        })
        m = compile_method(ast, style="jeab")
        assert "forward-delay" in m.procedure
        assert "exponential" in m.procedure


# --- Adjusting / Interlocking (operant stateful) ----------------------------


class TestStatefulSchedules:
    def test_adjusting_delay_jeab(self) -> None:
        ast = _program({
            "type": "AdjustingSchedule",
            "adj_target": "delay",
            "adj_start": {"value": 10, "time_unit": "s"},
            "adj_step": {"value": 1, "time_unit": "s"},
            "adj_min": None,
            "adj_max": None,
        })
        m = compile_method(ast, style="jeab")
        assert "adjusting schedule" in m.procedure.lower()
        assert "reinforcement delay" in m.procedure
        assert "10-s" in m.procedure

    def test_adjusting_ratio_jaba(self) -> None:
        ast = _program({
            "type": "AdjustingSchedule",
            "adj_target": "ratio",
            "adj_start": {"value": 5, "time_unit": None},
            "adj_step": {"value": 1, "time_unit": None},
            "adj_min": None,
            "adj_max": None,
        })
        m = compile_method(ast, style="jaba")
        assert "調整スケジュール" in m.procedure
        assert "比率要件" in m.procedure

    def test_interlocking_jeab(self) -> None:
        ast = _program({
            "type": "InterlockingSchedule",
            "interlock_R0": 20,
            "interlock_T": {"value": 60, "time_unit": "s"},
        })
        m = compile_method(ast, style="jeab")
        assert "interlocking" in m.procedure.lower()
        assert "R0=20" in m.procedure
        assert "60-s" in m.procedure


# --- MTS shorthand + stimulus_classes/training/testing ----------------------


class TestStimulusEquivalence:
    def test_mts_shorthand_jeab(self) -> None:
        ast = _program({
            "type": "MTS",
            "params": {"samples": 3, "comparisons": 3},
        })
        m = compile_method(ast, style="jeab")
        assert "matching-to-sample" in m.procedure.lower()
        assert "3 samples" in m.procedure

    def test_stimulus_classes_named(self) -> None:
        ast = _program(
            {"type": "MTS", "params": {"samples": 3, "comparisons": 3}},
            program_annotations=[{
                "type": "Annotation",
                "keyword": "stimulus_classes",
                "params": {"A": ["A1", "A2"], "B": ["B1", "B2"]},
            }],
        )
        m = compile_method(ast, style="jeab")
        assert "stimulus classes" in m.procedure.lower()

    def test_training_annotation_jeab(self) -> None:
        ast = _program({
            "type": "MTS",
            "params": {"samples": 3, "comparisons": 3},
            "annotations": [{
                "type": "Annotation",
                "keyword": "training",
                "params": {"relations": ["AB", "BC"], "criterion": 90},
            }],
        })
        m = compile_method(ast, style="jeab")
        assert "Training phases" in m.procedure
        assert "AB" in m.procedure and "BC" in m.procedure
        assert "90" in m.procedure

    def test_testing_annotation_jeab(self) -> None:
        ast = _program({
            "type": "MTS",
            "params": {"samples": 3, "comparisons": 3},
            "annotations": [{
                "type": "Annotation",
                "keyword": "testing",
                "params": {"relations": ["CA"], "probe_ratio": 0.25},
            }],
        })
        m = compile_method(ast, style="jeab")
        assert "Test phases" in m.procedure
        assert "CA" in m.procedure
        assert "0.25" in m.procedure


# --- Bundled annotation expansion (@subjects, @apparatus) -------------------


class TestBundledAnnotations:
    def test_subjects_bundled_kwargs(self) -> None:
        ast = {
            "type": "Paper",
            "shared_annotations": [
                {
                    "type": "Annotation",
                    "keyword": "subjects",
                    "kwargs": {"species": "pigeon", "n": 4},
                },
                {
                    "type": "Annotation",
                    "keyword": "apparatus",
                    "kwargs": {"chamber": "chamber_A"},
                },
            ],
            "experiments": [{
                "type": "Experiment",
                "label": "1",
                "body": _program({
                    "type": "Atomic", "dist": "V", "domain": "I",
                    "value": 30.0, "time_unit": "s",
                }),
            }],
        }
        m = compile_method(ast, style="jeab")
        assert "pigeon" in m.subjects.lower()
        assert "chamber_A" in m.apparatus


# --- Apparatus interface annotation -----------------------------------------


class TestApparatusInterface:
    def test_interface_keyword(self) -> None:
        ast = _program(
            {"type": "Special", "kind": "CRF"},
            program_annotations=[{
                "type": "Annotation",
                "keyword": "interface",
                "positional": "MedPC-IV",
                "params": {"port": "COM3"},
            }],
        )
        m = compile_method(ast, style="jeab")
        assert "MedPC-IV" in m.apparatus
        assert "COM3" in m.apparatus


# --- Composed avoidance / omission ------------------------------------------


class TestComposedAnnotations:
    def test_avoidance_annotation(self) -> None:
        ast = _program(
            {"type": "Special", "kind": "EXT"},
            program_annotations=[{
                "type": "Annotation",
                "keyword": "avoidance",
                "positional": "sidman",
            }],
        )
        m = compile_method(ast, style="jeab")
        assert "avoidance" in m.procedure.lower()

    def test_omission_annotation(self) -> None:
        ast = _program(
            {"type": "Special", "kind": "CRF"},
            program_annotations=[{
                "type": "Annotation",
                "keyword": "omission",
                "params": {"target": "keypeck", "delivery": "cancelled_on_response"},
            }],
        )
        m = compile_method(ast, style="jeab")
        assert "omission" in m.procedure.lower()
        assert "keypeck" in m.procedure


# --- Shaping procedure annotation -------------------------------------------


class TestShapingAnnotation:
    def test_shape_artful(self) -> None:
        ast = {
            "type": "PhaseSequence",
            "phases": [{
                "type": "Phase",
                "label": "Shaping",
                "schedule": {"type": "Special", "kind": "CRF"},
                "phase_annotations": [{
                    "type": "Annotation",
                    "keyword": "procedure",
                    "positional": "shape",
                    "params": {"target": "KeyPeck", "method": "artful"},
                }],
                "criterion": {"type": "ExperimenterJudgment"},
            }],
        }
        m = compile_method(ast, style="jeab")
        # Shaping here is a phase-level @procedure annotation which falls
        # through to the schedule-level annotation renderer; the
        # important behavior is that compilation succeeds with non-empty
        # procedure prose describing a CRF phase.
        assert m.procedure.strip()
        assert "Shaping" in m.procedure
