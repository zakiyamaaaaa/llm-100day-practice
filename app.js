import { allQuests, phases } from "./src/game-data.js";
import {
  getStats,
  isPhaseUnlocked,
  loadProgress,
  resetProgress,
  saveProgress,
  setActiveQuest,
  toggleQuest,
} from "./src/progress.js";

const validQuestIds = allQuests.map((quest) => quest.id);
let progress = loadProgress(localStorage, validQuestIds);
let selectedQuestId = progress.activeQuestId || getNextQuest()?.id || allQuests[0].id;

const map = document.querySelector("#quest-map");
const detail = document.querySelector("#quest-detail");
const statsRoot = document.querySelector("#player-stats");
const resetButton = document.querySelector("#reset-progress");
const resumeButton = document.querySelector("#resume-quest");

function getNextQuest() {
  return allQuests.find((quest) => !progress.completedQuestIds.includes(quest.id));
}

function phaseForQuest(questId) {
  return phases.find((phase) => phase.quests.some((quest) => quest.id === questId));
}

function persist(nextProgress) {
  progress = nextProgress;
  saveProgress(localStorage, progress);
  render();
}

function renderStats() {
  const stats = getStats(progress, allQuests);
  statsRoot.innerHTML = `
    <div class="rank-row">
      <div class="avatar" aria-hidden="true">AI</div>
      <div>
        <span class="overline">冒険者ランク</span>
        <strong>${stats.percent === 100 ? "LLM アーキテクト" : stats.percent >= 67 ? "実践エンジニア" : stats.percent >= 34 ? "RAG クラフター" : "学びの探索者"}</strong>
      </div>
    </div>
    <div class="xp-label"><span>総合進捗</span><strong>${stats.percent}%</strong></div>
    <div class="progress-track" role="progressbar" aria-valuenow="${stats.percent}" aria-valuemin="0" aria-valuemax="100">
      <span style="width: ${stats.percent}%"></span>
    </div>
    <div class="stat-grid">
      <div><strong>${stats.completedCount}</strong><span>完了</span></div>
      <div><strong>${stats.totalCount - stats.completedCount}</strong><span>残り</span></div>
      <div><strong>${stats.earnedXp.toLocaleString()}</strong><span>獲得XP</span></div>
    </div>
  `;

  const next = getNextQuest();
  resumeButton.textContent = progress.activeQuestId ? "進行中クエストへ" : "次のクエストへ";
  resumeButton.disabled = !next && !progress.activeQuestId;
}

