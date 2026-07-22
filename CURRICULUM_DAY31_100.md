# LLM / AIエンジニア 100日カリキュラム

作成日: 2026-07-21  
対象: Day 1〜30相当を終えた現在地点から、Day 100まで

## 進捗

- [x] Day 31: READMEによる現状の棚卸し、環境構築・実行手順・既知の課題の文書化
- [ ] Day 32: BM25を自作し、キーワード検索の仕組みを理解する
- [ ] 保留: `src/`構成、設定クラス、モデル名・閾値の一元管理

## 1. 現在地

このリポジトリでは、2026-07-12から2026-07-21にかけて、17コミットと未コミットの学習成果が確認できた。実日数は約10日だが、扱ったテーマ量を基準にすると、Day 1〜30相当まで進んだとみなせる。

### 時系列で確認できた内容

| 日付 | 学習テーマ | 主な成果物 |
|---|---|---|
| 07/12 | Pythonプロジェクト、OpenAI APIの初回呼び出し | `main.py`, `pyproject.toml` |
| 07/13 | 環境変数、Pydantic、構造化出力 | `structured_output.py` |
| 07/14 | LLMによる入力安全性判定 | `security_filter.py` |
| 07/15 | キーワードRAG、Embedding、コサイン類似度 | `simple_rag.py`, `vector_rag.py` |
| 07/16 | ChromaDBによる永続ベクトル検索、Tool Calling | `chroma_rag.py`, `chroma_rag_complete.py`, `agent_function.py` |
| 07/17〜18 | チャンキング、オーバーラップ、ファイル取り込み | `chanking_rag.py`, `file_ingest_rag.py`, `docs/` |
| 07/18 | ハイブリッド検索、RRF | `hybrid_test.py`, `hybrid_search.py`, `rrf_search.py` |
| 07/19〜20 | Function Callingの往復処理、ReActループ | `tool_calling_basic.py`, `tool_calling_complete.py`, `agent_react_loop.py` |
| 07/21 | エージェント状態管理の導入 | `agent_state_model.py`, `memo.md` |

### すでに身についていること

- LLM APIの基本的な呼び出しと環境変数による秘密情報管理
- Pydanticを使った構造化出力
- RAGの基本構造（Retrieve → Augment → Generate）
- Embedding、ベクトル検索、ChromaDB、チャンキング
- ベクトル検索の弱点と、キーワード検索・RRFによる補完
- Tool Callingのスキーマ、実行結果の返却、複数ターンのReActループ
- 状態、永続化、Human-in-the-Loopが必要になる理由の理解

### Day 31以降で埋めるべき穴

- `pytest`による単体・結合テスト、モック、型検査、Lint
- 正解データセットと指標を使ったRAG・エージェント評価
- BM25の実装、reranker、引用、検索失敗時の判定
- 例外処理、タイムアウト、再試行、レート制限、コスト管理
- 現行APIへの移行と、フレームワークを使う場合・使わない場合の判断
- FastAPI、非同期処理、DB、認証、ストリーミング
- ログ、トレース、メトリクス、セキュリティテスト
- Docker、CI/CD、クラウドへのデプロイ
- データ作成、fine-tuningの適否、マルチモーダル処理

## 2. 学習ルール

1日90〜150分を標準とする。

- 20分: 公式ドキュメントまたは原理を読む
- 60〜100分: 実装する
- 20分: テスト、計測、振り返りを行う
- 毎日: `memo.md`に「仮説・結果・失敗・次の一手」を追記する
- 毎週: README更新、全テスト実行、代表デモの録画またはスクリーンショットを残す

「コードを書いた」ではなく、その日の合格条件を満たしたら完了とする。API料金を使うテストと、モックだけで完結するテストを分離する。

## 3. Day 31〜100

### Week 5 — Day 31〜37: 検索アルゴリズムをサンプルで理解する

| Day | テーマ | 作るもの | 合格条件 |
|---:|---|---|---|
| 31 | 現状の棚卸し | READMEに構成図、実行方法、環境変数、既知の課題を記載 | 初見の人が15分以内に1例を実行できる |
| 32 | BM25 | BM25の式を自作し、型番・規程番号を検索する | `様式第4号`が正しく1位になる |
| 33 | 日本語tokenize | 形態素解析、文字n-gram、識別子分割を比較する | tokenizerの長所・限界を説明できる |
| 34 | ベクトル検索との比較 | 同じ質問セットでBM25とChromaDBを比較する | 検索方式ごとの得意・不得意を示せる |
| 35 | 実データでRRF | BM25とベクトル検索のIDランキングをRRFで統合する | 両方の順位を反映した結果を出せる |
| 36 | リランキング | rule-basedまたはLLMによるrerankerを追加する | rerank前後の順位変化を説明できる |
| 37 | Week 5演習 | ハイブリッド検索の小さなCLIを統合する | 質問、検索方式、最終順位を確認できる |

