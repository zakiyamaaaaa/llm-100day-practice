# LLM / AIエンジニア 100日カリキュラム

作成日: 2026-07-21  
改訂日: 2026-07-28  
現在地: Day 47完了、Day 48から再開

## 1. 最終ゴール

Day 100のゴールは、LLM APIのサンプルを書けることではなく、次の内容を設計・実装・評価・説明できる「採用レベルのLLM / AIエンジニア」になること。

- Token、Embedding、Attention、Context Windowを自分の言葉で説明できる
- RAGの検索・生成・引用・未回答を分離して評価できる
- Hybrid検索、Reranking、Context最適化を評価結果から選択できる
- Tool CallingとAgentを、型検証・停止条件・権限・承認付きで実装できる
- LLM機能をAPIとして公開し、非同期・Streaming・DB・認証を扱える
- Prompt Injection、権限越境、秘密漏洩をテストできる
- latency、token、cost、error、品質を観測できる
- pytest、型検査、Lint、Docker、CI/CDで再現可能な開発ができる
- 1つの完成プロジェクトについて、設計判断とトレードオフを面接で説明できる

最終成果物は「引用・評価・権限・承認・監視を備えた社内ナレッジ＆手続きエージェント」とする。

## 2. 1日の学習時間

1日約60分を標準とする。

- 10分: 用語・原理・前日の復習
- 30分: 既存コードを活かした実装
- 10分: 実行・テスト・評価
- 5分: 確認問題
- 5分: `notes/day-XXX.md`と`progress.md`の更新

1時間で終わらないテーマは複数Dayに分割する。大量の評価データ作成や全面的な書き直しだけを1日の課題にしない。

## 3. 重複を避けるルール

1. 以前作った機能は、同じ題材で再実装しない。
2. 再登場する技術は、監査・テスト・堅牢化・統合・性能測定のどれかに発展させる。
3. 新しいFrameworkは、既存の手書き実装と責務を比較してから導入する。
4. BM25、RRF、Reranker、Tool Calling、ReActは既存コードを土台にする。
5. `src/`構成への整理は、統合アプリの境界が見えたDay 93で行う。
6. API料金が必要なテストと、ローカルだけで完結するテストを分ける。
7. `memo.md`は個人メモとして変更せず、学習記録は`notes/`と`progress.md`へ保存する。

## 4. 現在までの到達点

### Phase 1 — Day 1〜30: LLM・RAG・Tool Callingの基礎

到達点:

- OpenAI API、環境変数、Pydantic、Structured Output
- Prompt Injectionの基本的な検知
- Embedding、コサイン類似度、ChromaDB
- Chunking、ファイル取り込み
- Hybrid検索、RRF
- Tool Callingの往復処理
- 手書きReActループと状態管理

### Phase 2 — Day 31〜47: 検索・評価・LLM内部理解

| Day | 学習内容 | 状態 |
|---:|---|:---:|
| 31 | リポジトリと学習履歴の棚卸し | 完了 |
| 32 | BM25の自作とスコア計算 | 完了 |
| 33 | 日本語Tokenizerの比較 | 完了 |
| 34 | BM25とベクトル検索の比較 | 完了 |
| 35 | RRFによるランキング統合 | 完了 |
| 36 | LLM Reranker | 完了 |
| 37 | Hybrid RAG Pipeline | 完了 |
| 38 | RAG評価ケースの設計 | 完了 |
| 39 | Hit@k、MRR、未回答評価 | 完了 |
| 40 | Groundedness、Relevance、正解判定 | 完了 |
| 41 | Zero-shot、Few-shot、Grounded Prompt比較 | 完了 |
| 42 | Optional、拒否、model validator | 完了 |
| 43 | Token、Embedding、Attention、Context Window | 完了 |
| 44 | Retrieval・Generation評価の統合レポート | 完了 |
| 45 | 30ケースへの機械的な増加 | 保留。既存評価セットで代替 |
| 46 | Recall@k | 完了 |
| 47 | Citation Precision、Recall、引用根拠性 | 完了 |

Phase 2の達成ポイント:

