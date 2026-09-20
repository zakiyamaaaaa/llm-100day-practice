export const phases = [
  {
    id: "foundation",
    order: 1,
    days: "Day 1–30",
    eyebrow: "はじまりの平原",
    title: "LLM基礎とRAG",
    icon: "✦",
    color: "#70d6a2",
    summary: "LLMの言葉を理解し、検索して答える最初の仕組みを組み立てる。",
    skills: ["Token / Embedding", "Structured Output", "RAG", "Tool Calling"],
    quests: [
      {
        id: "first-call",
        title: "最初の召喚",
        type: "基礎",
        duration: 45,
        xp: 120,
        description: "API、環境変数、構造化出力を理解し、安定したJSONを返す。",
        objectives: ["APIキーを安全に環境変数へ置く", "Pydanticで出力形式を定義する", "失敗時の挙動を説明する"],
        source: "README: APIと構造化出力",
      },
      {
        id: "rag-seed",
        title: "知識の種を探せ",
        type: "実装",
        duration: 60,
        xp: 160,
        description: "キーワード検索からEmbedding、ChromaDBまで最小RAGを育てる。",
        objectives: ["検索と生成の責務を分ける", "コサイン類似度を説明する", "根拠文書を回答へ渡す"],
        source: "README: RAGとEmbedding",
      },
      {
        id: "tool-scout",
        title: "道具使いの試練",
        type: "実装",
        duration: 60,
        xp: 180,
        description: "Tool CallingとReActで、考える・動く・観察するループを作る。",
        objectives: ["Toolの引数を構造化する", "実行結果をLLMへ返す", "最大ループ回数を設ける"],
        source: "README: Tool Callingとエージェント",
      },
    ],
  },
  {
    id: "retrieval",
    order: 2,
    days: "Day 31–47",
    eyebrow: "検索者の峡谷",
    title: "検索・評価・内部理解",
    icon: "⌕",
    color: "#73a9ff",
    summary: "勘ではなく指標で検索を比べ、LLMの内部と失敗箇所を説明する。",
    skills: ["BM25 / RRF", "Reranker", "Hit@k / MRR", "Citation評価"],
    quests: [
      {
        id: "hybrid-forge",
        title: "ふたつの検索を鍛えよ",
        type: "比較",
        duration: 60,
        xp: 190,
        description: "BM25とベクトル検索をRRFで統合し、得意分野の違いを測る。",
        objectives: ["BM25の式を説明する", "RRFで順位を統合する", "Hybridの改善を評価する"],
        source: "Curriculum Day 32–37",
      },
      {
        id: "metric-compass",
        title: "評価の羅針盤",
        type: "評価",
        duration: 60,
        xp: 220,
        description: "Hit@k、MRR、Recallで検索失敗と生成失敗を切り分ける。",
        objectives: ["固定評価ケースを用意する", "検索指標を計算する", "失敗カテゴリを記録する"],
        source: "Curriculum Day 38–46",
      },
      {
        id: "citation-oath",
        title: "引用の誓約",
        type: "評価",
        duration: 60,
        xp: 240,
        description: "正解らしさだけでなく、回答が根拠に支えられているかを測る。",
        objectives: ["Groundednessを評価する", "Citation Precisionを計算する", "Citation Recallを計算する"],
        source: "Curriculum Day 40 / 47",
      },
    ],
  },
  {
    id: "production-rag",
    order: 3,
    days: "Day 48–58",
    eyebrow: "知識工房",
    title: "Production RAG",
    icon: "◆",
    color: "#f7c86a",
    summary: "更新でき、引用でき、情報不足なら止まれるRAGを一本につなぐ。",
    skills: ["Metadata Ingest", "Query Rewrite", "Context Builder", "安全な未回答"],
    quests: [
      {
        id: "ingest-craft",
        title: "壊れない知識庫",
        type: "実装",
        duration: 60,
        xp: 260,
        description: "意味境界を守り、metadataとhashを持つ再投入可能なIngestを作る。",
        objectives: ["意味単位でChunkingする", "source・sectionを保持する", "重複と削除を扱う"],
        source: "Curriculum Day 48–51",
      },
      {
        id: "context-alchemy",
        title: "文脈錬成術",
        type: "改善",
        duration: 60,
        xp: 280,
        description: "Query Rewrite、Multi-query、Rerankerで必要な文脈だけを集める。",
        objectives: ["失敗Queryを書き換える", "複数検索結果を統合する", "Token上限内に整える"],
        source: "Curriculum Day 52–55",
      },
      {
        id: "rag-boss",
        title: "ボス：根拠なき回答",
        type: "ボス",
        duration: 90,
        xp: 360,
        description: "引用・未回答・評価を統合し、Production RAG v1を完成させる。",
        objectives: ["source付きで回答する", "根拠なしなら拒否する", "品質・費用・latencyを比較する"],
        source: "Curriculum Day 56–58",
      },
    ],
  },
  {
    id: "safe-agent",
    order: 4,
    days: "Day 59–70",
    eyebrow: "自律機械の遺跡",
    title: "安全なAgent・MCP",
    icon: "⬡",
    color: "#d49cff",
    summary: "動くだけのAgentを、止まり、再開し、承認を待てる仕組みにする。",
    skills: ["Tool Registry", "停止条件", "Checkpoint", "Human-in-the-Loop"],
    quests: [
      {
        id: "tool-guard",
        title: "道具庫の番人",
        type: "安全性",
        duration: 60,
        xp: 280,
        description: "型検証、Allowlist、timeoutで不正なTool実行を防ぐ。",
        objectives: ["Pydanticで引数検証する", "未知Toolを拒否する", "例外を構造化して返す"],
        source: "Curriculum Day 59–63",
      },
      {
        id: "state-maze",
        title: "状態迷宮からの帰還",
        type: "設計",
        duration: 60,
        xp: 310,
        description: "状態機械とCheckpointで、必ず止まり途中から再開できるAgentを作る。",
        objectives: ["node・edge・stateを分ける", "予算で停止する", "SQLiteから再開する"],
        source: "Curriculum Day 64–66",
      },
      {
        id: "approval-gate",
        title: "承認の門",
        type: "ボス",
        duration: 90,
        xp: 380,
        description: "副作用のあるToolを人の承認で制御し、RAGをMCPとして公開する。",
        objectives: ["approve・edit・rejectを実装する", "監査ログを残す", "MCP Toolを公開する"],
        source: "Curriculum Day 67–70",
      },
    ],
  },
  {
    id: "api",
    order: 5,
    days: "Day 71–80",
    eyebrow: "接続都市 API",
    title: "API・データ設計",
    icon: "⇄",
    color: "#ff9f7a",
    summary: "CLIの知能を、認証された他アプリが安全に使えるサービスへ変える。",
    skills: ["FastAPI", "Streaming", "DB / Migration", "認証・ACL"],
    quests: [
      {
        id: "api-gateway",
        title: "外界への門を開く",
        type: "実装",
        duration: 60,
        xp: 300,
        description: "型付きのQuery・Ingest APIとhealth checkを公開する。",
        objectives: ["OpenAPIを確認する", "入力エラーを統一する", "asyncで外部I/Oを扱う"],
        source: "Curriculum Day 71–73",
      },
      {
        id: "stream-vault",
        title: "流れる応答、残る記録",
        type: "設計",
        duration: 60,
        xp: 330,
        description: "SSE、DB、Background Jobで長い処理を扱う。",
        objectives: ["進捗Eventを配信する", "Migrationを作る", "job状態を永続化する"],
        source: "Curriculum Day 74–76",
      },
      {
        id: "acl-boss",
        title: "ボス：権限越境",
        type: "ボス",
        duration: 90,
        xp: 400,
        description: "認証・ACL・耐障害性を結合テストで保証する。",
        objectives: ["他ユーザー文書を遮断する", "timeout・retryを制御する", "主要経路を結合テストする"],
        source: "Curriculum Day 77–80",
      },
    ],
  },
  {
    id: "operations",
    order: 6,
    days: "Day 81–90",
    eyebrow: "観測者の塔",
    title: "Security・運用・Delivery",
    icon: "◉",
    color: "#63d7dc",
    summary: "安全性、品質、速度、費用を見える化し、再現可能に届ける。",
    skills: ["Threat Model", "Trace / Metrics", "SLO", "Docker / CI"],
    quests: [
      {
        id: "threat-map",
        title: "脅威の地図",
        type: "安全性",
        duration: 60,
        xp: 320,
        description: "Trust Boundaryを描き、Injectionと秘密漏洩を固定テストにする。",
        objectives: ["資産と攻撃経路を列挙する", "direct/indirect攻撃を試す", "多層Guardrailを設計する"],
        source: "Curriculum Day 81–83",
      },
      {
        id: "observatory",
        title: "品質観測所",
        type: "運用",
        duration: 60,
        xp: 350,
        description: "Log、Trace、Metricsで1リクエストの品質と費用を追う。",
        objectives: ["秘密なしの構造化Logを出す", "spanで失敗箇所を追う", "SLOを定義する"],
        source: "Curriculum Day 84–88",
      },
      {
        id: "delivery-line",
        title: "再現可能性の砦",
        type: "ボス",
        duration: 90,
        xp: 420,
        description: "DockerとCI/CDで、誰でも同じ品質のアプリを動かせるようにする。",
        objectives: ["1コマンドで起動する", "lint・型・test・evalを通す", "image buildを自動化する"],
        source: "Curriculum Day 89–90",
      },
    ],
  },
  {
    id: "graduation",
    order: 7,
    days: "Day 91–100",
    eyebrow: "最終到達地",
    title: "卒業制作・採用準備",
    icon: "♜",
    color: "#ff7d99",
    summary: "すべての設計判断を一つの完成品に統合し、説明できる証拠を残す。",
    skills: ["Architecture", "統合テスト", "Deployment", "Portfolio"],
    quests: [
      {
        id: "blueprint",
        title: "卒業制作の設計図",
        type: "設計",
        duration: 90,
        xp: 380,
        description: "要件、品質目標、Architecture、脅威モデルを言語化する。",
        objectives: ["user storyと対象外を決める", "責務と依存方向を描く", "設計の代替案を残す"],
        source: "Curriculum Day 91–93",
      },
      {
        id: "integration",
        title: "七つの力を統合せよ",
        type: "実装",
        duration: 120,
        xp: 480,
        description: "RAG、Agent、API、DB、認証、監視を一つのアプリに統合する。",
        objectives: ["Core RAGを統合する", "承認付きAgentを統合する", "品質・攻撃・負荷をテストする"],
        source: "Curriculum Day 94–97",
      },
      {
        id: "final-demo",
        title: "最終クエスト：15分の証明",
        type: "最終ボス",
        duration: 120,
        xp: 600,
        description: "第三者が再現できる形で配布し、設計判断を面接形式で語る。",
        objectives: ["READMEだけでDemoを再現する", "評価結果と制約を示す", "なぜこの設計かを説明する"],
        source: "Curriculum Day 98–100",
      },
    ],
  },
];

