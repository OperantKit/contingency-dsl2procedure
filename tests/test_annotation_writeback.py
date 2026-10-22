"""compile_method writes these annotations back as reader-recoverable prose."""

from contingency_dsl2procedure import compile_method
from contingency_dsl2procedure.references import FLESHLER_HOFFMAN_1962


def _program(*anns: dict) -> dict:
    return {
        "type": "Program",
        "program_annotations": list(anns),
        "param_decls": [],
        "bindings": [],
        "schedule": {
            "type": "Atomic", "dist": "V", "domain": "I",
            "value": 30.0, "time_unit": "s",
        },
    }


def _text(*anns: dict) -> str:
    return compile_method(_program(*anns)).to_text()


class TestProgramLevelSd:
    def test_each_sd_is_written_in_order(self) -> None:
        text = _text(
            {"type": "Annotation", "keyword": "sd", "positional": "red_light"},
            {"type": "Annotation", "keyword": "sd", "positional": "clicks"},
        )
        red = text.find("in the presence of red light.")
        clicks = text.find("in the presence of clicks.")
        assert 0 <= red < clicks

    def test_component_sd_is_not_repeated_as_program_sd(self) -> None:
        text = _text(
            {"type": "Annotation", "keyword": "sd", "positional": "tone",
             "params": {"component": 1}},
        )
        assert "in the presence of tone." not in text


class TestAlgorithmCitation:
    def test_inline_citation_uses_surnames(self) -> None:
        assert FLESHLER_HOFFMAN_1962.to_inline() == "Fleshler and Hoffman (1962)"

    def test_algorithm_sentence_cites_fleshler_and_hoffman(self) -> None:
        text = _text(
            {"type": "Annotation", "keyword": "algorithm",
             "positional": "fleshler-hoffman"},
        )
        assert "Fleshler and Hoffman (1962)" in text


class TestWarmupUnit:
    def test_params_time_unit_is_used(self) -> None:
        text = _text(
            {"type": "Annotation", "keyword": "warmup",
             "params": {"duration": 5.0, "time_unit": "min"}},
        )
        assert "5-min warm-up" in text
