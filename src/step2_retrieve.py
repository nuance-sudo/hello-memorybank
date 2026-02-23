"""
Step 2: メモリの取得（記事 3-2 に対応）

記事の「3-2. メモリの取得（RetrieveMemories）」セクション（①〜④）を
実際のコードで体験するハンズオンスクリプト。

  ① 3つの取得メソッドの使い分け（Retrieve / Get / List）
  ② スコープの「完全一致」制約の確認
  ③ 2種類のフィルタリング（メタデータ / システムフィールド / 複合）
  ④ セマンティック検索（類似性検索）

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
# ① 3つの取得メソッドの使い分け（記事 3-2 ① 参照）
# ============================================================
# | メソッド   | スコープ指定 | 主な用途                        |
# |-----------|------------|--------------------------------|
# | Retrieve  | 必要(完全一致)| プロンプト構築、類似検索           |
# | Get       | 不要       | 特定の記憶のピンポイント参照        |
# | List      | 不要       | 記憶の全体把握（デバッグ用）        |
print("\n" + "=" * 60)
print("① 3つの取得メソッドの使い分け（記事 3-2 ①）")
print("=" * 60)

# --- ①-a: Retrieve（スコープ内の記憶を取得）---
print("\n--- ①-a: Retrieve（スコープ内の記憶を取得）---")
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

# --- ①-b: Get（リソース名で1件取得）---
print("\n--- ①-b: Get（リソース名で1件取得）---")
if all_memories:
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

# --- ①-c: List（Agent Engine 内の全メモリを一覧取得）---
print("\n--- ①-c: List（Agent Engine 内の全メモリを一覧取得）---")
# 記事にある通り、デバッグ用途に重宝するメソッド。
# スコープ不要で全ユーザーの記憶が取得できる。
pager = client.agent_engines.memories.list(name=AGENT_ENGINE_NAME)
listed_memories = list(pager)
print(f"   Agent Engine 内の全メモリ数: {len(listed_memories)}")
for i, m in enumerate(listed_memories, 1):
    print(f"\n  [{i}] fact: {m.fact}")
    print(f"      scope: {m.scope}")
    if m.metadata:
        print(f"      metadata: {m.metadata}")

# ============================================================
# ② スコープの「完全一致」制約の確認（記事 3-2 ② 参照）
# ============================================================
# Retrieve を使う際、スコープは「完全一致」でなければならない。
# 存在しないスコープを指定すると 0 件が返る。
# 記事のアンチパターン「スコープで細かく分けすぎる」問題を体験する。
print("\n" + "=" * 60)
print("② スコープの「完全一致」制約の確認（記事 3-2 ②）")
print("=" * 60)

# --- ②-a: 存在しない user_id で取得（0件になるはず）---
print("\n--- ②-a: 存在しない user_id で取得 ---")
results_other = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope={"user_id": "user-999"},
)
other_memories = list(results_other)
print(f"   user-999 のメモリ件数: {len(other_memories)}")
print(f"   → user-1 のメモリは見えない（スコープで分離されている）")

# --- ②-b: 複合キーの部分一致では取得できないことの確認 ---
print("\n--- ②-b: 複合キーの部分一致は不可 ---")
print(f"   💡 記事のアンチパターン:")
print(f"      保存時: scope={{\"user_id\": \"user-1\", \"project_id\": \"project_A\"}}")
print(f"      取得時: scope={{\"user_id\": \"user-1\"}} では取得できない")
print(f"      → 横断検索したい属性はスコープではなくメタデータに持たせるべき")

# ============================================================
# ③ 2種類のフィルタリング（記事 3-2 ③ 参照）
# ============================================================
# A. メタデータフィルタ（filter_groups）: DNF形式、完全一致のみ
# B. システムフィールドフィルタ（filter）: EBNF構文、部分一致・日時範囲可
print("\n" + "=" * 60)
print("③ 2種類のフィルタリング（記事 3-2 ③）")
print("=" * 60)

# --- ③-A: メタデータフィルタ（filter_groups, DNF 形式）---
print("\n--- ③-A: メタデータフィルタ（filter_groups）---")

# A-1: category=learning で絞り込み
print("\n  [A-1] category=learning で絞り込み:")
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
    print(f"    [{i}] fact: {m.memory.fact}")
    if m.memory.metadata:
        print(f"        metadata: {m.memory.metadata}")

# A-2: 存在しないメタデータでの絞り込み（0件になるはず）
print("\n  [A-2] category=nonexistent で絞り込み（0件期待）:")
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

# --- ③-B: システムフィールドフィルタ（filter, EBNF 構文）---
print("\n--- ③-B: システムフィールドフィルタ（filter）---")

# B-1: fact の部分一致（正規表現）
print("\n  [B-1] fact に「Python」を含むメモリ:")
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
    print(f"    [{i}] fact: {m.memory.fact}")

# B-2: create_time でフィルタ（日時の範囲指定）
print("\n  [B-2] 本日以降に作成されたメモリ:")
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
    print(f"    [{i}] fact: {m.memory.fact}")
    print(f"        create_time: {m.memory.create_time}")

# B-3: トピックでフィルタ（マネージドトピック）
print("\n  [B-3] マネージドトピック USER_PREFERENCES でフィルタ:")
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
    print(f"    [{i}] fact: {m.memory.fact}")
    if hasattr(m.memory, "topics") and m.memory.topics:
        print(f"        topics: {m.memory.topics}")

# B-4: カスタムトピックでフィルタ（Step 0 で設定した technical_skills）
print("\n  [B-4] カスタムトピック technical_skills でフィルタ:")
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
    print(f"    [{i}] fact: {m.memory.fact}")

# --- ③-C: 複合フィルタ（filter + filter_groups の同時利用）---
print("\n--- ③-C: 複合フィルタ（filter + filter_groups の同時利用）---")

print("\n  category=learning AND fact に TypeScript を含む:")
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
    print(f"    [{i}] fact: {m.memory.fact}")
    if m.memory.metadata:
        print(f"        metadata: {m.memory.metadata}")

# ============================================================
# ④ セマンティック検索（類似性検索）（記事 3-2 ④ 参照）
# ============================================================
# similarity_search_params を指定することで、意味的な類似度に基づいた
# 検索が可能。ユークリッド距離が最小のものから順にソートされて返る。
print("\n" + "=" * 60)
print("④ セマンティック検索（類似性検索）（記事 3-2 ④）")
print("=" * 60)

# --- クエリ A: 仕事に関する質問 ---
print("\n--- クエリ A: 「どんな開発をしていますか？」 ---")
results_a = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
    similarity_search_params={
        "search_query": "どんな開発をしていますか？",
        "top_k": 3,
    },
)
for i, m in enumerate(list(results_a), 1):
    distance_str: Optional[str] = None
    if hasattr(m, "distance") and m.distance is not None:
        distance_str = f"{m.distance:.4f}"
    print(f"  [{i}] fact: {m.memory.fact}")
    print(f"      distance: {distance_str or '(なし)'}")

# --- クエリ B: 趣味に関する質問 ---
print("\n--- クエリ B: 「趣味は何？」 ---")
results_b = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
    similarity_search_params={
        "search_query": "趣味は何？",
        "top_k": 3,
    },
)
for i, m in enumerate(list(results_b), 1):
    distance_str = None
    if hasattr(m, "distance") and m.distance is not None:
        distance_str = f"{m.distance:.4f}"
    print(f"  [{i}] fact: {m.memory.fact}")
    print(f"      distance: {distance_str or '(なし)'}")

# --- クエリ C: 使用ツールに関する質問 ---
print("\n--- クエリ C: 「使っているツールは？」 ---")
results_c = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
    similarity_search_params={
        "search_query": "使っているツールは？",
        "top_k": 3,
    },
)
for i, m in enumerate(list(results_c), 1):
    distance_str = None
    if hasattr(m, "distance") and m.distance is not None:
        distance_str = f"{m.distance:.4f}"
    print(f"  [{i}] fact: {m.memory.fact}")
    print(f"      distance: {distance_str or '(なし)'}")

print(f"""
💡 セマンティック検索のポイント:
   - キーワード一致ではなく「意味的な類似度」で検索
   - distance が小さいほど類似度が高い（ユークリッド距離）
   - top_k で返す件数を制御できる
""")

# ============================================================
# まとめ
# ============================================================
print("=" * 60)
print("📊 まとめ")
print("=" * 60)
print(f"""
記事 3-2 の取得方法の整理:

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
