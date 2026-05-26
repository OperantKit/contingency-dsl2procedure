"""Tests for auto-collected citations across schedule primitives.

Each schedule type that has a canonical primary reference must auto-emit
that reference into MethodSection.references when the schedule is encountered.
"""

from __future__ import annotations

from contingency_dsl2procedure import compile_method
from contingency_dsl2procedure.references import BUILTIN_REFERENCES


def _program(schedule: dict) -> dict:
    return {
        "type": "Program",
        "param_decls": [],
        "bindings": [],
        "schedule": schedule,
    }


def _ref_keys(method) -> set[str]:
    return {r.key for r in method.references}


class TestBuiltinReferencesRegistered:
    """The new bibliographic entries must be available in the registry."""

    def test_zeiler_1968_registered(self) -> None:
        ref = BUILTIN_REFERENCES["zeiler_1968"]
        assert "Zeiler" in ref.authors
        assert ref.year == 1968
        assert "10.1901/jeab.1968.11-405" in ref.doi

    def test_millenson_1963_registered(self) -> None:
        ref = BUILTIN_REFERENCES["millenson_1963"]
        assert "Millenson" in ref.authors
        assert ref.year == 1963

    def test_mcsweeney_norman_1979_registered(self) -> None:
        ref = BUILTIN_REFERENCES["mcsweeney_norman_1979"]
        assert "McSweeney" in ref.authors
        assert ref.year == 1979

    def test_malagodi_1973_registered(self) -> None:
        ref = BUILTIN_REFERENCES["malagodi_1973"]
        assert "Malagodi" in ref.authors
        assert ref.year == 1973

    def test_richards_1993_registered(self) -> None:
        ref = BUILTIN_REFERENCES["richards_1993"]
        assert "Richards" in ref.authors
        assert ref.year == 1993

    def test_reed_2003_registered(self) -> None:
        ref = BUILTIN_REFERENCES["reed_2003"]
        assert "Reed" in ref.authors
        assert ref.year == 2003

    def test_rey_2019_registered(self) -> None:
        ref = BUILTIN_REFERENCES["rey_2019"]
        assert "Rey" in ref.authors
        assert ref.year == 2019

    def test_hunter_davison_1985_registered(self) -> None:
        ref = BUILTIN_REFERENCES["hunter_davison_1985"]
        assert "Hunter" in ref.authors
        assert ref.year == 1985


class TestAtomicAutoCitation:
    """Atomic-schedule visitors auto-cite the canonical primary reference."""

    def test_vt_cites_zeiler_1968(self) -> None:
        ast = _program(
            {"type": "Atomic", "dist": "V", "domain": "T",
             "value": 30.0, "time_unit": "s"},
        )
        method = compile_method(ast)
        assert "zeiler_1968" in _ref_keys(method)

    def test_ft_cites_zeiler_1968(self) -> None:
        ast = _program(
            {"type": "Atomic", "dist": "F", "domain": "T",
             "value": 30.0, "time_unit": "s"},
        )
        method = compile_method(ast)
        assert "zeiler_1968" in _ref_keys(method)

    def test_ri_cites_millenson_1963(self) -> None:
        ast = _program(
            {"type": "Atomic", "dist": "R", "domain": "I",
             "value": 30.0, "time_unit": "s"},
        )
        method = compile_method(ast)
        assert "millenson_1963" in _ref_keys(method)

    def test_vi_does_not_cite_zeiler(self) -> None:
        """Interval schedules should not pull in the time-schedule citation."""
        ast = _program(
            {"type": "Atomic", "dist": "V", "domain": "I",
             "value": 30.0, "time_unit": "s"},
        )
        method = compile_method(ast)
        keys = _ref_keys(method)
        assert "zeiler_1968" not in keys
        assert "fleshler_hoffman_1962" in keys

    def test_fr_does_not_cite_zeiler(self) -> None:
        """Ratio schedules should not pull in the time-schedule citation."""
        ast = _program(
            {"type": "Atomic", "dist": "F", "domain": "R", "value": 5.0},
        )
        method = compile_method(ast)
        assert "zeiler_1968" not in _ref_keys(method)


class TestModifierAutoCitation:
    """DR{L,H,O} cite their canonical primary references."""

    def test_drl_cites_richards_1993(self) -> None:
        ast = _program(
            {"type": "Modifier", "modifier": "DRL",
             "value": 3.0, "time_unit": "s"},
        )
        method = compile_method(ast)
        assert "richards_1993" in _ref_keys(method)

    def test_drh_cites_reed_2003(self) -> None:
        ast = _program(
            {"type": "Modifier", "modifier": "DRH",
             "value": 5.0},
        )
        method = compile_method(ast)
        assert "reed_2003" in _ref_keys(method)

    def test_dro_cites_rey_2019(self) -> None:
        ast = _program(
            {"type": "Modifier", "modifier": "DRO",
             "value": 10.0, "time_unit": "s"},
        )
        method = compile_method(ast)
        assert "rey_2019" in _ref_keys(method)


class TestCompoundAutoCitation:
    """Mix / Tand combinators cite their canonical primary references."""

    def test_mix_cites_mcsweeney_norman_1979(self) -> None:
        ast = _program(
            {
                "type": "Compound",
                "combinator": "Mix",
                "components": [
                    {"type": "Atomic", "dist": "F", "domain": "R", "value": 5.0},
                    {"type": "Atomic", "dist": "V", "domain": "I",
                     "value": 30.0, "time_unit": "s"},
                ],
            },
        )
        method = compile_method(ast)
        assert "mcsweeney_norman_1979" in _ref_keys(method)

    def test_tand_cites_malagodi_1973(self) -> None:
        ast = _program(
            {
                "type": "Compound",
                "combinator": "Tand",
                "components": [
                    {"type": "Atomic", "dist": "V", "domain": "I",
                     "value": 30.0, "time_unit": "s"},
                    {"type": "Atomic", "dist": "F", "domain": "R", "value": 5.0},
                ],
            },
        )
        method = compile_method(ast)
        assert "malagodi_1973" in _ref_keys(method)

    def test_frco_param_cites_hunter_davison_1985(self) -> None:
        ast = _program(
            {
                "type": "Compound",
                "combinator": "Conc",
                "components": [
                    {"type": "Atomic", "dist": "V", "domain": "I",
                     "value": 30.0, "time_unit": "s"},
                    {"type": "Atomic", "dist": "V", "domain": "I",
                     "value": 60.0, "time_unit": "s"},
                ],
                "params": {"FRCO": {"value": 5}},
            },
        )
        method = compile_method(ast)
        assert "hunter_davison_1985" in _ref_keys(method)

    def test_cod_param_cites_herrnstein_1961(self) -> None:
        """COD parameter should auto-cite Herrnstein (1961) where COD was
        introduced."""
        ast = _program(
            {
                "type": "Compound",
                "combinator": "Conc",
                "components": [
                    {"type": "Atomic", "dist": "V", "domain": "I",
                     "value": 30.0, "time_unit": "s"},
                    {"type": "Atomic", "dist": "V", "domain": "I",
                     "value": 60.0, "time_unit": "s"},
                ],
                "params": {"COD": {"value": 2.0, "time_unit": "s"}},
            },
        )
        method = compile_method(ast)
        assert "herrnstein_1961" in _ref_keys(method)
