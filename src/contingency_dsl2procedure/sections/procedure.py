"""Procedure section generator.

Schedule description is delegated to ``visitors/`` (one module per AST node
type, plus a respondent module). This module handles:

  - ``render_procedure()``: orchestration (schedule + params + annotations)
  - Program-level annotation extraction across the JEAB categories
    (Subjects / Apparatus / Procedure(stimulus / temporal / trial-structure
    / context) / Measurement / extensions)
  - Schedule-level annotation rendering via ``describe_annotations``
  - Phase / PhaseSequence narrative generation
"""

from __future__ import annotations

from ..ast_types import (
    PhaseNode,
    PhaseSequenceNode,
    ProgramNode,
    ScheduleNode,
)
from ..references import ReferenceCollector
from ..style import JEAB, Style
from .annotation_expander import expand_bundled_annotations
from .visitors import describe_schedule
from .visitors._common import (
    describe_annotations,
    fmt_val,
    format_component,
    format_duration,
    humanize,
)


def _program_annotations(program: ProgramNode) -> list[dict]:
    """Return program_annotations with bundled shapes expanded."""
    return expand_bundled_annotations(
        list(program.get("program_annotations", []) or [])
    )


def render_procedure(
    program: ProgramNode,
    style: Style = JEAB,
    refs: ReferenceCollector | None = None,
) -> str:
    """Generate the Procedure subsection.

    Accepts any of ProgramNode, PhaseSequenceNode, or a dict that contains
    a ``phases`` key (interpreted as a PhaseSequence). Experiment / Paper
    wrappers are unwrapped by the caller before reaching this function.
    """
    if not isinstance(program, dict):
        return ""

    node_type = program.get("type", "")
    if node_type == "PhaseSequence" or "phases" in program:
        return _render_phase_sequence(program, style, refs)

    return _render_program(program, style, refs)


def _collect_bindings(program: ProgramNode) -> dict[str, dict]:
    """Extract ``{name: ScheduleExpr}`` map from a Program's bindings."""
    out: dict[str, dict] = {}
    for b in program.get("bindings", []) or []:
        name = b.get("name")
        value = b.get("value")
        if isinstance(name, str) and isinstance(value, dict):
            out[name] = value
    return out


# --- Single-schedule Program -------------------------------------------------

def _render_program(
    program: ProgramNode, style: Style, refs: ReferenceCollector | None,
) -> str:
    schedule = program.get("schedule", {})
    if not schedule:
        return ""

    bindings = _collect_bindings(program)

    sentences: list[str] = []

    # 1. Core schedule description (delegated to visitors)
    desc = describe_schedule(
        schedule, style=style, refs=refs,
        first_mention=True, bindings=bindings,
    )
    if desc:
        sentences.append(desc)

    # 2. Program-level param_decls
    for pd in program.get("param_decls", []) or []:
        s = _describe_param_decl(pd, style)
        if s:
            sentences.append(s)

    # 3. Schedule-level annotations (attached to the root schedule node)
    sentences.extend(describe_annotations(schedule, style=style))

    # 4. Per-component details derived from program-level annotations
    sentences.extend(_describe_components(program, style, refs))

    # 5. Temporal parameters from procedure-temporal annotations
    sentences.extend(_describe_temporal(program, style, refs))

    # 6. Session termination / stability criteria
    sentences.extend(_describe_measurement(program, style, refs))

    # 7. Trial structure (procedure-trial-structure)
    sentences.extend(_describe_trial_structure(program, style, refs))

    # 8. Context (procedure-context)
    sentences.extend(_describe_context(program, style))

    # 9. Composed-layer annotations (avoidance / omission)
    sentences.extend(_describe_composed(program, style))

    # 10. Stimulus-classes / training / testing (Tier-B stimulus equivalence)
    sentences.extend(_describe_stimulus_equivalence(program, style))

    # 11. Shaping procedure declaration (procedure annotation with positional=shape)
    sentences.extend(_describe_shaping(program, style, refs))

    return " ".join(sentences)


# --- PhaseSequence -----------------------------------------------------------

