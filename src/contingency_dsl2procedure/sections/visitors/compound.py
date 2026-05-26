"""Compound schedule visitor.

Handles operant Compound expressions (Conc, Alt, Conj, Chain, Tand, Mult,
Mix, Overlay, Interpolate) along with combinator-specific params such as
directional COD, FRCO, BO, Interpolate count/onset, Overlay target,
and response-class-specific PUNISH entries.
"""

from __future__ import annotations

from ...ast_types import ScheduleNode
from ...references import ReferenceCollector
from ...style import Style
from ...vocabulary import format_combinator
from ._common import decorate_leaf, fmt_val, format_component, format_duration


def visit_compound(
    node: ScheduleNode, *, style: Style,
    refs: ReferenceCollector | None = None, first_mention: bool = True,
) -> str:
    combinator = node.get("combinator", "")
    components = node.get("components", []) or []

    # Respondent Compound (disambiguation via cs_list vs. components)
    if combinator == "" and "cs_list" in node:
        # Will be dispatched by a respondent visitor, not here.
        return ""

    if refs is not None:
        for c in components:
            if c.get("type") == "Atomic" and c.get("dist") == "V":
                refs.cite("fleshler_hoffman_1962")
                break
        combinator_refs = {
            "Mix": "mcsweeney_norman_1979",
            "Tand": "malagodi_1973",
        }
        key = combinator_refs.get(combinator)
        if key is not None:
            refs.cite_if_known(key)

    params = node.get("params", {}) or {}

    if combinator == "Overlay":
        return _visit_overlay(components, params, style=style, refs=refs)

    if combinator == "Interpolate":
        return _visit_interpolate(components, params, style=style, refs=refs)

    comb_name = format_combinator(combinator, style)
    component_names = [
        format_component(c, style=style, first_mention=False)
        for c in components
    ]
    components_str = " ".join(component_names)

    base = style.framing_reinforced.format(
        schedule=f"{comb_name} {components_str}"
    )

    sd_note = _sd_note(combinator, style)
    if sd_note:
        if style.locale == "ja":
            base = base.rstrip("。") + "。" + sd_note
        else:
            base = base.rstrip(".") + ". " + sd_note

    # Append compound-level parameter clauses (COD, FRCO, BO, PUNISH)
    extra_parts = _describe_compound_params(combinator, params, style, refs)
    if extra_parts:
        if style.locale == "ja":
            base = base.rstrip("。") + "。" + "".join(extra_parts)
        else:
            base = base.rstrip(".") + ". " + " ".join(extra_parts)

    return decorate_leaf(base, node, style=style)


# --- SD (discriminative-stimulus) note ---------------------------------------

_SD_NOTES_EN: dict[str, str] = {
    "Mult": (
        "Each component was signaled by a distinct exteroceptive "
        "discriminative stimulus."
    ),
    "Mix": (
        "No exteroceptive discriminative stimulus differentiated the "
        "components."
    ),
    "Chain": (
        "Successive components were signaled by distinct exteroceptive "
        "discriminative stimuli."
    ),
    "Tand": (
        "Component transitions occurred without any change in the "
        "exteroceptive discriminative stimulus."
    ),
}

_SD_NOTES_JA: dict[str, str] = {
    "Mult": "各成分はそれぞれ固有の外受容性弁別刺激で標識された。",
    "Mix": "成分を区別する外受容性弁別刺激は呈示されなかった。",
    "Chain": "各成分はそれぞれ固有の外受容性弁別刺激で標識された。",
    "Tand": "成分の移行に伴う外受容性弁別刺激の変化は呈示されなかった。",
}


def _sd_note(combinator: str, style: Style) -> str:
    table = _SD_NOTES_JA if style.locale == "ja" else _SD_NOTES_EN
    return table.get(combinator, "")


# --- Overlay -----------------------------------------------------------------

def _visit_overlay(
    components: list[ScheduleNode], params: dict,
    *, style: Style, refs: ReferenceCollector | None,
) -> str:
    if len(components) < 2:
        return ""
    baseline = format_component(components[0], style=style, first_mention=False)
    punisher = format_component(components[1], style=style, first_mention=False)
    target = params.get("target", "all")

    if target == "changeover":
        if style.locale == "ja":
            return (
                f"{baseline}スケジュールに従って反応が強化された。"
                f"加えて、切替反応に対して{punisher}スケジュールの"
                f"罰刺激が重畳された。"
            )
        return (
            f"Responses were reinforced under a {baseline} schedule. "
            f"In addition, a punishment contingency ({punisher}) was "
            f"superimposed on changeover responses only."
        )

    if style.locale == "ja":
        return (
            f"{baseline}スケジュールに従って反応が強化された。"
            f"加えて、{punisher}スケジュールに従って罰刺激が重畳された。"
        )
    return (
        f"Responses were reinforced under a {baseline} schedule. "
        f"In addition, a punishment contingency ({punisher}) "
        f"was superimposed on the baseline schedule."
    )


# --- Interpolate --------------------------------------------------------------