週の成果物: BM25実装、比較実験、実データ版RRF、reranker。  
到達基準: ベクトル検索だけに頼らず、質問の性質に応じて検索方式を選べる。

### Week 6 — Day 38〜44: RAG評価とLLMの入出力を深める

| Day | テーマ | 作るもの | 合格条件 |
|---:|---|---|---|
| 38 | 評価セット | 質問、正解文書、正解回答を30件作成する | 通常・表記揺れ・未回答を含む |
| 39 | Retrieval指標 | Hit@k、Recall@k、MRRを自作する | 固定データで再現可能な数値が出る |
| 40 | Generation評価 | groundedness、relevance、引用正確性を評価する | 人手評価とLLM評価を区別できる |
| 41 | Prompt実験 | context、指示、few-shotの差を比較する | 10ケース以上で差を記録できる |
| 42 | Structured Output深化 | Optional、Union、拒否、バリデーションを試す | 不正出力を安全に扱える |
| 43 | Transformerとtoken | token、embedding、attention、context windowを学ぶ | 小さな数値例で説明できる |
| 44 | Week 6演習 | `evaluate_rag`と学習レポートを作る | 1コマンドで評価を再実行できる |

週の成果物: 評価セット、検索・回答指標、prompt実験レポート、LLM原理ノート。  
到達基準: RAGとLLMの改善を、感想ではなく再現可能な実験結果で説明できる。

### Week 7 — Day 45〜51: 評価駆動RAG

| Day | テーマ | 作るもの | 合格条件 |
|---:|---|---|---|
| 45 | 評価セット設計 | 社内規程を題材に質問・正解文書・正解回答を30件作成 | 通常、表記揺れ、未回答、攻撃を含む |
| 46 | Retrieval指標 | Hit@k、MRR、Recall@kの実装 | 固定データで再現可能な数値が出る |
| 47 | Generation指標 | groundedness、answer relevance、引用正確性の評価 | 人手評価とLLM評価を分けて記録する |
| 48 | BM25 | 実際のBM25検索器を実装 | ベクトル・BM25を同一評価セットで比較する |
| 49 | Hybrid + RRF | 両検索器をRRFで統合 | 単独検索よりHit@3が改善、または失敗理由を説明できる |
| 50 | Chunk実験 | size、overlap、見出し保持をグリッド比較 | 最良設定を指標・費用・遅延から選ぶ |
| 51 | Week 7演習 | `evaluate_rag`コマンドとMarkdownレポート | 1コマンドで評価を再実行できる |

週の成果物: 30問以上の評価セット、検索・回答の評価レポート。  
到達基準: RAGの改善を「良さそう」ではなく数値で判断できる。

### Week 8 — Day 52〜58: 高精度RAGとデータパイプライン

| Day | テーマ | 作るもの | 合格条件 |
|---:|---|---|---|
| 52 | PDF/Markdown取り込み | loader、文字正規化、メタデータ抽出 | source、page、sectionを保持して検索できる |
| 53 | 更新・削除・重複排除 | content hashと差分ingest | 同じファイルを再投入して重複しない |
| 54 | Query transformation | query rewrite、multi-query、HyDEを比較 | 評価セットで効果と追加費用を示す |
| 55 | Reranking | cross-encoderまたはLLM rerankerを追加 | top-k精度と遅延のトレードオフを示す |
| 56 | 引用と拒否 | ページ付き引用、閾値以下では回答しない処理 | 引用元にない主張をテストで検出する |
| 57 | Context最適化 | 重複除去、並び替え、token budget制御 | context上限内で回答品質を維持する |
| 58 | Week 8演習 | Production RAG v1 | ingest、検索、回答、引用、評価が一続きで動く |

週の成果物: 更新可能で引用付きのRAGパイプライン。  
到達基準: 文書追加・更新・削除と、根拠付き回答を安全に扱える。

### Week 9 — Day 59〜65: Tool Calling、MCP、エージェント

