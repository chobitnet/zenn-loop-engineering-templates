#!/usr/bin/env python3
"""公開前の秘匿情報チェックのテンプレート。機械的ガード。デプロイ前に必ず実行する。
使い方: python3 check_article.py <記事ファイル>...  NG検出で exit 1。

- 検出語彙は、実際に漏れた・漏れかけた類型から足す。一般論のリストにしない。
- このファイルを実名・実情報で埋めた後は、このファイル自体を公開物に含めない。
  検出語彙のリストが秘匿情報の一覧そのものになる。
- 本テンプレートの語彙はすべてサンプルである。
"""
import re, sys
from pathlib import Path

# 検出パターン: 実名/アカウント/ローカルパス/内部ホスト情報
# 右側のラベルは検出時に表示する説明。自分の環境の実名・実値に置き換える
NG_PATTERNS = [
    (r"yamada_taro", "実名ユーザー名(サンプル)"),
    (r"taro-dev", "個人アカウント名(サンプル)"),
    (r"/Users/[A-Za-z]", "macOSホームパス"),
    (r"com\.yamada", "launchdラベル(サンプル)"),
    (r"secret-product|codename-x", "未公開プロダクト名(サンプル)"),
    (r"internal-hostname", "内部ホスト情報(サンプル)"),
    # 「外部からローカルへの経路」「認証情報の保存場所」など、構成が推測できる語彙もここへ足す。
    # 機械の検出は下限である。公開前の目視はこれより広く行う。
]

failed = False
for f in sys.argv[1:]:
    text = Path(f).read_text(encoding="utf-8")
    for pat, label in NG_PATTERNS:
        for m in re.finditer(pat, text):
            line = text[:m.start()].count("\n") + 1
            print(f"NG {f}:{line}: {label} => {m.group(0)!r}")
            failed = True
if failed:
    print("\n公開ブロック: 上記を除去/一般化してから再実行してください。", file=sys.stderr)
    sys.exit(1)
print("OK: 秘匿情報は検出されませんでした")