// Visual companions and rewards are kept in data so the roadmap can grow
// without hard-coding image markup in the renderer.  Missing files are
// expected during development; app.js renders initials/emoji fallbacks.
export const characterRoster = [
  { id: "minato", name: "ミナト", role: "境界を守るメンター", image: "assets/characters/minato.png", initials: "MN", color: "#70d6a2" },
  { id: "sora", name: "ソラ", role: "根拠を探すスカウト", image: "assets/characters/sora.png", initials: "SR", color: "#73a9ff" },
  { id: "kai", name: "カイ", role: "道具使いのスカウト", image: "assets/characters/kai.png", initials: "KI", color: "#86c7ff" },
  { id: "ren", name: "レン", role: "評価を読むアナリスト", image: "assets/characters/ren.png", initials: "RN", color: "#f7c86a" },
  { id: "aya", name: "アヤ", role: "順位を測るアナリスト", image: "assets/characters/aya.png", initials: "AY", color: "#ffb36d" },
  { id: "mio", name: "ミオ", role: "引用を守るガーディアン", image: "assets/characters/mio.png", initials: "MO", color: "#f2a5ff" },
  { id: "takumi", name: "タクミ", role: "知識庫を組むビルダー", image: "assets/characters/takumi.png", initials: "TK", color: "#d49cff" },
  { id: "nagi", name: "ナギ", role: "状態を記録するビルダー", image: "assets/characters/nagi.png", initials: "NG", color: "#c7a6ff" },
  { id: "gaku", name: "ガク", role: "脅威を見つけるガーディアン", image: "assets/characters/gaku.png", initials: "GK", color: "#63d7dc" },
  { id: "haru", name: "ハル", role: "再現性を届けるシッパー", image: "assets/characters/haru.png", initials: "HR", color: "#ff9f7a" },
  { id: "rei", name: "レイ", role: "APIを設計するシッパー", image: "assets/characters/rei.png", initials: "RE", color: "#ffbd83" },
  { id: "yuna", name: "ユナ", role: "最終デモのナビゲーター", image: "assets/characters/yuna.png", initials: "YN", color: "#ff7d99" },
];

export const gearCatalog = [
  { id: "api-key-seal", name: "API Key Seal", label: "環境変数の護符", image: "assets/gear/api-key-seal.png", rarity: "UNCOMMON", color: "#70d6a2" },
  { id: "retrieval-compass", name: "Retrieval Compass", label: "根拠を探す羅針盤", image: "assets/gear/retrieval-compass.png", rarity: "RARE", color: "#73a9ff" },
  { id: "tool-scout-badge", name: "Tool Scout Badge", label: "道具使いのバッジ", image: "assets/gear/tool-scout-badge.png", rarity: "RARE", color: "#86c7ff" },
  { id: "rrf-forge", name: "RRF Forge", label: "順位統合の炉", image: "assets/gear/rrf-forge.png", rarity: "RARE", color: "#f7c86a" },
  { id: "metric-lens", name: "Metric Lens", label: "評価のレンズ", image: "assets/gear/metric-lens.png", rarity: "EPIC", color: "#ffb36d" },
  { id: "citation-shield", name: "Citation Shield", label: "引用の盾", image: "assets/gear/citation-shield.png", rarity: "EPIC", color: "#f2a5ff" },
  { id: "ingest-hammer", name: "Ingest Hammer", label: "知識庫の鍛造槌", image: "assets/gear/ingest-hammer.png", rarity: "EPIC", color: "#d49cff" },
  { id: "checkpoint-key", name: "Checkpoint Key", label: "再開の鍵", image: "assets/gear/checkpoint-key.png", rarity: "EPIC", color: "#c7a6ff" },
  { id: "approval-seal", name: "Approval Seal", label: "承認の印", image: "assets/gear/approval-seal.png", rarity: "LEGENDARY", color: "#63d7dc" },
  { id: "api-gauntlet", name: "API Gauntlet", label: "接続都市の手甲", image: "assets/gear/api-gauntlet.png", rarity: "LEGENDARY", color: "#ff9f7a" },
  { id: "observability-orb", name: "Observability Orb", label: "観測者のオーブ", image: "assets/gear/observability-orb.png", rarity: "LEGENDARY", color: "#ffbd83" },
  { id: "architect-crown", name: "Architect Crown", label: "アーキテクトの冠", image: "assets/gear/architect-crown.png", rarity: "MYTHIC", color: "#ff7d99" },
];

// Short aliases keep the data convenient for small integrations while the
// descriptive names remain the canonical API used by the app.
export const characters = characterRoster;
export const gear = gearCatalog;

const phaseVisuals = {
  foundation: { characterIds: ["minato", "sora", "kai"], gearIds: ["api-key-seal", "retrieval-compass", "tool-scout-badge"] },
  retrieval: { characterIds: ["ren", "aya", "mio"], gearIds: ["rrf-forge", "metric-lens", "citation-shield"] },
  "production-rag": { characterIds: ["takumi", "mio", "sora"], gearIds: ["ingest-hammer", "retrieval-compass", "citation-shield"] },
  "safe-agent": { characterIds: ["gaku", "nagi", "kai"], gearIds: ["checkpoint-key", "approval-seal", "tool-scout-badge"] },
  api: { characterIds: ["haru", "rei", "gaku"], gearIds: ["api-gauntlet", "observability-orb", "approval-seal"] },
  operations: { characterIds: ["gaku", "haru", "rei"], gearIds: ["observability-orb", "api-gauntlet", "metric-lens"] },
  graduation: { characterIds: ["yuna", "minato", "takumi"], gearIds: ["architect-crown", "approval-seal", "observability-orb"] },
};

phases.forEach((phase) => Object.assign(phase, phaseVisuals[phase.id] || { characterIds: [], gearIds: [] }));

const makeLesson = (title, intro, points) => ({ title, intro, points });

const makeCheck = (
  id,
  label,
  { terms = [], anyTerms = [], hint, hints = null, success, minLength = 24 } = {},
) => ({
  id,
  label,
  terms,
  anyTerms,
  // A check can opt into several progressively specific hints.  Existing
  // workshop data remains valid because its single hint becomes level one.
  hint,
  hints: Array.isArray(hints) && hints.length ? hints : [hint].filter(Boolean),
  success,
  minLength,
});

const guideFiles = {
  mentor: "lumi",
  scout: "kernel",
  analyst: "lumi",
  builder: "kernel",
  guardian: "lumi",
  shipper: "kernel",
};

const guideCharacters = {
  mentor: "minato",
  scout: "sora",
  analyst: "ren",
  builder: "takumi",
  guardian: "gaku",
  shipper: "haru",
};

const makeWorkshop = ({ guide, guideName, lesson, kind, prompt, starter, placeholder, language, checks, reflectionPrompt }) => ({
  guideImage: `assets/guide-${guideFiles[guide] || guide}.png`,
  guideName,
  guideCharacterId: guideCharacters[guide] || guide,
  lesson,
  challenge: { kind, prompt, starter, placeholder, language },
  checks,
  reflectionPrompt,
});

