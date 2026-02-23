"""
Step 1d: 応用 — トピック・マルチモーダル・非同期（記事 3-1 (2)(8)(9) に対応）

  (2) トピック（Topics）の動作確認
  (8) マルチモーダル入力からのメモリ生成
  (9) 非同期生成
  最終確認 — 全メモリ一覧

前提: step1a_basics.py が実行済みで、user_123 にメモリが存在すること。

実行方法:
  uv run python src/step1d_advanced.py
"""

import datetime
import os
import time

import vertexai
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
LOCATION = os.environ["GCP_LOCATION"]
AGENT_ENGINE_NAME = os.environ["AGENT_ENGINE_NAME"]

client = vertexai.Client(project=PROJECT_ID, location=LOCATION)
print(f"✅ Client 初期化完了")
print(f"   Agent Engine: {AGENT_ENGINE_NAME}")

USER_ID = "user_123"
SCOPE = {"user_id": USER_ID, "system_id": "order_management"}

# ============================================================
# (2) トピック（Topics）の動作確認（記事 3-1 (2) 参照）
# ============================================================
# デフォルトの4トピック + カスタムトピック（Step 0 で設定済み）の動作を確認。
# LLM が会話の内容から自律的にトピックを分類する。
#
# 【記事の具体例：発注システムの場合】
#   「お疲れ様です」→ 挨拶なので記憶しない
#   「業者はA社でお願い」→ ユーザーの好み・重要な詳細として記憶
#   「覚えておいて」→ 明示的な指示として記憶
print("\n" + "=" * 60)
print("(2) トピック（Topics）の動作確認（記事 3-1 (2)）")
print("=" * 60)

# 発注ルールに関する会話でトピックの自動分類を確認する
session2 = client.agent_engines.sessions.create(
    name=AGENT_ENGINE_NAME,
    user_id=USER_ID,
)
session2_name: str = session2.response.name

topic_conversation: list[dict[str, str]] = [
    {"role": "user", "text": "発注の際のルールを共有します。10万円以上の発注は必ず部長承認が必要です。備品の発注は月末締めで翌月5日に一括処理してください。"},
]

for i, msg in enumerate(topic_conversation):
    client.agent_engines.sessions.events.append(
        name=session2_name,
        author="user",
        invocation_id="1",
        timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
        config={
            "content": {
                "role": msg["role"],
                "parts": [{"text": msg["text"]}],
            }
        },
    )

operation_custom = client.agent_engines.memories.generate(
    name=AGENT_ENGINE_NAME,
    vertex_session_source={"session": session2_name},
    scope=SCOPE,
)

print(f"   ✅ トピック確認用 generate() 完了")
if operation_custom.response is not None:
    for i, gm in enumerate(operation_custom.response.generated_memories, 1):
        memory = client.agent_engines.memories.get(name=gm.memory.name)
        print(f"   [{i}] action={gm.action}")
        print(f"        fact={memory.fact}")
        if hasattr(memory, "topics") and memory.topics:
            print(f"        topics={memory.topics}")
    print(f"\n   💡 Step 0 で設定した ordering_rules トピックが")
    print(f"      LLM により自動分類されているか確認してください。")

# ============================================================
# (8) マルチモーダル入力からのメモリ生成（記事 3-1 (8) 参照）
# ============================================================
# テキストだけでなく画像等からもメモリを生成できる。
# ただし生成されるメモリ自体はテキスト形式。
# 詳細は poi/step3_multimodal.py を参照。
#
# 【記事の具体例】
#   ユーザーが「これは私の犬です」+ ゴールデンレトリバーの画像を送信
#   → 「私の犬はゴールデンレトリバーです」というテキストメモリが生成される
print("\n" + "=" * 60)
print("(8) マルチモーダル入力からのメモリ生成（記事 3-1 (8)）")
print("=" * 60)

GCS_IMAGE_URI = "gs://cloud-samples-data/generative-ai/image/scones.jpg"

