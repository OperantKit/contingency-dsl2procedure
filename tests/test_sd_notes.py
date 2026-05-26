"""Tests for stimulus-control (S^D) notes appended to compound combinators.

The procedural distinction between Mult/Mix and Chain/Tand hinges on
whether components are signaled by distinct exteroceptive discriminative
stimuli (S^D). The generated prose must surface this distinction so
that readers of the Method section can determine the stimulus
arrangement without inspecting the AST.
"""

from __future__ import annotations

from contingency_dsl2procedure import compile_method


def _program(schedule: dict) -> dict:
    return {
        "type": "Program",
        "param_decls": [],
        "bindings": [],
        "schedule": schedule,
    }


def _components() -> list[dict]:
    return [
        {"type": "Atomic", "dist": "F", "domain": "R", "value": 5.0},
        {"type": "Atomic", "dist": "V", "domain": "I",
         "value": 30.0, "time_unit": "s"},
    ]


class TestSDNotesEnglish:
    def test_mult_has_signaled_note(self) -> None:
        ast = _program(
            {"type": "Compound", "combinator": "Mult",
             "components": _components()},
        )
        method = compile_method(ast)
        assert "signaled" in method.procedure.lower()
        assert "discriminative stimul" in method.procedure.lower()

    def test_mix_has_unsignaled_note(self) -> None:
        ast = _program(
            {"type": "Compound", "combinator": "Mix",
             "components": _components()},
        )
        method = compile_method(ast)
        text = method.procedure.lower()
        assert "no" in text or "without" in text or "not" in text
        assert "discriminative stimul" in text

    def test_chain_has_signaled_transition_note(self) -> None:
        ast = _program(
            {"type": "Compound", "combinator": "Chain",
             "components": _components()},
        )
        method = compile_method(ast)
        text = method.procedure.lower()
        assert "signaled" in text
        assert "discriminative stimul" in text

    def test_tand_has_unsignaled_transition_note(self) -> None:
        ast = _program(
            {"type": "Compound", "combinator": "Tand",
             "components": _components()},
        )
        method = compile_method(ast)
        text = method.procedure.lower()
        assert "discriminative stimul" in text
        assert "no" in text or "without" in text or "not" in text

    def test_conc_has_no_sd_note(self) -> None:
        """Conc is not a sequential-component combinator; no SD note."""
        ast = _program(
            {"type": "Compound", "combinator": "Conc",
             "components": _components()},
        )
        method = compile_method(ast)
        assert "discriminative stimul" not in method.procedure.lower()
        method_ja = compile_method(ast, style="jaba")
        assert "弁別刺激" not in method_ja.procedure


class TestSDNotesJapanese:
    def test_mult_ja_has_sd_note(self) -> None:
        ast = _program(
            {"type": "Compound", "combinator": "Mult",
             "components": _components()},
        )
        method = compile_method(ast, style="jaba")
        assert "弁別刺激" in method.procedure

    def test_mix_ja_has_sd_note(self) -> None:
        ast = _program(
            {"type": "Compound", "combinator": "Mix",
             "components": _components()},
        )
        method = compile_method(ast, style="jaba")
        assert "弁別刺激" in method.procedure

    def test_chain_ja_has_sd_note(self) -> None:
        ast = _program(
            {"type": "Compound", "combinator": "Chain",
             "components": _components()},
        )
        method = compile_method(ast, style="jaba")
        assert "弁別刺激" in method.procedure

    def test_tand_ja_has_sd_note(self) -> None:
        ast = _program(
            {"type": "Compound", "combinator": "Tand",
             "components": _components()},
        )
        method = compile_method(ast, style="jaba")
        assert "弁別刺激" in method.procedure
