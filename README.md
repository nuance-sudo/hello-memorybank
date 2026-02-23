# Hello Memory Bank 🧠

Vertex AI Agent Engine **Memory Bank** のハンズオン学習リポジトリ。

📝 **Zenn 記事**: [Vertex AI Agent Engine Memory Bank 入門](https://zenn.dev/esanuka/articles/hello-memorybank)

## プロジェクト構成

```
.
├── src/          # ステップごとの実行スクリプト
├── doc/          # 各ステップの解説（Insight）
├── poi/          # 補足スクリプト（マルチモーダル詳細・削除・リビジョン）
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

| Step | テーマ | 記事セクション | src | doc |
|------|-------|-------------|-----|-----|
| 0 | **設定**: Agent Engine 作成 & embedding モデル設定 | — | [step0](src/step0_setup.py) | [insight](doc/step0_insights.md) |
| 1 | **生成**: メモリの生成と保存 | 3-1（①〜⑨） | [step1](src/step1_generate.py) | [insight](doc/step1_insights.md) |
| 2 | **取得**: メモリの取得 | 3-2（①〜④） | [step2](src/step2_retrieve.py) | [insight](doc/step2_insights.md) |

### Step 1: メモリの生成と保存（記事 3-1）

| セクション | 内容 | キーワード |
|-----------|------|----------|
| ① | スコープの定義とセッション作成 | `sessions.create()`, `user_id`, 複合キー |
| ② | トピック（Topics）の動作確認 | マネージドトピック, カスタムトピック |
| ③ | 生成されるメモリのデータ構造 | `fact`, `scope`, `metadata`, `topics` |
| ④ | Generate と Create の違い | `generate()`, `create()` |
| ⑤ | 統合（Consolidation）のデモ | CREATED, UPDATED, DELETED |
| ⑥ | メタデータの付与 | `config.metadata`, `string_value` |
| ⑦ | メタデータの更新戦略 | `metadata_merge_strategy`, `REQUIRE_EXACT_MATCH` |
| ⑧ | マルチモーダル入力 | `file_data`, GCS URI |
| ⑨ | 非同期生成 | `wait_for_completion=False` |

### Step 2: メモリの取得（記事 3-2）

| セクション | 内容 | キーワード |
|-----------|------|----------|
| ① | 3つの取得メソッドの使い分け | `retrieve()`, `get()`, `list()` |
| ② | スコープの完全一致制約 | 完全一致, アンチパターン |
| ③ | 2種類のフィルタリング | `filter_groups`(DNF), `filter`(EBNF) |
| ④ | セマンティック検索 | `similarity_search_params`, `top_k`, distance |

### 補足（poi/）

| ファイル | テーマ | キーワード |
|---------|-------|-----------|
| [step3_multimodal.py](poi/step3_multimodal.py) | マルチモーダル入力の詳細 | `file_data`, `inline_data`, Sessions連携 |
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
