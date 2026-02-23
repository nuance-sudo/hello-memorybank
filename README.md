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

各ステップは **個別に実行可能** です。順番に実行してください。

| Step | テーマ | 記事セクション | src | doc |
|------|-------|-------------|-----|-----|
| 0 | **設定**: Agent Engine 作成 & embedding モデル設定 | — | [step0](src/step0_setup.py) | [insight](doc/step0_insights.md) |
| 1a | **基本**: スコープ・Generate・Create・データ構造 | 3-1（(1)(3)(4)） | [step1a](src/step1a_basics.py) | [insight](doc/step1_insights.md) |
| 1b | **統合**: Consolidation のデモ | 3-1（(5)） | [step1b](src/step1b_consolidation.py) | [insight](doc/step1_insights.md) |
| 1c | **メタデータ**: 付与と更新戦略 | 3-1（(6)(7)） | [step1c](src/step1c_metadata.py) | [insight](doc/step1_insights.md) |
| 1d | **応用**: トピック・マルチモーダル・非同期 | 3-1（(2)(8)(9)） | [step1d](src/step1d_advanced.py) | [insight](doc/step1_insights.md) |
| 2 | **取得**: メモリの取得 | 3-2（(1)〜(4)） | [step2](src/step2_retrieve.py) | [insight](doc/step2_insights.md) |

### 実行順序

```bash
# Step 0: Agent Engine を作成
uv run python src/step0_setup.py

# Step 1a: メモリ生成の基本（(1)(3)(4)）
uv run python src/step1a_basics.py

# Step 1b: 統合デモ（(5)）— 1a で作成したメモリの更新を確認
uv run python src/step1b_consolidation.py

# Step 1c: メタデータの付与（(6)(7)）
uv run python src/step1c_metadata.py

# Step 1d: 応用（(2)(8)(9)）
uv run python src/step1d_advanced.py

# Step 2: メモリの取得（(1)〜(4)）
uv run python src/step2_retrieve.py
```

> 💡 **なぜ分割？** Step 1b（統合デモ）は、Step 1a で作成済みのメモリが「更新される」ことを確認するデモです。結果を確認しながら進められるよう、各ステップを独立して実行可能にしています。

### Step 1: メモリの生成と保存（記事 3-1）

| セクション | 内容 | スクリプト | キーワード |
|-----------|------|----------|----------|
| (1) | スコープの定義とセッション作成 | step1a | `sessions.create()`, `user_id`, 複合キー |
| (2) | トピック（Topics）の動作確認 | step1d | マネージドトピック, カスタムトピック |
| (3) | 生成されるメモリのデータ構造 | step1a | `fact`, `scope`, `metadata`, `topics` |
| (4) | Generate と Create の違い | step1a | `generate()`, `create()` |
| (5) | 統合（Consolidation）のデモ | step1b | CREATED, UPDATED, DELETED |
| (6) | メタデータの付与 | step1c | `config.metadata`, `string_value` |
| (7) | メタデータの更新戦略 | step1c | `metadata_merge_strategy`, `REQUIRE_EXACT_MATCH` |
| (8) | マルチモーダル入力 | step1d | `file_data`, GCS URI |
| (9) | 非同期生成 | step1d | `wait_for_completion=False` |

### Step 2: メモリの取得（記事 3-2）

| セクション | 内容 | キーワード |
|-----------|------|----------|
| (1) | 3つの取得メソッドの使い分け | `retrieve()`, `get()`, `list()` |
| (2) | スコープの完全一致制約 | 完全一致, アンチパターン |
| (3) | 2種類のフィルタリング | `filter_groups`(DNF), `filter`(EBNF) |
| (4) | セマンティック検索 | `similarity_search_params`, `top_k`, distance |

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
