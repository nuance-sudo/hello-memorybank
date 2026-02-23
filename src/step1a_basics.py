"""
Step 1a: メモリ生成の基本（記事 3-1 (1)(3)(4) に対応）

メモリ生成の基本フローを体験するスクリプト。

  (1) スコープの定義とセッション作成
  (4) Generate と Create の違い
  (3) 生成されるメモリのデータ構造の確認

実行順: (1) → (4) → (3)（まず基本を押さえてから構造を確認）
前提: Step 0 が実行済みで、AGENT_ENGINE_NAME が .env に設定されていること。

実行方法:
  uv run python src/step1a_basics.py
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

# ============================================================
# (1) スコープの定義とセッション作成（記事 3-1 (1) 参照）
# ============================================================
# スコープは複合キー（最大5要素）として定義でき、
# 記憶の帰属先（誰の・どの文脈の記憶か）を決定する。
# Sessions API でセッションを作成すると user_id がスコープに設定される。
# 複合キー（例: system_id の追加）は generate() の scope で明示指定する。
print("\n" + "=" * 60)
print("(1) スコープの定義とセッション作成（記事 3-1 (1)）")
print("=" * 60)

# セッション作成（user_id が自動的にスコープに含まれる）
session = client.agent_engines.sessions.create(
    name=AGENT_ENGINE_NAME,
    user_id=USER_ID,
)

# 複合スコープの定義（最大5つまで設定可能）
# generate()/retrieve() で scope を渡すことで system_id 等を追加できる
SCOPE = {"user_id": USER_ID, "system_id": "order_management"}

session_name: str = session.response.name
print(f"   ✅ セッション作成完了")
print(f"   session name: {session_name}")
print(f"   user_id: {USER_ID}")
print(f"   → スコープ（generate時に指定）: {SCOPE}")

# 会話イベントを追加（記事②のトピック分類例に準拠）
# - 挨拶はトピックに該当せず記憶されない
# - 発注の好み・ルールは「ユーザーの好み」「重要な詳細」として記憶される
# - 「覚えておいて」は「明示的な指示」として記憶される
conversation: list[dict[str, str]] = [
    {"role": "user", "text": "お疲れ様です。今日は発注が多いですね"},
    {"role": "model", "text": "お疲れ様です！発注のお手伝いをしますね。何を発注しますか？"},
    {"role": "user", "text": "A4コピー用紙を発注して。業者はいつも通りA社でお願い。来月からは納品先を2階のオフィスに変更することを覚えておいて"},
]

print(f"\n   💬 会話イベントを追加中...")
for i, msg in enumerate(conversation):
    client.agent_engines.sessions.events.append(
        name=session_name,
        author="user",  # Sessions API の要件
        invocation_id=str((i // 2) + 1),  # 2メッセージで1ターン
        timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
        config={
            "content": {
                "role": msg["role"],
                "parts": [{"text": msg["text"]}],
            }
        },
    )
    print(f"   [{i + 1}] {msg['role']}: {msg['text'][:60]}...")

print(f"\n   ✅ {len(conversation)} 件のイベントを追加完了")

# ============================================================
# (4) Generate と Create の違い（記事 3-1 (4) 参照）
# ============================================================
# GenerateMemories: セッションの会話履歴を元に LLM が自動で事実を抽出・統合
# CreateMemory: 抽出済みの事実を直接 Memory Bank に書き込む（統合なし）
print("\n" + "=" * 60)
print("(4)-a GenerateMemories でメモリ生成（記事 3-1 (4)）")
print("=" * 60)

operation = client.agent_engines.memories.generate(
    name=AGENT_ENGINE_NAME,
    vertex_session_source={
        "session": session_name,
    },
    # scope で複合キーを明示指定（system_id を含める）
    scope=SCOPE,
)

print(f"   ✅ generate() 完了 (done={operation.done})")
if operation.response is not None:
    generated = operation.response.generated_memories
    print(f"   自動抽出: {len(generated)} 件")
    for i, gm in enumerate(generated, 1):
        memory = client.agent_engines.memories.get(name=gm.memory.name)
        print(f"   [{i}] action={gm.action}")
        print(f"        fact={memory.fact}")
else:
    print("   response=None（メモリ未生成）")

print("\n" + "=" * 60)
print("(4)-b CreateMemory でファクトを直接保存（記事 3-1 (4)）")
print("=" * 60)
# create() は統合を行わないため、同じスコープ内で記憶が重複するリスクに注意。
create_op = client.agent_engines.memories.create(
    name=AGENT_ENGINE_NAME,
    fact="A4コピー用紙の発注先はA社です",
    scope=SCOPE,
)

created_memory = create_op.response
print(f"   ✅ create() 完了")
print(f"   fact: {created_memory.fact}")
print(f"   name: {created_memory.name}")
print(f"   scope: {created_memory.scope}")
print(f"   → create() は統合を行わず、そのまま保存される")

# ============================================================
# (3) 生成されるメモリのデータ構造（記事 3-1 (3) 参照）
# ============================================================
# 保存されたメモリは構造化された Memory オブジェクトとして生成される。
# fact, scope, metadata, topics, create_time, update_time を持つ。
print("\n" + "=" * 60)
print("(3) 生成されるメモリのデータ構造の確認（記事 3-1 (3)）")
print("=" * 60)

results = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
)
memories = list(results)

print(f"   合計: {len(memories)} 件")
for i, m in enumerate(memories, 1):
    print(f"\n  [{i}] fact: {m.memory.fact}")
    print(f"      scope: {m.memory.scope}")
    if m.memory.metadata:
        print(f"      metadata: {m.memory.metadata}")
    if hasattr(m.memory, "topics") and m.memory.topics:
        print(f"      topics: {m.memory.topics}")
    print(f"      create_time: {m.memory.create_time}")
    print(f"      update_time: {m.memory.update_time}")

# ============================================================
# まとめ
# ============================================================
print(f"""
🎉 Step 1a 完了！

学習したこと:
  (1) スコープ = 記憶の帰属先（複合キー、最大5要素）
      例: {{"user_id": "user_123", "system_id": "order_management"}}
  (4) generate() = LLM が会話から自動抽出・統合
      create()   = 抽出済みの事実をそのまま保存（統合なし）
  (3) Memory オブジェクト = fact + scope + metadata + topics + timestamps

次のステップ:
  → step1b_consolidation.py で統合（Consolidation）のデモを体験
""")
