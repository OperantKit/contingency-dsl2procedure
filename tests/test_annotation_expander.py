"""Unit tests for annotation_expander.

Covers branches that the broader compile-pipeline tests don't reach:
non-dict input filtering, unknown sub-keyword dropping, and dict-valued
sub-annotation rendering as ``params``.
"""

from __future__ import annotations

from contingency_dsl2procedure.sections.annotation_expander import (
    expand_bundled_annotations,
)


class TestNonDictInput:
    def test_non_dict_entries_are_skipped(self) -> None:
        out = expand_bundled_annotations(
            ["not-a-dict", None, 42, {"keyword": "subjects", "kwargs": {"n": 4}}]
        )
        # The non-dict entries should be dropped; only the expanded sub-anns remain.
        assert out == [
            {"type": "Annotation", "keyword": "n", "positional": 4},
        ]


class TestUnknownSubKeyword:
    def test_unknown_sub_keyword_dropped(self) -> None:
        out = expand_bundled_annotations(
            [
                {
                    "keyword": "subjects",
                    "kwargs": {
                        "species": "pigeon",
                        "made_up_field": "ignored",
                    },
                }
            ]
        )
        kws = {a["keyword"] for a in out}
        assert "species" in kws
        assert "made_up_field" not in kws


class TestDictValueExpandedAsParams:
    def test_deprivation_dict_value_emits_params(self) -> None:
        out = expand_bundled_annotations(
            [
                {
                    "keyword": "subjects",
                    "kwargs": {
                        "deprivation": {"food": "85%", "water": "ad lib"},
                    },
                }
            ]
        )
        assert len(out) == 1
        ann = out[0]
        assert ann["keyword"] == "deprivation"
        assert ann["params"] == {"food": "85%", "water": "ad lib"}
        assert "positional" not in ann


class TestPassthroughAndParamsAlias:
    def test_non_bundled_annotation_passes_through(self) -> None:
        ann = {"type": "Annotation", "keyword": "procedure", "positional": "shape"}
        assert expand_bundled_annotations([ann]) == [ann]

    def test_params_alias_is_accepted(self) -> None:
        # When the bundle uses ``params`` instead of ``kwargs``.
        out = expand_bundled_annotations(
            [{"keyword": "apparatus", "params": {"chamber": "chamber_A"}}]
        )
        assert out == [
            {"type": "Annotation", "keyword": "chamber", "positional": "chamber_A"},
        ]
