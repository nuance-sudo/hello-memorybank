"""
Step 0: Agent Engine インスタンスの作成と設定

Agent Engine は Sessions・Memory Bank 等のサービスを束ねるインスタンス。
このステップではインスタンスを作成し、以下を設定する:
  - 日本語対応の embedding モデル
  - メモリトピック（マネージド + カスタム）

実行後、.env に AGENT_ENGINE_NAME を追記してください。
"""

import os
import vertexai
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
LOCATION = os.environ["GCP_LOCATION"]

# ============================================================
# 1. クライアント初期化
# ============================================================
client = vertexai.Client(project=PROJECT_ID, location=LOCATION)
print(f"✅ Client 初期化完了: project={PROJECT_ID}, location={LOCATION}")

# ============================================================
# 2. Agent Engine インスタンス作成
# ============================================================
# config なしで作ると Memory Bank のデフォルト設定で作成される。
# embedding モデルのデフォルトは text-embedding-005（英語最適化）。
print("\n📦 Agent Engine インスタンスを作成中...")
agent_engine = client.agent_engines.create()

agent_engine_name = agent_engine.api_resource.name
print(f"✅ 作成完了!")
print(f"   リソース名: {agent_engine_name}")

# ============================================================
# 3. Embedding モデル + メモリトピックを設定
# ============================================================
# デフォルトの embedding は text-embedding-005（英語最適化）。
# 日本語の類似検索精度を上げるため multilingual モデルに変更する。
#
# さらに、カスタムトピック（technical_skills）も設定する。
# デフォルトの4つのマネージドトピックに加え、独自の抽出カテゴリを追加できる。
# ⚠️ カスタムトピックを指定する場合、マネージドトピックも明示的に含める必要がある。
#
# update() で context_spec を変更すると、インスタンスに永続保存され、
# 以降の generate() / retrieve() すべてに反映される。

print("\n🌐 Embedding モデル + メモリトピックを設定中...")

EMBEDDING_MODEL = f"projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/text-multilingual-embedding-002"

client.agent_engines.update(
    name=agent_engine_name,
    config={
        "context_spec": {
            "memory_bank_config": {
                "similarity_search_config": {
                    "embedding_model": EMBEDDING_MODEL
                },
                "customization_configs": [{
                    "memory_topics": [
                        # マネージドトピック（デフォルトの4つ）
                        {"managed_memory_topic": {"managed_topic_enum": "USER_PERSONAL_INFO"}},
                        {"managed_memory_topic": {"managed_topic_enum": "USER_PREFERENCES"}},
                        {"managed_memory_topic": {"managed_topic_enum": "KEY_CONVERSATION_DETAILS"}},
                        {"managed_memory_topic": {"managed_topic_enum": "EXPLICIT_INSTRUCTIONS"}},
                        # カスタムトピック: 技術スキルに特化
                        {
                            "custom_memory_topic": {
                                "label": "technical_skills",
                                "description": "ユーザーが使用しているプログラミング言語、フレームワーク、ツール、技術スタック。具体的な技術名とその習熟度や使用状況を記録する。"
                            }
                        },
                    ]
                }]
            }
        }
    },
)
print(f"✅ 設定完了")
print(f"   embedding: text-multilingual-embedding-002")
print(f"   トピック: マネージド4つ + カスタム（technical_skills）")

# ============================================================
# 4. 設定確認
# ============================================================
print(f"\n{'=' * 60}")
print(f"📌 セットアップ完了！ .env に以下を追記してください:")
print(f"{'=' * 60}")
print(f"AGENT_ENGINE_NAME={agent_engine_name}")