def _render_phase_sequence(
    ps: PhaseSequenceNode, style: Style, refs: ReferenceCollector | None,
) -> str:
    sentences: list[str] = []
    phases = ps.get("phases", []) or []

    # Shared annotations and param_decls carry across all phases.
    shared_anns = expand_bundled_annotations(
        list(ps.get("shared_annotations", []) or [])
    )
    shared_decls = ps.get("shared_param_decls", []) or []

    # Render shared temporal/measurement annotations once up front.
    pseudo_program: dict = {
        "program_annotations": shared_anns,
        "param_decls": shared_decls,
    }
    sentences.extend(_describe_temporal(pseudo_program, style, refs))
    sentences.extend(_describe_measurement(pseudo_program, style, refs))
    sentences.extend(_describe_trial_structure(pseudo_program, style, refs))
    sentences.extend(_describe_context(pseudo_program, style))
    sentences.extend(_describe_components(pseudo_program, style, refs))
    sentences.extend(_describe_composed(pseudo_program, style))

    # Narrate each phase. PhaseSequence bindings live on each Phase
    # individually; we expose the outer bindings map from the pseudo
    # program so IdentifierRef inside a phase can still resolve.
    ps_bindings: dict[str, dict] = {}
    for ph in phases:
        if not isinstance(ph, dict):
            continue
        for b in ph.get("bindings", []) or []:
            nm = b.get("name")
            val = b.get("value")
            if isinstance(nm, str) and isinstance(val, dict):
                ps_bindings.setdefault(nm, val)

    for idx, phase in enumerate(phases):
        sentences.append(_describe_phase(phase, idx, style, refs, ps_bindings))

    return " ".join([s for s in sentences if s])


def _describe_phase(
    phase: PhaseNode, index: int, style: Style,
    refs: ReferenceCollector | None,
    bindings: dict[str, dict] | None = None,
) -> str:
    label = phase.get("label", f"Phase {index + 1}")
    schedule: ScheduleNode | None = phase.get("schedule")

    parts: list[str] = []
    if style.locale == "ja":
        parts.append(f"【{label}】")
    else:
        parts.append(f"In the {label} phase,")

    if schedule is None:
        if style.locale == "ja":
            parts.append("本フェーズではスケジュールは提示されなかった。")
        else:
            parts.append("no schedule was in effect.")
    else:
        desc = describe_schedule(
            schedule, style=style, refs=refs,
            first_mention=(index == 0), bindings=bindings,
        )
        if desc:
            # Strip leading style framing so it reads naturally after "In the X phase,"
            parts.append(desc)

    # Phase-level annotations
    anns_sentences = []
    for ann in phase.get("phase_annotations", []) or []:
        from .visitors._common import _render_schedule_annotation
        s = _render_schedule_annotation(ann, style)
        if s:
            anns_sentences.append(s)
    if anns_sentences:
        parts.extend(anns_sentences)

    # Phase termination criterion
    crit = phase.get("criterion")
    if crit:
        parts.append(_render_criterion(crit, style))

    return " ".join(parts).strip()


def _render_criterion(crit: dict, style: Style) -> str:
    t = crit.get("type", "")
    if t == "Stability":
        window = crit.get("window_sessions")
        pct = crit.get("max_change_pct")
        min_sess = crit.get("min_sessions")
        method = crit.get("method")
        measure = crit.get("measure", "rate")
        measure_labels = {
            "rate": ("response rates", "反応率"),
            "reinforcers": ("reinforcement rates", "強化率"),
            "iri": ("interresponse times", "反応間間隔"),
            "latency": ("latencies", "潜時"),
        }
        en_m, ja_m = measure_labels.get(measure, (measure, measure))
        if window is not None and pct is not None:
            if style.locale == "ja":
                return (
                    f"本フェーズは直近{int(window)}セッションの{ja_m}の変動が"
                    f"{fmt_val(pct)}%以内となった時点で終了した。"
                )
            return (
                f"The phase continued until {en_m} varied by no more than "
                f"{fmt_val(pct)}% across {int(window)} consecutive sessions."
            )
        # Alternative shape: visual / custom stability with a min_sessions guard.
        parts_en: list[str] = [
            f"The phase terminated when stability of {en_m} was reached"
        ]
        parts_ja: list[str] = [f"本フェーズは{ja_m}が安定した時点で終了した"]
        if method:
            parts_en.append(f"(method: {method})")
            parts_ja.append(f"（判定方法: {method}）")
        if min_sess is not None:
            parts_en.append(f"after a minimum of {int(min_sess)} sessions")
            parts_ja.append(f"（最低{int(min_sess)}セッション）")
        if style.locale == "ja":
            return "".join(parts_ja) + "。"
        return " ".join(parts_en) + "."
    if t == "FixedSessions":
        n = crit.get("count", 0)
        if style.locale == "ja":
            return f"本フェーズは{int(n)}セッション実施した。"
        return f"This phase lasted {int(n)} sessions."
    if t == "PerformanceCriterion":
        measure = crit.get("measure", "rate")
        threshold = crit.get("threshold")
        op = crit.get("op", "<")
        if style.locale == "ja":
            op_ja = {"<": "未満", "<=": "以下", ">": "超", ">=": "以上"}.get(op, op)
            return f"本フェーズは{measure}が{fmt_val(threshold)}{op_ja}となった時点で終了した。"
        return (
            f"The phase terminated when {measure} {op} {fmt_val(threshold)}."
        )
    if t == "CumulativeReinforcements":
        n = crit.get("count", 0)
        if style.locale == "ja":
            return f"累積強化子数が{int(n)}に達した時点で本フェーズを終了した。"
        return (
            f"The phase terminated after {int(n)} cumulative reinforcers."
        )
    if t == "ExperimenterJudgment":
        if style.locale == "ja":
            return "本フェーズの終了は実験者の判断による。"
        return "Phase termination was at the experimenter's discretion."
    return ""