- 検索失敗と生成失敗を分けて説明できる
- BM25、Vector、Hybrid、Rerankerの役割を説明できる
- 検索・回答・引用を数値で評価できる
- PromptやTokenizer変更の効果を再現可能な結果で比較できる

---

## 5. Day 48〜100

### Phase 3 — Day 48〜58: Production RAG

フェーズゴール:

> 既存のRAG部品を、更新可能・評価可能・引用付きの1本のPipelineとして統合する。

採用で示すもの:

- RAGの改善前後を比較した評価レポート
- 文書更新に対応したIngest
- 根拠付き回答と安全な未回答
- 単体テスト付きProduction RAG v1

| Day | テーマ | 前回内容の活用 | 60分の成果物・完了条件 |
|---:|---|---|---|
| 48 | BM25品質監査 | `bm25_search.py`, Day32 | BM25式を修正し、修正前後の検索結果と指標を比較する |
| 49 | Chunk境界の品質監査 | `chanking_rag.py`, `file_ingest_rag.py`、既存Tokenizer | 固定長の再実装ではなく、見出し・文・段落・形態素の役割を整理し、意味境界を壊さない分割方針を決める |
| 50 | Metadata付きIngest | 既存のファイル取り込み | source・section・chunk_idを検索結果まで保持する |
| 51 | 更新・削除・重複排除 | ChromaDBの永続化 | content hashで再投入時の重複を防ぐ |
| 52 | Query Rewrite | 既存の評価セット | Rewriteあり・なしで失敗Queryを比較する |
| 53 | Multi-query検索 | Vector検索とRRF | 1質問から複数Queryを作り、重複除去して統合する |
| 54 | Rerankerの定量評価 | `llm_reranker.py` | 精度・API回数・latencyのBefore/Afterを記録する |
| 55 | Context Builder | Hybrid検索結果 | 重複除去、並び替え、Token上限を1関数にまとめる |
| 56 | 引用・未回答の統合 | Day40、Day47 | 回答にsourceを付け、根拠なしでは拒否する |
| 57 | 失敗分類と閾値 | `evaluate_rag.py` | 検索失敗・生成失敗・引用失敗を分類し、拒否閾値を決める |
| 58 | Production RAG v1 | Day48〜57の部品 | ingest→retrieve→rerank→answer→cite→evaluateが1コマンドで動く |

Phase 3の達成ポイント:

- 文書追加・更新・再投入を安全に扱える
- 回答に検証可能なsourceが付く
- 情報不足時に推測せず回答を保留できる
- 変更による品質・費用・latencyの差を説明できる

---

### Phase 4 — Day 59〜70: 安全なAgent・Tool・MCP

フェーズゴール:

> 既存のTool CallingとReActを、暴走・誤実行・障害に耐える状態付きAgentへ発展させる。

採用で示すもの:

- 型安全なTool Registry
- 停止条件・予算・監査ログ付きAgent
- CheckpointとHuman-in-the-Loop
- RAG検索を公開するMCP Server

| Day | テーマ | 前回内容の活用 | 60分の成果物・完了条件 |
|---:|---|---|---|
| 59 | Tool引数とAllowlist | `tool_calling_complete.py` | Pydantic引数と許可済みTool Registryを追加する |
| 60 | Tool障害処理 | 既存Tool実行部 | JSON不正、未知Tool、例外、timeoutを構造化エラーで返す |
| 61 | 複数Tool実行 | `agent_react_loop.py` | 並列可能Toolと依存Toolの実行順をテストする |
| 62 | 停止条件と予算 | ReActの最大3ループ | 最大turn・Tool回数・時間・Token予算で必ず停止させる |
| 63 | RAGをTool化 | Production RAG v1 | `search_documents` Toolからsource付き検索結果を返す |
| 64 | 状態機械 | `agent_state_workflow.py` | state・node・edge・終了条件を純粋関数としてテストする |
| 65 | Framework選定 | 手書きReActと状態機械 | LangGraph・Agents SDKの責務を比較し、LangGraph版の最小Graphを作る |
| 66 | Checkpoint・再開 | LangGraphの状態 | SQLiteへ状態を保存し、プロセス終了後に再開する |
| 67 | Human-in-the-Loop | 書き込みTool | approve・edit・rejectの3経路をテストする |
| 68 | Memory設計 | 会話履歴とstate | 短期履歴・要約・ユーザー記憶を分離し、削除ルールを定義する |
| 69 | MCPの基本 | RAG Tool | RAG検索をMCP Tool / Resourceとして公開する |
| 70 | Agent v1演習 | Day59〜69 | 制限・再開・承認・監査ログ付きAgentをデモする |

