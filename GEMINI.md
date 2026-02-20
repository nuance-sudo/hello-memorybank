# プロジェクトルール

## 言語・スタイル
- 日本語で回答・ドキュメント作成
- `any` 型は使用禁止。必ず型定義する
- コードのコメントは日本語

## プロジェクト構成
- `src/stepN_*.py` — 各ステップの実行スクリプト
- `doc/stepN_insights.md` — 各ステップの学習ノート（Insight 形式）
- `.env` — 環境変数（`GCP_PROJECT_ID`, `GCP_LOCATION`, `AGENT_ENGINE_NAME`）
- パッケージ管理: `uv`
- 実行: `uv run python src/stepN_*.py`

## ステップ構成
- Step 0: セットアップ（Agent Engine 作成、embedding モデル、メモリトピック設定）
- Step 1: メモリ作成（generate / create / メタデータ / カスタムトピック動作確認）
- Step 2: メモリ取得（retrieve / 類似検索）
- Step 3: メモリ更新・削除
- Step 4: 応用（セッション連携等）
- Step 5: クリーンアップ

## 調査方法
- SDK の仕様や使い方を確認する際は `google-developer-knowledge` MCP（`search_documents`）を使う
- 公式ドキュメント: https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/
