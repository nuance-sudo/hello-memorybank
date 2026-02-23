"""
Step 1b: 統合（Consolidation）のデモ（記事 3-1 (5) に対応）

GenerateMemories は単純な追記ではなく、LLM による「統合」を行う。
既存の記憶と新しい情報を比較し、CREATED / UPDATED / DELETED を自動判断する。

このスクリプトでは、step1a で作成された「A4用紙の業者はA社」という既存の記憶に対して
「業者をC社に変更」という矛盾する情報を送り、統合の動作を確認する。

前提: step1a_basics.py が実行済みで、user_123 にメモリが存在すること。

実行方法:
  uv run python src/step1b_consolidation.py
"""

import datetime
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
# 統合前の状態を確認
# ============================================================
print("\n" + "=" * 60)
print("📥 統合前の状態確認")
print("=" * 60)

before_results = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
)
before_memories = list(before_results)
print(f"   現在のメモリ数: {len(before_memories)} 件")
for i, m in enumerate(before_memories, 1):
    print(f"   [{i}] {m.memory.fact}")

# ============================================================
# (5) 統合（Consolidation）のデモ（記事 3-1 (5) 参照）
# ============================================================
# 新しいセッションで「業者の変更」を伝える。
# 既存の記憶「A4用紙の業者はA社」に矛盾する新情報を送り、
# LLM が UPDATED/CREATED/DELETED のどれを選ぶか確認する。
#
# 【記事の具体例】
#   既存の記憶: 「A4用紙のデフォルト発注業者はA社」
#   今回の会話: 「来月からA4用紙の業者はC社に変更して」
#   期待される動作: 既存の「A社」の記憶を「C社」に更新（UPDATED）
print("\n" + "=" * 60)
print("(5) 統合（Consolidation）のデモ（記事 3-1 (5)）")
print("=" * 60)

session_consol = client.agent_engines.sessions.create(
    name=AGENT_ENGINE_NAME,
    user_id=USER_ID,
)
session_consol_name: str = session_consol.response.name

# 既存の記憶「A4用紙の業者はA社」に矛盾する新情報を送る
consolidation_conversation: list[dict[str, str]] = [
    {"role": "user", "text": "来月からA4用紙の業者はC社に変更して。A社はもう使いません。"},
]

for i, msg in enumerate(consolidation_conversation):
    client.agent_engines.sessions.events.append(
        name=session_consol_name,
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

op_consol = client.agent_engines.memories.generate(
    name=AGENT_ENGINE_NAME,
    vertex_session_source={"session": session_consol_name},
    scope=SCOPE,
)

print(f"   ✅ generate() 完了 (done={op_consol.done})")
if op_consol.response is not None:
    for i, gm in enumerate(op_consol.response.generated_memories, 1):
        action_name: str = str(gm.action).split(".")[-1]  # CREATED / UPDATED / DELETED
        print(f"   [{i}] action={action_name}")
        # DELETED の場合、メモリは既に削除されているため get() できない
        if "DELETED" in action_name:
            print(f"        → 古い記憶が削除された（name={gm.memory.name}）")
        else:
            memory = client.agent_engines.memories.get(name=gm.memory.name)
            print(f"        fact={memory.fact}")
    print(f"\n   💡 統合の結果:")
    print(f"      UPDATED → 既存の「A社」が「C社」に更新された")
    print(f"      CREATED → 全く新しい事実が追加された")
    print(f"      DELETED → 矛盾する古い記憶が削除された")
else:
    print("   response=None（メモリ未生成）")

# ============================================================
# 統合後の状態を確認
# ============================================================
print("\n" + "=" * 60)
print("📥 統合後の状態確認")
print("=" * 60)

after_results = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
)
after_memories = list(after_results)
print(f"   現在のメモリ数: {len(after_memories)} 件")
for i, m in enumerate(after_memories, 1):
    print(f"   [{i}] {m.memory.fact}")

print(f"""
🎉 Step 1b 完了！

学習したこと:
  (5) GenerateMemories は単純な追記ではなく LLM による「統合」を行う
      - CREATED: 新しい事実の追加
      - UPDATED: 既存の記憶を最新情報で更新（例：業者A社→C社）
      - DELETED: 矛盾する古い記憶を削除

次のステップ:
  → step1c_metadata.py でメタデータの付与と更新戦略を体験
""")
