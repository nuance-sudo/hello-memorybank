# プロジェクトルール

## 言語・スタイル
- 日本語で回答・ドキュメント作成
- `any` 型は使用禁止。必ず型定義する
- コードのコメントは日本語

## プロジェクト構成
- `src/step0_setup.py` — Agent Engine 作成、embedding モデル、メモリトピック設定
- `src/step1a_basics.py` — メモリ生成の基本（(1)(3)(4)）
- `src/step1b_consolidation.py` — 統合デモ（(5)）
- `src/step1c_metadata.py` — メタデータの付与と更新戦略（(6)(7)）
- `src/step1d_advanced.py` — トピック・マルチモーダル・非同期（(2)(8)(9)）
- `src/step2_retrieve.py` — メモリの取得（(1)〜(4)）
- `doc/stepN_insights.md` — 各ステップの学習ノート（Insight 形式）
- `.env` — 環境変数（`GCP_PROJECT_ID`, `GCP_LOCATION`, `AGENT_ENGINE_NAME`）
- パッケージ管理: `uv`
- 実行: `uv run python src/stepN_*.py`

## ステップ構成
- Step 0: セットアップ（Agent Engine 作成、embedding モデル、メモリトピック設定）
- Step 1a: メモリ生成の基本（スコープ・Generate/Create・データ構造）
- Step 1b: 統合（Consolidation）のデモ
- Step 1c: メタデータの付与と更新戦略
- Step 1d: 応用（トピック・マルチモーダル・非同期）
- Step 2: メモリの取得（Retrieve/Get/List・フィルタ・セマンティック検索）
- Step 5: クリーンアップ

## 調査方法
- SDK の仕様や使い方を確認する際は `google-developer-knowledge` MCP（`search_documents`）を使う
- 公式ドキュメント: https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/