def _visit_interpolate(
    components: list[ScheduleNode], params: dict,
    *, style: Style, refs: ReferenceCollector | None,
) -> str:
    if refs is not None:
        refs.cite_if_known("ferster_skinner_1957")
    if len(components) < 2:
        return ""
    background = format_component(components[0], style=style, first_mention=False)
    interp = format_component(components[1], style=style, first_mention=False)
    count = params.get("count", {}).get("value")
    onset = params.get("onset") or {}
    onset_str = ""
    if onset:
        onset_str = format_duration(
            onset.get("value", 0), onset.get("time_unit", "s"), style,
        )

    if style.locale == "ja":
        pieces = [f"{background}スケジュールを基礎として反応が維持された。"]
        if onset_str:
            pieces.append(f"{onset_str}経過後、")
        if count is not None:
            pieces.append(f"{interp}スケジュールによる挿入ブロック（{int(count)}強化）が実施された。")
        else:
            pieces.append(f"{interp}スケジュールによる挿入ブロックが実施された。")
        return "".join(pieces)

    parts = [f"Responses were maintained on a {background} baseline."]
    head = ""
    if onset_str:
        head = f"After {onset_str}, "
    if count is not None:
        parts.append(
            f"{head}an interpolated block of {interp} was conducted "
            f"for {int(count)} reinforcers."
        )
    else:
        parts.append(f"{head}an interpolated block of {interp} was conducted.")
    return " ".join(parts)


# --- Compound params clauses (COD / FRCO / BO / PUNISH) ----------------------

def _describe_compound_params(
    combinator: str, params: dict, style: Style,
    refs: ReferenceCollector | None,
) -> list[str]:
    sentences: list[str] = []

    cod = params.get("COD")
    if cod is not None:
        if refs is not None:
            refs.cite_if_known("herrnstein_1961")
        sentences.extend(_describe_cod(cod, style))

    frco = params.get("FRCO")
    if frco is not None:
        if refs is not None:
            refs.cite_if_known("hunter_davison_1985")
        count = int(frco.get("value", 0))
        if style.locale == "ja":
            sentences.append(f"{count}反応の固定比率切替が設定された。")
        else:
            sentences.append(f"A {count}-response fixed-ratio changeover was in effect.")

    bo = params.get("BO")
    if bo is not None:
        dur = format_duration(bo.get("value", 0), bo.get("time_unit", "s"), style)
        if style.locale == "ja":
            sentences.append(f"成分間に{dur}のブラックアウトが挿入された。")
        else:
            sentences.append(f"A {dur} blackout separated components.")

    punish = params.get("PUNISH")
    if punish is not None:
        sentences.extend(_describe_punish(punish, style, refs))

    return sentences


def _describe_cod(cod: dict, style: Style) -> list[str]:
    # Symmetric form: has "value"
    if "value" in cod and "directional" not in cod and "base" not in cod:
        dur = format_duration(cod.get("value", 0), cod.get("time_unit", "s"), style)
        if style.locale == "ja":
            return [f"{dur}の切替遅延が設定された。"]
        return [f"A {dur} changeover delay was in effect."]

    sentences: list[str] = []
    base = cod.get("base")
    if base:
        dur = format_duration(base.get("value", 0), base.get("time_unit", "s"), style)
        if style.locale == "ja":
            sentences.append(f"基本切替遅延は{dur}に設定された。")
        else:
            sentences.append(f"A base changeover delay of {dur} was in effect.")

    directional = cod.get("directional", []) or []
    for entry in directional:
        dur = format_duration(
            entry.get("value", 0),
            entry.get("time_unit", "s"),
            style,
        )
        frm = entry.get("from")
        to_c = entry.get("to")
        if style.locale == "ja":
            sentences.append(
                f"成分{frm}→成分{to_c}の切替では切替遅延を{dur}に設定した。"
            )
        else:
            sentences.append(
                f"Changeovers from component {frm} to component {to_c} "
                f"received a {dur} changeover delay."
            )
    return sentences


def _describe_punish(
    punish: dict, style: Style, refs: ReferenceCollector | None,
) -> list[str]:
    sentences: list[str] = []
    changeover = punish.get("changeover")
    if changeover is not None:
        sched_str = format_component(changeover, style=style, first_mention=False)
        if style.locale == "ja":
            sentences.append(f"切替反応は{sched_str}スケジュールで罰された。")
        else:
            sentences.append(
                f"Changeover responses were punished under a {sched_str} schedule."
            )

    for entry in punish.get("directional", []) or []:
        sched_str = format_component(
            entry.get("schedule", {}), style=style, first_mention=False,
        )
        frm = entry.get("from")
        to_c = entry.get("to")
        if style.locale == "ja":
            sentences.append(
                f"成分{frm}→成分{to_c}の切替は{sched_str}スケジュールで罰された。"
            )
        else:
            sentences.append(
                f"Transitions from component {frm} to component {to_c} "
                f"were punished under a {sched_str} schedule."
            )

    for entry in punish.get("component", []) or []:
        sched_str = format_component(
            entry.get("schedule", {}), style=style, first_mention=False,
        )
        comp = entry.get("component")
        if style.locale == "ja":
            sentences.append(
                f"成分{comp}への反応は{sched_str}スケジュールで罰された。"
            )
        else:
            sentences.append(
                f"Responses on component {comp} were punished under a "
                f"{sched_str} schedule."
            )

    return sentences