function renderMap() {
  map.innerHTML = phases.map((phase, phaseIndex) => {
    const unlocked = isPhaseUnlocked(phaseIndex, phases, progress);
    const completedCount = phase.quests.filter((quest) =>
      progress.completedQuestIds.includes(quest.id),
    ).length;
    const isComplete = completedCount === phase.quests.length;
    const status = isComplete ? "踏破済み" : unlocked ? `${completedCount} / ${phase.quests.length} 完了` : "前フェーズを踏破で解放";

    return `
      <section class="phase ${unlocked ? "" : "phase--locked"}" style="--phase-color: ${phase.color}" aria-labelledby="phase-${phase.id}">
        <div class="phase-rail" aria-hidden="true">
          <div class="phase-node">${unlocked ? phase.icon : "⌁"}</div>
        </div>
        <div class="phase-content">
          <header class="phase-header">
            <div>
              <span class="phase-kicker">PHASE ${String(phase.order).padStart(2, "0")} · ${phase.days}</span>
              <h2 id="phase-${phase.id}">${phase.eyebrow}<small>${phase.title}</small></h2>
            </div>
            <span class="phase-status ${isComplete ? "phase-status--complete" : ""}">${status}</span>
          </header>
          <p class="phase-summary">${phase.summary}</p>
          <div class="skill-row" aria-label="獲得スキル">
            ${phase.skills.map((skill) => `<span>${skill}</span>`).join("")}
          </div>
          <div class="quest-grid">
            ${phase.quests.map((quest, index) => {
              const complete = progress.completedQuestIds.includes(quest.id);
              const active = progress.activeQuestId === quest.id;
              const selected = selectedQuestId === quest.id;
              return `
                <button class="quest-card ${complete ? "quest-card--complete" : ""} ${active ? "quest-card--active" : ""} ${selected ? "quest-card--selected" : ""}"
                  data-quest="${quest.id}" ${unlocked ? "" : "disabled"} aria-label="${quest.title}の詳細を見る">
                  <span class="quest-number">${complete ? "✓" : String(index + 1).padStart(2, "0")}</span>
                  <span class="quest-copy">
                    <span class="quest-meta">${quest.type} · ${quest.duration}分</span>
                    <strong>${quest.title}</strong>
                    <span>${quest.description}</span>
                  </span>
                  <span class="quest-xp">+${quest.xp} XP</span>
                </button>
              `;
            }).join("")}
          </div>
        </div>
      </section>
    `;
  }).join("");

  map.querySelectorAll("[data-quest]").forEach((button) => {
    button.addEventListener("click", () => {
      selectedQuestId = button.dataset.quest;
      renderDetail();
      map.querySelectorAll(".quest-card").forEach((card) =>
        card.classList.toggle("quest-card--selected", card.dataset.quest === selectedQuestId),
      );
      if (window.innerWidth < 980) detail.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
}

function renderDetail() {
  const quest = allQuests.find((item) => item.id === selectedQuestId);
  const phase = phaseForQuest(selectedQuestId);
  const complete = progress.completedQuestIds.includes(quest.id);
  const active = progress.activeQuestId === quest.id;

  detail.style.setProperty("--detail-color", phase.color);
  detail.innerHTML = `
    <div class="detail-topline">
      <span>${phase.eyebrow}</span>
      <span class="detail-xp">報酬 ${quest.xp} XP</span>
    </div>
    <span class="detail-type">${quest.type}クエスト · 約${quest.duration}分</span>
    <h2>${quest.title}</h2>
    <p class="detail-description">${quest.description}</p>
    <div class="objective-box">
      <span class="overline">クリア条件</span>
      <ol>
        ${quest.objectives.map((objective) => `<li><span>✓</span>${objective}</li>`).join("")}
      </ol>
    </div>
    <div class="source-note">
      <span>教材ソース</span>
      <strong>${quest.source}</strong>
    </div>
    <div class="detail-actions">
      <button class="primary-button" id="toggle-complete">${complete ? "未完了に戻す" : "クエスト完了"}</button>
      ${complete ? "" : `<button class="secondary-button" id="set-active">${active ? "進行中です" : "このクエストを開始"}</button>`}
    </div>
    <p class="save-note"><span aria-hidden="true">●</span> 進捗はこのブラウザへ自動保存されます</p>
  `;

  detail.querySelector("#toggle-complete").addEventListener("click", () => {
    persist(toggleQuest(progress, quest.id));
    selectedQuestId = getNextQuest()?.id || quest.id;
    render();
  });

  const activeButton = detail.querySelector("#set-active");
  activeButton?.addEventListener("click", () => persist(setActiveQuest(progress, quest.id)));
}

function render() {
  renderStats();
  renderMap();
  renderDetail();
}

resumeButton.addEventListener("click", () => {
  const target = progress.activeQuestId || getNextQuest()?.id;
  if (!target) return;
  selectedQuestId = target;
  render();
  document.querySelector(`[data-quest="${target}"]`)?.scrollIntoView({ behavior: "smooth", block: "center" });
});

resetButton.addEventListener("click", () => {
  if (!window.confirm("すべてのクエスト進捗をリセットしますか？")) return;
  progress = resetProgress();
  selectedQuestId = allQuests[0].id;
  saveProgress(localStorage, progress);
  render();
});

render();