# === Schedule / program params ==============================================

def _describe_param_decl(pd: dict, style: Style) -> str:
    name = pd.get("name", "")
    value = pd.get("value", 0)
    unit = pd.get("time_unit", "s")

    if name == "RD":
        dur = format_duration(value, unit, style)
        if style.locale == "ja":
            return f"スケジュール要件充足から強化子呈示までに{dur}の遅延が課された。"
        return (
            f"A {dur} delay was imposed between the response that "
            f"completed the schedule requirement and reinforcer delivery."
        )

    if name == "FRCO":
        count = fmt_val(value)
        if style.locale == "ja":
            return f"{count}反応の固定比率切替が設定された。"
        return f"A {count}-response fixed-ratio changeover was in effect."

    dur = format_duration(value, unit, style)
    labels = {
        "COD": ("changeover delay", "切替遅延"),
        "LH": ("limited hold", "リミテッドホールド"),
        "BO": ("blackout", "ブラックアウト"),
    }
    en_label, ja_label = labels.get(name, (name, name))

    if style.locale == "ja":
        return f"{dur}の{ja_label}が設定された。"
    return f"A {dur} {en_label} was in effect."


# === Annotation-based descriptions =========================================

def _describe_components(
    program: ProgramNode, style: Style, refs: ReferenceCollector | None,
) -> list[str]:
    sentences: list[str] = []
    operanda: list[dict] = []
    reinforcer = ""
    punisher_params: list[dict] = []
    sd_map: dict[int, str] = {}
    program_sds: list[str] = []

    for ann in _program_annotations(program):
        kw = ann.get("keyword", "")
        params = ann.get("params", {}) or {}
        positional = ann.get("positional")
        if kw == "operandum":
            operanda.append({"name": positional or "", **params})
        elif kw in ("reinforcer", "consequentStimulus"):
            reinforcer = str(positional or "")
        elif kw == "punisher":
            punisher_params.append({"name": positional or "", **params})
        elif kw == "sd":
            comp = params.get("component")
            if comp is not None:
                sd_map[int(comp)] = str(positional or "")
            elif positional:
                program_sds.append(str(positional))

    if reinforcer:
        if style.locale == "ja":
            sentences.append(f"強化子として{reinforcer}を使用した。")
        else:
            sentences.append(f"Reinforcement consisted of {reinforcer} delivery.")

    if punisher_params:
        names = [humanize(p.get("name", "")) for p in punisher_params]
        if style.locale == "ja":
            sentences.append(f"罰刺激として{'、'.join(names)}を使用した。")
        else:
            if len(names) == 1:
                sentences.append(f"{names[0]} served as the punisher.")
            else:
                items = ", ".join(names[:-1]) + f", and {names[-1]}"
                sentences.append(f"{items} served as punishers.")

    # Discriminative stimuli not tied to a component: one sentence each, in
    # annotation order, so the reader's "in the presence of X" form recovers
    # them in the same order.
    for sd in program_sds:
        if style.locale == "ja":
            sentences.append(f"反応は（{humanize(sd)}点灯時）に記録した。")
        else:
            sentences.append(
                f"Responding was recorded in the presence of {humanize(sd)}."
            )

    schedule = program.get("schedule", {})
    if operanda and schedule.get("type") == "Compound":
        components = schedule.get("components", []) or []
        for op in operanda:
            comp_idx = op.get("component")
            if comp_idx is not None and 0 < comp_idx <= len(components):
                comp_sched = components[comp_idx - 1]
                sched_name = format_component(comp_sched, style=style, first_mention=False)
                op_name = humanize(op.get("name", ""))
                sd = humanize(sd_map.get(comp_idx, ""))
                if style.locale == "ja":
                    sd_part = f"（{sd}点灯時）" if sd else ""
                    sentences.append(
                        f"{op_name}への反応は{sched_name}スケジュール{sd_part}"
                        f"に従って強化された。"
                    )
                else:
                    sd_part = f" in the presence of {sd}" if sd else ""
                    sentences.append(
                        f"Responses on the {op_name} were reinforced "
                        f"according to a {sched_name} schedule{sd_part}."
                    )

    return sentences


def _describe_temporal(
    program: ProgramNode, style: Style, refs: ReferenceCollector | None,
) -> list[str]:
    sentences: list[str] = []

    for ann in _program_annotations(program):
        kw = ann.get("keyword", "")
        if kw == "algorithm":
            sentences.append(_render_algorithm(ann, style, refs))
        elif kw == "warmup":
            sentences.append(_render_warmup(ann, style))
        elif kw == "warmup_exclude":
            sentences.append(_render_warmup_exclude(ann, style))
        elif kw == "clock":
            sentences.append(_render_clock(ann, style))
        elif kw == "iti":
            sentences.append(_render_iti_annotation(ann, style))
        elif kw == "cs_interval":
            sentences.append(_render_cs_interval(ann, style))
        elif kw == "iri_window":
            sentences.append(_render_iri_window(ann, style))

    return [s for s in sentences if s]


