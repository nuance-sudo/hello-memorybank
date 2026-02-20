"""
Step 4: メモリライフサイクル（リビジョン）

メモリが作成・更新・削除されるたびに自動保存される MemoryRevision の
仕組みを体験するスクリプト。

  1. メモリ作成 → リビジョン確認
  2. generate() で更新 → リビジョン蓄積確認
  3. ロールバック（以前のリビジョンに戻す）
  4. リビジョンラベル（ラベル付与とフィルタ）
  5. クリーンアップ

📖 公式ドキュメント:
   https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/revisions
"""

import os
import time

import vertexai
from dotenv import load_dotenv
from vertexai._genai import types

load_dotenv()

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
LOCATION = os.environ["GCP_LOCATION"]
AGENT_ENGINE_NAME = os.environ["AGENT_ENGINE_NAME"]

client = vertexai.Client(project=PROJECT_ID, location=LOCATION)
print(f"✅ Client 初期化完了")
print(f"   Agent Engine: {AGENT_ENGINE_NAME}")

# リビジョン操作用のスコープ
SCOPE = {"user_id": "lifecycle-test-user"}


# --- ヘルパー関数 ---
def show_revisions(memory_name: str, label: str) -> list[types.MemoryRevision]:
    """メモリのリビジョン一覧を表示するヘルパー"""
    revisions = list(
        client.agent_engines.memories.revisions.list(name=memory_name)
    )
    print(f"\n   📋 {label}: {len(revisions)} 件のリビジョン")
    for i, rev in enumerate(revisions, 1):
        # リビジョン ID はリソース名の最後のセグメント
        rev_id: str = rev.name.split("/")[-1] if rev.name else "N/A"
        print(f"     [{i}] revision_id: {rev_id}")
        print(f"         fact: {rev.fact}")
        print(f"         create_time: {rev.create_time}")
        if rev.extracted_memories:
            for em in rev.extracted_memories:
                print(f"         extracted: {em.fact}")
        if rev.labels:
            print(f"         labels: {rev.labels}")
    return revisions


# ============================================================
# 1. メモリ作成 → リビジョン確認
# ============================================================
# メモリを作成すると、Memory リソースと子 MemoryRevision が
# 1件ずつ自動的に作成される。
print("\n" + "=" * 60)
print("📝 1. メモリ作成 → リビジョン確認")
print("=" * 60)

create_op = client.agent_engines.memories.create(
    name=AGENT_ENGINE_NAME,
    fact="好きなプログラミング言語は Python です",
    scope=SCOPE,
)
memory_name: str = create_op.response.name
print(f"   ✅ メモリ作成完了: {memory_name}")

# 作成直後のメモリを確認
memory = client.agent_engines.memories.get(name=memory_name)
print(f"   fact: {memory.fact}")

# リビジョンを確認（1件のはず）
revisions_after_create = show_revisions(memory_name, "作成後のリビジョン")

# ============================================================
# 2. generate() で更新 → リビジョン蓄積確認
# ============================================================
# 同じスコープで generate() を呼ぶと、既存メモリと重複・補完する
# 情報は統合（マージ）され、新しいリビジョンが追加される。
print("\n" + "=" * 60)
print("🔄 2. generate() で更新 → リビジョン蓄積確認")
print("=" * 60)

print("   generate() で追加情報を送信...")
gen_op = client.agent_engines.memories.generate(
    name=AGENT_ENGINE_NAME,
    direct_contents_source={
        "events": [
            {
                "content": {
                    "role": "user",
                    "parts": [
                        {
                            "text": "特に Python のデータ分析ライブラリ（pandas, numpy）が得意です。"
                             "最近は FastAPI でバックエンド開発もしています。"
                        }
                    ],
                }
            }
        ]
    },
    scope=SCOPE,
    config={"wait_for_completion": True},
)

print(f"   ✅ generate() 完了 (done={gen_op.done})")
if gen_op.response is not None:
    for i, gm in enumerate(gen_op.response.generated_memories, 1):
        print(f"   [{i}] action={gm.action}")
        if gm.memory:
            print(f"        fact: {gm.memory.fact}")
        if gm.previous_revision:
            print(f"        previous_revision: {gm.previous_revision}")

# 更新後のメモリ本体を確認
memory_updated = client.agent_engines.memories.get(name=memory_name)
print(f"\n   📖 更新後の fact: {memory_updated.fact}")

# リビジョンを確認（2件以上になっているはず）
revisions_after_update = show_revisions(memory_name, "更新後のリビジョン")

# ============================================================
# 3. ロールバック
# ============================================================
# rollback() で、メモリを過去のリビジョンの状態に戻す。
# ロールバック自体も新しいリビジョンとして記録される。
print("\n" + "=" * 60)
print("⏪ 3. ロールバック（作成時の状態に戻す）")
print("=" * 60)

