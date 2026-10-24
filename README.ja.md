# contingency-dsl2procedure

:gb: [English README](README.md)

contingency-dsl2procedure は、強化スケジュールから方法セクション（Method 節）の Procedure の段落を書きます。英語は *Journal of the Experimental Analysis of Behavior*（JEAB）の書き方、日本語は日本行動分析学会（J-ABA）の書き方です。スケジュールにアノテーションがあれば、Subjects と Apparatus の段落も書きます。入力は [contingency-dsl](https://github.com/OperantKit/contingency-dsl) の式を構文解析した結果なので、[OperantKit](https://github.com/OperantKit) では、セッションを動かす式とその記述を生む式が同じものになります。

**要点**

- 段落は実際にプログラムしたスケジュールから作られるので、切替遅延（changeover delay, COD）や制限時間（limited hold）のようなパラメータが書き漏らされません。
- 使った手続きの文献が、組み込みの 29 件の一覧から自動で加わります（例: VI の間隔の数列には Fleshler & Hoffman, 1962）。
- 同じ入力から英語と日本語の両方を書けます。

## インストール

Python 3.11 以上が必要です。パッケージはまだ PyPI に登録されていないので、GitHub から入れます。

```bash
pip install git+https://github.com/OperantKit/contingency-dsl2procedure
```

依存パッケージはありません。スケジュールを辞書ではなくテキストで書くには、パーサ [contingency-dsl-py](https://github.com/OperantKit/contingency-dsl-py) も入れます: `pip install git+https://github.com/OperantKit/contingency-dsl-py`。

## 例

構文解析済みの辞書で与えた `Conc(VI30s, VI60s, COD=2s)` を JEAB の書き方の段落にし、引用する文献を一覧し、同じスケジュールを J-ABA の書き方で書きます。

```python
from contingency_dsl2procedure import compile_method

# Conc(VI30s, VI60s, COD=2s) を contingency-dsl の AST の dict で表したもの
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

`method.to_text()` は、文献の一覧を含む Method 節全体を Markdown で返します。

```
## Method

### Procedure

Responses were reinforced under a concurrent VI 30-s VI 60-s schedule. A 2-s changeover delay was in effect.

### References

Fleshler, M., & Hoffman, H. S. (1962). A progression for generating variable-interval schedules. *Journal of the Experimental Analysis of Behavior*, *5*, 529-530. https://doi.org/10.1901/jeab.1962.5-529
Herrnstein, R. J. (1961). Relative and absolute strength of response as a function of frequency of reinforcement. *Journal of the Experimental Analysis of Behavior*, *4*, 267-272. https://doi.org/10.1901/jeab.1961.4-267
```

contingency-dsl-py を入れてあれば、`to_dict(parse("Conc(VI30s, VI60s, COD=2s)"))` で上の辞書（と空の `program_annotations` の一覧）ができ、同じ段落になります。

## 書けるもの

- 単一のスケジュール（FR、VR、RR、FI、VI、RI、FT、VT、RT、および EXT/CRF）、複合スケジュール（`Conc`、`Alt`、`Conj`、`Chain`、`Tand`、`Mult`、`Mix`、`Overlay`、`Interpolate`）、DRL / DRH / DRO、累進比率、二次スケジュール、制限時間、嫌悪性の手続き、調整スケジュールと連動スケジュール、見本合わせと go/no-go、レスポンデントの手続き、複数フェーズのデザイン。
- 切替遅延、固定比率の切替、ブラックアウト、制限時間、強化遅延は文として書かれます。
- `Mult` と `Chain` の成分は、それぞれ異なる外受容性の弁別刺激で信号されたと書かれ、`Mix` と `Tand` の成分は信号されなかったと書かれます。
- `compile_paper` は複数の実験を含む論文全体を扱います。`register_style` と `register_citation_format` で、独自の雑誌の書き方や文献の形式を加えられます。

## コマンドライン

同じ処理をコマンドラインから実行できます。入力は構文解析済みの辞書を入れた JSON ファイルか、標準入力を表す `-` です。

```bash
contingency-dsl2procedure ast.json --style jaba --output method.md
```

`--heading-level` で Markdown の見出しの深さを、`--all-experiments` で論文の最初の実験だけでなく全実験を出力するよう指定できます。

## 制限

- 入力は構文解析済みの辞書です。このパッケージはスケジュールのテキストを読まないので、それには contingency-dsl-py を使います。
- 複合スケジュールの中で、状態を持つスケジュール（調整、連動）、嫌悪性の手続き、`let` で名前を付けたスケジュールが成分になっていると、その成分は文から抜け落ちます。例えば `Mult(Interlock(R0=300, T=10min), EXT)` からは「Responses were reinforced under a multiple  extinction schedule.」が出力されます。
- 書くのは、式とそのアノテーションに書かれていることだけです。Method 節に必要なそれ以外のことは、手で書き足す必要があります。

## 開発に参加する人へ

```bash
git clone https://github.com/OperantKit/contingency-dsl2procedure
cd contingency-dsl2procedure
python -m venv .venv
.venv/bin/python -m pip install -e ".[test]"
.venv/bin/python -m pytest -q
```

テストは辞書を直接組み立てるので、contingency-dsl-py は要りません。`tests/test_conformance_smoke.py` は、隣に [contingency-dsl](https://github.com/OperantKit/contingency-dsl) の clone があればそのテストケースも変換し、無ければ飛ばされます。この README と `README.md` の `python` ブロックは、すべて `tests/test_readme_examples.py` で実行されます。AI のコーディングエージェント向けの説明は [AGENTS.md](AGENTS.md) にあります。

## 参考文献

- Fleshler, M., & Hoffman, H. S. (1962). A progression for generating variable-interval schedules. *Journal of the Experimental Analysis of Behavior*, 5(4), 529–530. https://doi.org/10.1901/jeab.1962.5-529

## 引用とライセンス

このパッケージを引用するときは [CITATION.cff](CITATION.cff) を使ってください。MIT License です。[LICENSE](LICENSE) を参照してください。