def _render_warmup_exclude(ann: dict, style: Style) -> str:
    params = ann.get("params", {}) or {}
    duration = params.get("duration") or ann.get("positional")
    if duration is None:
        return ""
    if isinstance(duration, dict):
        dur_str = format_duration(
            duration.get("value", 0),
            duration.get("time_unit") or duration.get("unit", "s"),
            style,
        )
    else:
        dur_str = format_duration(float(duration), "s", style)
    if style.locale == "ja":
        return f"各セッションの最初の{dur_str}は解析から除外した。"
    return (
        f"Data from the first {dur_str} of each session were excluded "
        f"from analysis."
    )


def _render_iri_window(ann: dict, style: Style) -> str:
    params = ann.get("params", {}) or {}
    value = params.get("value") or params.get("duration") or ann.get("positional")
    unit = params.get("time_unit") or params.get("unit") or "s"
    if value is None:
        return ""
    if isinstance(value, dict):
        dur_str = format_duration(
            value.get("value", 0),
            value.get("time_unit") or value.get("unit", "s"),
            style,
        )
    else:
        dur_str = format_duration(float(value), unit, style)
    if style.locale == "ja":
        return f"反応間間隔は{dur_str}のウィンドウで集計した。"
    return f"Inter-response times were summarised over a {dur_str} window."


def _render_algorithm(
    ann: dict, style: Style, refs: ReferenceCollector | None,
) -> str:
    name = str(ann.get("positional", "") or "")
    params = ann.get("params", {}) or {}
    n = params.get("n")
    if name.lower() in ("fleshler-hoffman", "fleshler_hoffman"):
        ref = refs.cite("fleshler_hoffman_1962") if refs is not None else None
        n_part_en = f" with {int(n)} intervals" if n else ""
        n_part_ja = f"（N={int(n)}）" if n else ""
        cite = ref.to_inline() if ref else "Fleshler and Hoffman (1962)"
        if style.locale == "ja":
            return f"変動スケジュールの値は{cite}の数列{n_part_ja}から導出した。"
        return (
            f"Variable-schedule values were derived from the progression "
            f"described by {cite}{n_part_en}."
        )
    return ""


def _render_warmup(ann: dict, style: Style) -> str:
    params = ann.get("params", {}) or {}
    dur = params.get("duration")
    if dur is None:
        return ""
    if isinstance(dur, dict):
        dur_val = dur.get("value", 0)
        dur_unit = dur.get("time_unit", "s")
    else:
        dur_val = float(dur)
        dur_unit = params.get("time_unit", "s")
    dur_str = format_duration(dur_val, dur_unit, style)
    if style.locale == "ja":
        return f"各セッション開始時に{dur_str}のウォームアップ期間を設けた。"
    return f"A {dur_str} warm-up period preceded each session."


def _render_clock(ann: dict, style: Style) -> str:
    unit = (ann.get("params") or {}).get("unit")
    if not unit:
        return ""
    if style.locale == "ja":
        return f"セッションの時間単位は {unit} であった。"
    return f"Session time was recorded in {unit}."


def _render_iti_annotation(ann: dict, style: Style) -> str:
    params = ann.get("params", {}) or {}
    dist = params.get("distribution") or ann.get("positional")
    mean = params.get("mean")
    if not dist:
        return ""
    if isinstance(mean, dict):
        mean_val = mean.get("value", 0)
        mean_unit = mean.get("time_unit") or mean.get("unit") or "s"
    elif mean is not None:
        mean_val = float(mean)
        mean_unit = "s"
    else:
        mean_val = None
        mean_unit = "s"
    mean_str = format_duration(mean_val, mean_unit, style) if mean_val else ""
    if style.locale == "ja":
        dist_ja = {"fixed": "固定", "uniform": "一様", "exponential": "指数"}.get(
            str(dist), str(dist)
        )
        return (
            f"試行間間隔は{dist_ja}分布に従った"
            f"（平均{mean_str}）。" if mean_str else f"試行間間隔は{dist_ja}分布に従った。"
        )
    return (
        f"The inter-trial interval followed a {dist} distribution "
        f"(mean {mean_str})." if mean_str else f"The inter-trial interval followed a {dist} distribution."
    )


def _render_cs_interval(ann: dict, style: Style) -> str:
    params = ann.get("params", {}) or {}
    val = params.get("value", ann.get("positional"))
    unit = params.get("time_unit", params.get("unit", "s"))
    if val is None:
        return ""
    dur = format_duration(float(val), unit, style)
    if style.locale == "ja":
        return f"CS-US 間隔は{dur}であった。"
    return f"The CS-US interval was {dur}."


