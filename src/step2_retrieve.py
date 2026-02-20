"""
Step 2: メモリの取得（Retrieve）

取得方法を網羅的に体験するスクリプト。

  1. 全件取得（retrieve, scope のみ）
  2. 類似検索（retrieve + similarity_search_params）
  3. スコープ分離の確認
  4. 単一メモリ取得（get）
  5. メモリ一覧（list）
  6. メタデータフィルタ（filter_groups, DNF 形式）
  7. システムフィールドフィルタ（filter, EBNF 構文）
  8. 複合フィルタ（filter + filter_groups の同時利用）

前提: Step 1 が実行済みで、user-1 にメモリが存在すること。
"""

import os
from typing import Optional

import vertexai
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
LOCATION = os.environ["GCP_LOCATION"]
AGENT_ENGINE_NAME = os.environ["AGENT_ENGINE_NAME"]

client = vertexai.Client(project=PROJECT_ID, location=LOCATION)
print(f"✅ Client 初期化完了")
print(f"   Agent Engine: {AGENT_ENGINE_NAME}")

SCOPE = {"user_id": "user-1"}

# ============================================================
# 1. 全件取得（Simple Retrieval）
# ============================================================
# scope を指定して、そのスコープの全メモリを取得する。
# similarity_search_params を指定しなければ全件返る。
print("\n" + "=" * 60)
print("📥 1. 全件取得（Simple Retrieval）")
print("=" * 60)

results = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
)
all_memories = list(results)

print(f"   取得件数: {len(all_memories)}")
for i, m in enumerate(all_memories, 1):
    print(f"\n  [{i}] fact: {m.memory.fact}")
    print(f"      scope: {m.memory.scope}")
    print(f"      update_time: {m.memory.update_time}")
    if m.memory.metadata:
        print(f"      metadata: {m.memory.metadata}")

# ============================================================
# 2. 類似検索（Similarity Search）
# ============================================================
# クエリに意味的に近いメモリだけを取得する。
# 内部でエンべディングモデルを使ったベクトル検索が行われる。
# 結果は distance（ユークリッド距離）の昇順で返る。
# distance が小さいほど類似度が高い。
print("\n" + "=" * 60)
print("🔍 2. 類似検索（Similarity Search）")
print("=" * 60)

# --- 検索クエリ A: 仕事に関する質問 ---
print("\n--- クエリ A: 「どんな開発をしていますか？」 ---")
results_a = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
    similarity_search_params={
        "search_query": "どんな開発をしていますか？",
        "top_k": 2,
    },
)
for i, m in enumerate(list(results_a), 1):
    # distance は類似検索時のみ設定される（ユークリッド距離）
    distance_str: Optional[str] = None
    if hasattr(m, "distance") and m.distance is not None:
        distance_str = f"{m.distance:.4f}"
    print(f"  [{i}] fact: {m.memory.fact}")
    print(f"      distance: {distance_str or '(なし)'}")

# --- 検索クエリ B: 趣味に関する質問 ---
print("\n--- クエリ B: 「趣味は何？」 ---")
results_b = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
    similarity_search_params={
        "search_query": "趣味は何？",
        "top_k": 2,
    },
)
for i, m in enumerate(list(results_b), 1):
    distance_str = None
    if hasattr(m, "distance") and m.distance is not None:
        distance_str = f"{m.distance:.4f}"
    print(f"  [{i}] fact: {m.memory.fact}")
    print(f"      distance: {distance_str or '(なし)'}")

# --- 検索クエリ C: 使用ツールに関する質問 ---
print("\n--- クエリ C: 「使っているツールは？」 ---")
results_c = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
    similarity_search_params={
        "search_query": "使っているツールは？",
        "top_k": 2,
    },
)
for i, m in enumerate(list(results_c), 1):
    distance_str = None
    if hasattr(m, "distance") and m.distance is not None:
        distance_str = f"{m.distance:.4f}"
    print(f"  [{i}] fact: {m.memory.fact}")
    print(f"      distance: {distance_str or '(なし)'}")

# ============================================================
# 3. スコープ分離の確認
# ============================================================
# 別の user_id ではメモリが見えないことを確認する。
# scope は完全一致でフィルタされる。
print("\n" + "=" * 60)
print("🚫 3. 別スコープで取得（分離の確認）")
print("=" * 60)