op_multi = client.agent_engines.memories.generate(
    name=AGENT_ENGINE_NAME,
    direct_contents_source={
        "events": [
            {
                "content": {
                    "role": "user",
                    "parts": [
                        {"text": "これは今回納品された備品の写真です。検品結果を記録しておいてください。"},
                        {
                            "file_data": {
                                "file_uri": GCS_IMAGE_URI,
                                "mime_type": "image/jpeg",
                            }
                        },
                    ],
                }
            }
        ]
    },
    scope=SCOPE,
)

print(f"   ✅ マルチモーダル generate() 完了 (done={op_multi.done})")
if op_multi.response is not None:
    for i, gm in enumerate(op_multi.response.generated_memories, 1):
        memory = client.agent_engines.memories.get(name=gm.memory.name)
        print(f"   [{i}] action={gm.action}")
        print(f"        fact={memory.fact}")
    print(f"\n   💡 画像自体は保存されず、LLM が画像を分析した")
    print(f"      テキスト形式のメモリが生成される。")
else:
    print("   response=None（メモリ未生成）")

print(f"\n   📝 より詳細なマルチモーダルの例（inline_data, Sessions連携）は")
print(f"      poi/step3_multimodal.py を参照してください。")

# ============================================================
# (9) 非同期生成（記事 3-1 (9) 参照）
# ============================================================
# wait_for_completion=False にすることで、メモリ生成を
# バックグラウンドで非同期に実行できる。
print("\n" + "=" * 60)
print("(9) 非同期生成（記事 3-1 (9)）")
print("=" * 60)

session_async = client.agent_engines.sessions.create(
    name=AGENT_ENGINE_NAME,
    user_id=USER_ID,
)
session_async_name: str = session_async.response.name

client.agent_engines.sessions.events.append(
    name=session_async_name,
    author="user",
    invocation_id="1",
    timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
    config={
        "content": {
            "role": "user",
            "parts": [{"text": "経理部の田中さんから連絡があり、今後の消耗品の予算上限は月30万円になりました。"}],
        }
    },
)

op_async = client.agent_engines.memories.generate(
    name=AGENT_ENGINE_NAME,
    vertex_session_source={"session": session_async_name},
    scope=SCOPE,
    config={
        "wait_for_completion": False,
    },
)

print(f"   ✅ 非同期 generate() 呼び出し完了")
print(f"   done={op_async.done}")
print(f"   → wait_for_completion=False なので即座に制御が返る")
print(f"   → エージェントはメモリ生成の完了を待たずに次の処理へ進める")

# 非同期処理が完了するまで少し待つ（デモ用）
print(f"\n   ⏳ 非同期処理の完了を待機中（5秒）...")
time.sleep(5)

# ============================================================
# 最終確認 — 全メモリ一覧
# ============================================================
print("\n" + "=" * 60)
print("📥 最終確認 — 全メモリ一覧")
print("=" * 60)

all_results = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
)
all_memories = list(all_results)

print(f"   合計: {len(all_memories)} 件")
for i, m in enumerate(all_memories, 1):
    print(f"\n  [{i}] fact: {m.memory.fact}")
    if m.memory.metadata:
        print(f"      metadata: {m.memory.metadata}")
    if hasattr(m.memory, "topics") and m.memory.topics:
        print(f"      topics: {m.memory.topics}")

print(f"""
📊 記事 3-1 のまとめ:

| セクション | 内容                       | 使用メソッド / 設定              |
|-----------|---------------------------|--------------------------------|
| (1)       | スコープの定義              | sessions.create(user_id=...)    |
| (2)       | トピックの自動分類           | カスタムトピック（Step 0で設定）   |
| (3)       | メモリのデータ構造           | fact, scope, metadata, topics   |
| (4)       | Generate vs Create         | generate() / create()           |
| (5)       | 統合（Consolidation）       | CREATED / UPDATED / DELETED     |
| (6)       | メタデータの付与             | config.metadata                 |
| (7)       | メタデータ更新戦略           | metadata_merge_strategy          |
| (8)       | マルチモーダル入力           | file_data / inline_data          |
| (9)       | 非同期生成                  | wait_for_completion=False        |
""")

print(f"🎉 Step 1 全体完了！ 次は Step 2 でメモリの取得を体験しましょう。")