def _describe_measurement(
    program: ProgramNode, style: Style, refs: ReferenceCollector | None,
) -> list[str]:
    sentences: list[str] = []

    for ann in _program_annotations(program):
        kw = ann.get("keyword", "")
        params = ann.get("params", {}) or {}
        if kw == "session_end":
            sentences.append(_render_session_end(params, style))
        elif kw == "steady_state":
            sentences.append(_render_steady_state(params, style))
        elif kw == "baseline":
            sentences.append(_render_baseline(params, style))
        elif kw == "dependent_measure":
            sentences.append(_render_dependent_measure(params, style))
        elif kw == "microstructure":
            sentences.append(_render_microstructure(params, ann, style))
        elif kw == "logging":
            sentences.append(_render_logging(params, ann, style))
        elif kw == "phase_end":
            sentences.append(_render_phase_end(params, style))
        elif kw == "probe_policy":
            sentences.append(_render_probe_policy(params, style))
        elif kw == "training_volume":
            sentences.append(_render_training_volume(params, style))

    return [s for s in sentences if s]


def _render_microstructure(params: dict, ann: dict, style: Style) -> str:
    measures = params.get("measures") or params.get("variables") or []
    positional = ann.get("positional")
    if not measures and isinstance(positional, list):
        measures = positional
    if not measures and isinstance(positional, str):
        measures = [positional]
    if not measures:
        return ""
    if style.locale == "ja":
        names = "、".join(str(m) for m in measures)
        return f"応答ミクロ構造として{names}を記録した。"
    if len(measures) == 1:
        return f"Response microstructure was characterised by {measures[0]}."
    items = ", ".join(str(m) for m in measures[:-1]) + f", and {measures[-1]}"
    return f"Response microstructure was characterised by {items}."


def _render_logging(params: dict, ann: dict, style: Style) -> str:
    rate = params.get("rate")
    resolution = params.get("resolution")
    target = params.get("events") or ann.get("positional")
    details: list[str] = []
    if target:
        if isinstance(target, list):
            details.append(("イベント: " if style.locale == "ja" else "events: ")
                            + ", ".join(str(t) for t in target))
        else:
            details.append(("イベント: " if style.locale == "ja" else "events: ") + str(target))
    if resolution is not None:
        if isinstance(resolution, dict):
            r = format_duration(
                resolution.get("value", 0),
                resolution.get("time_unit") or resolution.get("unit", "s"),
                style,
            )
        else:
            r = format_duration(float(resolution), "ms", style)
        details.append(("分解能 " if style.locale == "ja" else "resolution ") + r)
    if rate is not None:
        details.append(
            (f"サンプリング {rate} Hz" if style.locale == "ja" else f"sampled at {rate} Hz")
        )
    if not details:
        return ""
    joined = "、".join(details) if style.locale == "ja" else "; ".join(details)
    if style.locale == "ja":
        return f"測定ロギング: {joined}。"
    return f"Measurement logging used {joined}."


def _render_phase_end(params: dict, style: Style) -> str:
    rule = params.get("rule", "")
    sessions = params.get("sessions")
    if rule and sessions is not None:
        if style.locale == "ja":
            return (
                f"フェーズは{int(sessions)}セッション後の{rule}条件で終了した。"
            )
        return (
            f"Each phase terminated when the {rule} criterion was met after "
            f"{int(sessions)} sessions."
        )
    if sessions is not None:
        if style.locale == "ja":
            return f"フェーズは{int(sessions)}セッションで終了した。"
        return f"Each phase terminated after {int(sessions)} sessions."
    if rule:
        if style.locale == "ja":
            return f"フェーズは{rule}条件で終了した。"
        return f"Each phase terminated upon the {rule} criterion."
    return ""


def _render_probe_policy(params: dict, style: Style) -> str:
    ratio = params.get("probe_ratio") or params.get("ratio")
    schedule = params.get("schedule") or params.get("insertion")
    parts: list[str] = []
    if ratio is not None:
        parts.append(
            (f"確率 {ratio}" if style.locale == "ja" else f"probe ratio {ratio}")
        )
    if schedule:
        parts.append(
            (f"挿入方式 {schedule}" if style.locale == "ja" else f"insertion pattern {schedule}")
        )
    if not parts:
        return ""
    joined = "、".join(parts) if style.locale == "ja" else "; ".join(parts)
    if style.locale == "ja":
        return f"プローブ試行の挿入方針は{joined}であった。"
    return f"Probe trials were inserted according to {joined}."


