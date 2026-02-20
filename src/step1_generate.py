"""
Step 1: メモリの作成（Sessions 連携 & create）

メモリを作る方法は2つある:
  - generate(): 会話データから LLM がファクトを自動抽出・統合する
  - create():   自分で指定したファクトをそのまま保存する

このステップでは Sessions API を使って会話を記録し、
そこからメモリを生成する「本来のフロー」を体験する。

  1. セッション作成（sessions.create）
  2. イベント追加（sessions.events.append）
  3. Sessions からメモリ生成（generate + vertex_session_source）
  4. create() — ファクトを直接保存
  5. generate() + メタデータ — メモリにタグを付与
  6. カスタムトピックの動作確認
  7. 最終確認 — 全メモリ一覧

📝 direct_contents_source について:
   Sessions を使わず、generate() に会話データを直接渡すこともできる。
   テストや外部システム連携で Sessions を使わない場合に便利。
   例: generate(direct_contents_source={"events": [...]}, scope=SCOPE)
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

USER_ID = "user-1"

# ============================================================
# 1. セッション作成
# ============================================================
# sessions.create() でセッションを作成する。
# user_id を渡すと、generate() 時のスコープが自動的に
# {"user_id": USER_ID} に設定される。
print("\n" + "=" * 60)
print("📡 1. セッション作成")
print("=" * 60)

session = client.agent_engines.sessions.create(
    name=AGENT_ENGINE_NAME,
    user_id=USER_ID,
)

session_name: str = session.response.name
print(f"   ✅ セッション作成完了")
print(f"   session name: {session_name}")
print(f"   user_id: {USER_ID}")

# ============================================================
# 2. イベント追加（会話の記録）
# ============================================================
# sessions.events.append() で会話イベントを1件ずつ追加する。
# author: イベントの作成者（Sessions API で必須）
# invocation_id: 1回のやり取り（ターン）を識別する ID
# timestamp: イベントのタイムスタンプ（UTC）
# config.content: 会話内容（Content 形式）
print("\n" + "=" * 60)
print("💬 2. イベント追加（会話の記録）")
print("=" * 60)

# ユーザーとモデルの会話データ
conversation: list[dict[str, str]] = [
    {"role": "user", "text": "こんにちは！私はPythonが好きなエンジニアです。最近はLLMエージェントの開発をしています。"},
    {"role": "model", "text": "こんにちは！Pythonでエージェント開発をされているんですね。どんなエージェントを作っていますか？"},
    {"role": "user", "text": "絵の練習を支援するコーチングエージェントです。ユーザーが描いた絵を分析してフィードバックします。趣味は絵を描くことと猫と遊ぶことです。"},
]

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
    print(f"   [{i + 1}] {msg['role']}: {msg['text'][:50]}...")

print(f"\n   ✅ {len(conversation)} 件のイベントを追加完了")

# ============================================================
# 3. Sessions からメモリ生成（vertex_session_source）
# ============================================================
# generate() に vertex_session_source を渡すことで、
# Sessions に記録された会話からメモリを自動生成する。
#
# direct_contents_source との違い:
# - 会話データを渡す必要がない（Session の名前だけでOK）
# - scope は省略可能（session の user_id から自動設定）
# - start_time / end_time で時間範囲の指定も可能
print("\n" + "=" * 60)
print("🧠 3. Sessions からメモリ生成（vertex_session_source）")
print("=" * 60)

operation = client.agent_engines.memories.generate(
    name=AGENT_ENGINE_NAME,
    vertex_session_source={
        "session": session_name,
    },
    # scope は省略可能。省略すると {"user_id": session.user_id} が自動適用。
)

print(f"✅ generate() 完了 (done={operation.done})")
if operation.response is not None:
    generated = operation.response.generated_memories
    print(f"   自動抽出: {len(generated)} 件")
    for i, gm in enumerate(generated, 1):
        memory = client.agent_engines.memories.get(name=gm.memory.name)
        print(f"   [{i}] action={gm.action}")
        print(f"        fact={memory.fact}")
else:
    print("   response=None（メモリ未生成）")

# ============================================================
# 4. create() — ファクトを直接保存
# ============================================================
# create() は自分で指定した fact をそのまま保存する。
# generate() と違い、LLM による抽出・統合は行われない。
# Sessions を使わず、直接メモリを追加したい場合に使う。
print("\n" + "=" * 60)
print("📝 4. create() — ファクトを直接保存")
print("=" * 60)

create_op = client.agent_engines.memories.create(
    name=AGENT_ENGINE_NAME,
    fact="好きなエディタは VS Code です",
    scope={"user_id": USER_ID},
)

created_memory = create_op.response
print(f"✅ create() 完了")
print(f"   fact: {created_memory.fact}")
print(f"   name: {created_memory.name}")
print(f"   scope: {created_memory.scope}")

# ============================================================
# 5. 保存されたメモリを全件取得して確認
# ============================================================
print("\n" + "=" * 60)
print("📥 5. 保存されたメモリを全件取得")
print("=" * 60)

results = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope={"user_id": USER_ID},
)
memories = list(results)

print(f"   合計: {len(memories)} 件")
for i, m in enumerate(memories, 1):
    print(f"\n  [{i}] fact: {m.memory.fact}")
    print(f"      scope: {m.memory.scope}")

# ============================================================
# 6. generate() + メタデータ — メモリにタグを付与
# ============================================================
# generate() の config にメタデータを渡すと、メモリに構造化タグを付与できる。
# メタデータは retrieve() でのフィルタリングに使える。
#
# ここでは Sessions ではなく direct_contents_source を使う例も示す。
# テストやバッチ処理など、Sessions を介さない場合に便利。
print("\n" + "=" * 60)
print("🏷️  6. generate() + メタデータ（direct_contents_source の例）")
print("=" * 60)

operation_meta = client.agent_engines.memories.generate(
    name=AGENT_ENGINE_NAME,
    # Sessions を使わず直接渡す例
    direct_contents_source={
        "events": [
            {
                "content": {
                    "role": "user",
                    "parts": [{"text": "最近 TypeScript も勉強し始めました。Next.js でWebアプリを作っています。"}]
                }
            },
        ]
    },
    scope={"user_id": USER_ID},
    config={
        "metadata": {
            "category": {"string_value": "learning"},
        },
    },
)

print(f"✅ メタデータ付き generate() 完了")
if operation_meta.response is not None:
    for i, gm in enumerate(operation_meta.response.generated_memories, 1):
        memory = client.agent_engines.memories.get(name=gm.memory.name)
        print(f"   [{i}] action={gm.action}")
        print(f"        fact={memory.fact}")
        print(f"        metadata={memory.metadata}")

# ============================================================
# 7. カスタムトピックの動作確認 — 技術スキルの抽出
# ============================================================
# Step 0 でカスタムトピック（technical_skills）を設定済み。
# ここでも Sessions 経由で技術的な会話を記録してメモリ化する。
print("\n" + "=" * 60)
print("🎯 7. カスタムトピックの動作確認")
print("=" * 60)

# 新しいセッションを作成
session2 = client.agent_engines.sessions.create(
    name=AGENT_ENGINE_NAME,
    user_id=USER_ID,
)
session2_name: str = session2.response.name

# 技術スキルに関する会話を追加
tech_conversation: list[dict[str, str]] = [
    {"role": "user", "text": "Dockerは毎日使っています。Kubernetesは基本的な操作ならできます。CIはGitHub Actionsを使っています。"},
]

for i, msg in enumerate(tech_conversation):
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
)

print(f"✅ カスタムトピック付き generate() 完了")
if operation_custom.response is not None:
    for i, gm in enumerate(operation_custom.response.generated_memories, 1):
        memory = client.agent_engines.memories.get(name=gm.memory.name)
        print(f"   [{i}] action={gm.action}")
        print(f"        fact={memory.fact}")

# ============================================================
# 8. 最終確認 — 全メモリ一覧
# ============================================================
print("\n" + "=" * 60)
print("📥 8. 最終確認 — 全メモリ一覧")
print("=" * 60)

all_results = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope={"user_id": USER_ID},
)
all_memories = list(all_results)

print(f"   合計: {len(all_memories)} 件")
for i, m in enumerate(all_memories, 1):
    print(f"\n  [{i}] fact: {m.memory.fact}")
    if m.memory.metadata:
        print(f"      metadata: {m.memory.metadata}")

print(f"\n🎉 Step 1 完了！")
