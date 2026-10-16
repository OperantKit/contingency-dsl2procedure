# contingency-dsl2procedure

:gb: [English README](README.md)

[contingency-dsl](https://github.com/OperantKit/contingency-dsl) の JSON AST から学術論文の Method セクションへ変換するコンパイラ。

外部依存ゼロ。適合する `ast-schema.json` を生成する任意のパーサと連携可能。

## インストール

```bash
pip install git+https://github.com/OperantKit/contingency-dsl2procedure
```

## 30 秒で動く例

AST の dict で与えた `Conc(VI30s, VI60s, COD=2s)` を JEAB スタイルの Procedure 段落に変換し、引用した文献を一覧し、同じスケジュールを J-ABA スタイル（日本語）でも書く:

```python
from contingency_dsl2procedure import compile_method

# Conc(VI30s, VI60s, COD=2s) を contingency-dsl の AST dict で書いたもの
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

`method.to_text()` は Method 節全体（Subjects・Apparatus・Procedure・References）を Markdown で書き出す。dict ではなくテキストでスケジュールを書くなら、[contingency-dsl-py](https://github.com/OperantKit/contingency-dsl-py)（`pip install contingency-dsl-py`）で構文解析する。`to_dict(parse("Conc(VI30s, VI60s, COD=2s)"))` は上の dict（に空の `program_annotations` リストを加えたもの）を返し、同じ段落に変換される。

## 自作の 50 行では足りない理由

`f"a {name} {value}-s schedule"` のようなテンプレートで書けるのは単一のスケジュール 1 つだけである。Method 節には次のものが要り、どれもこのパッケージで実装・試験している:

- **スケジュールの網羅.** 単一スケジュール 9 種（F/V/R × 比率・時隔・時間: FR, VR, RR, FI, VI, RI, FT, VT, RT）、複合スケジュールの結合子 9 種（`Conc`, `Alt`, `Conj`, `Chain`, `Tand`, `Mult`, `Mix`, `Overlay`, `Interpolate`）に加えて、修飾子（DRL, DRH, DRO, 累進比率 ほか）、二次スケジュール、Limited Hold、嫌悪性スケジュール（Sidman 型回避、弁別回避、逃避）、調整スケジュールと連動スケジュール、試行型（見本合わせ、Go/No-Go）、レスポンデント手続き、多フェーズの実験計画。
- **パラメータを文章にする.** 切替遅延（`COD`）、固定比率の切替要件（`FRCO`）、Limited Hold、ブラックアウト、強化遅延を落とさず文として書く。
- **弁別刺激の注記.** `Mult` と `Chain` では成分ごとに異なる外受容性の弁別刺激が呈示されたことを、`Mix` と `Tand` では呈示されなかったことを書き添えるので、読み手が刺激配置を区別できる。
- **引用の自動収集.** 組み込みの APA 文献 29 件（VI/VR の値の系列なら Fleshler & Hoffman, 1962、並立スケジュールなら Herrnstein, 1961 など）から、実際に使ったスケジュールに対応するものを集めて `method.references` に入れる。
- **英語と日本語.** `jeab` と `jaba` のスタイルは 1 つのコンパイラを共有する。独自のスタイルや引用形式は `register_style` と `register_citation_format` で登録できる。
- **往復変換.** [contingency-procedure2dsl](https://github.com/OperantKit/contingency-procedure2dsl) はこの文章からスケジュールの AST を抽出する。たとえば `Mult(FR5, EXT)` と `Chain(FR10, FI30s)` から生成した段落は、元のスケジュールに読み戻される。

## 使い方

```python
from contingency_dsl2procedure import compile_method

# 入力: contingency-dsl/ast-schema.json に適合する素の dict
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

# JEAB スタイル（英語、デフォルト）
method = compile_method(ast, style="jeab")
print(method.procedure)
# Responses were reinforced under a concurrent VI 30-s VI 60-s schedule.

# J-ABA スタイル（日本語）
method_ja = compile_method(ast, style="jaba")
print(method_ja.procedure)
# 並立 VI 30-s VI 60-sスケジュールに従って反応が強化された。

# 参考文献は自動収集される
print(method.references)
# (Reference(key='fleshler_hoffman_1962', ...),)
```

同じコンパイラはコマンドラインからも使える。`INPUT` は JSON ファイル、または標準入力を表す `-`:

```bash
contingency-dsl2procedure ast.json --style jaba --output method.md
```