Phase 4の達成ポイント:

- Tool、Agent、Workflow、MCPの違いを説明できる
- 不正な引数や未知Toolを実行しない
- 無限ループを防ぎ、途中状態から再開できる
- 副作用のある処理は人間の承認なしに実行されない

---

### Phase 5 — Day 71〜80: LLMアプリのAPI・データ設計

フェーズゴール:

> CLIサンプルを、他アプリから安全に利用できるRAG / Agent APIへ変える。

採用で示すもの:

- FastAPIのOpenAPI仕様
- Streaming対応Query API
- 永続DBとMigration
- 認証・ACL・結合テスト

| Day | テーマ | 前回内容の活用 | 60分の成果物・完了条件 |
|---:|---|---|---|
| 71 | FastAPI基礎 | Production RAG v1 | `/health`と`/query`を作りOpenAPI UIで実行する |
| 72 | Ingest API | Metadata付きIngest | `/ingest`に型検証とエラー応答を追加する |
| 73 | 非同期処理 | OpenAI・Embedding呼び出し | async版を作り、同期版との処理時間を比較する |
| 74 | Streaming | 回答生成とAgent Event | SSEでTokenまたは進捗Eventを逐次返す |
| 75 | DB Schema | 文書・会話・評価結果 | SQLite/PostgreSQL向けSchemaとMigrationを作る |
| 76 | Background Job | Ingest処理 | job_id、進捗、成功、失敗理由を取得できる |
| 77 | 認証・文書ACL | source metadata | user/adminを分け、他ユーザー文書を検索できないようにする |
| 78 | APIの耐障害性 | timeout・retry・予算 | rate limit、timeout、retry、エラー形式を統一する |
| 79 | API結合テスト | pytestと固定評価データ | ingest→query→citationの主要経路を自動テストする |
| 80 | RAG API v1 | Day71〜79 | 認証・DB・Streaming付きAPIをREADME手順で再現する |

Phase 5の達成ポイント:

- LLM機能をHTTP APIとして提供できる
- 非同期・Streaming・DB・認証の役割を説明できる
- API障害を一定の形式で返し、結合テストで保証できる

---

### Phase 6 — Day 81〜90: Security・Observability・Delivery

フェーズゴール:

> 品質・安全性・速度・費用を継続的に観測し、再現可能な形で配布する。

採用で示すもの:

- 脅威モデルと攻撃テスト
- 構造化Log、Trace、Metrics、SLO
- 費用・負荷テスト
- DockerとCI/CD

| Day | テーマ | 前回内容の活用 | 60分の成果物・完了条件 |
|---:|---|---|---|
| 81 | 脅威モデリング | RAG APIとAgent | asset、trust boundary、attack path、対策を図示する |
| 82 | 攻撃評価 | Prompt Injection検知 | direct/indirect injection、data exfiltrationの固定テストを作る |
| 83 | 多層Guardrail | Structured Output・ACL | 入力・検索・出力・Tool・権限の防御を分離する |
| 84 | 構造化Log | APIとAgent実行 | request_id、latency、token、cost、Tool結果を秘密なしで記録する |
| 85 | Tracing | Retrieval・LLM・Tool | 1リクエストをspanで追跡し、失敗箇所を特定する |
| 86 | MetricsとSLO | 評価指標とAPI計測 | p50/p95、成功率、Grounded率、費用の目標値を決める |
| 87 | 費用・latency最適化 | Prompt・Context Builder | cache、batch、model routingを1条件ずつ比較する |
| 88 | 負荷テスト | RAG API v1 | 同時実行時のp95、error率、1件単価を記録する |
| 89 | Docker | API・DB・設定 | 新しい環境で1コマンド起動できる |
| 90 | CI/CD | tests・eval・Docker | lint、型、test、eval、image buildを自動実行する |

