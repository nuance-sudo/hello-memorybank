"""
Step 2: メモリの取得（記事 3-2 に対応）

記事の「3-2. メモリの取得（RetrieveMemories）」セクション（(1)〜(4)）を
実際のコードで体験するハンズオンスクリプト。

  (0) 準備: 別スコープ（user_999）のメモリを作成
  (1) 3つの取得メソッドの使い分け（Retrieve / Get / List）
      + List vs Retrieve のスコープの違いを確認
  (2) スコープの「完全一致」制約の確認
  (3) 2種類のフィルタリング（メタデータ / システムフィールド / 複合）
  (4) セマンティック検索（類似性検索）

前提: Step 1 が実行済みで、user_123 にメモリが存在すること。
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

SCOPE = {"user_id": "user_123", "system_id": "order_management"}

# ============================================================
# (0) 準備: 別スコープ（user_999）のメモリを作成
# ============================================================
# List と Retrieve のスコープの違いを確認するために、
# user_123 とは異なるスコープのメモリを作成しておく。
print("\n" + "=" * 60)
print("(0) 準備: 別スコープ（user_999）のメモリを作成")
print("=" * 60)

SCOPE_999 = {"user_id": "user_999", "system_id": "order_management"}
print(f"\n   user_123 のスコープ: {SCOPE}")
print(f"   user_999 のスコープ: {SCOPE_999}")

create_op_1 = client.agent_engines.memories.create(
    name=AGENT_ENGINE_NAME,
    fact="B5用紙の発注先はD社です",
    scope=SCOPE_999,
)
print(f"\n   ✅ 作成: {create_op_1.response.fact}")

create_op_2 = client.agent_engines.memories.create(
    name=AGENT_ENGINE_NAME,
    fact="納品先は3階の倉庫です",
    scope=SCOPE_999,
)
print(f"   ✅ 作成: {create_op_2.response.fact}")

# 後でクリーンアップするために name を保持
user_999_memory_names: list[str] = [
    create_op_1.response.name,
    create_op_2.response.name,
]
print(f"\n   user_999 のメモリを {len(user_999_memory_names)} 件作成完了")

# ============================================================
# (1) 3つの取得メソッドの使い分け（記事 3-2 (1) 参照）
# ============================================================
# | メソッド   | スコープ指定 | 主な用途                        |
# |-----------|------------|--------------------------------|
# | Retrieve  | 必要(完全一致)| プロンプト構築、類似検索           |
# | Get       | 不要       | 特定の記憶のピンポイント参照        |
# | List      | 不要       | 記憶の全体把握（デバッグ用）        |
print("\n" + "=" * 60)
print("(1) 3つの取得メソッドの使い分け（記事 3-2 (1)）")
print("=" * 60)

# --- (1)-a: Retrieve（スコープ内の記憶を取得）---
print("\n--- (1)-a: Retrieve（スコープ内の記憶を取得）---")
results = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
)
all_memories = list(results)

print(f"   取得件数: {len(all_memories)}（scope={SCOPE} に一致するもののみ）")
for i, m in enumerate(all_memories, 1):
    print(f"\n  [{i}] fact: {m.memory.fact}")
    print(f"      scope: {m.memory.scope}")
    print(f"      update_time: {m.memory.update_time}")
    if m.memory.metadata:
        print(f"      metadata: {m.memory.metadata}")

# --- (1)-b: Get（リソース名で1件取得）---
print("\n--- (1)-b: Get（リソース名で1件取得）---")
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

# --- (1)-c: List（Agent Engine 内の全メモリを一覧取得）---
print("\n--- (1)-c: List（Agent Engine 内の全メモリを一覧取得）---")
pager = client.agent_engines.memories.list(name=AGENT_ENGINE_NAME)
listed_memories = list(pager)
print(f"   Agent Engine 内の全メモリ数: {len(listed_memories)}")
for i, m in enumerate(listed_memories, 1):
    print(f"\n  [{i}] fact: {m.fact}")
    print(f"      scope: {m.scope}")
    if m.metadata:
        print(f"      metadata: {m.metadata}")

# --- (1)-d: List vs Retrieve の結果の違い ---
print("\n--- (1)-d: List vs Retrieve の結果の違い ---")

list_count: int = len(listed_memories)

# Retrieve: user_123 のスコープ完全一致のみ
retrieve_123_count: int = len(all_memories)

# Retrieve: user_999 のスコープ完全一致のみ
results_999 = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE_999,
)
retrieve_999_memories = list(results_999)
retrieve_999_count: int = len(retrieve_999_memories)

print(f"   list()              → {list_count} 件（全スコープのメモリ）")
print(f"   retrieve(user_123)  → {retrieve_123_count} 件")
print(f"   retrieve(user_999)  → {retrieve_999_count} 件")
print(f"\n   💡 List はスコープに関係なく Agent Engine 内の全メモリを返す")
print(f"      Retrieve はスコープが完全一致するメモリのみを返す")
print(f"      → List はデバッグ用途、Retrieve はアプリケーション用途")

# ============================================================
# (2) スコープの「完全一致」制約の確認（記事 3-2 (2) 参照）
# ============================================================
# Retrieve を使う際、スコープは「完全一致」でなければならない。
# 複合キーの一部だけでは取得できない。
print("\n" + "=" * 60)
print("(2) スコープの「完全一致」制約の確認（記事 3-2 (2)）")
print("=" * 60)

# --- (2)-a: 複合キーの部分一致では取得できないことの確認 ---
print("\n--- (2)-a: 複合キーの部分一致は不可 ---")
# user_id だけでは取得できない（system_id が不足）
results_partial = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope={"user_id": "user_123"},  # system_id なし
)
partial_memories = list(results_partial)
print(f"   retrieve(user_id のみ) → {len(partial_memories)} 件")
print(f"   → system_id を含めた完全一致でないと取得できない")

# --- (2)-b: 対比まとめ ---
print("\n--- (2)-b: 対比まとめ ---")
print(f"   list()                → {list_count} 件（スコープ不要、全件）")
print(f"   retrieve(user_123)    → {retrieve_123_count} 件（完全一致）")
print(f"   retrieve(user_999)    → {retrieve_999_count} 件（完全一致）")
print(f"   retrieve(user_id のみ) → {len(partial_memories)} 件（部分一致 = 取得不可）")

print(f"\n   💡 記事のアンチパターン:")
print(f'      保存時: scope={{"user_id": "user_123", "project_id": "project_A"}}')
print(f'      取得時: scope={{"user_id": "user_123"}} だけでは取得できない')
print(f"      → 横断検索したい属性はスコープではなくメタデータに持たせるべき")

# ============================================================
# (3) 2種類のフィルタリング（記事 3-2 (3) 参照）
# ============================================================
# A. メタデータフィルタ（filter_groups）: DNF形式、完全一致のみ
# B. システムフィールドフィルタ（filter）: EBNF構文、部分一致・日時範囲可
print("\n" + "=" * 60)
print("(3) 2種類のフィルタリング（記事 3-2 (3)）")
print("=" * 60)

# --- (3)-A: メタデータフィルタ（filter_groups, DNF 形式）---
print("\n--- (3)-A: メタデータフィルタ（filter_groups）---")

# A-1: department=sales で絞り込み
print("\n  [A-1] department=sales で絞り込み:")
results_meta = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
    config={
        "filter_groups": [
            {
                "filters": [
                    {
                        "key": "department",
                        "value": {"string_value": "sales"},
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
print("\n  [A-2] department=nonexistent で絞り込み（0件期待）:")
results_none = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
    config={
        "filter_groups": [
            {
                "filters": [
                    {
                        "key": "department",
                        "value": {"string_value": "nonexistent"},
                    }
                ]
            }
        ]
    },
)
none_memories = list(results_none)
print(f"   ヒット件数: {len(none_memories)} （期待: 0）")

# A-3: 複数条件（department=sales AND item_category=stationery）
# 記事の「プロジェクトA」かつ「優先度：高」に相当する複合条件
print("\n  [A-3] department=sales AND item_category=stationery:")
results_multi = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
    config={
        "filter_groups": [
            {
                "filters": [
                    {
                        "key": "department",
                        "value": {"string_value": "sales"},
                    },
                    {
                        "key": "item_category",
                        "value": {"string_value": "stationery"},
                    },
                ]
            }
        ]
    },
)
multi_memories = list(results_multi)
print(f"   ヒット件数: {len(multi_memories)}")
for i, m in enumerate(multi_memories, 1):
    print(f"    [{i}] fact: {m.memory.fact}")
    if m.memory.metadata:
        print(f"        metadata: {m.memory.metadata}")

# --- (3)-B: システムフィールドフィルタ（filter, EBNF 構文）---
print("\n--- (3)-B: システムフィールドフィルタ（filter）---")

# B-1: fact の部分一致（正規表現）— 記事の例: fact=~".*PC.*"
print('\n  [B-1] fact に「PC」を含むメモリ:')
results_fact = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
    config={
        "filter": 'fact=~".*PC.*"',
    },
)
fact_memories = list(results_fact)
print(f"   ヒット件数: {len(fact_memories)}")
for i, m in enumerate(fact_memories, 1):
    print(f"    [{i}] fact: {m.memory.fact}")

# B-2: create_time でフィルタ（日時の範囲指定）— 記事の例に準拠
print('\n  [B-2] 2026年以降に作成されたメモリ:')
results_time = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
    config={
        "filter": 'create_time>="2026-01-01T00:00:00Z"',
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

# B-4: カスタムトピックでフィルタ（Step 0 で設定したカスタムトピック）
print("\n  [B-4] カスタムトピック ordering_rules でフィルタ:")
results_custom_topic = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
    config={
        "filter": "topics.custom_memory_topic_label: ordering_rules",
    },
)
custom_topic_memories = list(results_custom_topic)
print(f"   ヒット件数: {len(custom_topic_memories)}")
for i, m in enumerate(custom_topic_memories, 1):
    print(f"    [{i}] fact: {m.memory.fact}")

# --- (3)-C: 複合フィルタ（filter + filter_groups の同時利用）---
print("\n--- (3)-C: 複合フィルタ（filter + filter_groups の同時利用）---")

# 記事の例に準拠: 「PC」を含む記憶のうち、2026年以降に作成されたもの
print('\n  department=sales AND fact に「用紙」を含む:')
results_combined = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
    config={
        # メタデータフィルタ
        "filter_groups": [
            {
                "filters": [
                    {
                        "key": "department",
                        "value": {"string_value": "sales"},
                    }
                ]
            }
        ],
        # システムフィールドフィルタ
        "filter": 'fact=~".*用紙.*"',
    },
)
combined_memories = list(results_combined)
print(f"   ヒット件数: {len(combined_memories)}")
for i, m in enumerate(combined_memories, 1):
    print(f"    [{i}] fact: {m.memory.fact}")
    if m.memory.metadata:
        print(f"        metadata: {m.memory.metadata}")

# ============================================================
# (4) セマンティック検索（類似性検索）（記事 3-2 (4) 参照）
# ============================================================
# similarity_search_params を指定することで、意味的な類似度に基づいた
# 検索が可能。ユークリッド距離が最小のものから順にソートされて返る。
#
# 記事の例:「趣味は何？」→「休日はよく絵を描いています」が抽出される
print("\n" + "=" * 60)
print("(4) セマンティック検索（類似性検索）（記事 3-2 (4)）")
print("=" * 60)

# --- クエリ A: いつもの業者を知りたい ---
print('\n--- クエリ A: 「いつもの発注業者は？」 ---')
results_a = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
    similarity_search_params={
        "search_query": "いつもの発注業者は？",
        "top_k": 3,
    },
)
for i, m in enumerate(list(results_a), 1):
    distance_str: Optional[str] = None
    if hasattr(m, "distance") and m.distance is not None:
        distance_str = f"{m.distance:.4f}"
    print(f"  [{i}] fact: {m.memory.fact}")
    print(f"      distance: {distance_str or '(なし)'}")

# --- クエリ B: 納品先についての質問 ---
print('\n--- クエリ B: 「納品先はどこですか？」 ---')
results_b = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
    similarity_search_params={
        "search_query": "納品先はどこですか？",
        "top_k": 3,
    },
)
for i, m in enumerate(list(results_b), 1):
    distance_str = None
    if hasattr(m, "distance") and m.distance is not None:
        distance_str = f"{m.distance:.4f}"
    print(f"  [{i}] fact: {m.memory.fact}")
    print(f"      distance: {distance_str or '(なし)'}")

# --- クエリ C: 予算に関する質問 ---
print('\n--- クエリ C: 「予算の上限は？」 ---')
results_c = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
    similarity_search_params={
        "search_query": "予算の上限は？",
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
# クリーンアップ: user_999 のメモリを削除
# ============================================================
print("=" * 60)
print("🧹 クリーンアップ: user_999 のメモリを削除")
print("=" * 60)
for mem_name in user_999_memory_names:
    client.agent_engines.memories.delete(name=mem_name)
    print(f"   🗑️ 削除: {mem_name}")
print(f"   ✅ user_999 のメモリを {len(user_999_memory_names)} 件削除完了")

# ============================================================
# まとめ
# ============================================================
print("\n" + "=" * 60)
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
