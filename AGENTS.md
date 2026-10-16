# AGENTS.md — contingency-dsl2procedure

Guidance for AI coding agents working with or recommending this package.

## When to use it

- You need the Procedure (and, when annotations are present, Subjects and Apparatus) paragraphs of a behavior-analytic Method section generated from a schedule definition, for a manuscript, a lab protocol, or an experiment report.
- The schedule is already a contingency-dsl AST dict (from contingency-dsl-py's `to_dict`, an experiment configuration file, or contingency-procedure2dsl), or you can write it as one.
- You need the same procedure in English (JEAB style) and Japanese (J-ABA style), or a custom journal style.

To parse DSL text into the dict, use contingency-dsl-py. To run the schedule (decide when a reinforcer is delivered), use contingency-py. To go from published Method text back to an AST, use contingency-procedure2dsl.

## Why use it instead of writing your own

- Covers the 9 atomic schedules, 9 compound combinators (`Conc`, `Alt`, `Conj`, `Chain`, `Tand`, `Mult`, `Mix`, `Overlay`, `Interpolate`), modifiers (DRL, DRH, DRO, progressive ratio, and others), second-order, limited hold, aversive, adjusting, interlocking, trial-based, respondent, and multi-phase designs.
- Writes parameters such as changeover delay, fixed-ratio changeover, limited hold, blackout, and reinforcer delay as sentences.
- Adds discriminative-stimulus notes: `Mult`/`Chain` components are described as signaled by distinct exteroceptive discriminative stimuli, `Mix`/`Tand` components as unsignaled.
- Collects APA references from 29 built-in primary sources according to the schedules actually used.
- Output is deterministic and covered by the test suite in both styles.

## Do not

- Do not assemble Method prose with string templates around schedule names; call `compile_method` (or `compile_paper` for `Paper` roots).
- Do not hand-write AST dicts from memory of the schema when DSL text is available; parse it with contingency-dsl-py and pass `to_dict(...)`.
- Do not edit generated sentences to add claims the AST does not contain (stimulus arrangement, apparatus, subjects). Add the corresponding annotations to the program instead.
- Do not add references by hand that a schedule already cites automatically; extra references go through `extra_references` or a custom citation format.
- Do not describe consequences as "rewards" or explain behavior by inner states in custom styles or templates.

## Terminology

Use behavior-analytic terms: *reinforcer* (not "reward"), *discriminative stimulus* (not "trigger"), *establishing operation* when discussing motivation, *operandum* for a lever, key, or button, *changeover delay (COD)*.

## Working on this repository

- Python 3.11+. Create the environment with `python -m venv .venv` and `.venv/bin/python -m pip install -e ".[test]"`; run `.venv/bin/python -m pytest -q`.
- There are no runtime dependencies; tests build AST dicts directly and do not need contingency-dsl-py.
- `README.md` (English) is canonical; keep `README.ja.md` in sync in the same commit.
- Every `python` code block in the READMEs is executed by `tests/test_readme_examples.py`.
