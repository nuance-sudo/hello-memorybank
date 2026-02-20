# Hello Memory Bank 🧠

Vertex AI Agent Engine **Memory Bank** のハンズオン学習リポジトリ。

## プロジェクト構成

```
.
├── src/          # ステップごとの実行スクリプト
├── doc/          # 各ステップの解説（Insight）
├── poi/          # 補足スクリプト（削除・リビジョン）
├── .env          # 環境変数（GCP_PROJECT_ID 等）
└── README.md
```

## セットアップ

```bash
# 依存インストール
uv sync

# .env を編集（プロジェクトID・リージョンを設定）
cp .env.example .env
```

## 学習ステップ

| Step | テーマ | src | doc | キーワード |
|------|-------|-----|-----|-----------|
| 0 | **設定**: Agent Engine 作成 & embedding モデル設定 | [step0](src/step0_setup.py) | [insight](doc/step0_insights.md) | `create()`, `update()`, `context_spec`, multilingual embedding |
| 1 | **作成**: Sessions 連携でメモリ生成 | [step1](src/step1_generate.py) | [insight](doc/step1_insights.md) | `sessions.create()`, `vertex_session_source`, `generate()`, `create()` |
| 2 | **取得**: 全件取得 & 類似検索 & フィルタ | [step2](src/step2_retrieve.py) | [insight](doc/step2_insights.md) | `retrieve()`, `similarity_search_params`, `filter`, `filter_groups` |
| 3 | **マルチモーダル**: 画像からメモリ生成 | [step3](src/step3_multimodal.py) | [insight](doc/step3_insights.md) | `file_data`, `inline_data`, マルチモーダル入力 |

### 補足（poi/）

| ファイル | テーマ | キーワード |
|---------|-------|-----------|
| [step3_delete.py](poi/step3_delete.py) | メモリの削除 | `delete()`, `purge()` |
| [step4_lifecycle.py](poi/step4_lifecycle.py) | リビジョン管理 | `rollback()`, `revisions` |

## 参考ドキュメント

| テーマ | 公式ドキュメント |
|-------|----------------|
| Memory Bank 概要 | [Memory Bank overview](https://cloud.google.com/agent-builder/agent-engine/memory-bank/overview) |
| クイックスタート | [Quickstart: SDK](https://cloud.google.com/agent-builder/agent-engine/memory-bank/quickstart-api) |
| メモリ生成 | [Generate memories](https://cloud.google.com/agent-builder/agent-engine/memory-bank/generate-memories) |
| メモリ取得 | [Fetch memories](https://cloud.google.com/agent-builder/agent-engine/memory-bank/fetch-memories) |
| Sessions 管理 | [Manage sessions](https://cloud.google.com/agent-builder/agent-engine/sessions/manage-sessions) |

## 環境変数

| 変数名 | 説明 |
|-------|------|
| `GCP_PROJECT_ID` | GCP プロジェクト ID |
| `GCP_LOCATION` | リージョン（例: `us-central1`） |
| `AGENT_ENGINE_NAME` | Agent Engine のリソース名（Step 0 実行後に追記） |