| Day | テーマ | 作るもの | 合格条件 |
|---:|---|---|---|
| 59 | 堅牢なTool Calling | Pydantic引数、許可リスト、timeout、エラー戻り値 | 壊れたJSON・未知tool・tool障害を処理できる |
| 60 | 並列・依存tool | 並列可能な呼び出しと逐次呼び出しの実装 | 実行順序をテストで保証する |
| 61 | 停止条件と予算 | 最大turn、最大tool回数、token・時間予算 | 無限ループが必ず停止する |
| 62 | Agents SDK | 現在の手書きReActをSDK版で再実装 | 手書き版との責務の違いを説明できる |
| 63 | MCPの基本 | tools、resources、promptsを持つローカルMCP server | Inspectorまたはclientから3 primitiveを確認できる |
| 64 | MCPセキュリティ | 入力検証、最小権限、秘密情報非表示、監査ログ | 危険toolは明示承認なしに実行されない |
| 65 | Week 9演習 | RAG検索をMCP tool/resourceとして公開 | 別clientから検索し、source付き結果を取得できる |

週の成果物: 制限付きエージェントとローカルMCP server。  
到達基準: tool、agent、MCPを混同せず、用途で選択できる。

### Week 10 — Day 66〜72: 状態付きワークフローとHuman-in-the-Loop

| Day | テーマ | 作るもの | 合格条件 |
|---:|---|---|---|
| 66 | 状態機械 | agent state、node、edge、終了条件を図とコードで定義 | 同じ入力から決定的な遷移テストができる |
| 67 | LangGraph基礎 | ReActをgraphとして再実装 | 各nodeを単体テストできる |
| 68 | Checkpoint | SQLiteへ状態を保存し再開 | プロセス終了後も途中から再開できる |
| 69 | Human-in-the-Loop | 書き込みtool直前にapprove/edit/reject | 3判断すべてをテストする |
| 70 | Time travel | 過去checkpointからforkして再実行 | 元の履歴を壊さず別分岐を作れる |
| 71 | Memory設計 | 会話履歴、要約、ユーザー記憶を分離 | retentionと削除ルールを明記する |
| 72 | Week 10演習 | 承認付き社内手続きagent | 中断、再起動、承認、再開をデモできる |

週の成果物: 永続化・承認・再開が可能な状態付きagent。  
到達基準: 「会話配列」ではなく、障害復旧可能なワークフローとして設計できる。

### Week 11 — Day 73〜79: API・データベース・非同期処理

| Day | テーマ | 作るもの | 合格条件 |
|---:|---|---|---|
| 73 | FastAPI | `/health`, `/ingest`, `/query` | OpenAPI UIから3 endpointを操作できる |
| 74 | 非同期処理 | async client、並列embedding、timeout | 同条件の同期版より処理時間を短縮する |
| 75 | Streaming | SSEでtokenとagent eventを返す | client切断時に処理を適切に停止する |
| 76 | 永続DB | 会話、文書、評価結果のschemaとmigration | DBを作り直して同じ状態を再現できる |
| 77 | Background jobs | 大容量ingestをjob化 | 状態・進捗・失敗理由を取得できる |
| 78 | 認証と認可 | user/admin、文書ACL、rate limit | 他ユーザーの文書を検索できない |
| 79 | Week 11演習 | 複数ユーザー対応RAG API | API結合テストが通る |

週の成果物: 認証・非同期・streamingを備えたRAG API。  
到達基準: notebookやCLIではなく、他アプリから安全に利用できる。

### Week 12 — Day 80〜86: セキュリティ・観測・継続評価

| Day | テーマ | 作るもの | 合格条件 |
|---:|---|---|---|
| 80 | 脅威モデリング | asset、trust boundary、attack path、対策表 | prompt injection以外を5種類以上扱う |
| 81 | RAG security | indirect injection、data exfiltration、poisoningの試験 | 攻撃セットを自動テストできる |
| 82 | Guardrails | 入力・出力・tool・権限の多層防御 | 単一LLM判定だけに依存しない |
| 83 | 構造化ログ | request ID、latency、token、cost、tool結果 | 秘密・個人情報をログに残さない |
| 84 | Tracing | model、retrieval、toolをspanとして可視化 | 失敗した1リクエストを追跡できる |
| 85 | Metrics/SLO | p50/p95、成功率、groundedness、費用のdashboard | SLOとalert条件を文章化する |
| 86 | Week 12演習 | nightly evalと回帰判定 | 品質低下時にCIが失敗する |

週の成果物: 攻撃テスト、trace、metrics、継続評価。  
到達基準: 本番の失敗を再現・分類・検知できる。

### Week 13 — Day 87〜93: マルチモーダル、データ改善、デプロイ