def _render_training_volume(params: dict, style: Style) -> str:
    sessions = params.get("sessions")
    trials_per_session = params.get("trials_per_session") or params.get("trials")
    total_trials = params.get("total_trials")
    pieces_en: list[str] = []
    pieces_ja: list[str] = []
    if sessions is not None:
        pieces_en.append(f"{int(sessions)} sessions")
        pieces_ja.append(f"{int(sessions)}セッション")
    if trials_per_session is not None:
        pieces_en.append(f"{int(trials_per_session)} trials per session")
        pieces_ja.append(f"1セッション{int(trials_per_session)}試行")
    if total_trials is not None:
        pieces_en.append(f"{int(total_trials)} trials overall")
        pieces_ja.append(f"総計{int(total_trials)}試行")
    if not pieces_en:
        return ""
    if style.locale == "ja":
        return f"訓練量は{'、'.join(pieces_ja)}であった。"
    return "Training consisted of " + ", ".join(pieces_en) + "."


def _render_session_end(params: dict, style: Style) -> str:
    rule = params.get("rule", "")
    time_info = params.get("time")
    reinforcers = params.get("reinforcers")

    time_str = ""
    if time_info:
        if isinstance(time_info, dict):
            raw_val = time_info.get("value", 0)
            u = time_info.get("time_unit", "s")
        else:
            raw_val = float(time_info)
            u = "s"
        val_s = _to_seconds(raw_val, u)
        display_val, display_unit = _humanize_duration(val_s)
        time_str = f"{fmt_val(display_val)} {display_unit}"

    if rule == "first" and time_str and reinforcers:
        r = int(reinforcers)
        if style.locale == "ja":
            return f"セッションは{time_str}経過または{r}回の強化子呈示のいずれか早い方で終了した。"
        return (
            f"Sessions terminated after {time_str} or "
            f"{r} reinforcer deliveries, whichever occurred first."
        )
    if rule == "time_only" and time_str:
        if style.locale == "ja":
            return f"セッションは{time_str}経過後に終了した。"
        return f"Sessions terminated after {time_str}."
    if rule == "reinforcers_only" and reinforcers:
        r = int(reinforcers)
        if style.locale == "ja":
            return f"セッションは{r}回の強化子呈示後に終了した。"
        return f"Sessions terminated after {r} reinforcer deliveries."
    return ""


def _to_seconds(value: float, unit: str) -> float:
    if unit == "ms":
        return value / 1000
    if unit == "min":
        return value * 60
    return value


def _humanize_duration(seconds: float) -> tuple[float, str]:
    if seconds >= 60 and seconds % 60 == 0:
        return seconds / 60, "min"
    if seconds < 1 and seconds > 0:
        return seconds * 1000, "ms"
    return seconds, "s"


def _render_steady_state(params: dict, style: Style) -> str:
    window = params.get("window_sessions")
    pct = params.get("max_change_pct")
    measure = params.get("measure", "rate")
    min_sess = params.get("min_sessions")

    if window is None or pct is None:
        return ""

    measure_labels = {
        "rate": ("response rates", "反応率"),
        "reinforcers": ("reinforcement rates", "強化率"),
        "iri": ("interresponse times", "反応間間隔"),
        "latency": ("latencies", "潜時"),
    }
    en_measure, ja_measure = measure_labels.get(measure, (measure, measure))
    min_part_en = f" (minimum {int(min_sess)} sessions)" if min_sess else ""
    min_part_ja = f"（最低{int(min_sess)}セッション）" if min_sess else ""

    if style.locale == "ja":
        return (
            f"安定性は直近{int(window)}セッションの{ja_measure}の変動が"
            f"{int(pct)}%以内であることを基準とした{min_part_ja}。"
        )
    return (
        f"Stability was assessed over the last {int(window)} sessions, "
        f"with a criterion of no more than {int(pct)}% variation in "
        f"{en_measure}{min_part_en}."
    )


def _render_baseline(params: dict, style: Style) -> str:
    pre = params.get("pre_training_sessions")
    if pre is None:
        return ""
    if style.locale == "ja":
        return f"実験開始前に{int(pre)}セッションの事前訓練を実施した。"
    return f"Prior to the experiment, {int(pre)} pretraining sessions were conducted."


def _render_dependent_measure(params: dict, style: Style) -> str:
    variables = params.get("variables") or []
    if not variables:
        return ""
    if style.locale == "ja":
        names = "、".join(str(v) for v in variables)
        return f"主要従属変数は{names}であった。"
    if len(variables) == 1:
        return f"The primary dependent measure was {variables[0]}."
    items = ", ".join(str(v) for v in variables[:-1]) + f", and {variables[-1]}"
    return f"Dependent measures included {items}."


def _describe_trial_structure(
    program: ProgramNode, style: Style, refs: ReferenceCollector | None,
) -> list[str]:
    sentences: list[str] = []
    for ann in _program_annotations(program):
        kw = ann.get("keyword", "")
        if kw == "trial_mix":
            sentences.append(_render_trial_mix(ann.get("params", {}) or {}, style))
        elif kw == "session":
            sentences.append(_render_session_struct(ann.get("params", {}) or {}, style))
    return [s for s in sentences if s]


