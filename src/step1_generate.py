"""
Step 1: メモリの生成と保存（記事 3-1 に対応）

記事の「3-1. メモリの生成と保存」セクション（①〜⑨）を
実際のコードで体験するハンズオンスクリプト。

  ① スコープの定義とセッション作成
  ② トピック（Topics）の動作確認
  ③ 生成されるメモリのデータ構造の確認
  ④ Generate と Create の違い
  ⑤ 統合（Consolidation）のデモ
  ⑥ メタデータ（Metadata）の付与
  ⑦ メタデータの更新戦略（metadata_merge_strategy）
  ⑧ マルチモーダル入力からのメモリ生成
  ⑨ 非同期生成
  最終確認 — 全メモリ一覧

前提: Step 0 が実行済みで、AGENT_ENGINE_NAME が .env に設定されていること。
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

USER_ID = "user-1"

# ============================================================
# ① スコープの定義とセッション作成（記事 3-1 ① 参照）
# ============================================================
# スコープは複合キー（最大5要素）として定義でき、
# 記憶の帰属先（誰の・どの文脈の記憶か）を決定する。
# Sessions API でセッションを作成すると user_id がスコープに設定される。
print("\n" + "=" * 60)
print("① スコープの定義とセッション作成（記事 3-1 ①）")
print("=" * 60)

session = client.agent_engines.sessions.create(
    name=AGENT_ENGINE_NAME,
    user_id=USER_ID,
)

session_name: str = session.response.name
print(f"   ✅ セッション作成完了")
print(f"   session name: {session_name}")
print(f"   user_id: {USER_ID}")
print(f"   → スコープは自動的に {{\"user_id\": \"{USER_ID}\"}} に設定される")

# 会話イベントを追加
conversation: list[dict[str, str]] = [
    {"role": "user", "text": "こんにちは！私はPythonが好きなエンジニアです。最近はLLMエージェントの開発をしています。"},
    {"role": "model", "text": "こんにちは！Pythonでエージェント開発をされているんですね。どんなエージェントを作っていますか？"},
    {"role": "user", "text": "絵の練習を支援するコーチングエージェントです。ユーザーが描いた絵を分析してフィードバックします。趣味は絵を描くことと猫と遊ぶことです。"},
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
    print(f"   [{i + 1}] {msg['role']}: {msg['text'][:50]}...")

print(f"\n   ✅ {len(conversation)} 件のイベントを追加完了")

# ============================================================
# ④ Generate と Create の違い（記事 3-1 ④ 参照）
# ============================================================
# GenerateMemories: セッションの会話履歴を元に LLM が自動で事実を抽出・統合
# CreateMemory: 抽出済みの事実を直接 Memory Bank に書き込む（統合なし）
print("\n" + "=" * 60)
print("④-a GenerateMemories でメモリ生成（記事 3-1 ④）")
print("=" * 60)

operation = client.agent_engines.memories.generate(
    name=AGENT_ENGINE_NAME,
    vertex_session_source={
        "session": session_name,
    },
    # scope は省略可能。省略すると {"user_id": session.user_id} が自動適用。
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
print("④-b CreateMemory でファクトを直接保存（記事 3-1 ④）")
print("=" * 60)
# create() は統合を行わないため、同じスコープ内で記憶が重複するリスクに注意。
create_op = client.agent_engines.memories.create(
    name=AGENT_ENGINE_NAME,
    fact="好きなエディタは VS Code です",
    scope={"user_id": USER_ID},
)

created_memory = create_op.response
print(f"   ✅ create() 完了")
print(f"   fact: {created_memory.fact}")
print(f"   name: {created_memory.name}")
print(f"   scope: {created_memory.scope}")
print(f"   → create() は統合を行わず、そのまま保存される")

# ============================================================
# ③ 生成されるメモリのデータ構造（記事 3-1 ③ 参照）
# ============================================================
# 保存されたメモリは構造化された Memory オブジェクトとして生成される。
# fact, scope, metadata, topics, create_time, update_time を持つ。
print("\n" + "=" * 60)
print("③ 生成されるメモリのデータ構造の確認（記事 3-1 ③）")
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
    if m.memory.metadata:
        print(f"      metadata: {m.memory.metadata}")
    if hasattr(m.memory, "topics") and m.memory.topics:
        print(f"      topics: {m.memory.topics}")
    print(f"      create_time: {m.memory.create_time}")
    print(f"      update_time: {m.memory.update_time}")

# ============================================================
# ⑤ 統合（Consolidation）のデモ（記事 3-1 ⑤ 参照）
# ============================================================
# GenerateMemories は単純な追記ではなく、LLM による「統合」を行う。
# 既存の記憶と新しい情報を比較し、CREATED / UPDATED / DELETED を判断。
print("\n" + "=" * 60)
print("⑤ 統合（Consolidation）のデモ（記事 3-1 ⑤）")
print("=" * 60)

# 新しいセッションで「好みの変更」を伝える
session_consol = client.agent_engines.sessions.create(
    name=AGENT_ENGINE_NAME,
    user_id=USER_ID,
)
session_consol_name: str = session_consol.response.name

# 既存の記憶「Pythonが好き」に矛盾する新情報を送る
consolidation_conversation: list[dict[str, str]] = [
    {"role": "user", "text": "最近は Rust に乗り換えました。メインの言語は Rust です。Pythonはもうあまり使いません。"},
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
)

print(f"   ✅ generate() 完了 (done={op_consol.done})")
if op_consol.response is not None:
    for i, gm in enumerate(op_consol.response.generated_memories, 1):
        memory = client.agent_engines.memories.get(name=gm.memory.name)
        print(f"   [{i}] action={gm.action}")  # UPDATED or CREATED
        print(f"        fact={memory.fact}")
    print(f"\n   💡 統合の結果:")
    print(f"      UPDATED → 既存の記憶が最新の情報で更新された")
    print(f"      CREATED → 全く新しい事実が追加された")
    print(f"      DELETED → 矛盾する古い記憶が削除された")
else:
    print("   response=None（メモリ未生成）")

# ============================================================
# ⑥ メタデータ（Metadata）の付与（記事 3-1 ⑥ 参照）
# ============================================================
# メタデータは個々の記憶に付与する「タグ」。
# 検索時の確実な条件絞り込み（Exact Match）に利用できる。
print("\n" + "=" * 60)
print("⑥ メタデータの付与（記事 3-1 ⑥）")
print("=" * 60)

operation_meta = client.agent_engines.memories.generate(
    name=AGENT_ENGINE_NAME,
    # Sessions を使わず直接渡す例（direct_contents_source）
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

print(f"   ✅ メタデータ付き generate() 完了")
if operation_meta.response is not None:
    for i, gm in enumerate(operation_meta.response.generated_memories, 1):
        memory = client.agent_engines.memories.get(name=gm.memory.name)
        print(f"   [{i}] action={gm.action}")
        print(f"        fact={memory.fact}")
        print(f"        metadata={memory.metadata}")

# ============================================================
# ⑦ メタデータの更新戦略（記事 3-1 ⑦ 参照）
# ============================================================
# metadata_merge_strategy で統合時のメタデータの扱いを制御する。
# - MERGE（デフォルト）: 新旧のメタデータを結合
# - OVERWRITE: 古いメタデータを完全に置き換え
# - REQUIRE_EXACT_MATCH: 完全一致するメタデータのみ統合対象に
print("\n" + "=" * 60)
print("⑦ メタデータの更新戦略（記事 3-1 ⑦）")
print("=" * 60)

# REQUIRE_EXACT_MATCH の例:
# 「履歴として蓄積したい記憶」で意図しない上書きを防ぐ
operation_exact = client.agent_engines.memories.generate(
    name=AGENT_ENGINE_NAME,
    direct_contents_source={
        "events": [
            {
                "content": {
                    "role": "user",
                    "parts": [{"text": "今日のデッサン練習は球体を描きました。光と影の表現が難しかったです。"}]
                }
            },
        ]
    },
    scope={"user_id": USER_ID},
    config={
        "metadata": {
            "category": {"string_value": "drawing_log"},
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
print(f"      → 時系列の履歴を消さずに残したいケースに有効。")

# ============================================================
# ② トピック（Topics）の動作確認（記事 3-1 ② 参照）
# ============================================================
# デフォルトの4トピック + カスタムトピック（Step 0 で設定済み）の動作を確認。
# LLM が会話の内容から自律的にトピックを分類する。
print("\n" + "=" * 60)
print("② トピック（Topics）の動作確認（記事 3-1 ②）")
print("=" * 60)

# 技術スキルに特化した会話で、カスタムトピックの分類を確認する
session2 = client.agent_engines.sessions.create(
    name=AGENT_ENGINE_NAME,
    user_id=USER_ID,
)
session2_name: str = session2.response.name

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

print(f"   ✅ カスタムトピック付き generate() 完了")
if operation_custom.response is not None:
    for i, gm in enumerate(operation_custom.response.generated_memories, 1):
        memory = client.agent_engines.memories.get(name=gm.memory.name)
        print(f"   [{i}] action={gm.action}")
        print(f"        fact={memory.fact}")
        if hasattr(memory, "topics") and memory.topics:
            print(f"        topics={memory.topics}")
    print(f"\n   💡 Step 0 で設定した technical_skills トピックが")
    print(f"      LLM により自動分類されているか確認してください。")

# ============================================================
# ⑧ マルチモーダル入力からのメモリ生成（記事 3-1 ⑧ 参照）
# ============================================================
# テキストだけでなく画像等からもメモリを生成できる。
# ただし生成されるメモリ自体はテキスト形式。
# 詳細は poi/step3_multimodal.py を参照。
print("\n" + "=" * 60)
print("⑧ マルチモーダル入力からのメモリ生成（記事 3-1 ⑧）")
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
                        {"text": "これは私が週末に作ったスコーンです。ベーキングが趣味なんです。"},
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
    scope={"user_id": USER_ID},
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
# ⑨ 非同期生成（記事 3-1 ⑨ 参照）
# ============================================================
# wait_for_completion=False にすることで、メモリ生成を
# バックグラウンドで非同期に実行できる。
print("\n" + "=" * 60)
print("⑨ 非同期生成（記事 3-1 ⑨）")
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
            "parts": [{"text": "週末は猫カフェに行きました。三毛猫が可愛かったです。"}],
        }
    },
)

op_async = client.agent_engines.memories.generate(
    name=AGENT_ENGINE_NAME,
    vertex_session_source={"session": session_async_name},
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
    scope={"user_id": USER_ID},
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
| ①        | スコープの定義              | sessions.create(user_id=...)    |
| ②        | トピックの自動分類           | カスタムトピック（Step 0で設定）   |
| ③        | メモリのデータ構造           | fact, scope, metadata, topics   |
| ④        | Generate vs Create         | generate() / create()           |
| ⑤        | 統合（Consolidation）       | CREATED / UPDATED / DELETED     |
| ⑥        | メタデータの付与             | config.metadata                 |
| ⑦        | メタデータ更新戦略           | metadata_merge_strategy          |
| ⑧        | マルチモーダル入力           | file_data / inline_data          |
| ⑨        | 非同期生成                  | wait_for_completion=False        |
""")

print(f"🎉 Step 1 完了！")