results_other = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope={"user_id": "user-999"},
)
other_memories = list(results_other)
print(f"   user-999 のメモリ件数: {len(other_memories)}")
print(f"   → user-1 のメモリは見えない（スコープで分離されている）")

# ============================================================
# 4. 単一メモリ取得（get）
# ============================================================
# メモリの name（完全修飾名）を指定して1件取得する。
# retrieve() と違い、scope は不要。name さえあれば取得できる。
# 全フィールド（fact, scope, metadata, topics, create_time, update_time）を表示する。
print("\n" + "=" * 60)
print("🔑 4. 単一メモリ取得（get）")
print("=" * 60)

if all_memories:
    # セクション1で取得した最初のメモリの name を使う
    first_memory_name: str = all_memories[0].memory.name
    print(f"   取得対象: {first_memory_name}")

    memory = client.agent_engines.memories.get(name=first_memory_name)
    print(f"   fact: {memory.fact}")
    print(f"   scope: {memory.scope}")
    print(f"   create_time: {memory.create_time}")
    print(f"   update_time: {memory.update_time}")
    if memory.metadata:
        print(f"   metadata: {memory.metadata}")
    if hasattr(memory, "topics") and memory.topics:
        print(f"   topics: {memory.topics}")
else:
    print("   ⚠️ メモリが存在しないため、get() をスキップしました")

# ============================================================
# 5. メモリ一覧（list）
# ============================================================
# list() は Agent Engine 内の全メモリを一覧表示する。
# retrieve() と違い、scope の指定は不要。
# ページネーション対応のイテレータを返す。
print("\n" + "=" * 60)
print("📋 5. メモリ一覧（list）")
print("=" * 60)

pager = client.agent_engines.memories.list(name=AGENT_ENGINE_NAME)
listed_memories = list(pager)
print(f"   Agent Engine 内の全メモリ数: {len(listed_memories)}")
for i, m in enumerate(listed_memories, 1):
    print(f"\n  [{i}] fact: {m.fact}")
    print(f"      scope: {m.scope}")
    if m.metadata:
        print(f"      metadata: {m.metadata}")

# ============================================================
# 6. メタデータフィルタ（filter_groups）
# ============================================================
# Step 1 で category=learning のメタデータを付与したメモリがある。
# filter_groups は DNF（論理和標準形）で指定する:
#   - filter_groups のリスト要素同士は OR で結合
#   - 各 filter_groups 内の filters は AND で結合
#
# 例: (A AND B) OR (C)
#   filter_groups = [
#     {"filters": [A, B]},  # A AND B
#     {"filters": [C]},     # C
#   ]
print("\n" + "=" * 60)
print("🏷️  6. メタデータフィルタ（filter_groups）")
print("=" * 60)

# --- 6a: category=learning で絞り込み ---
print("\n--- 6a: category=learning で絞り込み ---")
results_meta = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
    config={
        "filter_groups": [
            {
                "filters": [
                    {
                        "key": "category",
                        "value": {"string_value": "learning"},
                    }
                ]
            }
        ]
    },
)
meta_memories = list(results_meta)
print(f"   ヒット件数: {len(meta_memories)}")
for i, m in enumerate(meta_memories, 1):
    print(f"  [{i}] fact: {m.memory.fact}")
    if m.memory.metadata:
        print(f"      metadata: {m.memory.metadata}")

# --- 6b: 存在しないメタデータでの絞り込み（0件になるはず） ---
print("\n--- 6b: category=nonexistent で絞り込み（0件期待） ---")
results_none = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
    config={
        "filter_groups": [
            {
                "filters": [
                    {
                        "key": "category",
                        "value": {"string_value": "nonexistent"},
                    }
                ]
            }
        ]
    },
)
none_memories = list(results_none)
print(f"   ヒット件数: {len(none_memories)} （期待: 0）")

# ============================================================
# 7. システムフィールドフィルタ（filter）
# ============================================================
# filter は EBNF 構文の文字列で指定する。
# 使えるフィールド:
#   - fact: 部分一致（正規表現）
#   - create_time / update_time: 比較演算子
#   - topics.managed_memory_topic: マネージドトピック
#   - topics.custom_memory_topic_label: カスタムトピック
#
# 演算子:
#   - =~ : 正規表現マッチ
#   - >= / <= / > / < : 比較
#   - : (HAS) : 値を含む
#   - AND / OR : 組み合わせ
print("\n" + "=" * 60)
print("🔧 7. システムフィールドフィルタ（filter）")
print("=" * 60)