def _render_trial_mix(params: dict, style: Style) -> str:
    kind = params.get("type", "")
    if not kind:
        return ""
    if style.locale == "ja":
        ja = {
            "peak": "ピーク",
            "reinstatement": "再燃",
            "temporal_bisection": "時間弁別",
        }.get(kind, kind)
        return f"試行は{ja}手続きの構成で呈示された。"
    label = {
        "peak": "peak procedure",
        "reinstatement": "reinstatement procedure",
        "temporal_bisection": "temporal bisection procedure",
    }.get(kind, kind)
    return f"Trials were organized according to a {label}."


def _render_session_struct(params: dict, style: Style) -> str:
    trials = params.get("trials")
    blocks = params.get("blocks")
    block_size = params.get("block_size")
    if trials is None and blocks is None:
        return ""
    if blocks and block_size:
        if style.locale == "ja":
            return (
                f"各セッションは{int(blocks)}ブロック×{int(block_size)}試行で構成された。"
            )
        return (
            f"Each session consisted of {int(blocks)} blocks of "
            f"{int(block_size)} trials."
        )
    if trials:
        if style.locale == "ja":
            return f"各セッションは{int(trials)}試行で構成された。"
        return f"Each session consisted of {int(trials)} trials."
    return ""


def _describe_composed(program: ProgramNode, style: Style) -> list[str]:
    sentences: list[str] = []
    for ann in _program_annotations(program):
        kw = ann.get("keyword", "")
        params = ann.get("params", {}) or {}
        if kw == "avoidance":
            sentences.append(_render_avoidance(params, ann, style))
        elif kw == "omission":
            sentences.append(_render_omission(params, ann, style))
    return [s for s in sentences if s]


def _render_avoidance(params: dict, ann: dict, style: Style) -> str:
    scheme = params.get("scheme") or ann.get("positional") or ""
    delivery = params.get("delivery", "")
    csus = params.get("cs_us_interval") or params.get("csusInterval")
    extras: list[str] = []
    if delivery:
        extras.append(
            (f"配信 {delivery}" if style.locale == "ja"
             else f"delivery: {delivery}")
        )
    if isinstance(csus, dict):
        dur = format_duration(
            csus.get("value", 0),
            csus.get("time_unit") or csus.get("unit", "s"),
            style,
        )
        extras.append(
            (f"CS-US 間隔 {dur}" if style.locale == "ja"
             else f"CS-US interval {dur}")
        )
    tail_ja = "（" + "、".join(extras) + "）" if extras else ""
    tail_en = f" ({'; '.join(extras)})" if extras else ""
    scheme_str = str(scheme) if scheme else ""
    if style.locale == "ja":
        body = (
            f"回避手続き（{scheme_str}）" if scheme_str else "回避手続き"
        )
        return f"{body}を実施した{tail_ja}。"
    body_en = (
        f"An avoidance procedure ({scheme_str})"
        if scheme_str
        else "An avoidance procedure"
    )
    return f"{body_en} was arranged{tail_en}."


def _render_omission(params: dict, ann: dict, style: Style) -> str:
    target = params.get("target") or ann.get("positional") or ""
    delivery = params.get("delivery", "")
    window = params.get("window")
    window_str = ""
    if isinstance(window, dict):
        window_str = format_duration(
            window.get("value", 0),
            window.get("time_unit") or window.get("unit", "s"),
            style,
        )
    if style.locale == "ja":
        pieces = ["オミッション手続きを実施した"]
        extras_ja: list[str] = []
        if target:
            extras_ja.append(f"対象: {target}")
        if delivery:
            extras_ja.append(f"配信: {delivery}")
        if window_str:
            extras_ja.append(f"ウィンドウ {window_str}")
        if extras_ja:
            pieces.append("（" + "、".join(extras_ja) + "）")
        return "".join(pieces) + "。"
    pieces_en = ["An omission procedure was arranged"]
    extras_en: list[str] = []
    if target:
        extras_en.append(f"target: {target}")
    if delivery:
        extras_en.append(f"delivery: {delivery}")
    if window_str:
        extras_en.append(f"response window {window_str}")
    if extras_en:
        pieces_en.append(" (" + "; ".join(extras_en) + ")")
    return "".join(pieces_en) + "."


