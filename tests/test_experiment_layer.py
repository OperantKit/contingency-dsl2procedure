"""Tests for pre-expansion experiment-layer visitors.

Shaping / ProgressiveTraining / PhaseRef are pre-expansion AST primitives
that the compiler tolerates when a custom parser supplies them directly
(without resolver desugaring). Coverage here exercises both the
integration path through ``compile_method`` and the visitor functions
directly to pin user-visible prose against regression.
"""

from __future__ import annotations

from contingency_dsl2procedure import compile_method
from contingency_dsl2procedure.references import ReferenceCollector
from contingency_dsl2procedure.sections.visitors.experiment_layer import (
    visit_phase_ref,
    visit_progressive_training,
    visit_shaping,
)
from contingency_dsl2procedure.sections.visitors.limited_hold import (
    visit_limited_hold,
)
from contingency_dsl2procedure.style import JABA, JEAB


# --- visit_shaping ----------------------------------------------------------


class TestShapingJEAB:
    def test_default_artful(self) -> None:
        prose = visit_shaping({"type": "Shaping"}, style=JEAB)
        assert "shaped" in prose
        assert "experimenter-directed successive-approximation" in prose
        assert prose.endswith(".")
        assert "target response" in prose

    def test_explicit_target(self) -> None:
        prose = visit_shaping(
            {"type": "Shaping", "target": "key-peck"}, style=JEAB,
        )
        assert "key-peck" in prose
        assert "shaped" in prose

    def test_percentile_method(self) -> None:
        prose = visit_shaping(
            {"type": "Shaping", "method": "percentile"}, style=JEAB,
        )
        assert "percentile-based shaping" in prose

    def test_staged_method(self) -> None:
        prose = visit_shaping(
            {"type": "Shaping", "method": "staged"}, style=JEAB,
        )
        assert "staged shaping" in prose

    def test_unknown_method_passes_through(self) -> None:
        prose = visit_shaping(
            {"type": "Shaping", "method": "custom-method"}, style=JEAB,
        )
        assert "custom-method" in prose

    def test_dimension_included(self) -> None:
        prose = visit_shaping(
            {"type": "Shaping", "dimension": "force"}, style=JEAB,
        )
        assert "along the force dimension" in prose

    def test_approximations_sequence_rendered(self) -> None:
        prose = visit_shaping(
            {
                "type": "Shaping",
                "approximations": ["orient", "approach", "press"],
            },
            style=JEAB,
        )
        assert "orient" in prose
        assert "approach" in prose
        assert "press" in prose
        assert "→" in prose


class TestShapingJABA:
    def test_default_artful_ja(self) -> None:
        prose = visit_shaping({"type": "Shaping"}, style=JABA)
        assert "シェイピング" in prose
        assert "実験者の判断" in prose
        assert prose.endswith("。")

    def test_percentile_ja(self) -> None:
        prose = visit_shaping(
            {"type": "Shaping", "method": "percentile"}, style=JABA,
        )
        assert "パーセンタイル法" in prose

    def test_staged_ja(self) -> None:
        prose = visit_shaping(
            {"type": "Shaping", "method": "staged"}, style=JABA,
        )
        assert "段階的シェイピング" in prose

    def test_dimension_ja(self) -> None:
        prose = visit_shaping(
            {"type": "Shaping", "dimension": "force"}, style=JABA,
        )
        assert "次元 force" in prose

    def test_approximations_ja(self) -> None:
        prose = visit_shaping(
            {
                "type": "Shaping",
                "approximations": ["orient", "approach", "press"],
            },
            style=JABA,
        )
        assert "近似系列" in prose
        assert "orient→approach→press" in prose


class TestShapingReferences:
    def test_artful_cites_skinner_1953(self) -> None:
        refs = ReferenceCollector()
        visit_shaping({"type": "Shaping"}, style=JEAB, refs=refs)
        keys = {r.key for r in refs.sorted_references()}
        assert "skinner_1953" in keys

    def test_percentile_also_cites_galbicka_1994(self) -> None:
        refs = ReferenceCollector()
        visit_shaping(
            {"type": "Shaping", "method": "percentile"},
            style=JEAB, refs=refs,
        )
        keys = {r.key for r in refs.sorted_references()}
        assert "skinner_1953" in keys
        assert "galbicka_1994" in keys


# --- visit_progressive_training ---------------------------------------------


