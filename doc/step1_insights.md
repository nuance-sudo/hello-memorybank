# Step 1: メモリの生成と保存（記事 3-1 対応）

## 対応する記事セクション

| セクション | 記事 3-1 | スクリプト内 |
|-----------|---------|------------|
| ① | スコープの定義とセッション作成 | セッション作成 + イベント追加 |
| ② | トピック（Topics）の動作確認 | カスタムトピックの分類確認 |
| ③ | 生成されるメモリのデータ構造 | 全フィールドの表示 |
| ④ | Generate と Create の違い | generate() と create() の比較 |
| ⑤ | 統合（Consolidation）のデモ | 好みの変更 → UPDATED の確認 |
| ⑥ | メタデータ（Metadata）の付与 | metadata 付き generate() |
| ⑦ | メタデータの更新戦略 | REQUIRE_EXACT_MATCH の例 |
| ⑧ | マルチモーダル入力 | GCS 画像 + テキストの例 |
| ⑨ | 非同期生成 | wait_for_completion=False |

## 学習ポイント

### ① スコープ（Scope）

- スコープは複合キー（最大5要素の辞書型）で定義できる
- `user_id` だけでなく `system_id` を組み合わせることで、同じユーザーでもシステムの文脈を分けて管理可能
- Sessions API で `user_id` を指定すると、自動的にスコープに設定される

### ② トピック（Topics）

- デフォルトの4つのマネージドトピック:
  - `USER_PERSONAL_INFO`
  - `USER_PREFERENCES`
  - `KEY_CONVERSATION_DETAILS`
  - `EXPLICIT_INSTRUCTIONS`
- カスタムトピックは Step 0 の `update()` で設定済み
- LLM が会話の中から自律的にトピックを分類する

### ③ メモリのデータ構造

- `fact`: LLM が一人称視点で生成した事実テキスト
- `scope`: 記憶の帰属先キー
- `metadata`: 開発者が付与したタグ情報
- `topics`: LLM が自動分類したトピック
- `create_time` / `update_time`: 自動付与されるタイムスタンプ

### ④ Generate vs Create

| メソッド | 統合 | 用途 |
|---------|------|------|
| `generate()` | あり（自動で既存記憶と比較・統合） | 基本はこちらを使用 |
| `create()` | なし（そのまま保存） | 抽出済みの事実を直接保存 |

### ⑤ 統合（Consolidation）

- `GenerateMemories` は単純な追記ではなく LLM による「統合」を行う
- 3つのアクション: CREATED / UPDATED / DELETED
- 既存の記憶と新しい情報を自動比較し、最適な操作を判断

### ⑥ メタデータの付与

- `config.metadata` に辞書形式で付与
- 値は `{"string_value": "..."}` 形式
- 取得時のフィルタリング（filter_groups）に利用可能

### ⑦ メタデータの更新戦略

- `MERGE`（デフォルト）: 新旧メタデータを結合
- `OVERWRITE`: 完全に置き換え
- `REQUIRE_EXACT_MATCH`: 完全一致するメタデータの記憶のみ統合対象
- 時系列履歴を保持したい場合は `REQUIRE_EXACT_MATCH` + セッションIDを推奨

### ⑧ マルチモーダル入力

- テキスト・画像・動画・音声からメモリを生成可能
- 生成されるメモリ自体はテキスト形式（画像は保存されない）
- テキストでコンテキストを添えると精度が上がる
- 詳細な例は `poi/step3_multimodal.py` を参照

### ⑨ 非同期生成

- `wait_for_completion=False` でバックグラウンド処理
- エージェントはメモリ生成完了を待たずにレスポンスを返せる
