#!/usr/bin/env python3
"""公開テキストの文体チェックのテンプレート。ですます調の統一。check_article と併用する。

- 1文単位で狩らない。修辞としての体言止めは残す。
- 閾値は、混入率8%超かつ3文以上。全体の調子が変わったことだけを検出する。
- 対象は地の文のみ。引用「」『』・blockquote(>)・箇条書き・見出し・表・コードは除外する。
- 強調 ** の壊れは、混入率とは別に1件でもNGにする。画面に ** がそのまま出る不具合であるため。
"""
import re, sys, unicodedata
from pathlib import Path

OK_END = re.compile(r'(です|ます|でした|ました|ません|でしょう|ましょう|ください)[)」』*]*。$')
SKIP_PREFIX = ("-", ">", "#", "|", "*", "```")


# 強調 ** の壊れ検出。
# CommonMark では閉じ側の ** は「直前が句読点なら、直後は空白か句読点でなければならない」。
# 和文で「。**」と書いて直後に文字が続くと、閉じ側として認識されない。
# 修正は句点を強調の外へ出す。「です**。次の文」の形にする。
def _is_ws(c):    return c == '' or c.isspace()
def _is_punct(c): return c == '' or unicodedata.category(c).startswith('P') or unicodedata.category(c) == 'Sm'

def broken_emphasis(text):
    """閉じられない ** を含む行を (行番号, 行) で返す。引数はファイル全文。"""
    out, in_fence, in_front = [], False, False
    for ln, line in enumerate(text.split("\n"), 1):
        if ln == 1 and line.strip() == "---":
            in_front = True; continue
        if in_front:
            if line.strip() == "---": in_front = False
            continue
        if line.lstrip().startswith("```"):
            in_fence = not in_fence; continue
        # インラインコード内の ** は記法ではないので潰す。ただし空文字にしない。
        # 空にすると `**`code` に…**` の開き側の直後が空白に見えて誤検知する。
        # 1文字に畳めば、隣接文字による flanking 判定が実際の描画と一致する。
        line = re.sub(r'`[^`]*`', 'X', line)
        if in_fence or "**" not in line:
            continue
        opens = []
        for i in [m.start() for m in re.finditer(r'\*\*', line)]:
            prev = line[i-1] if i > 0 else ''
            nxt  = line[i+2] if i+2 < len(line) else ''
            left  = (not _is_ws(nxt)) and (not _is_punct(nxt) or _is_ws(prev) or _is_punct(prev))
            right = (not _is_ws(prev)) and (not _is_punct(prev) or _is_ws(nxt) or _is_punct(nxt))
            if opens and right:  opens.pop()
            elif left:           opens.append(i)
            else:                out.append((ln, line.strip()))
        if opens:
            out.append((ln, line.strip()))
    return out


failed = False
for f in sys.argv[1:]:
    text = Path(f).read_text(encoding="utf-8")
    parts = text.split("---", 2)
    body = parts[2] if len(parts) > 2 else text          # frontmatter除外
    body = re.sub(r'```.*?```', '', body, flags=re.S)     # コードブロック除外
    body = re.sub(r'「[^」]*」|『[^』]*』', '「引用」', body)  # 引用は文体自由
    total, ng = 0, []
    for line in body.split("\n"):
        s = line.strip()
        if not s or s.startswith(SKIP_PREFIX) or re.match(r'^\d+\.', s):
            continue
        for sent in re.findall(r'[^。]+。', s):
            sent = sent.strip()
            if re.fullmatch(r'[「引用」、。 ]+', sent):
                continue
            total += 1
            if not OK_END.search(sent):
                ng.append(sent)
    ratio = len(ng) / total if total else 0
    status = "NG" if (ratio > 0.08 and len(ng) >= 3) else "ok"
    print(f"{status} {Path(f).name}: 地の文{total}文中 常体/体言止め{len(ng)} ({ratio:.0%})")
    if status == "NG":
        failed = True
        for s in ng[:15]:
            print(f"   => {s[:60]!r}")

    for ln, line in broken_emphasis(text):
        failed = True
        print(f"NG {Path(f).name} L{ln}: 強調(**)が閉じていません。和文では句点を強調の外へ出してください")
        print(f"   => {line[:80]!r}")

if failed:
    print("\n文体ブロック: 全体がですます調から外れています。修正してください。", file=sys.stderr)
    sys.exit(1)
print("OK: 文体は基準内です。少量の意図的な体言止めは許容")
