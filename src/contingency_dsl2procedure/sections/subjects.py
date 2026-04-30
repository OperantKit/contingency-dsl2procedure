"""Subjects section generator.

Consumes program_annotations:
    {"keyword": "species", "positional": "rat"}
    {"keyword": "strain", "positional": "Sprague-Dawley"}
    {"keyword": "n", "positional": 6}
    {"keyword": "deprivation", "params": {"hours": 23, "target": "food"}}
    {"keyword": "history", "positional": "naive"}
"""

from __future__ import annotations

from ..ast_types import ProgramNode
from ..references import ReferenceCollector
from ..style import JEAB, Style
from .annotation_expander import expand_bundled_annotations


def render_subjects(
    program: ProgramNode,
    style: Style = JEAB,
    refs: ReferenceCollector | None = None,
) -> str:
    """Generate the Subjects subsection from program-level annotations."""
    attrs = _extract_subject_attrs(program)
    if not attrs:
        return ""

    species = attrs.get("species", "")
    strain = attrs.get("strain", "")
    n = attrs.get("n")
    population = attrs.get("population", "")
    deprivation = attrs.get("deprivation", {})
    history = attrs.get("history", "")

    # When @species is "human" and @population is set ("children", "adults",
    # ...), the population term reads more naturally than the bare species.
    if species == "human" and population:
        species = population[:-1] if population.endswith("s") else population

    sentences: list[str] = []

    if n is not None or species:
        sentences.append(_build_subject_sentence(n, strain, species, style))
    if deprivation:
        s = _build_deprivation_sentence(deprivation, style)
        if s:
            sentences.append(s)
    if history:
        s = _build_history_sentence(history, species, style)
        if s:
            sentences.append(s)

    return " ".join(sentences)


def _extract_subject_attrs(program: ProgramNode) -> dict:
    """Extract subject-related attributes from program_annotations.

    Accepts both unbundled (``@species("pigeon")``) and bundled
    (``@subjects(species="pigeon", n=4)``) annotation shapes.

    When multiple @species values are present (e.g. cross-species review or
    multi-cohort study) only the first is used for sentence generation to
    keep render_subjects → extract_subject_annotations round-trips stable.
    Later conflicting @species values are ignored.
    """
    result: dict = {}
    anns = expand_bundled_annotations(
        list(program.get("program_annotations", []) or [])
    )
    for ann in anns:
        kw = ann.get("keyword", "")
        if kw == "species":
            # First-wins to match extract_subject_annotations reading order.
            if "species" not in result:
                result["species"] = ann.get("positional", "")
        elif kw == "population":
            if "population" not in result:
                result["population"] = ann.get("positional", "")
        elif kw == "strain":
            if "strain" not in result:
                result["strain"] = ann.get("positional", "")
        elif kw == "n":
            if "n" not in result:
                result["n"] = int(ann.get("positional", 0))
        elif kw == "deprivation":
            result["deprivation"] = ann.get("params", {})
        elif kw == "history":
            result["history"] = ann.get("positional", "")
    return result


def _build_subject_sentence(
    n: int | None, strain: str, species: str, style: Style,
) -> str:
    if style.locale == "ja":
        n_str = str(n) if n is not None else ""
        strain_str = f"{strain} 系" if strain else ""
        sp = _ja_species(species)
        return f"{n_str}匹の{strain_str}{sp}を被験体とした。"
    else:
        parts: list[str] = []
        if n is not None:
            parts.append(_number_to_word(n, style).capitalize())
        if strain:
            parts.append(strain)
        if species:
            parts.append(
                species if n is None or n == 1 else _pluralize(species)
            )
        subject = " ".join(parts) if parts else "Subjects"
        return f"{subject} served as subjects."


def _build_deprivation_sentence(dep: dict, style: Style) -> str:
    hours = dep.get("hours")
    target = dep.get("target", "food")
    if hours is None:
        return ""
    h = int(hours) if float(hours) == int(hours) else hours
    if style.locale == "ja":
        return (
            f"各セッションの約{h}時間前から{target}摂取を制限し、"
            f"自由摂食時体重の約80%に維持した。"
        )
    return (
        f"They were maintained at approximately 80% of their free-feeding "
        f"weights by {target} deprivation for approximately {h} hr "
        f"before each session."
    )


def _build_history_sentence(history: str, species: str, style: Style) -> str:
    if style.locale == "ja":
        if history.lower() == "naive":
            return "すべての被験体は実験開始時に実験経験がなかった。"
        return f"実験開始前に、被験体は{history}の経験があった。"
    else:
        if history.lower() == "naive":
            sw = _pluralize(species) if species else "subjects"
            return (
                f"All {sw} were experimentally naive at the start "
                f"of the experiment."
            )
        return (
            f"Prior to the experiment, subjects had experience with {history}."
        )


def _number_to_word(n: int, style: Style) -> str:
    if n >= style.spell_numbers_below or style.spell_numbers_below == 0:
        return str(n)
    words = {
        1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
        6: "six", 7: "seven", 8: "eight", 9: "nine",
    }
    return words.get(n, str(n))


def _pluralize(species: str) -> str:
    # Words that are already plural or have an invariant plural.
    already_plural = {
        "children", "mice", "geese", "men", "women", "people",
        "sheep", "fish",
        "adults", "infants", "adolescents", "students", "participants",
        "humans", "individuals", "boys", "girls", "rats", "pigeons",
    }
    if species.lower() in already_plural:
        return species
    irregulars = {
        "mouse": "mice",
        "goose": "geese",
        "child": "children",
        "man": "men",
        "woman": "women",
        "person": "people",
    }
    if species.lower() in irregulars:
        return irregulars[species.lower()]
    if species.lower().endswith(("s", "sh", "ch")):
        return species + "es"
    return species + "s"


def _ja_species(species: str) -> str:
    mapping = {"rat": "ラット", "pigeon": "ハト", "mouse": "マウス"}
    return mapping.get(species.lower(), species)