// The workshop is deliberately data-driven.  Every quest has a small theory
// card, an editable response, and deterministic browser-side checks.  It keeps
// the game useful without an API key or an external chat window.
const workshops = {
  "first-call": makeWorkshop({
    guide: "mentor", guideName: "ミナト / 境界を守るメンター",
    lesson: makeLesson("信頼できる入出力の境界", "LLMを呼ぶ処理は、秘密・入力・出力・失敗を別々の責務として扱うと壊れにくくなります。", [
      { title: "秘密はコードの外", text: "APIキーは環境変数から読み、ログやリポジトリへ出さない。" },
      { title: "出力を契約にする", text: "Pydanticのモデルで必須フィールドと型を先に決める。" },
      { title: "失敗もデータ", text: "ValidationErrorやAPI障害を、呼び出し側が扱える形へ整える。" },
    ]),
    kind: "code", prompt: "入力は question: str、出力は answer: str と sources: list[str]、失敗は code/message を持つ ErrorModel とします。OPENAI_API_KEY を os.getenv で読み、Pydantic の RequestModel・ResponseModel・ErrorModel を定義する擬似Pythonを書いてください。ValidationError、missing API key、API timeout の3ケースをそれぞれどう返すかまで示します。",
    starter: "import os\nfrom pydantic import BaseModel, Field, ValidationError\n\nclass RequestModel(BaseModel):\n    question: str = Field(min_length=1)\n\nclass ResponseModel(BaseModel):\n    answer: str\n    sources: list[str]\n\nclass ErrorModel(BaseModel):\n    code: str\n    message: str\n\ndef call_llm(request: RequestModel) -> ResponseModel | ErrorModel:\n    api_key = os.getenv(\"OPENAI_API_KEY\")\n    # 入力: question。出力: answer と sources。\n    # 失敗ケース: ValidationError / missing API key / API timeout。\n    raise NotImplementedError\n",
    placeholder: "ここに実装案を書いてください…", language: "python",
    checks: [
      makeCheck("safe-env", "OPENAI_API_KEYを環境変数から読む", { terms: ["os.getenv", "OPENAI_API_KEY"], anyTerms: ["if not api_key", "api_key is None"], hints: ["os.getenv(\"OPENAI_API_KEY\") のように、秘密の値そのものを書かない。", "missing API keyなら起動を止め、キーをログへ出さずErrorModelを返す。"], hint: "os.getenv(\"OPENAI_API_KEY\") のように、秘密の値そのものを書かない。missing API key は安全なエラーへ変換する。", success: "OPENAI_API_KEYをコードへ埋め込まず、秘密の境界を守れています。" }),
      makeCheck("schema", "Request・Response・ErrorのPydanticモデルを定義する", { terms: ["BaseModel", "RequestModel", "ResponseModel", "ErrorModel"], anyTerms: ["Pydantic", "Field"], hints: ["入力のquestion、出力のanswer/sources、失敗のcode/messageを型付きモデルへ分ける。", "ResponseModelをLLMのstructured outputに指定し、sourcesをlist[str]で固定する。"], hint: "入力のquestion、出力のanswer/sources、失敗のcode/messageを型付きモデルへ分ける。", success: "入力・出力・エラーの契約を別モデルで表現できています。" }),
      makeCheck("failure", "3種類の失敗ケースを返す", { terms: ["ValidationError", "missing API key", "API timeout"], anyTerms: ["except"], hints: ["ValidationError、missing API key、API timeoutを隠さず、ErrorModelのcode/messageとして返す。", "呼び出し側が分岐できるよう、各ケースにvalidation_error / missing_api_key / api_timeoutのcodeを付ける。"], hint: "ValidationError、missing API key、API timeoutを隠さず、ErrorModelのcode/messageとして返す。", success: "ValidationError・missing API key・API timeoutを呼び出し側が扱える形にできています。" }),
    ],
    reflectionPrompt: "秘密と失敗を分けて考えたことで、以前の実装と何が変わりましたか？",
  }),
  "rag-seed": makeWorkshop({
    guide: "scout", guideName: "ソラ / 根拠を探すスカウト",
    lesson: makeLesson("検索と生成を分ける", "RAGは、関連する文書を探す工程と、見つけた根拠から答えを組み立てる工程の組み合わせです。", [
      { title: "責務を分離", text: "検索器は候補文書を返し、生成器は候補以外の知識を勝手に足さない。" },
      { title: "距離を意味にする", text: "Embeddingのコサイン類似度は、ベクトルの向きの近さを測る。" },
      { title: "根拠を添える", text: "回答へsourceや抜粋を渡すと、後から検証できる。" },
    ]),
    kind: "code", prompt: "入力は question: str と document{id, text, source} の配列、出力は answer: str と sources: list[str] のJSONです。検索→上位根拠の選択→根拠だけで生成する関数を書き、該当文書が0件なら推測せず未回答を返す失敗ケースも示してください。",
    starter: "def answer(question: str, documents: list[dict]) -> dict:\n    # 入力: question と id/text/source を持つ文書配列。\n    hits = search(question, documents)\n    context = [{\"id\": hit[\"id\"], \"text\": hit[\"text\"]} for hit in hits[:3]]\n    if not context:\n        return {\"answer\": \"根拠がないため未回答\", \"sources\": []}\n    # 出力: context だけを渡した answer と sources。\n    return generate_with_evidence(question, context)\n",
    placeholder: "検索と生成の責務が分かる擬似コード…", language: "python",
    checks: [
      makeCheck("separate", "検索と生成の責務を分ける", { terms: ["検索", "生成"], hint: "retriever/searchとgenerator/LLMを別の段階または関数で示す。", success: "検索と生成を独立した責務として配置できています。" }),
      makeCheck("similarity", "コサイン類似度を説明する", { terms: ["類似度"], anyTerms: ["コサイン", "cosine", "内積"], hint: "ベクトルの向きや正規化との関係を一言添える。", success: "Embeddingの近さを測る考え方が表現されています。" }),
      makeCheck("evidence", "根拠文書を回答へ渡す", { terms: ["根拠"], anyTerms: ["source", "引用", "context"], hint: "回答オブジェクトにsource、またはプロンプトにcontextを渡す。", success: "回答が根拠へ戻れるようになっています。" }),
    ],
    reflectionPrompt: "根拠がないときに答えないために、次の実装で追加したい条件は何ですか？",
  }),
  "tool-scout": makeWorkshop({
    guide: "scout", guideName: "カイ / 道具使いのスカウト",
    lesson: makeLesson("考える・動く・観察する", "Tool Callingは、モデルに任せる部分とアプリが検証・実行する部分を明確にするループです。", [
      { title: "引数は契約", text: "Tool名と引数をスキーマで検証し、予期しない入力を実行しない。" },
      { title: "結果を戻す", text: "ツール結果を観察可能なメッセージとしてLLMへ返す。" },
      { title: "停止条件", text: "最大ステップ数、timeout、完了条件を必ず設ける。" },
    ]),
    kind: "code", prompt: "入力は model_call{name, arguments}、出力は final_answer または observation の履歴です。許可済みToolを引数schemaで検証して実行し、unknown tool・invalid arguments・timeout・MAX_STEPS到達をそれぞれ停止可能なエラーとして返すReActループを書いてください。",
    starter: "MAX_STEPS = 4\n\ndef react_loop(question: str) -> dict:\n    # 入力: question と model_call{name, arguments}。出力: answer/observation履歴。\n    history = []\n    for step in range(MAX_STEPS):\n        call = model_next(question, history)\n        if call.name not in ALLOWLIST:\n            return {\"error\": \"unknown tool\", \"history\": history}\n        args = validate_arguments(call.name, call.arguments)\n        observation = run_with_timeout(call.name, args)\n        history.append({\"observation\": observation})\n        if is_final(observation):\n            return {\"final_answer\": observation, \"history\": history}\n    return {\"error\": \"MAX_STEPS reached\", \"history\": history}\n",
    placeholder: "Tool Calling / ReAct のループ…", language: "python",
    checks: [
      makeCheck("arguments", "Toolの引数を構造化する", { terms: ["引数"], anyTerms: ["schema", "スキーマ", "arguments"], hint: "引数の型や必須項目を検証してから実行する。", success: "Toolの境界に入力契約があります。" }),
      makeCheck("result", "実行結果をLLMへ返す", { terms: ["実行結果"], anyTerms: ["tool result", "観察", "observation"], hint: "実行結果を次のモデル入力へ追加する流れを書く。", success: "考えるだけでなく、観察結果を次へ渡せています。" }),
      makeCheck("stop", "最大ループ回数を設ける", { terms: [], anyTerms: ["MAX_STEPS", "最大", "stop", "停止", "timeout"], hint: "無限ループを避けるカウンターまたはtimeoutを置く。", success: "Agentが止まれる条件を持っています。" }),
    ],
    reflectionPrompt: "Toolが失敗したとき、次の一手をモデルに任せる範囲とアプリが止める範囲はどこですか？",
  }),
  "hybrid-forge": makeWorkshop({
    guide: "analyst", guideName: "レン / 順位を測るアナリスト",
    lesson: makeLesson("二つの検索を一つの判断へ", "語の一致に強いBM25と意味の近さに強いベクトル検索は、順位を統合すると補完関係を作れます。", [
      { title: "BM25", text: "語の頻度と文書頻度、文書長を使ってキーワードの関連度を測る。" },
      { title: "RRF", text: "複数ランキングの順位を 1 / (k + rank) に変換して足し合わせる。" },
      { title: "比較は測定", text: "改善したと言う前に、同じ評価セットでベースラインと比べる。" },
    ]),
    kind: "code", prompt: "入力は query: str と id/text を持つ同一文書集合、出力は上位5件の id と RRF score、BM25単独との Recall@5/MRR 比較です。BM25順位とvector順位を k=60 の RRF で統合し、空集合・埋め込み失敗時のエラー扱いも書いてください。",
    starter: "def hybrid_search(query: str, documents: list[dict]) -> dict:\n    # 入力: query と id/text 文書。出力: top5[{id, rrf_score}] と比較指標。\n    if not documents:\n        return {\"results\": [], \"error\": \"empty documents\"}\n    bm25_rank = bm25(query, documents)\n    vector_rank = vector_search(query, documents)\n    scores = {}\n    for rank, item in enumerate(bm25_rank, start=1):\n        scores[item[\"id\"]] = scores.get(item[\"id\"], 0) + 1 / (60 + rank)\n    for rank, item in enumerate(vector_rank, start=1):\n        scores[item[\"id\"]] = scores.get(item[\"id\"], 0) + 1 / (60 + rank)\n    return {\"results\": top5(scores), \"comparison\": evaluate_against_baseline()}\n",
    placeholder: "BM25 / vector / RRF の比較コード…", language: "python",
    checks: [
      makeCheck("bm25", "BM25の式を説明する", { terms: ["BM25"], anyTerms: ["term", "頻度", "文書長"], hint: "BM25が語の頻度・文書頻度・文書長を見ることを書く。", success: "BM25が何を見ているか説明できています。" }),
      makeCheck("rrf", "RRFで順位を統合する", { terms: ["RRF", "順位"], anyTerms: ["rank", "1 /"], hint: "順位をスコアへ変換して、複数ランキングを足す考えを示す。", success: "ランキングを統合する手順が見えています。" }),
      makeCheck("improvement", "Hybridの改善を評価する", { terms: ["比較"], anyTerms: ["改善", "baseline", "Recall", "MRR"], hint: "ベースライン、同一ケース、指標の3点を明記する。", success: "検索方式の差を測定で確かめる設計です。" }),
    ],
    reflectionPrompt: "BM25とベクトル検索のどちらが苦手な質問を、どんな評価ケースで見つけますか？",
  }),
  "metric-compass": makeWorkshop({
    guide: "analyst", guideName: "レン / 評価を読むアナリスト",
    lesson: makeLesson("失敗箇所を指標で切り分ける", "検索が正しい文書を拾えていないのか、拾った文書から答えられていないのかを別々に測ります。", [
      { title: "固定ケース", text: "query、正解文書、期待順位を小さな評価セットとして固定する。" },
      { title: "Hit@k / MRR", text: "Top-kに入ったか、最初の正解が何位かを数字にする。" },
      { title: "分類して直す", text: "検索失敗と生成失敗を分けると、改善策が具体化する。" },
    ]),
    kind: "design", prompt: "入力は5件の固定ケース {query, gold_doc_ids} と各検索器の ranked_ids、出力は Hit@5・MRR・Recall と case_id別の failure_category です。gold_doc_ids欠損、検索結果0件、生成だけが失敗するケースを区別して記録する設計メモを書いてください。",
    starter: "## 評価セット（5件を固定）\n- case_id: q01〜q05\n- 入力: query と gold_doc_ids\n- 出力: ranked_ids と answer\n\n## 指標\n- Hit@5 = 正解が上位5件に入ったケースの割合\n- MRR = 最初の正解順位の逆数の平均\n- Recall = gold_doc_ids の回収率\n\n## 失敗カテゴリ\n- retrieval_miss: 検索結果0件または正解文書なし\n- generation_miss: 根拠はあるが回答が不正確\n- invalid_case: gold_doc_ids欠損を入力エラーにする\n",
    placeholder: "評価ケースと指標の設計メモ…", language: "markdown",
    checks: [
      makeCheck("cases", "固定評価ケースを用意する", { terms: ["評価"], anyTerms: ["case", "query", "正解文書"], hint: "ケース数、query、正解文書または正解順位を固定する。", success: "再現可能な評価セットの入口があります。" }),
      makeCheck("metrics", "検索指標を計算する", { terms: [], anyTerms: ["Hit@k", "MRR", "Recall"], hint: "Hit@k、MRR、Recallのうち何をどう計算するか書く。", success: "順位を数字で比較できる指標を選べています。" }),
      makeCheck("failure-categories", "失敗カテゴリを記録する", { terms: ["検索", "生成"], anyTerms: ["失敗", "カテゴリ", "原因"], hint: "検索失敗と生成失敗を分け、ケースごとに原因を残す。", success: "失敗を次の改善へつなげる記録になっています。" }),
    ],
    reflectionPrompt: "数字が改善してもユーザー体験が悪いままになるケースは、どんなものですか？",
  }),
  "citation-oath": makeWorkshop({
    guide: "guardian", guideName: "ユイ / 根拠を守るガーディアン",
    lesson: makeLesson("答えの正しさと根拠の正しさ", "引用の評価では、答えが正しいかだけでなく、主張が提示した根拠に支えられているかを確認します。", [
      { title: "Groundedness", text: "回答の主張がコンテキストから導ける割合を確認する。" },
      { title: "Citation Precision", text: "付けた引用のうち、本当にその主張を支える引用の割合。" },
      { title: "Citation Recall", text: "必要な主張へ引用を付け漏らしていない割合。" },
    ]),
    kind: "design", prompt: "入力は回答の3主張、各主張の citation_ids、参照コンテキストです。出力は groundedness・Citation Precision・Citation Recall の小数値と主張別の判定表にします。根拠にない主張、無関係な引用、引用漏れを別の失敗として扱う手順を書いてください。",
    starter: "## 回答評価の手順\n1. 回答を3つの主張 claim_id に分割する\n2. 各claim_idへ citation_ids とコンテキストを対応付ける\n3. 根拠から導けるかを grounded / unsupported で判定する\n4. Precision = 支持する引用数 / 付与した引用数\n5. Recall = 引用が必要な主張数のうち引用済みの割合\n\n## 失敗と合格基準\n- unsupported_claim / irrelevant_citation / missing_citation を記録する\n- 3指標が0.8以上、かつ重大主張に引用漏れなし\n",
    placeholder: "Groundedness と引用指標の評価設計…", language: "markdown",
    checks: [
      makeCheck("groundedness", "Groundednessを評価する", { terms: ["根拠"], anyTerms: ["groundedness", "主張"], hint: "主張ごとに、提示したコンテキストから導けるか判定する。", success: "回答が根拠に支えられているか測れます。" }),
      makeCheck("citation-precision", "Citation Precisionを計算する", { terms: ["precision"], anyTerms: ["citation", "引用"], hint: "付けた引用のうち、主張を支える引用の割合を書く。", success: "過剰な引用を検出する視点があります。" }),
      makeCheck("citation-recall", "Citation Recallを計算する", { terms: ["recall"], anyTerms: ["citation", "引用"], hint: "必要な主張のうち、引用を付けられた割合を書く。", success: "引用の付け漏れを測れる設計です。" }),
    ],
    reflectionPrompt: "引用を増やすほど良いとは限らないのはなぜですか？",
  }),
  "ingest-craft": makeWorkshop({
    guide: "builder", guideName: "タクミ / 知識庫を組むビルダー",
    lesson: makeLesson("更新できる知識庫の入口", "Ingestはファイルを分割して登録するだけでなく、後から更新・削除・追跡できる識別子を残す仕事です。", [
      { title: "意味単位で分ける", text: "見出しや段落の意味境界を守り、過度な分割で文脈を壊さない。" },
      { title: "出所を持つ", text: "source、section、hashをmetadataに保存すると再現性が上がる。" },
      { title: "再投入に耐える", text: "同じhashは重複登録せず、削除された文書も同期できるようにする。" },
    ]),
    kind: "code", prompt: "入力は source・section・text・updated_at を持つ文書、出力は id/text と source/section/hash のchunkレコードです。見出し・段落の意味境界で分割し、同じhashは再登録せず、削除済みsourceは無効化するIngestを書いてください。",
    starter: "def ingest(document: dict) -> list[dict]:\n    # 入力: source/section/text/updated_at。出力: chunk と metadata。\n    chunks = split_on_headings_and_paragraphs(document[\"text\"])\n    records = []\n    for index, text in enumerate(chunks):\n        record = {\n            \"id\": f\"{document['source']}:{index}\",\n            \"text\": text,\n            \"source\": document[\"source\"],\n            \"section\": document[\"section\"],\n            \"hash\": sha256(text),\n        }\n        if not store.has_hash(record[\"hash\"]):\n            store.upsert(record)\n            records.append(record)\n    mark_deleted_sources_as_inactive()\n    return records\n",
    placeholder: "再投入できるIngestの処理…", language: "python",
    checks: [
      makeCheck("chunking", "意味単位でChunkingする", { terms: ["chunk"], anyTerms: ["意味単位", "見出し", "段落"], hint: "文字数だけでなく、見出し・段落などの意味境界に触れる。", success: "文脈を壊しにくい分割方針です。" }),
      makeCheck("metadata", "source・sectionを保持する", { terms: ["source", "section"], anyTerms: ["metadata", "メタデータ"], hint: "chunkと一緒にsourceとsectionを保存する形を示す。", success: "後から根拠へ戻れるmetadataがあります。" }),
      makeCheck("dedupe", "重複と削除を扱う", { terms: ["hash"], anyTerms: ["重複", "削除", "idempotent"], hint: "hashで同一chunkを判定し、消えたsourceの扱いも書く。", success: "更新を前提にしたIngestになっています。" }),
    ],
    reflectionPrompt: "chunkの境界を誤ると、検索結果と引用にどんな影響が出ますか？",
  }),
  "context-alchemy": makeWorkshop({
    guide: "builder", guideName: "タクミ / 文脈を錬成するビルダー",
    lesson: makeLesson("必要な文脈だけを集める", "検索結果をそのまま詰め込むのではなく、質問を書き換え、複数候補を統合し、Token予算へ収めます。", [
      { title: "Query Rewrite", text: "曖昧な質問を検索しやすい語へ展開し、元の意図を失わないようにする。" },
      { title: "多様な候補", text: "Multi-queryで視点を増やし、重複除去とrerankで順序を整える。" },
      { title: "予算を守る", text: "コンテキストのToken上限を越えたら、低い候補から落とす。" },
    ]),
    kind: "code", prompt: "入力は曖昧な question: str と token_limit=1200、出力は重複除去・再順位付け済みの context と selected_sources です。Query Rewrite→3本の検索→merge/rerank→上限内切り詰めを実装し、候補0件と予算超過時は未回答可能な結果にしてください。",
    starter: "def build_context(question: str, token_limit: int = 1200) -> dict:\n    # 入力: question と token_limit。出力: context/selected_sources。\n    rewritten = rewrite_query(question)\n    candidates = merge_results([search(query) for query in rewritten[:3]])\n    ranked = rerank(dedupe(candidates))\n    context = take_until_token_limit(ranked, token_limit)\n    if not context:\n        return {\"context\": [], \"selected_sources\": [], \"status\": \"no evidence\"}\n    return {\"context\": context, \"selected_sources\": sources(context)}\n",
    placeholder: "Query Rewrite / Multi-query / Token予算…", language: "python",
    checks: [
      makeCheck("rewrite", "失敗Queryを書き換える", { terms: ["rewrite"], anyTerms: ["書き換え", "query", "展開"], hint: "検索用の別表現を生成し、元の質問と照合する工程を書く。", success: "検索の入口を改善する工程があります。" }),
      makeCheck("merge", "複数検索結果を統合する", { terms: ["統合"], anyTerms: ["multi-query", "重複", "rerank"], hint: "複数Queryの結果を重複除去または再順位付けしてまとめる。", success: "候補の多様性と順序を両立できています。" }),
      makeCheck("budget", "Token上限内に整える", { terms: ["上限"], anyTerms: ["token", "予算", "切り詰め"], hint: "Token数を数え、上限を越えた候補を落とす。", success: "文脈の量を制御できる設計です。" }),
    ],
    reflectionPrompt: "文脈を増やすことで起きるノイズや費用の問題を、どう観測しますか？",
  }),
  "rag-boss": makeWorkshop({
    guide: "guardian", guideName: "ユイ / 根拠なき回答を止めるガーディアン",
    lesson: makeLesson("根拠があるときだけ答える", "Production RAGでは、回答・引用・未回答・品質のトレードオフを一つの運用設計として扱います。", [
      { title: "回答にsource", text: "主張の近くにsourceを残し、ユーザーが検証できるようにする。" },
      { title: "安全な未回答", text: "信頼度や根拠が足りないとき、推測せず不足を伝える。" },
      { title: "品質だけではない", text: "品質・費用・latencyを同じ評価表で比べる。" },
    ]),
    kind: "design", prompt: "入力は query と上位検索候補（score/source付き）、出力は source付き answer または abstain=true の未回答JSONです。confidence<0.75、sourceなし、latency>2秒を失敗ケースとして分岐し、品質・費用・latencyを同じ評価表へ記録するProduction RAG v1の設計を書いてください。",
    starter: "## 回答ポリシー\n- confidence >= 0.75 かつ sourceあり: source付き answer を返す\n- confidence < 0.75 または sourceなし: {abstain: true, reason: \"根拠不足\"} を返す\n- latency > 2s: timeout扱いで再試行せず未回答にする\n\n## 記録する指標（同じ評価ケースで比較）\n- 品質: groundedness / citation recall\n- 費用: input_tokens + output_tokens と金額\n- latency: p50 / p95 と timeout件数\n",
    placeholder: "Production RAG v1 の設計と評価…", language: "markdown",
    checks: [
      makeCheck("sources", "source付きで回答する", { terms: ["source"], anyTerms: ["引用", "根拠"], hint: "回答の主張とsourceの対応を保存・表示する。", success: "検証可能な回答の出口があります。" }),
      makeCheck("abstain", "根拠なしなら拒否する", { terms: [], anyTerms: ["根拠なし", "拒否", "abstain", "未回答"], hint: "信頼できる根拠がない分岐では、推測せず未回答にする。", success: "答えない勇気を仕様にできています。" }),
      makeCheck("tradeoffs", "品質・費用・latencyを比較する", { terms: ["費用", "latency"], anyTerms: ["品質", "quality", "速度"], hint: "同じ評価ケースで品質、費用、latencyを並べて比較する。", success: "本番運用のトレードオフを見ています。" }),
    ],
    reflectionPrompt: "このRAGが推測で答えてしまう最悪のケースと、その防止策は何ですか？",
  }),
  "tool-guard": makeWorkshop({
    guide: "guardian", guideName: "ガク / 道具庫のガーディアン",
    lesson: makeLesson("実行前に境界を検証する", "安全なAgentは、Toolを増やす前に引数・許可された名前・例外の形式を固定します。", [
      { title: "型検証", text: "Pydanticなどで引数を検証し、文字列をそのままコマンドへ渡さない。" },
      { title: "Allowlist", text: "登録済みのToolだけを名前で解決し、未知Toolは拒否する。" },
      { title: "構造化例外", text: "timeoutや実行エラーも、ログとモデルが扱える形で返す。" },
    ]),
    kind: "code", prompt: "入力は tool_name: str と payload: dict、出力は ToolResult(data) または ErrorModel(code, message, retryable) です。Allowlist未登録、Pydantic ValidationError、timeoutを実行前後で構造化し、未知Toolを一度も呼ばない処理を書いてください。",
    starter: "TOOLS = {\"search\": SearchArgs, \"save\": SaveArgs}  # 登録済みToolだけ\n\nclass ErrorModel(BaseModel):\n    code: str\n    message: str\n    retryable: bool\n\ndef execute(name: str, payload: dict) -> dict:\n    # 入力: tool_name/payload。出力: data または ErrorModel。\n    if name not in TOOLS:\n        return ErrorModel(code=\"unknown_tool\", message=\"not allowed\", retryable=False).model_dump()\n    try:\n        args = TOOLS[name].model_validate(payload)\n        return run_with_timeout(name, args)\n    except ValidationError as exc:\n        return ErrorModel(code=\"invalid_arguments\", message=str(exc), retryable=False).model_dump()\n    except TimeoutError:\n        return ErrorModel(code=\"timeout\", message=\"tool timed out\", retryable=True).model_dump()\n",
    placeholder: "安全なTool Registryの処理…", language: "python",
    checks: [
      makeCheck("validate", "Pydanticで引数検証する", { terms: ["Pydantic"], anyTerms: ["BaseModel", "検証", "schema"], hint: "ToolごとのPydanticモデルを通してから実行する。", success: "実行前に引数を検証できています。" }),
      makeCheck("allowlist", "未知Toolを拒否する", { terms: ["allowlist"], anyTerms: ["許可", "登録済み", "拒否"], hint: "辞書やAllowlistにないTool名は実行せず、拒否結果を返す。", success: "許可された道具だけが動く境界です。" }),
      makeCheck("errors", "例外を構造化して返す", { terms: ["例外"], anyTerms: ["error", "timeout", "構造化"], hint: "error type・message・retry可否などを同じ形で返す。", success: "失敗を観測・再試行できる形にしています。" }),
    ],
    reflectionPrompt: "Allowlistを更新するときに、誰が何を確認すべきですか？",
  }),
  "state-maze": makeWorkshop({
    guide: "builder", guideName: "ナギ / 状態を記録するビルダー",
    lesson: makeLesson("止まれるAgent、戻れるAgent", "状態機械では、何を実行するか（node）、どこへ進むか（edge）、現在のデータ（state）を分けます。", [
      { title: "状態を明示", text: "node・edge・stateを分けると、再開地点と遷移理由が追跡できる。" },
      { title: "予算で停止", text: "step数、時間、費用などの予算を超える前にcheckpointを保存する。" },
      { title: "再開可能", text: "SQLiteなどへ状態を書き、プロセス再起動後も同じ地点から再開する。" },
    ]),
    kind: "design", prompt: "入力は run_id と質問、node/edge/state を持つ状態機械、step_budget=6 です。出力は各遷移後のSQLite checkpoint と再開結果です。step・時間・費用の予算超過と、再開時のTool二重実行を失敗ケースとして扱う設計図を書いてください。",
    starter: "## 状態モデル\n- node: retrieve / decide / act / finish\n- edge: success / needs_evidence / error の遷移条件\n- state: run_id, question, cursor, tool_result, idempotency_key\n\n## 停止と再開\n- checkpoint: 各node完了後にstateとcursorを保存\n- budget: step_budget=6 または time/cost 上限で停止\n- storage: SQLite checkpoints(run_id, node, state_json, updated_at)\n- resume: run_idを読み、idempotency_key済みToolは再実行しない\n",
    placeholder: "Agentの状態機械とCheckpoint設計…", language: "markdown",
    checks: [
      makeCheck("model", "node・edge・stateを分ける", { terms: ["node", "edge", "state"], anyTerms: ["状態", "遷移"], hint: "実行単位・遷移条件・保持データを別々に定義する。", success: "状態機械の責務が分離されています。" }),
      makeCheck("budget", "予算で停止する", { terms: ["予算"], anyTerms: ["budget", "step", "停止"], hint: "step、時間、費用のいずれかを数え、上限で停止する。", success: "Agentを無限に走らせない制御があります。" }),
      makeCheck("resume", "SQLiteから再開する", { terms: ["SQLite"], anyTerms: ["checkpoint", "再開", "保存"], hint: "checkpointをSQLiteへ保存し、run_idなどで読み戻す。", success: "途中状態を永続化して戻れる設計です。" }),
    ],
    reflectionPrompt: "再開時に同じToolを二重実行しないため、どんなidempotency設計が必要ですか？",
  }),
  "approval-gate": makeWorkshop({
    guide: "guardian", guideName: "ユイ / 承認を守るガーディアン",
    lesson: makeLesson("副作用の前に人を置く", "送信・削除・公開などの副作用は、Agentの判断だけで通さず、承認・編集・拒否と監査の証跡を残します。", [
      { title: "三つの判断", text: "approve、edit、rejectを明示し、承認前は副作用Toolを実行しない。" },
      { title: "監査ログ", text: "誰が、何を、いつ、どの入力で承認したかを後から追えるようにする。" },
      { title: "MCP境界", text: "公開するToolの説明・入力・権限をMCPの契約として整理する。" },
    ]),
    kind: "design", prompt: "入力は Agent が作った send_email(to, body) 提案と actor_id、出力は approve/edit/reject の判断・実行結果・監査ログです。承認前は副作用を実行せず、権限なし・期限切れ・reject時の失敗結果も含むHuman-in-the-Loop/MCP設計を書いてください。",
    starter: "## 承認フロー\n1. Agentが send_email(to, body) と理由を提案（まだ送信しない）\n2. 人が approve / edit / reject を選ぶ。期限切れはreject扱い\n3. approveのみ送信し、editは編集後の内容を再承認、rejectは停止\n4. actor_id・timestamp・入力hash・判断・結果を監査ログへ保存\n\n## MCP Tool契約\n- name: send_email\n- input schema: to: str, body: str\n- permission: email:send、副作用あり、承認必須\n",
    placeholder: "approve / edit / reject の安全設計…", language: "markdown",
    checks: [
      makeCheck("decision", "approve・edit・rejectを実装する", { terms: ["approve", "edit", "reject"], anyTerms: ["承認", "拒否"], hint: "三つの選択肢それぞれで、実行する／修正する／止めるを示す。", success: "人の判断を明示的な状態として扱えています。" }),
      makeCheck("audit", "監査ログを残す", { terms: ["監査"], anyTerms: ["audit", "誰", "いつ", "ログ"], hint: "actor、timestamp、入力、判断をログへ残す。", success: "あとから判断を説明できる証跡があります。" }),
      makeCheck("mcp", "MCP Toolを公開する", { terms: ["MCP"], anyTerms: ["Tool", "権限", "入力"], hint: "Tool名・入力schema・権限・副作用をMCP契約として記載する。", success: "Toolを安全な境界として公開する視点があります。" }),
    ],
    reflectionPrompt: "人の承認を省略してはいけない副作用は、あなたのアプリでは何ですか？",
  }),
  "api-gateway": makeWorkshop({
    guide: "shipper", guideName: "ハル / APIを届けるシッパー",
    lesson: makeLesson("CLIの知能をサービスへ", "API化では、入力・出力・エラー・依存I/Oを明示し、利用者が契約を読んで再現できるようにします。", [
      { title: "OpenAPIを読む", text: "型付きQueryやIngestの契約をドキュメントとして確認する。" },
      { title: "エラーを統一", text: "入力不備を同じJSON形式とHTTPステータスで返す。" },
      { title: "I/Oを待つ", text: "外部検索やDBアクセスはasyncで扱い、イベントループを塞がない。" },
    ]),
    kind: "code", prompt: "入力は POST /query の {question: str, top_k: int}、POST /ingest の {source: str, text: str}、GET /health です。出力は query結果、ingest件数、health={status:'ok'} とし、Pydantic ValidationError=422、依存先timeout=504の統一 ErrorModel を返すFastAPI風コードを書いてください。",
    starter: "app = FastAPI()\n\nclass QueryRequest(BaseModel):\n    question: str = Field(min_length=1)\n    top_k: int = Field(ge=1, le=20)\n\nclass IngestRequest(BaseModel):\n    source: str\n    text: str = Field(min_length=1)\n\nclass ErrorModel(BaseModel):\n    code: str\n    message: str\n\n@app.get(\"/health\")\nasync def health():\n    return {\"status\": \"ok\"}\n\n@app.post(\"/query\")\nasync def query(request: QueryRequest):\n    # 出力: answer と sources。ValidationErrorは422、依存timeoutは504。\n    return await search_and_answer(request)\n\n@app.post(\"/ingest\")\nasync def ingest(request: IngestRequest):\n    return {\"ingested\": await save_document(request)}\n",
    placeholder: "型付きAPIのエンドポイント設計…", language: "python",
    checks: [
      makeCheck("openapi", "OpenAPIを確認する", { terms: ["OpenAPI"], anyTerms: ["schema", "契約", "docs"], hint: "OpenAPI schemaを生成・確認する手順を書く。", success: "API契約をドキュメントで確認できます。" }),
      makeCheck("errors", "入力エラーを統一する", { terms: [], anyTerms: ["422", "validation", "入力エラー", "エラー形式"], hint: "HTTP statusとerror code/messageを同じJSON形に揃える。", success: "利用者が扱いやすいエラー契約です。" }),
      makeCheck("async", "asyncで外部I/Oを扱う", { terms: ["async"], anyTerms: ["await", "外部I/O", "DB"], hint: "DBや検索など待ち時間のある処理をasync/awaitで表す。", success: "I/O待ちで他のリクエストを止めない設計です。" }),
    ],
    reflectionPrompt: "API利用者が最初に困る曖昧さは、入力・エラー・認証のどれですか？",
  }),
  "stream-vault": makeWorkshop({
    guide: "shipper", guideName: "ハル / 流れと記録のシッパー",
    lesson: makeLesson("長い処理を見失わない", "ストリーミングは進捗を届け、DBとBackground Jobは処理の事実を残します。どちらも再接続と再実行を考えます。", [
      { title: "進捗Event", text: "SSEなどでstarted・progress・completed・failedを配信する。" },
      { title: "状態を永続化", text: "Migrationでjob状態と結果のschemaを管理する。" },
      { title: "再接続に強く", text: "job_idやsequenceを使い、途中から進捗を取り直せるようにする。" },
    ]),
    kind: "design", prompt: "入力は POST /jobs が受ける source と query、出力は job_id と SSE の started/progress/completed/failed Event です。queued→running→completed/failed/cancelled の状態、Migrationで作るjobsテーブル、切断後のsequence再接続とtimeoutを含む設計を書いてください。",
    starter: "## Job状態\n- queued -> running -> completed\n- running -> failed / cancelled\n\n## Event（job_id, sequence, status, progress）\n- started -> progress(0..99) -> completed または failed\n\n## 永続化\n- Migration: jobs(id, query, status, result, error, updated_at)\n- reconnect: Last-Event-ID/sequence以降をSSEで再送\n- failure: timeoutはfailedと記録し、重複jobはidempotency keyで拒否\n",
    placeholder: "SSE / Migration / Job状態の設計…", language: "markdown",
    checks: [
      makeCheck("events", "進捗Eventを配信する", { terms: ["SSE"], anyTerms: ["event", "進捗", "progress"], hint: "started / progress / completed / failedなどのEventを定義する。", success: "クライアントが処理の進み具合を追えます。" }),
      makeCheck("migration", "Migrationを作る", { terms: ["Migration"], anyTerms: ["schema", "table", "DB"], hint: "job状態を保存するtableと、変更を追えるMigrationを示す。", success: "データ構造の変更を再現可能にしています。" }),
      makeCheck("job", "job状態を永続化する", { terms: ["job"], anyTerms: ["状態", "永続化", "再接続"], hint: "job_id、status、result、updated_atなどを保存する。", success: "長い処理の現在地を失わない設計です。" }),
    ],
    reflectionPrompt: "クライアントが切断して再接続したとき、どのEventや状態を返しますか？",
  }),
  "acl-boss": makeWorkshop({
    guide: "guardian", guideName: "ガク / 権限を守るガーディアン",
    lesson: makeLesson("境界をテストで証明する", "認証できたことと、対象リソースへ権限があることは別です。異常系のtimeout・retryも含めて結合テストします。", [
      { title: "所有者で絞る", text: "user_idやtenant_idを全クエリへ適用し、他人の文書を候補に出さない。" },
      { title: "再試行は有限", text: "timeoutとretryに上限・backoffを設け、重複副作用を避ける。" },
      { title: "経路をつなぐ", text: "認証→ACL→検索→回答という主要経路を実際のテストで確認する。" },
    ]),
    kind: "code", prompt: "入力は user A の token と user B が所有する document_id、外部検索の timeout 設定です。出力は他人の文書が0件/403になること、最大2回のretry後に停止すること、認証→ACL→検索→回答のintegration結果です。cross-tenant漏洩とtimeoutを失敗ケースにした結合テストを書いてください。",
    starter: "def test_user_cannot_read_other_document():\n    # 入力: user A token と user B document_id。出力: 0件または403。\n    token = login_as(\"user-a\")\n    response = query(document_id=\"doc-owned-by-b\", token=token)\n    assert response.status_code in (403, 404)\n    assert response.json()[\"documents\"] == []\n\ndef test_timeout_retry_and_integration():\n    # timeoutを最大2回retryし、認証→ACL→検索→回答をintegrationで確認する\n    result = call_with_retry(timeout=2.0, max_retries=2)\n    assert result.error is None or result.error.code == \"timeout\"\n",
    placeholder: "認証・ACL・耐障害性の結合テスト…", language: "python",
    checks: [
      makeCheck("boundary", "他ユーザー文書を遮断する", { terms: ["ACL"], anyTerms: ["user", "ユーザー", "権限", "tenant"], hint: "所有者条件を検索へ必ず加え、別ユーザーの文書が0件になるテストを書く。", success: "認証後の認可境界を検証しています。" }),
      makeCheck("retry", "timeout・retryを制御する", { terms: ["timeout", "retry"], anyTerms: ["backoff", "上限"], hint: "有限回のretry、backoff、timeout時の最終エラーを示す。", success: "障害時にも暴走しない呼び出しです。" }),
      makeCheck("integration", "主要経路を結合テストする", { terms: ["integration"], anyTerms: ["結合テスト", "認証", "検索"], hint: "認証から検索・回答までを一つのテストでつなぐ。", success: "境界を単体の想定だけでなく経路で確認できます。" }),
    ],
    reflectionPrompt: "ACLの漏れを本番ログで早く検知するには、何を記録し何を記録しませんか？",
  }),
  "threat-map": makeWorkshop({
    guide: "guardian", guideName: "ガク / 脅威を見つけるガーディアン",
    lesson: makeLesson("攻撃者の経路を先に描く", "Threat Modelは、資産・Trust Boundary・攻撃経路を明示し、Guardrailを一箇所に置かないための地図です。", [
      { title: "資産と境界", text: "秘密、文書、Tool、ユーザー入力を列挙し、信頼境界を線で分ける。" },
      { title: "二種類のInjection", text: "直接入力だけでなく、検索文書経由のindirect攻撃も試す。" },
      { title: "多層防御", text: "入力、取得、Tool実行、出力それぞれでGuardrailを置く。" },
    ]),
    kind: "design", prompt: "入力はユーザー質問、検索文書、OPENAI_API_KEY、send_email Toolです。出力は資産×境界×攻撃経路×Guardrailの表にします。direct prompt injection と文書内 indirect injection、秘密漏洩・Tool副作用を検出して遮断する多層設計を書いてください。",
    starter: "## 資産と境界\n- 資産: OPENAI_API_KEY、文書、ユーザー回答、send_email Tool\n- Trust Boundary: user input / retriever documents / model / Tool executor の間\n\n## 攻撃ケース\n- direct: ユーザーが秘密を表示させるprompt injection\n- indirect: 検索文書に埋めた命令でsend_emailを呼ばせる injection\n\n## Guardrail\n- 入力: prompt injection検知と長さ制限\n- 取得: untrusted文書を命令として扱わない\n- Tool: allowlist・schema・承認・timeout\n- 出力: 秘密のredactionとcitation確認\n",
    placeholder: "Threat Model とGuardrailの設計…", language: "markdown",
    checks: [
      makeCheck("assets", "資産と攻撃経路を列挙する", { terms: ["資産", "攻撃"], anyTerms: ["Trust Boundary", "境界", "経路"], hint: "秘密・文書・Toolなどの資産と、入力から到達する経路を書く。", success: "守る対象と攻撃経路が地図になっています。" }),
      makeCheck("injection", "direct/indirect攻撃を試す", { terms: ["direct", "indirect"], anyTerms: ["攻撃", "injection", "文書"], hint: "ユーザー入力と検索文書に埋め込まれた攻撃を別ケースにする。", success: "直接攻撃と間接攻撃を区別できています。" }),
      makeCheck("guardrail", "多層Guardrailを設計する", { terms: ["Guardrail"], anyTerms: ["多層", "入力", "出力", "Tool"], hint: "入力・取得・Tool・出力の複数地点に防御を置く。", success: "単一のフィルターに依存しない防御です。" }),
    ],
    reflectionPrompt: "文書を信頼データとして扱ってしまうと、どこで攻撃が成立しますか？",
  }),
  "observatory": makeWorkshop({
    guide: "analyst", guideName: "レン / 品質を観測するアナリスト",
    lesson: makeLesson("一回のリクエストを追跡する", "Structured Log、Trace、Metricsを相関IDでつなぐと、品質・エラー・費用の変化を同じ事実から説明できます。", [
      { title: "秘密を出さないLog", text: "JSONの固定フィールドを使い、promptやAPIキーなどの秘密をマスクする。" },
      { title: "spanで分解", text: "retrieve、rerank、generateなど処理単位にspanを置く。" },
      { title: "SLO", text: "成功率やlatencyの目標と、測定窓・エラーバジェットを決める。" },
    ]),
    kind: "code", prompt: "入力は request_id と retrieve/generate の各処理、出力は secret-free な Structured Log・span・Metrics（latency, error_rate, cost）です。APIキーとprompt本文をredactし、成功率99%・p95 latency 2秒のSLOを超えたらアラートする観測コードを書いてください。",
    starter: "def observe(request_id: str, question: str) -> dict:\n    # 入力: request_id と処理段階。出力: Structured Log/Trace/Metrics。\n    with span(\"retrieve\", request_id=request_id):\n        docs = retrieve(question)\n    with span(\"generate\", request_id=request_id):\n        answer = generate(docs)\n    log = {\"request_id\": request_id, \"status\": \"ok\", \"api_key\": \"[redacted]\", \"prompt\": \"[redacted]\"}\n    metrics.observe(latency_ms(), error_rate(), cost())\n    slo = {\"success_rate\": 0.99, \"p95_latency_ms\": 2000}\n    return {\"log\": log, \"slo\": slo, \"answer\": answer}\n",
    placeholder: "Log / Trace / Metrics / SLO の設計コード…", language: "python",
    checks: [
      makeCheck("logs", "秘密なしの構造化Logを出す", { terms: ["Log"], anyTerms: ["structured", "構造化", "mask", "秘密"], hint: "固定JSONフィールドと、秘密をマスク／除外するルールを書く。", success: "安全に集計できるLog設計です。" }),
      makeCheck("spans", "spanで失敗箇所を追う", { terms: ["span"], anyTerms: ["trace", "retrieve", "generate"], hint: "処理段階ごとのspanとrequest_idの相関を示す。", success: "一回のリクエストを段階ごとに追えます。" }),
      makeCheck("slo", "SLOを定義する", { terms: ["SLO"], anyTerms: ["latency", "成功率", "error budget"], hint: "対象指標、目標値、測定窓の3点を定義する。", success: "品質を運用目標へ落とし込めています。" }),
    ],
    reflectionPrompt: "品質低下を検知したあと、最初に見るspanと、ユーザーへ影響を判断する指標は何ですか？",
  }),
  "delivery-line": makeWorkshop({
    guide: "shipper", guideName: "ハル / 再現性を届けるシッパー",
    lesson: makeLesson("誰でも同じように動かす", "Deliveryの目的は、環境差を減らし、lint・test・evalを通った成果物だけを同じ手順で配布することです。", [
      { title: "一つの入口", text: "READMEとcomposeなど、初回起動を一つのコマンドへ寄せる。" },
      { title: "品質ゲート", text: "lint、型検査、test、evalをCIで順番に実行する。" },
      { title: "成果物を固定", text: "Docker imageをタグ付けし、同じ依存と設定で再利用する。" },
    ]),
    kind: "code", prompt: "入力は clean checkout と commit SHA、出力は同じ手順で起動できる Docker image とCIのpass/fail結果です。start→lint→type→test→eval→image build の品質ゲートを定義し、lint/test/eval失敗時やimage build失敗時は配布しない設定を書いてください。",
    starter: "# Makefile or CI config\nstart:\n\tdocker compose up --build\n\ncheck:\n\tlint && typecheck && test && eval\n\nbuild:\n\tdocker build -t llm-quest:${GIT_SHA} .\n\n# どのゲートも失敗したらimageをpushせず、成功時だけSHA tagを配布する\n",
    placeholder: "Docker / CI の再現可能な設定…", language: "yaml",
    checks: [
      makeCheck("start", "1コマンドで起動する", { terms: ["docker"], anyTerms: ["起動", "compose", "start"], hint: "READMEからdocker composeなど一つの入口で起動する流れを書く。", success: "初回利用者の入口が明確です。" }),
      makeCheck("quality", "lint・型・test・evalを通す", { terms: ["lint", "test"], anyTerms: ["型", "type", "eval"], hint: "lint、型検査、test、evalをCIの品質ゲートに並べる。", success: "品質チェックを自動化する順序があります。" }),
      makeCheck("image", "image buildを自動化する", { terms: ["image", "build"], anyTerms: ["Docker", "CI", "tag"], hint: "CIでDocker imageをbuildし、再利用できるtagを付ける。", success: "同じ成果物を再現できるDeliveryです。" }),
    ],
    reflectionPrompt: "CIで最初に落とすべき失敗は何で、それを開発者へどう伝えますか？",
  }),
  "blueprint": makeWorkshop({
    guide: "mentor", guideName: "ミナト / 設計を言葉にするメンター",
    lesson: makeLesson("作る前に、作らないものを決める", "卒業制作では、ユーザー価値・対象外・責務・代替案を先に残すと、実装の迷いと説明の曖昧さが減ります。", [
      { title: "User story", text: "誰が、何をしたくて、何ができれば成功かを一文にする。" },
      { title: "依存方向", text: "UI・API・Core・Storageの責務と依存方向を図または文章で固定する。" },
      { title: "代替案", text: "採用しなかった案とトレードオフを残し、判断を後から説明する。" },
    ]),
    kind: "design", prompt: "入力は対象ユーザー1人の user story と、100日で実装できる制約です。出力は対象外、UI/API/Core/Storageの責務・依存方向、脅威モデル、採用案と見送った代替案です。要件が曖昧、予算超過、未検証のセキュリティ境界を失敗ケースとして扱う設計書を書いてください。",
    starter: "## User story\n- AIエンジニアが社内文書を質問し、source付き回答を60秒以内に得る\n\n## 対象外\n- 多言語翻訳、無制限ファイル、完全自動の副作用Tool\n\n## 責務と依存\n- UI -> API -> Core(RAG/Agent) -> Storage/Model\n- CoreはStorage interfaceに依存し、UIはDBへ直接依存しない\n\n## 脅威と代替案\n- 境界: user input / untrusted docs / Tool executor\n- 採用: hybrid retrieval。代替: vector-only（語の一致と監査性を失うため見送り）\n- 失敗: 要件不明、予算超過、未検証の認可境界はリリースしない\n",
    placeholder: "卒業制作のArchitecture設計書…", language: "markdown",
    checks: [
      makeCheck("scope", "user storyと対象外を決める", { terms: ["user story"], anyTerms: ["対象外", "scope", "成功"], hint: "対象ユーザー、達成したいこと、今回やらないことを明記する。", success: "価値とスコープが分かれています。" }),
      makeCheck("architecture", "責務と依存方向を描く", { terms: ["責務"], anyTerms: ["依存", "Architecture", "境界"], hint: "コンポーネントの責務と、どちら向きに依存するかを書く。", success: "後から拡張できる境界を考えています。" }),
      makeCheck("alternatives", "設計の代替案を残す", { terms: ["代替"], anyTerms: ["理由", "trade-off", "比較", "採用"], hint: "採用案だけでなく、見送った案と理由を残す。", success: "設計判断を説明できる証拠があります。" }),
    ],
    reflectionPrompt: "今の設計で一番大きなリスクと、早く検証したい仮説は何ですか？",
  }),
  "integration": makeWorkshop({
    guide: "builder", guideName: "タクミ / 七つの力をつなぐビルダー",
    lesson: makeLesson("部品をつないで、経路を証明する", "統合では、RAGやAgentを足すだけでなく、認証・DB・監視まで通った一つのユーザー経路をテストします。", [
      { title: "Core RAG", text: "検索・根拠・回答の最小経路を独立したCoreとして統合する。" },
      { title: "承認付きAgent", text: "副作用のあるToolはapproveなどのHuman-in-the-Loopを通す。" },
      { title: "多面的テスト", text: "品質だけでなく、攻撃耐性と負荷でも完成条件を確認する。" },
    ]),
    kind: "design", prompt: "入力は認証済みユーザーの query request、出力は source付き回答または承認待ちイベントと trace_id です。API→認証/ACL→Core RAG→承認付きAgent→DB→監視の経路をつなぎ、品質・攻撃・負荷の失敗時レスポンスまで含む統合テスト計画を書いてください。",
    starter: "## 統合経路\nrequest -> auth/ACL -> Core RAG(search/context/answer) -> approval gate -> Agent Tool -> DB -> trace_id付きresponse\n- 根拠不足: abstain\n- 副作用Tool: approval_required event\n\n## テスト\n- quality: source付きanswerのgroundednessとcitation\n- attack: tenant越境、direct/indirect injection、承認前Tool実行\n- load: p95 latency、timeout、retry、同時100件\n- failure: 401/403/504と監視アラートを確認\n",
    placeholder: "完成品の統合経路とテスト計画…", language: "markdown",
    checks: [
      makeCheck("rag", "Core RAGを統合する", { terms: ["RAG"], anyTerms: ["retrieval", "検索", "根拠"], hint: "検索→根拠→回答のCore経路を他の層から呼び出す。", success: "RAGの中心経路を統合できています。" }),
      makeCheck("agent", "承認付きAgentを統合する", { terms: ["Agent", "承認"], anyTerms: ["approve", "Tool", "副作用"], hint: "副作用Toolの前にapproveなどの承認状態を置く。", success: "Agentと人の承認境界がつながっています。" }),
      makeCheck("tests", "品質・攻撃・負荷をテストする", { terms: ["品質", "攻撃", "負荷"], anyTerms: ["test", "評価", "統合"], hint: "正しさ・安全性・性能の3軸でテストケースを分ける。", success: "完成条件を複数のリスクから確認できます。" }),
    ],
    reflectionPrompt: "統合時に最も壊れやすい境界はどこで、どのテストが先に知らせますか？",
  }),
  "final-demo": makeWorkshop({
    guide: "mentor", guideName: "ミナト / 15分の証明を導くメンター",
    lesson: makeLesson("第三者が再現できる証拠", "最終デモは機能紹介だけではなく、README・評価結果・制約・設計理由を短い物語として伝える場です。", [
      { title: "再現の入口", text: "READMEだけでセットアップ、データ準備、Demoを再現できるようにする。" },
      { title: "数字と制約", text: "評価結果と、まだ解けていない条件を同じ画面に示す。" },
      { title: "なぜこの設計か", text: "代替案との比較を含め、判断をユーザー価値へつなげて説明する。" },
    ]),
    kind: "design", prompt: "入力は clean checkout と第三者の15分、出力はREADMEだけで再現できる実行ログ・評価結果・制約・設計判断です。setup失敗、評価の再現不能、未説明の設計変更を失敗ケースとして、分単位のデモ台本を書いてください。",
    starter: "## 15分デモ台本\n1. 0-3分 READMEのsetupとdocker compose up（失敗時はログと復旧手順）\n2. 3-8分 query→source付きanswer→承認Toolの実演（trace_idを表示）\n3. 8-11分 Hit@5/MRR、groundedness、p95 latency、costを評価結果として表示\n4. 11-13分 未対応言語・根拠不足・timeoutを制約として明示\n5. 13-15分 hybrid RRFと承認境界を選んだ理由、代替案とのtrade-offを説明\n",
    placeholder: "第三者へ渡せる最終デモ台本…", language: "markdown",
    checks: [
      makeCheck("reproduce", "READMEだけでDemoを再現する", { terms: ["README"], anyTerms: ["Demo", "再現", "起動"], hint: "初回セットアップからDemo実行までをREADMEの手順として示す。", success: "第三者が試せる入口を用意できています。" }),
      makeCheck("evidence", "評価結果と制約を示す", { terms: ["評価", "制約"], anyTerms: ["結果", "metric", "限界"], hint: "数字の結果と、まだ保証できない条件をセットで書く。", success: "できることと、できないことを正直に示せます。" }),
      makeCheck("decision", "なぜこの設計かを説明する", { terms: ["設計", "理由"], anyTerms: ["代替", "trade-off", "判断"], hint: "ユーザー価値、制約、代替案との比較から採用理由を語る。", success: "設計判断が15分の物語になっています。" }),
    ],
    reflectionPrompt: "100日を通じて、最初の自分へ一つだけ伝えるなら何を伝えますか？",
  }),
};

