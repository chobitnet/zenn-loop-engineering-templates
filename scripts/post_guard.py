#!/usr/bin/env python3
"""SNS投稿スクリプトの機械的ガード部のテンプレート。

- 投稿スクリプトのうち、送信前の機械検査だけを抜き出した骨格である。
  投稿APIの呼び出し部分はプラットフォームごとに異なるため含めない。
- ガードはプロンプトではなくコードに置く。エージェントがどんな文面を組み立てても、
  送信直前にこの関数が同じ基準で検査する。
- 検査項目と値は自分の運用に合わせて決める。下の項目は一例である。
- 値の変更は人間ゲート経由で行い、変更履歴を日付つきでこのファイルに残す。
"""
import datetime, json, re, sys
from pathlib import Path

# ==== 機械的ガード。モデル非依存 ====
DAILY_CAP = 2                                   # 1日の投稿上限
CHAR_LIMIT = 140                                # 文字数上限。プラットフォームのプランに合わせる
ALLOWED_URL_PREFIXES = ("https://__YOUR_BLOG_DOMAIN__",)  # 投稿に含めてよいリンク先の許可リスト
POST_LOG = Path.home() / ".config/__YOUR_HARNESS__/post_log.json"  # 投稿記録。日次上限の判定に使う


def guard(text):
    """ポリシー違反の投稿を機械的に拒否する。理由文字列を返す。問題なければNone。"""
    for u in re.findall(r"https?://\S+", text):
        if not u.startswith(ALLOWED_URL_PREFIXES):
            return f"許可外URL: {u}。許可リスト: {ALLOWED_URL_PREFIXES}"
    if len(text) > CHAR_LIMIT:
        return f"文字数超過: {len(text)}文字。上限{CHAR_LIMIT}文字"
    if re.search(r"(^|[^\w])@[A-Za-z0-9_]{1,15}", text):
        return "@メンションを含む投稿は禁止"
    log = json.loads(POST_LOG.read_text()) if POST_LOG.exists() else []
    today = datetime.date.today().isoformat()
    if sum(1 for e in log if e["date"] == today) >= DAILY_CAP:
        return f"本日の投稿上限 {DAILY_CAP}件 に達しています"
    return None


def record_post(post_id, text):
    """投稿の記録。日次上限の判定材料なので、投稿成功のたびに必ず呼ぶ。"""
    log = json.loads(POST_LOG.read_text()) if POST_LOG.exists() else []
    log.append({"date": datetime.date.today().isoformat(), "id": post_id, "text": text[:50]})
    POST_LOG.parent.mkdir(parents=True, exist_ok=True)
    POST_LOG.write_text(json.dumps(log, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    # ハイフン始まりの未知引数は本文として投稿せず拒否する。
    if arg.startswith("-"):
        print(f"ERROR: 未知のフラグ '{arg}'。使い方: post_guard.py \"本文\"", file=sys.stderr)
        sys.exit(2)
    reason = guard(arg)
    if reason:
        print(f"BLOCKED: {reason}", file=sys.stderr)
        sys.exit(2)
    # ここにプラットフォームのAPI呼び出しを実装し、成功したら record_post() を呼ぶ
    print("guard passed。API呼び出し部分はプラットフォームに合わせて実装してください")