class TestProgressiveTrainingJEAB:
    def test_default_no_steps(self) -> None:
        prose = visit_progressive_training(
            {"type": "ProgressiveTraining"}, style=JEAB,
        )
        assert "parametric training progression" in prose
        assert "Progression" in prose
        assert prose.endswith(".")

    def test_with_label(self) -> None:
        prose = visit_progressive_training(
            {"type": "ProgressiveTraining", "label": "FRRamp"},
            style=JEAB,
        )
        assert "FRRamp" in prose

    def test_with_steps(self) -> None:
        prose = visit_progressive_training(
            {
                "type": "ProgressiveTraining",
                "steps": [
                    {"name": "n", "values": [1, 2, 4, 8]},
                    {"name": "vi", "values": [15, 30, 60]},
                ],
            },
            style=JEAB,
        )
        assert "n ∈ {1, 2, 4, 8}" in prose
        assert "vi ∈ {15, 30, 60}" in prose

    def test_step_without_name_is_skipped(self) -> None:
        prose = visit_progressive_training(
            {
                "type": "ProgressiveTraining",
                "steps": [{"values": [1, 2, 3]}],
            },
            style=JEAB,
        )
        # No sweep token because the step has no name
        assert "with sweeps" not in prose


class TestProgressiveTrainingJABA:
    def test_default_ja(self) -> None:
        prose = visit_progressive_training(
            {"type": "ProgressiveTraining"}, style=JABA,
        )
        assert "パラメトリック訓練" in prose
        assert prose.endswith("。")

    def test_with_steps_ja(self) -> None:
        prose = visit_progressive_training(
            {
                "type": "ProgressiveTraining",
                "label": "FRRamp",
                "steps": [
                    {"name": "n", "values": [1, 2, 4]},
                ],
            },
            style=JABA,
        )
        assert "FRRamp" in prose
        assert "スイープ" in prose
        assert "n ∈ {1, 2, 4}" in prose


# --- visit_phase_ref --------------------------------------------------------


class TestPhaseRef:
    def test_jeab_with_ref(self) -> None:
        prose = visit_phase_ref({"type": "PhaseRef", "ref": "Baseline"}, style=JEAB)
        assert prose == "The Baseline phase procedure was repeated."

    def test_jaba_with_ref(self) -> None:
        prose = visit_phase_ref({"type": "PhaseRef", "ref": "Baseline"}, style=JABA)
        assert prose == "フェーズ Baseline の手続きを反復した。"

    def test_empty_ref_returns_empty(self) -> None:
        assert visit_phase_ref({"type": "PhaseRef"}, style=JEAB) == ""
        assert visit_phase_ref({"type": "PhaseRef", "ref": ""}, style=JABA) == ""


# --- Integration via compile_method (root unwrap path) ----------------------


class TestCompileShapingRoot:
    """Shaping as the root AST is auto-wrapped into a PhaseSequence by
    ``_unwrap_root`` (compiler.py L173-186). Verify the prose surfaces."""

    def test_shaping_root_jeab(self) -> None:
        method = compile_method(
            {
                "type": "Shaping",
                "target": "lever-press",
                "method": "percentile",
                "approximations": ["orient", "approach"],
            },
            style="jeab",
        )
        assert "lever-press" in method.procedure
        assert "percentile-based shaping" in method.procedure

    def test_shaping_root_jaba(self) -> None:
        method = compile_method(
            {"type": "Shaping", "target": "レバー押し", "method": "artful"},
            style="jaba",
        )
        assert "レバー押し" in method.procedure
        assert "シェイピング" in method.procedure


class TestCompileProgressiveTrainingRoot:
    def test_progressive_training_root(self) -> None:
        method = compile_method(
            {
                "type": "ProgressiveTraining",
                "label": "FRRamp",
                "steps": [{"name": "n", "values": [1, 2, 4, 8, 16]}],
            },
            style="jeab",
        )
        assert "FRRamp" in method.procedure
        assert "n ∈ {1, 2, 4, 8, 16}" in method.procedure


# --- visit_limited_hold (deprecated shim) -----------------------------------


class TestLimitedHoldDeprecatedShim:
    """The LimitedHold wrapper was removed from the AST; the visitor is
    retained as a compatibility shim that always returns the empty string.
    """

    def test_returns_empty_jeab(self) -> None:
        assert visit_limited_hold({"type": "LimitedHold"}, style=JEAB) == ""

    def test_returns_empty_jaba(self) -> None:
        assert visit_limited_hold({"type": "LimitedHold"}, style=JABA) == ""


class TestCompilePhaseRefInPhaseSequence:
    """PhaseRef is not auto-unwrapped as a root; it appears inside phases."""

    def test_phase_ref_in_phase_sequence(self) -> None:
        method = compile_method(
            {
                "type": "PhaseSequence",
                "phases": [
                    {
                        "type": "Phase",
                        "label": "Baseline",
                        "schedule": {
                            "type": "Atomic", "dist": "V", "domain": "I",
                            "value": 30.0, "time_unit": "s",
                        },
                    },
                    {
                        "type": "Phase",
                        "label": "BaselineReturn",
                        "schedule": {"type": "PhaseRef", "ref": "Baseline"},
                    },
                ],
            },
            style="jeab",
        )
        assert "Baseline phase procedure was repeated" in method.procedure