export function runWorkshopChecks(quest, response) {
  const text = typeof response === "string" ? response : "";
  const normalized = text.toLocaleLowerCase();

  return (quest.workshop?.checks || []).map((check) => {
    const requiredTerms = Array.isArray(check.terms) ? check.terms : [];
    const missingTerms = requiredTerms.filter((term) => !normalized.includes(String(term).toLocaleLowerCase()));
    const alternatives = Array.isArray(check.anyTerms) ? check.anyTerms : [];
    const alternativePassed = alternatives.length === 0
      || alternatives.some((term) => normalized.includes(String(term).toLocaleLowerCase()));
    const lengthPassed = text.trim().length >= (check.minLength || 0);
    const passed = lengthPassed && missingTerms.length === 0 && alternativePassed;
    const missing = [
      ...missingTerms,
      ...(alternativePassed || alternatives.length === 0 ? [] : [`${alternatives.join(" / ")} のいずれか`]),
    ];
    const message = passed
      ? check.success
      : `${missing.length ? `不足: ${missing.join("、")}` : "内容をもう少し具体化"}。回答を更新して、必要なら下のヒントを一段ずつ確認してください。`;

    return {
      id: check.id,
      label: check.label,
      passed,
      message,
      hint: check.hint,
    };
  });
}

export const allQuests = phases.flatMap((phase) =>
  phase.quests.map((quest, questIndex) => ({
    ...quest,
    phaseId: phase.id,
    phaseOrder: phase.order,
    companionIds: phase.characterIds,
    rewardId: quest.rewardId || phase.gearIds[questIndex % Math.max(phase.gearIds.length, 1)],
    workshop: workshops[quest.id],
  })),
);