def _describe_shaping(
    program: ProgramNode,
    style: Style,
    refs: ReferenceCollector | None,
) -> list[str]:
    sentences: list[str] = []
    for ann in _program_annotations(program):
        if ann.get("keyword") != "procedure":
            continue
        if ann.get("positional") != "shape":
            continue
        params = ann.get("params", {}) or {}
        target = params.get("target")
        method = params.get("method", "artful")
        approximations = params.get("approximations") or []
        if refs is not None:
            refs.cite_if_known("skinner_1953")
            if method == "percentile":
                refs.cite_if_known("galbicka_1994")
        if style.locale == "ja":
            parts = [
                "目標反応 " + (target or "未指定") + " を",
                {
                    "artful": "実験者の判断による",
                    "percentile": "パーセンタイル法による",
                    "staged": "段階的",
                }.get(method, method) + "シェイピングで形成した",
            ]
            if approximations:
                parts.append(
                    "（近似系列: "
                    + "→".join(str(a) for a in approximations)
                    + "）"
                )
            sentences.append("".join(parts) + "。")
        else:
            method_en = {
                "artful": "experimenter-directed successive-approximation",
                "percentile": "percentile-based",
                "staged": "staged",
            }.get(method, method)
            base = (
                f"The {target or 'target response'} was shaped via "
                f"{method_en} shaping."
            )
            if approximations:
                base = base.rstrip(".") + (
                    ". Approximations followed the sequence: "
                    + " → ".join(str(a) for a in approximations) + "."
                )
            sentences.append(base)
    return sentences


def _describe_stimulus_equivalence(
    program: ProgramNode,
    style: Style,
) -> list[str]:
    sentences: list[str] = []
    for ann in _program_annotations(program):
        if ann.get("keyword") == "stimulus_classes":
            s = _render_stimulus_classes(ann, style)
            if s:
                sentences.append(s)
    schedule = program.get("schedule", {}) or {}
    sentences.extend(_render_training_testing_from(schedule, style))
    return sentences


def _render_stimulus_classes(ann: dict, style: Style) -> str:
    params = ann.get("params", {}) or {}
    pos = ann.get("positional")
    if params:
        items = [f"{k}={v}" for k, v in params.items()]
        joined = "、".join(items) if style.locale == "ja" else "; ".join(items)
        if style.locale == "ja":
            return f"刺激クラスは {joined} として定義された。"
        return f"Stimulus classes were defined as {joined}."
    if pos is not None:
        if style.locale == "ja":
            return f"{pos} 個の刺激クラスを用いた。"
        return f"The procedure used {pos} stimulus classes."
    return ""


def _render_training_testing_from(
    schedule: dict, style: Style,
) -> list[str]:
    out: list[str] = []
    if not isinstance(schedule, dict):
        return out
    for ann in schedule.get("annotations", []) or []:
        kw = ann.get("keyword", "")
        params = ann.get("params", {}) or {}
        if kw == "training":
            out.append(_render_training_relation(params, style))
        elif kw == "testing":
            out.append(_render_testing_relation(params, style))
    return [s for s in out if s]


def _render_training_relation(params: dict, style: Style) -> str:
    relations = params.get("relations") or []
    criterion = params.get("criterion")
    consecutive = params.get("consecutive_blocks")
    extras_en: list[str] = []
    extras_ja: list[str] = []
    if criterion is not None:
        extras_en.append(f"criterion {criterion}% correct")
        extras_ja.append(f"基準正答率 {criterion}%")
    if consecutive is not None:
        extras_en.append(f"across {int(consecutive)} consecutive blocks")
        extras_ja.append(f"{int(consecutive)}ブロック連続")
    rel_en = ", ".join(str(r) for r in relations)
    rel_ja = "、".join(str(r) for r in relations)
    if style.locale == "ja":
        tail = (
            "（" + "、".join(extras_ja) + "）" if extras_ja else ""
        )
        return f"訓練段階では {rel_ja} 関係を訓練した{tail}。"
    plural = "s" if len(relations) != 1 else ""
    tail = " (" + "; ".join(extras_en) + ")" if extras_en else ""
    return (
        f"Training phases targeted the {rel_en} relation{plural}{tail}."
    )


def _render_testing_relation(params: dict, style: Style) -> str:
    relations = params.get("relations") or []
    probe_ratio = params.get("probe_ratio")
    rel_en = ", ".join(str(r) for r in relations)
    rel_ja = "、".join(str(r) for r in relations)
    extras_en = (
        f" (probe ratio {probe_ratio})" if probe_ratio is not None else ""
    )
    extras_ja = (
        f"（プローブ率 {probe_ratio}）" if probe_ratio is not None else ""
    )
    if style.locale == "ja":
        return f"テスト段階では {rel_ja} 関係をプローブした{extras_ja}。"
    plural = "s" if len(relations) != 1 else ""
    return (
        f"Test phases probed the {rel_en} relation{plural}{extras_en}."
    )


def _describe_context(program: ProgramNode, style: Style) -> list[str]:
    sentences: list[str] = []
    for ann in _program_annotations(program):
        if ann.get("keyword") == "context":
            pos = ann.get("positional")
            cues = (ann.get("params") or {}).get("cues")
            if style.locale == "ja":
                cue_part = f"（{cues}）" if cues else ""
                sentences.append(f"文脈{pos}{cue_part}で実施された。")
            else:
                cue_part = f" (cues: {cues})" if cues else ""
                sentences.append(
                    f"The procedure was conducted in context {pos}{cue_part}."
                )
    return sentences