if len(revisions_after_create) > 0:
    # 作成時のリビジョン ID を取得（一覧の最後 = 最も古いリビジョン）
    oldest_revision = revisions_after_create[-1]
    target_revision_id: str = oldest_revision.name.split("/")[-1]
    print(f"   ロールバック先: revision_id={target_revision_id}")
    print(f"   ロールバック先の fact: {oldest_revision.fact}")

    # ロールバック実行
    rollback_op = client.agent_engines.memories.rollback(
        name=memory_name,
        target_revision_id=target_revision_id,
        config={"wait_for_completion": True},
    )
    print(f"   ✅ rollback() 完了 (done={rollback_op.done})")

    # ロールバック後のメモリを確認
    memory_rollback = client.agent_engines.memories.get(name=memory_name)
    print(f"   📖 ロールバック後の fact: {memory_rollback.fact}")

    # リビジョンを確認（ロールバック分が追加されているはず）
    show_revisions(memory_name, "ロールバック後のリビジョン")
else:
    print("   ⚠️ リビジョンが見つかりません。スキップします。")

# ============================================================
# 4. リビジョンラベル
# ============================================================
# generate() の config.revision_labels でラベルを付与できる。
# revisions.list() の config.filter でラベルによるフィルタリングが可能。
print("\n" + "=" * 60)
print("🏷️  4. リビジョンラベル")
print("=" * 60)

# ラベル付きで generate() を実行
print("   ラベル付きで generate() を実行...")
label_op = client.agent_engines.memories.generate(
    name=AGENT_ENGINE_NAME,
    direct_contents_source={
        "events": [
            {
                "content": {
                    "role": "user",
                    "parts": [
                        {
                            "text": "最近 Rust にも興味を持ち始めました。"
                        }
                    ],
                }
            }
        ]
    },
    scope=SCOPE,
    config={
        "wait_for_completion": True,
        "revision_labels": {
            "data_source": "step4_test",
            "batch_id": "batch_001",
        },
    },
)
print(f"   ✅ generate() 完了 (done={label_op.done})")

if label_op.response is not None:
    for gm in label_op.response.generated_memories:
        if gm.memory:
            labeled_memory_name: str = gm.memory.name
            print(f"   対象メモリ: {labeled_memory_name}")

            # ラベルでフィルタしてリビジョンを一覧
            print("\n   --- ラベルフィルタで検索 ---")
            filtered_revisions = list(
                client.agent_engines.memories.revisions.list(
                    name=labeled_memory_name,
                    config={
                        "filter": 'labels.data_source="step4_test"',
                    },
                )
            )
            print(f"   フィルタ結果: {len(filtered_revisions)} 件")
            for i, rev in enumerate(filtered_revisions, 1):
                rev_id = rev.name.split("/")[-1] if rev.name else "N/A"
                print(f"     [{i}] revision_id: {rev_id}")
                print(f"         fact: {rev.fact}")
                print(f"         labels: {rev.labels}")

            # 全リビジョンも表示して比較
            show_revisions(labeled_memory_name, "全リビジョン（比較用）")

# ============================================================
# 5. クリーンアップ
# ============================================================
print("\n" + "=" * 60)
print("🧹 5. クリーンアップ")
print("=" * 60)

# テスト用メモリの削除
# purge ではなく、scopeで全メモリを取得して個別に削除
cleanup_results = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
)
cleanup_memories = list(cleanup_results)
print(f"   削除対象: {len(cleanup_memories)} 件")

for m in cleanup_memories:
    client.agent_engines.memories.delete(name=m.memory.name)
    print(f"   ✅ 削除: {m.memory.fact[:40]}...")

print(f"""
{'=' * 60}
📊 まとめ
{'=' * 60}

メモリリビジョンのライフサイクル:

┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  create()   │───▶│ Revision #1 │    │  Memory     │
│             │    │ (初期状態)   │    │ (最新の fact│
└─────────────┘    └─────────────┘    │  を保持)    │
                                      └─────────────┘
┌─────────────┐    ┌─────────────┐         │
│ generate()  │───▶│ Revision #2 │─────────┘
│ / update()  │    │ (統合後)    │   ← Memory の fact が更新される
└─────────────┘    └─────────────┘

┌─────────────┐    ┌─────────────┐
│ rollback()  │───▶│ Revision #3 │   ← 指定リビジョンの fact に戻る
│             │    │ (ロールバック)│      ロールバック自体も記録
└─────────────┘    └─────────────┘

┌─────────────┐    ┌─────────────┐
│  delete()   │───▶│ Revision #N │   ← fact が空の最終リビジョン
│             │    │ (削除記録)  │      48時間は revisions にアクセス可能
└─────────────┘    └─────────────┘

主要 API:
| メソッド                  | 用途                              |
|--------------------------|-----------------------------------|
| revisions.list(name)     | メモリのリビジョン一覧を取得          |
| revisions.get(name)      | 特定のリビジョンを取得               |
| rollback(name, rev_id)   | 過去のリビジョンに戻す               |
| config.revision_labels   | generate() 時にラベルを付与          |
| config.revision_ttl      | リビジョンの保持期間（デフォルト365日）  |
""")

print("🎉 Step 4 完了！")