| Day | テーマ | 作るもの | 合格条件 |
|---:|---|---|---|
| 87 | Vision | 表・図を含む画像/PDFへの質問応答 | 文字だけでは解けない10問で評価する |
| 88 | 音声またはRealtime | 音声入力→tool→音声/テキスト回答の試作 | interruptionとtimeoutを処理できる |
| 89 | Fine-tuning判断 | prompt/RAG/fine-tuningの選定表 | 目的、データ量、評価法から採否を説明できる |
| 90 | データセット品質 | train/dev/test分割、重複・漏洩検査 | testデータを調整に使わない手順を作る |
| 91 | Docker | API、worker、DBの開発環境 | 新しい環境で1コマンド起動できる |
| 92 | CI/CD | lint、型、test、eval、image build | pull request相当で全checkが自動実行される |
| 93 | 負荷・費用テスト | concurrency、cache、batch、rate limit実験 | 想定負荷のp95と1件単価を報告できる |

週の成果物: マルチモーダル試作とデプロイ可能なcontainer。  
到達基準: 品質、速度、費用の3軸で本番構成を説明できる。

### Week 14 — Day 94〜100: 卒業制作

卒業制作は「引用・権限・承認・評価を備えた社内ナレッジ＆手続きエージェント」とする。題材は変更してよいが、要件は減らさない。

| Day | テーマ | 作るもの | 合格条件 |
|---:|---|---|---|
| 94 | 要件定義 | user story、非機能要件、脅威モデル、評価指標 | 完了条件が数値化されている |
| 95 | 設計 | architecture、DB schema、API、agent state図 | 各componentの責務と境界が明確 |
| 96 | Core実装 | ingest、hybrid retrieval、rerank、引用回答 | end-to-endの主要経路が動く |
| 97 | Agent実装 | MCP/tool、永続state、承認、再開 | 危険操作が必ず承認待ちになる |
| 98 | 品質仕上げ | tests、security suite、eval、負荷試験 | 主要SLOと品質閾値を満たす |
| 99 | 公開準備 | Docker、CI/CD、運用手順、デモ動画 | 第三者がREADMEだけで再現できる |
| 100 | 卒業審査 | 15分デモ、設計説明、障害対応、振り返り | 下記チェックリストをすべて満たす |

## 4. Day 100の卒業基準

- 50問以上の固定評価セットがある
- RetrievalのHit@k/MRRと、回答のgroundednessを継続計測している
- 回答にsource・pageまたはsectionの引用が付く
- 情報不足時は推測せず回答を保留できる
- prompt injection、権限越境、秘密漏洩の自動テストがある
- toolに型検証、timeout、retry、停止条件、権限、監査ログがある
- 副作用のあるtoolはHuman-in-the-Loopを通る
- 会話やagent処理をcheckpointから再開できる
- APIに認証、rate limit、streaming、health checkがある
- trace、latency、token、cost、error rateを確認できる
- lint、型検査、単体・結合・評価テストがCIで通る
- Dockerで再現でき、READMEに構成、実行、評価、制約が書かれている
- 「なぜこのモデル・検索方式・agent構成にしたか」を評価結果で説明できる

## 5. 週次レビューの採点表

毎週末、各項目を0〜2点で自己採点する。合計8点未満なら翌週の初日に補習する。

| 項目 | 0点 | 1点 | 2点 |
|---|---|---|---|
| 理解 | 説明できない | 例を見れば説明できる | 制約と代替案まで説明できる |
| 実装 | 未完成 | happy pathのみ | 例外・境界値も扱う |
| テスト | なし | 手動確認 | 自動テストと固定データがある |
| 評価 | 感想のみ | 一部を計測 | 再現可能な指標で比較した |
| 文書化 | なし | メモのみ | 第三者が再現できる |

## 6. 公式資料の起点

APIやフレームワークは変化するため、ブログ記事より公式資料を優先し、モデル名やAPI形状をハードコードする前に再確認する。

- [OpenAI API model guidance](https://developers.openai.com/api/docs/guides/latest-model)
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)
- [OpenAI Agents SDK tracing](https://openai.github.io/openai-agents-python/tracing/)
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [LangChain Human-in-the-Loop](https://docs.langchain.com/oss/python/langchain/human-in-the-loop)
- [MCP architecture](https://modelcontextprotocol.io/docs/learn/architecture)
- [MCP authorization](https://modelcontextprotocol.io/docs/tutorials/security/authorization)

## 7. 直近の着手順

次回はDay 31から始める。ただし、最初の1週間では新しいagent frameworkを追加しない。先に既存のRRF、chunking、Tool Callingを純粋関数へ分割してテストで固定する。その後に同じ機能をResponses API、Agents SDK、LangGraphへ段階的に移すことで、フレームワーク内部の仕事を理解した状態で使えるようにする。
