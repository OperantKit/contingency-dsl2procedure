# contingency-dsl2procedure

:jp: [日本語版 README](README.ja.md)

Compiler from [contingency-dsl](https://github.com/OperantKit/contingency-dsl) JSON AST to academic paper Method sections.

Zero external dependencies. Works with any parser that emits conformant `ast-schema.json`.

## Install

```bash
pip install git+https://github.com/OperantKit/contingency-dsl2procedure
```

## 30-second example

Compile `Conc(VI30s, VI60s, COD=2s)`, given as an AST dict, into a JEAB-style Procedure paragraph, list the references it cites, and render the same schedule in J-ABA style (Japanese):

```python
from contingency_dsl2procedure import compile_method

# Conc(VI30s, VI60s, COD=2s) as a contingency-dsl AST dict
ast = {
    "type": "Program",
    "param_decls": [],
    "bindings": [],
    "schedule": {
        "type": "Compound",
        "combinator": "Conc",
        "components": [
            {"type": "Atomic", "dist": "V", "domain": "I", "value": 30.0, "time_unit": "s"},
            {"type": "Atomic", "dist": "V", "domain": "I", "value": 60.0, "time_unit": "s"},
        ],
        "params": {"COD": {"value": 2.0, "time_unit": "s"}},
    },
}

method = compile_method(ast, style="jeab")
print(method.procedure)
# Responses were reinforced under a concurrent VI 30-s VI 60-s schedule. A 2-s changeover delay was in effect.
print([ref.key for ref in method.references])
# ['fleshler_hoffman_1962', 'herrnstein_1961']
print(compile_method(ast, style="jaba").procedure)
# 並立 VI 30-s VI 60-sスケジュールに従って反応が強化された。2-sの切替遅延が設定された。
```

`method.to_text()` renders the whole Method section (Subjects, Apparatus, Procedure, References) as Markdown. To write the schedule as text instead of a dict, parse it with [contingency-dsl-py](https://github.com/OperantKit/contingency-dsl-py) (`pip install contingency-dsl-py`): `to_dict(parse("Conc(VI30s, VI60s, COD=2s)"))` produces the dict above (plus an empty `program_annotations` list) and compiles to the same paragraph.

## Why not a 50-line hand-written generator?

A template such as `f"a {name} {value}-s schedule"` covers one atomic schedule; a Method section needs the following, and each item is implemented and tested here:

- **Schedule coverage.** All 9 atomic schedules (F/V/R × ratio/interval/time: FR, VR, RR, FI, VI, RI, FT, VT, RT), 9 compound combinators (`Conc`, `Alt`, `Conj`, `Chain`, `Tand`, `Mult`, `Mix`, `Overlay`, `Interpolate`), plus modifiers (DRL, DRH, DRO, progressive ratio, and others), second-order, limited hold, aversive (Sidman avoidance, discriminated avoidance, escape), adjusting and interlocking, trial-based (matching-to-sample, go/no-go), respondent procedures, and multi-phase designs.
- **Parameters in prose.** Changeover delay (`COD`), fixed-ratio changeover (`FRCO`), limited hold, blackout, and reinforcer delay are written as sentences rather than dropped.
- **Discriminative-stimulus notes.** `Mult` and `Chain` state that components were signaled by distinct exteroceptive discriminative stimuli; `Mix` and `Tand` state that they were not, so readers can tell the stimulus arrangement apart.
- **Automatic citations.** 29 built-in APA references (for example Fleshler & Hoffman, 1962, for VI/VR progressions and Herrnstein, 1961, for concurrent schedules) are collected from the schedules actually used and listed in `method.references`.
- **English and Japanese.** The `jeab` and `jaba` styles share one compiler; custom styles and citation formats can be registered with `register_style` and `register_citation_format`.
- **Round trip.** [contingency-procedure2dsl](https://github.com/OperantKit/contingency-procedure2dsl) extracts a schedule AST from this prose; for example, the paragraphs generated for `Mult(FR5, EXT)` and `Chain(FR10, FI30s)` are read back to the original schedule.

## Usage

```python
from contingency_dsl2procedure import compile_method

# Input: plain dict conforming to contingency-dsl/ast-schema.json
ast = {
    "type": "Program",
    "param_decls": [],
    "bindings": [],
    "schedule": {
        "type": "Compound",
        "combinator": "Conc",
        "components": [
            {"type": "Atomic", "dist": "V", "domain": "I", "value": 30.0, "time_unit": "s"},
            {"type": "Atomic", "dist": "V", "domain": "I", "value": 60.0, "time_unit": "s"},
        ],
    },
}

# JEAB (English, default)
method = compile_method(ast, style="jeab")
print(method.procedure)
# Responses were reinforced under a concurrent VI 30-s VI 60-s schedule.

# J-ABA (Japanese)
method_ja = compile_method(ast, style="jaba")
print(method_ja.procedure)
# 並立 VI 30-s VI 60-sスケジュールに従って反応が強化された。

# References are auto-collected
print(method.references)
# (Reference(key='fleshler_hoffman_1962', ...),)
```

The same compiler is available on the command line; `INPUT` is a JSON file or `-` for stdin:

```bash
contingency-dsl2procedure ast.json --style jaba --output method.md
```
