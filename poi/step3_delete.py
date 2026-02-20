"""
Step 3: メモリの削除

メモリを削除する方法を体験するスクリプト。

  1. 名前指定の削除（delete）
  2. フィルタ指定の一括削除 — ドライラン（purge, force=False）
  3. フィルタ指定の一括削除 — 実行（purge, force=True）
  4. セマンティック削除（generate で「忘れて」指示）
  5. 最終確認（retrieve で残りのメモリを確認）

⚠️ このスクリプトはメモリを実際に削除する。
   再実行する場合は先に Step 1 を実行してメモリを作り直すこと。

📝 update() について:
   公式ドキュメントに update() の記載があるが、これはメタデータ専用。
   fact（事実）を直接書き換えるメソッドは存在しない。
   fact を変更したい場合は generate() で統合するか、rollback() で戻す。
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

SCOPE = {"user_id": "user-1"}


# --- ヘルパー関数 ---
def show_all_memories(label: str) -> list[object]:
    """現在のメモリを一覧表示するヘルパー"""
    results = client.agent_engines.memories.retrieve(
        name=AGENT_ENGINE_NAME,
        scope=SCOPE,
    )
    memories = list(results)
    print(f"\n   📋 {label}: {len(memories)} 件")
    for i, m in enumerate(memories, 1):
        print(f"     [{i}] fact: {m.memory.fact}")
        if m.memory.metadata:
            print(f"         metadata: {m.memory.metadata}")
    return memories



# ============================================================
# 1. 名前指定の削除（delete）
# ============================================================
# delete() で特定のメモリを name で削除する。
# delete() は同期操作のため、呼び出しが戻ると削除は完了している。
print("\n" + "=" * 60)
print("🗑️  1. 名前指定の削除（delete）")
print("=" * 60)

# 削除用のメモリを1件作成してから削除する
print("   まず削除テスト用のメモリを作成...")
create_op = client.agent_engines.memories.create(
    name=AGENT_ENGINE_NAME,
    fact="これは削除テスト用のメモリです",
    scope=SCOPE,
)
delete_target_name: str = create_op.response.name
print(f"   作成完了: {delete_target_name}")

# 削除実行（同期操作）
client.agent_engines.memories.delete(
    name=delete_target_name,
)
print(f"   ✅ delete() 完了")

# 削除されたか確認
try:
    deleted_memory = client.agent_engines.memories.get(name=delete_target_name)
    print(f"   ❌ まだ存在しています: {deleted_memory.fact}")
except Exception as e:
    print(f"   ✅ 削除確認: メモリは存在しません（期待通り）")
    print(f"      エラー: {type(e).__name__}")

# ============================================================
# 2. フィルタ指定の一括削除 — ドライラン（purge, force=False）
# ============================================================
# purge() はフィルタに合致するメモリを一括削除する。
# force=False にすると実際には削除せず、削除対象の件数だけ返す。
# これにより「何件消えるか」を事前に確認できる。
#
# filter（システムフィールド）または filter_groups（メタデータ）
# の少なくとも1つを指定する必要がある。
print("\n" + "=" * 60)
print("🔍 2. フィルタ指定の一括削除 — ドライラン（purge）")
print("=" * 60)

# まず purge テスト用のメモリを作成
print("   purge テスト用のメモリを作成...")
for i in range(3):
    client.agent_engines.memories.create(
        name=AGENT_ENGINE_NAME,
        fact=f"purge テスト用メモリ #{i + 1}",
        scope=SCOPE,
        config={
            "metadata": {
                "for_purge": {"string_value": "yes"},
            },
        },
    )
print("   3件作成完了")

# ドライラン: force=False で件数確認
print("\n   --- ドライラン（force=False）---")
dry_run_op = client.agent_engines.memories.purge(
    name=AGENT_ENGINE_NAME,
    filter_groups=[
        {
            "filters": [
                {
                    "key": "for_purge",
                    "value": {"string_value": "yes"},
                }
            ]
        }
    ],
    force=False,  # ドライラン: 実際には削除しない
    config={"wait_for_completion": True},
)
purge_count_dry: int = dry_run_op.response.purge_count
print(f"   削除対象件数: {purge_count_dry} 件（まだ削除されていない）")

# ============================================================
# 3. フィルタ指定の一括削除 — 実行（purge, force=True）
# ============================================================
# force=True にすると実際に削除される。
print("\n" + "=" * 60)
print("💥 3. フィルタ指定の一括削除 — 実行（purge）")
print("=" * 60)

purge_op = client.agent_engines.memories.purge(
    name=AGENT_ENGINE_NAME,
    filter_groups=[
        {
            "filters": [
                {
                    "key": "for_purge",
                    "value": {"string_value": "yes"},
                }
            ]
        }
    ],
    force=True,  # 実行: 実際に削除する
    config={"wait_for_completion": True},
)
purge_count: int = purge_op.response.purge_count
print(f"   ✅ purge() 完了: {purge_count} 件削除")

# ============================================================
# 4. セマンティック削除（generate で「忘れて」指示）
# ============================================================
# generate() に「忘れて」という自然言語の指示を渡すと、
# LLM が既存メモリの中から該当するものを判断して削除する。
# EXPLICIT_INSTRUCTIONS トピックが設定されている場合に機能する。
#
# ⚠️ LLM の判断に依存するため、結果は非決定的。
#    確実に削除したい場合は delete() や purge() を使うこと。
print("\n" + "=" * 60)
print("🧠 4. セマンティック削除（generate による忘却指示）")
print("=" * 60)

# セマンティック削除テスト用のメモリを作成
print("   セマンティック削除テスト用のメモリを作成...")
client.agent_engines.memories.create(
    name=AGENT_ENGINE_NAME,
    fact="好きな食べ物はカレーです",
    scope=SCOPE,
)
print("   作成完了: 「好きな食べ物はカレーです」")

# 「忘れて」指示を generate() で送信
print("\n   「食べ物の好みを忘れて」と指示...")
forget_op = client.agent_engines.memories.generate(
    name=AGENT_ENGINE_NAME,
    direct_contents_source={
        "events": [
            {
                "content": {
                    "role": "user",
                    "parts": [{"text": "食べ物の好みを忘れてください。"}],
                }
            }
        ]
    },
    scope=SCOPE,
)

print(f"   ✅ generate() 完了 (done={forget_op.done})")
if forget_op.response is not None:
    for i, gm in enumerate(forget_op.response.generated_memories, 1):
        print(f"   [{i}] action={gm.action}")
        if gm.memory:
            print(f"        memory name={gm.memory.name}")
else:
    print("   response=None")

# ============================================================
# 5. 最終確認（全メモリを表示）
# ============================================================
print("\n" + "=" * 60)
print("📊 5. 最終確認")
print("=" * 60)

final_memories = show_all_memories("最終状態")

print(f"""
操作方法の整理:

| メソッド      | 用途                              | 確実性    |
|-------------|-----------------------------------|----------|
| delete()    | 名前を指定して1件削除                 | 確実      |
| purge()     | フィルタで一括削除（ドライラン可）      | 確実      |
| generate()  | 自然言語で「忘れて」指示              | 非決定的   |

📝 update() はメタデータ専用。fact を直接書き換えることはできない。
   fact の変更は generate() で統合するか rollback() で戻す。
""")

print(f"🎉 Step 3 完了！")
