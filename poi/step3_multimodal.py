"""
Step 3（補足）: マルチモーダル入力からメモリを生成（詳細版）

記事 3-1 ⑧ のマルチモーダル入力の詳細を体験するスクリプト。
step1_generate.py では GCS 画像の簡易例のみ扱っているが、
ここではより多くの入力方法を網羅的に確認する。

  1. GCS の画像 URL からメモリ生成（file_data）
  2. ローカル画像からメモリ生成（inline_data）
  3. テキスト + 画像の組み合わせ（Sessions 連携）
  4. 生成されたメモリの確認
  5. クリーンアップ

📝 マルチモーダル入力の注意点:
   - メモリとして抽出されるのはテキスト情報のみ（画像自体は保存されない）
   - text, inline_data, file_data のみが対象。function call/response は無視される
   - 画像にコンテキスト（テキスト）を添えると、より意味のあるメモリが生成される
"""

import datetime
import os
import urllib.request

import vertexai
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
LOCATION = os.environ["GCP_LOCATION"]
AGENT_ENGINE_NAME = os.environ["AGENT_ENGINE_NAME"]

client = vertexai.Client(project=PROJECT_ID, location=LOCATION)
print(f"✅ Client 初期化完了")
print(f"   Agent Engine: {AGENT_ENGINE_NAME}")

USER_ID = "user-multimodal-test"
SCOPE = {"user_id": USER_ID}

# ============================================================
# 1. GCS の画像からメモリ生成（file_data）
# ============================================================
print("\n" + "=" * 60)
print("🖼️  1. GCS の画像からメモリ生成（file_data）")
print("=" * 60)

GCS_IMAGE_URI = "gs://cloud-samples-data/generative-ai/image/scones.jpg"

op1 = client.agent_engines.memories.generate(
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
    scope=SCOPE,
)

print(f"   ✅ generate() 完了 (done={op1.done})")
if op1.response is not None:
    for i, gm in enumerate(op1.response.generated_memories, 1):
        memory = client.agent_engines.memories.get(name=gm.memory.name)
        print(f"   [{i}] action={gm.action}")
        print(f"        fact={memory.fact}")
else:
    print("   response=None（メモリ未生成）")

# ============================================================
# 2. ローカル画像からメモリ生成（inline_data）
# ============================================================
print("\n" + "=" * 60)
print("📷 2. ローカル画像からメモリ生成（inline_data）")
print("=" * 60)

SAMPLE_IMAGE_URL = "https://storage.googleapis.com/cloud-samples-data/generative-ai/image/scones.jpg"
LOCAL_IMAGE_PATH = "/tmp/sample_scones.jpg"

print(f"   サンプル画像をダウンロード中...")
urllib.request.urlretrieve(SAMPLE_IMAGE_URL, LOCAL_IMAGE_PATH)
print(f"   ダウンロード完了: {LOCAL_IMAGE_PATH}")

with open(LOCAL_IMAGE_PATH, "rb") as f:
    image_bytes: bytes = f.read()

print(f"   画像サイズ: {len(image_bytes)} bytes")

op2 = client.agent_engines.memories.generate(
    name=AGENT_ENGINE_NAME,
    direct_contents_source={
        "events": [
            {
                "content": {
                    "role": "user",
                    "parts": [
                        {"text": "これは私の犬です。名前はポチです。"},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image_bytes,
                            }
                        },
                    ],
                }
            }
        ]
    },
    scope=SCOPE,
)

print(f"   ✅ generate() 完了 (done={op2.done})")
if op2.response is not None:
    for i, gm in enumerate(op2.response.generated_memories, 1):
        memory = client.agent_engines.memories.get(name=gm.memory.name)
        print(f"   [{i}] action={gm.action}")
        print(f"        fact={memory.fact}")
else:
    print("   response=None（メモリ未生成）")

# ============================================================
# 3. Sessions + マルチモーダル
# ============================================================
print("\n" + "=" * 60)
print("📡 3. Sessions + マルチモーダル")
print("=" * 60)

session = client.agent_engines.sessions.create(
    name=AGENT_ENGINE_NAME,
    user_id=USER_ID,
)
session_name: str = session.response.name
print(f"   セッション作成: {session_name}")

client.agent_engines.sessions.events.append(
    name=session_name,
    author="user",
    invocation_id="1",
    timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
    config={
        "content": {
            "role": "user",
            "parts": [
                {"text": "旅行先で食べたスコーンが美味しかったです。来年もまた行きたいです。"},
                {
                    "file_data": {
                        "file_uri": "gs://cloud-samples-data/generative-ai/image/scones.jpg",
                        "mime_type": "image/jpeg",
                    }
                },
            ],
        }
    },
)
print(f"   イベント追加完了（テキスト + 画像）")

op3 = client.agent_engines.memories.generate(
    name=AGENT_ENGINE_NAME,
    vertex_session_source={"session": session_name},
)

print(f"   ✅ generate() 完了 (done={op3.done})")
if op3.response is not None:
    for i, gm in enumerate(op3.response.generated_memories, 1):
        memory = client.agent_engines.memories.get(name=gm.memory.name)
        print(f"   [{i}] action={gm.action}")
        print(f"        fact={memory.fact}")
else:
    print("   response=None（メモリ未生成）")

# ============================================================
# 4. 生成されたメモリの確認
# ============================================================
print("\n" + "=" * 60)
print("📥 4. 生成されたメモリの確認")
print("=" * 60)

results = client.agent_engines.memories.retrieve(
    name=AGENT_ENGINE_NAME,
    scope=SCOPE,
)
all_memories = list(results)

print(f"   合計: {len(all_memories)} 件")
for i, m in enumerate(all_memories, 1):
    print(f"\n  [{i}] fact: {m.memory.fact}")

print(f"""
📊 マルチモーダル入力のまとめ:

| 方法           | 渡し方                           | 用途                    |
|---------------|----------------------------------|------------------------|
| file_data     | GCS URI を指定                    | GCS に画像がある場合     |
| inline_data   | バイナリを直接埋め込む              | ローカルファイルの場合    |

💡 ポイント:
  - 画像自体は保存されない。LLM が画像を分析し、テキストのメモリとして保存する
  - テキストでコンテキスト（「これは私の犬です」等）を添えると精度が上がる
  - Sessions 経由でもマルチモーダルイベントを記録可能
""")

# ============================================================
# 5. クリーンアップ
# ============================================================
print("=" * 60)
print("🧹 5. クリーンアップ")
print("=" * 60)

purge_op = client.agent_engines.memories.purge(
    name=AGENT_ENGINE_NAME,
    filter=f'scope.user_id="{USER_ID}"',
    force=True,
    config={"wait_for_completion": True},
)
count: int = purge_op.response.purge_count
print(f"   ✅ {count} 件削除")

if os.path.exists(LOCAL_IMAGE_PATH):
    os.remove(LOCAL_IMAGE_PATH)
    print(f"   ✅ ローカル画像削除: {LOCAL_IMAGE_PATH}")

print(f"\n🎉 マルチモーダルの詳細ハンズオン完了！")