Phase 6の達成ポイント:

- 本番障害を再現・分類・追跡できる
- 秘密情報をLogに残さず、品質と費用を計測できる
- Pull Request相当の変更で品質低下を自動検出できる
- Dockerで第三者が同じ環境を再現できる

---

### Phase 7 — Day 91〜100: 卒業制作・採用準備

フェーズゴール:

> これまでの部品を1つの完成プロジェクトに統合し、採用面接で設計・実装・評価・運用を説明できる状態にする。

卒業制作:

「引用・権限・承認・評価・監視を備えた社内ナレッジ＆手続きエージェント」

| Day | テーマ | 前回内容の活用 | 60分の成果物・完了条件 |
|---:|---|---|---|
| 91 | 要件定義 | 全フェーズの到達点 | user story、対象外、品質・latency・費用目標を決める |
| 92 | Architecture・脅威モデル | RAG、Agent、API、DB | Component責務、Data flow、Trust boundaryを図示する |
| 93 | Repository整理 | 独立Pythonスクリプト群 | 必要な責務だけ`src/`へ移し、設定と依存方向を固定する |
| 94 | Core RAG統合 | Production RAG v1 | Ingest、Hybrid、Rerank、引用、未回答を統合する |
| 95 | Agent統合 | Agent v1 | Tool、Checkpoint、承認、再開を統合する |
| 96 | API・DB統合 | RAG API v1 | 認証、ACL、Streaming、履歴保存をつなぐ |
| 97 | 品質仕上げ | eval、攻撃、負荷テスト | unit、integration、eval、security、loadを通す |
| 98 | 配布・Deployment | Docker、CI/CD | 環境変数と秘密管理を含め、デプロイまたは再現手順を完成する |
| 99 | Portfolio文書 | 評価結果と設計判断 | README、構成図、ADR、デモ手順、制約、改善案を書く |
| 100 | 卒業審査 | 完成プロジェクト | 15分デモ、設計質疑、障害説明、履歴書用要約を完成する |

## 6. Day 100の採用レベル判定

以下をすべて説明または実演できれば完了とする。

- LLMのToken、Embedding、Attention、Context Windowを説明できる
- Prompt、RAG、Fine-tuningの使い分けを説明できる
- Hybrid検索とRerankerの採用理由を評価結果から説明できる
- Retrieval、Generation、Citationを別々に評価できる
- 15件以上の厳選した固定評価セットに、通常・未回答・攻撃・回帰ケースがある
- 回答にsourceまたはsectionの引用が付く
- 情報不足時は推測せず回答を拒否できる
- Toolに型検証、Allowlist、timeout、停止条件、予算、監査Logがある
- 副作用のあるToolはHuman-in-the-Loopを通る
- AgentをCheckpointから再開できる
- APIに認証、ACL、rate limit、Streaming、health checkがある
- latency、token、cost、error、品質を追跡できる
- unit、integration、eval、security testがある
- Lint、型検査、test、eval、Docker buildがCIで通る
- DockerまたはDeployment手順で第三者が再現できる
- READMEだけで15分以内に主要Demoを実行できる
- 「なぜこの設計にしたか」「代替案は何か」を面接形式で説明できる

## 7. 毎日の完了ルール

次の順番を守る。

1. `CURRICULUM_DAY31_100.md`と`progress.md`から現在Dayを確認する
2. 用語と目的を初心者向けに説明する
3. 既存成果を確認し、重複しない実装を行う
4. 実行結果を確認する
5. 確認問題を出し、1問ずつ採点する
6. 不十分なら小さな追加問題を出す
7. 理解できたら`notes/day-XXX.md`を作成または更新する
8. `progress.md`へ完了状況、問題数、正答率、API費用、要復習事項を記録する
9. 記録が終わるまで次のDayへ進まない

## 8. 範囲外・卒業後の選択科目

採用レベルのCoreを優先するため、以下はDay100後の選択科目とする。

- Vision・画像/PDF理解の高度化
- Realtime音声
- Fine-tuningの実行
- 複数Agentによる役割分担
- Kubernetes
- 大規模分散Vector DB

これらは必要性が生じたときに追加し、Coreの未完成を残したまま広げない。