# --- 7a: fact の部分一致 ---
print("\n--- 7a: fact に「Python」を含むメモリ ---")
results_fact = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
    config={
        "filter": 'fact=~".*Python.*"',
    },
)
fact_memories = list(results_fact)
print(f"   ヒット件数: {len(fact_memories)}")
for i, m in enumerate(fact_memories, 1):
    print(f"  [{i}] fact: {m.memory.fact}")

# --- 7b: create_time でフィルタ ---
print("\n--- 7b: 本日以降に作成されたメモリ ---")
results_time = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
    config={
        "filter": 'create_time>="2026-02-18T00:00:00Z"',
    },
)
time_memories = list(results_time)
print(f"   ヒット件数: {len(time_memories)}")
for i, m in enumerate(time_memories, 1):
    print(f"  [{i}] fact: {m.memory.fact}")
    print(f"      create_time: {m.memory.create_time}")

# --- 7c: トピックでフィルタ（マネージドトピック） ---
print("\n--- 7c: マネージドトピック USER_PREFERENCES でフィルタ ---")
results_topic = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
    config={
        "filter": "topics.managed_memory_topic: USER_PREFERENCES",
    },
)
topic_memories = list(results_topic)
print(f"   ヒット件数: {len(topic_memories)}")
for i, m in enumerate(topic_memories, 1):
    print(f"  [{i}] fact: {m.memory.fact}")
    if hasattr(m.memory, "topics") and m.memory.topics:
        print(f"      topics: {m.memory.topics}")

# --- 7d: カスタムトピックでフィルタ ---
# Step 0 で設定した technical_skills トピックを使う
print("\n--- 7d: カスタムトピック technical_skills でフィルタ ---")
results_custom_topic = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
    config={
        "filter": "topics.custom_memory_topic_label: technical_skills",
    },
)
custom_topic_memories = list(results_custom_topic)
print(f"   ヒット件数: {len(custom_topic_memories)}")
for i, m in enumerate(custom_topic_memories, 1):
    print(f"  [{i}] fact: {m.memory.fact}")

# ============================================================
# 8. 複合フィルタ（filter + filter_groups の同時利用）
# ============================================================
# メタデータフィルタとシステムフィールドフィルタは同時に使える。
# 両方の条件を満たすメモリだけが返る。
print("\n" + "=" * 60)
print("🎯 8. 複合フィルタ（filter + filter_groups）")
print("=" * 60)

print("\n--- category=learning AND fact に TypeScript を含む ---")
results_combined = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
    config={
        # メタデータフィルタ
        "filter_groups": [
            {
                "filters": [
                    {
                        "key": "category",
                        "value": {"string_value": "learning"},
                    }
                ]
            }
        ],
        # システムフィールドフィルタ
        "filter": 'fact=~".*TypeScript.*"',
    },
)
combined_memories = list(results_combined)
print(f"   ヒット件数: {len(combined_memories)}")
for i, m in enumerate(combined_memories, 1):
    print(f"  [{i}] fact: {m.memory.fact}")
    if m.memory.metadata:
        print(f"      metadata: {m.memory.metadata}")

# ============================================================
# まとめ
# ============================================================
print("\n" + "=" * 60)
print("📊 まとめ")
print("=" * 60)
print(f"""
取得方法の整理:

| メソッド    | 用途                         | scope必要? |
|------------|------------------------------|-----------|
| get()      | 1件取得（name指定）            | 不要       |
| list()     | 全メモリ一覧                   | 不要       |
| retrieve() | スコープ内の取得 + 類似検索      | 必要       |

フィルタの整理:

| フィルタ種別         | パラメータ       | 形式    | 対象               |
|--------------------|-----------------|---------|--------------------|
| メタデータフィルタ    | filter_groups   | DNF     | ユーザー定義メタデータ |
| システムフィールド    | filter          | EBNF    | fact/topics/時間    |
| 複合フィルタ         | 両方同時        | -       | 上記の組み合わせ      |
""")

print(f"🎉 Step 2 完了！")
