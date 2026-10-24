# contingency-dsl2procedure

:jp: [日本語版 README](README.ja.md)

contingency-dsl2procedure writes the Procedure paragraph of a Method section from a schedule of reinforcement, in the English style of the *Journal of the Experimental Analysis of Behavior* (JEAB) or in Japanese in the style of the Japanese Association for Behavior Analysis (J-ABA). When the schedule carries annotations, it also writes the Subjects and Apparatus paragraphs. It takes the parsed form of a [contingency-dsl](https://github.com/OperantKit/contingency-dsl) expression, so in [OperantKit](https://github.com/OperantKit) the expression that runs the session is the same one that produces its description.

**In short**

- The paragraph is generated from the schedule that was programmed, so parameters such as the changeover delay (COD) and the limited hold are stated, not forgotten.
- References are added for the procedures actually used, from a built-in list of 29 sources (for example Fleshler & Hoffman, 1962, for VI progressions).
- English and Japanese come from the same input.

## Installation

Python 3.11 or newer. The package is not on PyPI yet; install it from GitHub:

```bash
pip install git+https://github.com/OperantKit/contingency-dsl2procedure
```

It has no dependencies. To write schedules as text rather than as dictionaries, also install the parser [contingency-dsl-py](https://github.com/OperantKit/contingency-dsl-py): `pip install git+https://github.com/OperantKit/contingency-dsl-py`.

## Example

Compile `Conc(VI30s, VI60s, COD=2s)`, given as a parsed dictionary, into a JEAB-style paragraph, list the references it cites, and write the same schedule in J-ABA style:

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

`method.to_text()` returns the whole Method section as Markdown, with the References list:

```
## Method

### Procedure

Responses were reinforced under a concurrent VI 30-s VI 60-s schedule. A 2-s changeover delay was in effect.

### References

Fleshler, M., & Hoffman, H. S. (1962). A progression for generating variable-interval schedules. *Journal of the Experimental Analysis of Behavior*, *5*, 529-530. https://doi.org/10.1901/jeab.1962.5-529
Herrnstein, R. J. (1961). Relative and absolute strength of response as a function of frequency of reinforcement. *Journal of the Experimental Analysis of Behavior*, *4*, 267-272. https://doi.org/10.1901/jeab.1961.4-267
```

With contingency-dsl-py installed, `to_dict(parse("Conc(VI30s, VI60s, COD=2s)"))` produces the dictionary above (plus an empty `program_annotations` list) and compiles to the same paragraph.

## What it covers

- Atomic schedules (FR, VR, RR, FI, VI, RI, FT, VT, RT, and EXT/CRF), compound schedules (`Conc`, `Alt`, `Conj`, `Chain`, `Tand`, `Mult`, `Mix`, `Overlay`, `Interpolate`), DRL / DRH / DRO, progressive ratio, second-order schedules, limited hold, aversive procedures, adjusting and interlocking schedules, matching-to-sample and go/no-go, respondent procedures, and multi-phase designs.
- Changeover delay, fixed-ratio changeover, limited hold, blackout, and reinforcement delay are written as sentences.
- `Mult` and `Chain` components are described as signaled by distinct exteroceptive discriminative stimuli; `Mix` and `Tand` components as unsignaled.
- `compile_paper` handles a whole paper with several experiments. `register_style` and `register_citation_format` add your own journal style or citation format.

## Command line

The same compiler runs from the command line. The input is a JSON file with the parsed dictionary, or `-` for standard input:

```bash
contingency-dsl2procedure ast.json --style jaba --output method.md
```

`--heading-level` sets the Markdown heading depth, and `--all-experiments` renders every experiment of a paper instead of only the first.

## Limitations

- The input is the parsed dictionary. This package does not read schedule text; use contingency-dsl-py for that.
- Inside a compound schedule, a component that is a stateful schedule (adjusting, interlocking), an aversive procedure, or a name bound with `let` is left out of the sentence. For example, `Mult(Interlock(R0=300, T=10min), EXT)` gives "Responses were reinforced under a multiple  extinction schedule."
- It writes only what the expression and its annotations state. Anything else that belongs in the Method section has to be added by hand.

## For contributors

```bash
git clone https://github.com/OperantKit/contingency-dsl2procedure
cd contingency-dsl2procedure
python -m venv .venv
.venv/bin/python -m pip install -e ".[test]"
.venv/bin/python -m pytest -q
```

The tests build the dictionaries directly and do not need contingency-dsl-py. `tests/test_conformance_smoke.py` also compiles the [contingency-dsl](https://github.com/OperantKit/contingency-dsl) test cases when a contingency-dsl clone sits next to this one; otherwise it is skipped. Every `python` block in this README and in `README.ja.md` is run by `tests/test_readme_examples.py`. Notes for AI coding agents are in [AGENTS.md](AGENTS.md).

## References

- Fleshler, M., & Hoffman, H. S. (1962). A progression for generating variable-interval schedules. *Journal of the Experimental Analysis of Behavior*, 5(4), 529–530. https://doi.org/10.1901/jeab.1962.5-529

## Citation and license

Cite this package with [CITATION.cff](CITATION.cff). MIT License; see [LICENSE](LICENSE).
