"""Modifier schedule visitors: DRL / DRH / DRO / PR / Lag / Repeat / Pctl.

Each subtype has a dedicated payload shape per the discriminated union
defined in schema/operant/ast.schema.json. Leaf-level decorations
(limitedHold, timeout, responseCost) apply to DR modifiers only; PR / Lag /
Pctl are self-contained.
"""

from __future__ import annotations

from ...ast_types import ScheduleNode
from ...references import ReferenceCollector
from ...style import Style
from ._common import decorate_leaf, fmt_val, format_component


def visit_modifier(
    node: ScheduleNode, *, style: Style,
    refs: ReferenceCollector | None = None, first_mention: bool = True,
) -> str:
    modifier = node.get("modifier", "")

    if modifier in ("DRL", "DRH", "DRO"):
        return _dr(node, style, refs)
    if modifier == "PR":
        return _pr(node, style, refs)
    if modifier == "Lag":
        return _lag(node, style, refs)
    if modifier == "Repeat":
        inner = node.get("inner", {})
        inner_desc = format_component(inner, style=style, first_mention=first_mention)
        n = int(node.get("value", 1))
        if style.locale == "ja":
            return f"{inner_desc}スケジュールを{n}回反復する手続きに従って反応が強化された。"
        return (
            f"Responses were reinforced under a schedule consisting of "
            f"{n} repetitions of {inner_desc}."
        )
    if modifier == "Pctl":
        return _pctl(node, style, refs)
    return ""


def _dr(node: ScheduleNode, style: Style, refs: ReferenceCollector | None) -> str:
    modifier = node.get("modifier", "")
    value = node.get("value", 0)
    unit = node.get("time_unit")

    if refs is not None:
        dr_refs = {
            "DRL": "richards_1993",
            "DRH": "reed_2003",
            "DRO": "rey_2019",
        }
        key = dr_refs.get(modifier)
        if key is not None:
            refs.cite_if_known(key)

    names_en = {
        "DRL": "differential-reinforcement-of-low-rate",
        "DRH": "differential-reinforcement-of-high-rate",
        "DRO": "differential-reinforcement-of-other-behavior",
    }
    names_ja = {
        "DRL": "低反応率分化強化",
        "DRH": "高反応率分化強化",
        "DRO": "他行動分化強化",
    }
    val_str = fmt_val(value)
    if unit and style.time_unit_hyphen:
        param = f"{val_str}-{unit}"
    elif unit:
        param = f"{val_str} {unit}"
    else:
        param = val_str

    if style.locale == "ja":
        full = names_ja.get(modifier, modifier)
        base = f"{full} ({modifier}) {param}スケジュールに従って反応が強化された。"
    else:
        full = names_en.get(modifier, modifier)
        base = f"Responses were reinforced under a {full} ({modifier}) {param} schedule."
    return decorate_leaf(base, node, style=style)


def _pr(node: ScheduleNode, style: Style, refs: ReferenceCollector | None) -> str:
    step = node.get("pr_step", "linear")
    start = node.get("pr_start")
    increment = node.get("pr_increment")
    ratio = node.get("pr_ratio")

    if refs is not None and step == "hodos":
        refs.cite_if_known("hodos_1961")

    step_names_en = {
        "linear": "linear", "hodos": "Hodos",
        "exponential": "exponential", "geometric": "geometric",
    }
    step_names_ja = {
        "linear": "線形", "hodos": "Hodos",
        "exponential": "指数", "geometric": "幾何",
    }
    step_name = (
        step_names_ja.get(step, step)
        if style.locale == "ja"
        else step_names_en.get(step, step)
    )
    params_parts: list[str] = []
    if start is not None:
        params_parts.append(
            f"開始値={fmt_val(start)}" if style.locale == "ja"
            else f"start={fmt_val(start)}"
        )
    if increment is not None:
        params_parts.append(
            f"増分={fmt_val(increment)}" if style.locale == "ja"
            else f"step={fmt_val(increment)}"
        )
    if ratio is not None:
        params_parts.append(
            f"比率={fmt_val(ratio)}" if style.locale == "ja"
            else f"ratio={fmt_val(ratio)}"
        )
    params_str = f" ({', '.join(params_parts)})" if params_parts else ""

    if style.locale == "ja":
        return f"{step_name}漸進比率スケジュール{params_str}に従って反応が強化された。"
    return f"Responses were reinforced under a {step_name} progressive-ratio schedule{params_str}."


def _lag(node: ScheduleNode, style: Style, refs: ReferenceCollector | None) -> str:
    length = int(node.get("length", 1))
    if refs is not None:
        refs.cite_if_known("page_neuringer_1985")
    if style.locale == "ja":
        return f"Lag {length}スケジュールに従って反応が強化された。"
    return f"Responses were reinforced under a Lag {length} schedule."


def _pctl(node: ScheduleNode, style: Style, refs: ReferenceCollector | None) -> str:
    target = node.get("pctl_target", "IRT")
    rank = node.get("pctl_rank", 50)
    window = node.get("pctl_window")
    direction = node.get("pctl_dir", "below")
    if refs is not None:
        refs.cite_if_known("platt_1973")
    window_part = ""
    if window:
        window_part = (
            f"（ウィンドウ={int(window)}）" if style.locale == "ja"
            else f" (window={int(window)})"
        )
    if style.locale == "ja":
        dir_ja = "以下" if direction == "below" else "以上"
        return (
            f"{target}の第{fmt_val(rank)}百分位{dir_ja}を満たす反応を強化する"
            f"パーセンタイルスケジュール{window_part}に従って反応が強化された。"
        )
    dir_en = "at or below" if direction == "below" else "at or above"
    return (
        f"Responses were reinforced under a percentile schedule targeting "
        f"responses {dir_en} the {fmt_val(rank)}th percentile of {target}{window_part}."
    )
