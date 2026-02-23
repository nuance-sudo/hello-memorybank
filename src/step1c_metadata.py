"""
Step 1c: メタデータの付与と更新戦略（記事 3-1 (6)(7) に対応）

メタデータは個々の記憶に付与する「タグ」。
検索時の確実な条件絞り込み（Exact Match）に利用できる。

  (6) メタデータ（Metadata）の付与
  (7) メタデータの更新戦略（metadata_merge_strategy）

前提: step1a_basics.py が実行済みで、user_123 にメモリが存在すること。

実行方法:
  uv run python src/step1c_metadata.py
"""

import os

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
# (6) メタデータ（Metadata）の付与（記事 3-1 (6) 参照）
# ============================================================
# メタデータは個々の記憶に付与する「タグ」。
# 検索時の確実な条件絞り込み（Exact Match）に利用できる。
#
# 【記事の具体例：発注システムの場合】
#   department: 「営業部」のタグ
#   item_category: 「文房具」のタグ
#   → 後から「営業部」かつ「文房具」のメタデータを持つ記憶だけをピンポイント取得できる
print("\n" + "=" * 60)
print("(6) メタデータの付与（記事 3-1 (6)）")
print("=" * 60)

operation_meta = client.agent_engines.memories.generate(
    name=AGENT_ENGINE_NAME,
    # Sessions を使わず直接渡す例（direct_contents_source）
    direct_contents_source={
        "events": [
            {
                "content": {
                    "role": "user",
                    "parts": [{"text": "営業部用にA3ポスター用紙を20枚発注して。プレゼン資料の印刷に使います。"}]
                }
            },
        ]
    },
    scope=SCOPE,
    config={
        "metadata": {
            "department": {"string_value": "sales"},
            "item_category": {"string_value": "stationery"},
        },
    },
)

print(f"   ✅ メタデータ付き generate() 完了")
if operation_meta.response is not None:
    for i, gm in enumerate(operation_meta.response.generated_memories, 1):
        memory = client.agent_engines.memories.get(name=gm.memory.name)
        print(f"   [{i}] action={gm.action}")
        print(f"        fact={memory.fact}")
        print(f"        metadata={memory.metadata}")

# ============================================================
# (7) メタデータの更新戦略（記事 3-1 (7) 参照）
# ============================================================
# metadata_merge_strategy で統合時のメタデータの扱いを制御する。
# - MERGE（デフォルト）: 新旧のメタデータを結合
# - OVERWRITE: 古いメタデータを完全に置き換え
# - REQUIRE_EXACT_MATCH: 完全一致するメタデータのみ統合対象に
#
# 【記事の具体例：デッサン練習の成長スコア】
#   MERGE を使うと、同じモチーフの評価が上書きされ過去の履歴が消える
#   → 時系列で残したい場合は REQUIRE_EXACT_MATCH + session_id を使う
print("\n" + "=" * 60)
print("(7) メタデータの更新戦略（記事 3-1 (7)）")
print("=" * 60)

# REQUIRE_EXACT_MATCH の例:
# 「履歴として蓄積したい記憶」で意図しない上書きを防ぐ
# 発注履歴を時系列で残すため、session_id をメタデータに含める
operation_exact = client.agent_engines.memories.generate(
    name=AGENT_ENGINE_NAME,
    direct_contents_source={
        "events": [
            {
                "content": {
                    "role": "user",
                    "parts": [{"text": "総務部用にPC周辺機器を発注しました。モニターアーム5台とキーボード10台です。"}]
                }
            },
        ]
    },
    scope=SCOPE,
    config={
        "metadata": {
            "department": {"string_value": "general_affairs"},
            "item_category": {"string_value": "pc_peripherals"},
            "session_id": {"string_value": "session_20260223"},
        },
        "metadata_merge_strategy": "REQUIRE_EXACT_MATCH",
    },
)

print(f"   ✅ REQUIRE_EXACT_MATCH 付き generate() 完了")
if operation_exact.response is not None:
    for i, gm in enumerate(operation_exact.response.generated_memories, 1):
        memory = client.agent_engines.memories.get(name=gm.memory.name)
        print(f"   [{i}] action={gm.action}")
        print(f"        fact={memory.fact}")
        print(f"        metadata={memory.metadata}")
print(f"\n   💡 REQUIRE_EXACT_MATCH を使うと:")
print(f"      メタデータが完全一致する記憶のみ統合対象になり、")
print(f"      異なるメタデータを持つ記憶は独立して蓄積される。")
print(f"      → 発注履歴を時系列で消さずに残したいケースに有効。")

# ============================================================
# 確認 — メタデータ付きメモリの一覧
# ============================================================
print("\n" + "=" * 60)
print("📥 メタデータ付きメモリの確認")
print("=" * 60)

all_results = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
)
all_memories = list(all_results)

# メタデータを持つメモリだけ表示
meta_count = 0
for i, m in enumerate(all_memories, 1):
    if m.memory.metadata:
        meta_count += 1
        print(f"\n  [{meta_count}] fact: {m.memory.fact}")
        print(f"      metadata: {m.memory.metadata}")

print(f"\n   合計: {len(all_memories)} 件中 {meta_count} 件がメタデータ付き")

print(f"""
🎉 Step 1c 完了！

学習したこと:
  (6) メタデータ = 記憶に付与する「タグ」（検索フィルタに利用可能）
      例: department="sales", item_category="stationery"
  (7) metadata_merge_strategy で統合時のメタデータ制御
      - MERGE: 新旧結合（デフォルト）
      - OVERWRITE: 完全置き換え
      - REQUIRE_EXACT_MATCH: 完全一致のみ統合対象

次のステップ:
  → step1d_advanced.py でトピック・マルチモーダル・非同期を体験
""")
