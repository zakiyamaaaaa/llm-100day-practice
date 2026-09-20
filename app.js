import {
  allQuests,
  characterRoster,
  gearCatalog,
  phases,
  runWorkshopChecks,
} from "./src/game-data.js";
import {
  completeQuest,
  getQuestState,
  getHintLevel,
  getStats,
  hasCompletedChecks,
  isPhaseUnlocked,
  loadProgress,
  recordWorkshopRun,
  reopenQuest,
  resetProgress,
  revealHint,
  saveProgress,
  setActiveQuest,
  updateQuestState,
} from "./src/progress.js";

const validQuestIds = allQuests.map((quest) => quest.id);
let progress = loadProgress(localStorage, validQuestIds);
let selectedQuestId = progress.activeQuestId || getNextQuest()?.id || allQuests[0].id;
let workshopQuestId = null;
let workshopReturnFocus = null;

const map = document.querySelector("#quest-map");
const detail = document.querySelector("#quest-detail");
const statsRoot = document.querySelector("#player-stats");
const rosterRoot = document.querySelector("#character-roster");
const resetButton = document.querySelector("#reset-progress");
const resumeButton = document.querySelector("#resume-quest");
const workshopRoot = document.querySelector("#workshop");
const workshopContent = document.querySelector("#workshop-content");

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function getNextQuest() {
  return allQuests.find((quest) => !progress.completedQuestIds.includes(quest.id));
}

function phaseForQuest(questId) {
  return phases.find((phase) => phase.quests.some((quest) => quest.id === questId));
}

function characterFor(characterId) {
  return characterRoster.find((character) => character.id === characterId);
}

function gearFor(gearId) {
  return gearCatalog.find((gear) => gear.id === gearId);
}

function assetMarkup(item, kind, label = "") {
  if (!item) return "";
  const isCharacter = kind === "character";
  const fallback = isCharacter ? item.initials : "◇";
  return `
    <span class="${kind}-asset" style="--asset-color: ${escapeHtml(item.color || "var(--lime)")}" data-asset-frame>
      <img data-asset-image src="${escapeHtml(item.image)}" alt="${escapeHtml(label || item.name)}" />
      <span data-asset-fallback aria-hidden="true">${escapeHtml(fallback)}</span>
    </span>
  `;
}

function bindAssetFallbacks(root) {
  root?.querySelectorAll("[data-asset-image]").forEach((image) => {
    const fallback = image.parentElement?.querySelector("[data-asset-fallback]");
    if (!fallback) return;
    const showFallback = () => {
      image.hidden = true;
      fallback.hidden = false;
    };
    const hideFallback = () => {
      image.hidden = false;
      fallback.hidden = true;
    };
    image.addEventListener("error", showFallback, { once: true });
    image.addEventListener("load", hideFallback, { once: true });
    fallback.hidden = true;
    if (image.complete && image.naturalWidth === 0) showFallback();
  });
}

function renderRoster() {
  if (!rosterRoot) return;
  rosterRoot.innerHTML = `
    <section class="roster-section" aria-labelledby="character-roster-title">
      <div class="roster-heading">
        <span class="overline">PARTY / 12 OPERATORS</span>
        <h2 id="character-roster-title">旅の仲間</h2>
        <p>フェーズごとに専門家が合流します。</p>
      </div>
      <div class="roster-grid">
        ${characterRoster.map((character) => `
          <article class="character-card" title="${escapeHtml(character.role)}">
            ${assetMarkup(character, "character", `${character.name}のキャラクター画像`)}
            <strong>${escapeHtml(character.name)}</strong>
            <small>${escapeHtml(character.role)}</small>
          </article>
        `).join("")}
      </div>
    </section>
  `;
  bindAssetFallbacks(rosterRoot);
}

function commit(nextProgress, { renderUi = true } = {}) {
  progress = nextProgress;
  saveProgress(localStorage, progress);
  if (renderUi) render();
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
    <div class="progress-track" role="progressbar" aria-label="総合進捗" aria-valuenow="${stats.percent}" aria-valuemin="0" aria-valuemax="100">
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
    const phaseCharacters = (phase.characterIds || []).map(characterFor).filter(Boolean);
    const phaseGear = (phase.gearIds || []).map(gearFor).filter(Boolean);

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
          <div class="phase-loadout" aria-label="${escapeHtml(phase.eyebrow)}の仲間と報酬">
            <div class="phase-party">
              <span class="loadout-label">PARTY</span>
              <div class="phase-party-list">
                ${phaseCharacters.map((character) => `
                  <span class="phase-party-member" title="${escapeHtml(character.name)} — ${escapeHtml(character.role)}">
                    ${assetMarkup(character, "character", `${character.name}の画像`)}
                    <span>${escapeHtml(character.name)}</span>
                  </span>
                `).join("")}
              </div>
            </div>
            <div class="phase-rewards">
              <span class="loadout-label">REWARDS</span>
              <div class="phase-reward-list">
                ${phaseGear.map((gear) => `
                  <span class="phase-reward" title="${escapeHtml(gear.label)}">
                    ${assetMarkup(gear, "gear", `${gear.label}の報酬画像`)}
                    <span>${escapeHtml(gear.label)}</span>
                  </span>
                `).join("")}
              </div>
            </div>
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

  bindAssetFallbacks(map);

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
  const quest = allQuests.find((item) => item.id === selectedQuestId) || allQuests[0];
  const phase = phaseForQuest(quest.id);
  const complete = progress.completedQuestIds.includes(quest.id);
  const active = progress.activeQuestId === quest.id;
  const state = getQuestState(progress, quest.id);
  const passedCount = quest.workshop.checks.filter((check) => state.checkResults?.[check.id]?.passed).length;

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
      <span class="overline">ワークショップのクリア条件</span>
      <ol>
        ${quest.objectives.map((objective, index) => `
          <li class="${state.checkResults?.[quest.workshop.checks[index].id]?.passed ? "objective--passed" : ""}">
            <span>${state.checkResults?.[quest.workshop.checks[index].id]?.passed ? "✓" : "○"}</span>${objective}
          </li>
        `).join("")}
      </ol>
      <small class="detail-check-count">${passedCount} / ${quest.workshop.checks.length} 条件を検証済み</small>
    </div>
    <div class="source-note">
      <span>教材ソース</span>
      <strong>${quest.source}</strong>
    </div>
    <div class="detail-actions">
      <button class="primary-button" id="start-workshop">${complete ? "ワークショップを再訪" : "ワークショップを開始"}</button>
      ${complete ? `<button class="secondary-button" id="reopen-quest">完了を取り消す</button>` : active ? `<span class="active-note">● ワークショップ進行中 · 自動保存</span>` : ""}
    </div>
    <p class="save-note"><span aria-hidden="true">●</span> 回答とふり返りはクエストごとにこのブラウザへ保存されます</p>
  `;

  detail.querySelector("#start-workshop").addEventListener("click", () => openWorkshop(quest.id));
  detail.querySelector("#reopen-quest")?.addEventListener("click", () => {
    commit(reopenQuest(progress, quest.id));
  });
}

function workshopResultFor(state, check) {
  return state.checkResults?.[check.id] || {
    passed: false,
    message: "まだ検証していません。回答を書いて実行してください。",
  };
}

function buildModelAnswer(challenge, checks) {
  if (challenge.solution) return challenge.solution;
  const prefix = challenge.kind === "code" ? "#" : "-";
  const reviewPoints = checks.map((check) => {
    const hints = Array.isArray(check.hints) ? check.hints : check.hint ? [check.hint] : [];
    const keywords = [...(check.terms || []), ...(check.anyTerms?.slice(0, 1) || [])];
    return `${prefix} ${check.label}: ${hints.at(-1) || check.success}${keywords.length ? ` [確認語: ${keywords.join(" / ")}]` : ""}`;
  });
  return `${challenge.starter.trim()}\n\n${prefix} --- 解答例の確認ポイント ---\n${reviewPoints.join("\n")}\n`;
}

function renderWorkshop() {
  if (!workshopQuestId) return;
  const quest = allQuests.find((item) => item.id === workshopQuestId);
  if (!quest?.workshop) return;
  const phase = phaseForQuest(quest.id);
  const state = getQuestState(progress, quest.id);
  const complete = progress.completedQuestIds.includes(quest.id);
  const checks = quest.workshop.checks;
  const passedCount = checks.filter((check) => workshopResultFor(state, check).passed).length;
  const checksPassed = hasCompletedChecks(progress, quest.id, checks.map((check) => check.id));
  const hasRun = Boolean(state.lastRunAt);
  const challenge = quest.workshop.challenge;
  const draft = state.draft === null ? challenge.starter : state.draft;
  const modelAnswer = buildModelAnswer(challenge, checks);
  const guideCharacter = characterFor(quest.workshop.guideCharacterId);
  const phaseCharacters = (phase.characterIds || []).map(characterFor).filter(Boolean);
  const workshopCharacters = [guideCharacter, ...phaseCharacters]
    .filter(Boolean)
    .filter((character, index, list) => list.findIndex((item) => item.id === character.id) === index)
    .slice(0, 4);
  const reward = gearFor(quest.rewardId) || gearFor(phase.gearIds?.[0]);

  workshopRoot.style.setProperty("--workshop-color", phase.color);
  workshopContent.innerHTML = `
    <header class="workshop-header">
      <div>
        <span class="workshop-kicker">${phase.eyebrow} · ${quest.type}クエスト</span>
        <h2 id="workshop-title">${quest.title}</h2>
        <p id="workshop-description">ここで学び、書き、検証してからクエストを完了します。</p>
      </div>
      <button class="workshop-close" type="button" data-workshop-close aria-label="ワークショップを閉じる">×</button>
    </header>

    <div class="workshop-guide">
      <div class="guide-portrait">
        <img data-guide-image src="${quest.workshop.guideImage}" alt="${quest.workshop.guideName}のガイド画像" />
        <span data-guide-fallback aria-hidden="true">✦</span>
      </div>
      <div>
        <span class="overline">GUIDE SIGNAL</span>
        <strong>${quest.workshop.guideName}</strong>
        <p>まず理論を読み、あなたの言葉とコードで一つの答えを作ってみよう。</p>
      </div>
      <span class="workshop-status ${complete ? "workshop-status--complete" : checksPassed ? "workshop-status--ready" : ""}">${complete ? "完了済み" : checksPassed ? "検証クリア" : `${passedCount} / ${checks.length} 条件`}</span>
    </div>

    <div class="workshop-loadout" aria-label="今回の仲間と報酬">
      <div class="workshop-companions">
        <span class="loadout-label">ACTIVE CREW</span>
        <div class="workshop-companion-list">
          ${workshopCharacters.map((character) => `
            <span class="workshop-companion" title="${escapeHtml(character.name)} — ${escapeHtml(character.role)}">
              ${assetMarkup(character, "character", `${character.name}の画像`)}
              <span>${escapeHtml(character.name)}</span>
            </span>
          `).join("")}
        </div>
      </div>
      ${reward ? `
        <div class="workshop-reward">
          <span class="loadout-label">QUEST REWARD</span>
          <div class="workshop-reward-item">
            ${assetMarkup(reward, "gear", `${reward.label}の報酬画像`)}
            <div><strong>${escapeHtml(reward.label)}</strong><small>${escapeHtml(reward.rarity)} · ${escapeHtml(reward.name)}</small></div>
          </div>
        </div>
      ` : ""}
    </div>

    <div class="workshop-steps" aria-label="学習ステップ">
      <span class="workshop-step workshop-step--done"><b>01</b> 学ぶ</span>
      <span class="workshop-step ${state.draft !== null ? "workshop-step--done" : ""}"><b>02</b> 実装する</span>
      <span class="workshop-step ${hasRun ? "workshop-step--done" : ""}"><b>03</b> 検証する</span>
      <span class="workshop-step ${complete ? "workshop-step--done" : ""}"><b>04</b> ふり返る</span>
    </div>

    <div class="workshop-grid">
      <article class="lesson-card">
        <span class="overline">01 / LESSON</span>
        <h3>${quest.workshop.lesson.title}</h3>
        <p>${quest.workshop.lesson.intro}</p>
        <div class="lesson-points">
          ${quest.workshop.lesson.points.map((point, index) => `
            <div class="lesson-point"><span>${String(index + 1).padStart(2, "0")}</span><div><strong>${point.title}</strong><p>${point.text}</p></div></div>
          `).join("")}
        </div>
      </article>

      <article class="challenge-card">
        <div class="challenge-heading">
          <div><span class="overline">02 / IMPLEMENT</span><h3>${challenge.kind === "design" ? "設計レスポンス" : "実装ラボ"}</h3></div>
          <span class="editor-language">${challenge.language}</span>
        </div>
        <p class="challenge-prompt">${challenge.prompt}</p>
        <div class="editor-toolbar"><span>EDITABLE WORKSPACE</span><button class="text-button" type="button" id="reset-draft">スターターに戻す</button></div>
        <textarea id="workshop-response" class="workshop-editor" rows="12" spellcheck="${challenge.kind === "design" ? "true" : "false"}" aria-label="${quest.title}の回答" placeholder="${challenge.placeholder}"></textarea>
        <div class="editor-footer"><span class="autosave-status" id="autosave-status">${state.draft !== null ? "自動保存済み" : "スターターから開始"}</span><span>ブラウザ内で保存</span></div>
        <button class="primary-button workshop-run" type="button" id="workshop-run"><span>▶</span> 回答を実行して検証</button>
        <aside class="solution-rescue" aria-labelledby="solution-heading">
          <div>
            <span class="overline">STUCK?</span>
            <strong id="solution-heading">どうしても分からない場合</strong>
            <p>ヒントでも進めないときは解答例と自分の回答を比較できます。</p>
          </div>
          <button class="secondary-button solution-toggle" type="button" id="show-solution" aria-expanded="false" aria-controls="solution-example">解答例を見る</button>
          <div class="solution-example" id="solution-example" hidden>
            <pre><code>${escapeHtml(modelAnswer)}</code></pre>
            <p>解答例を読んで理由を確認してから、自分の言葉で直すのがおすすめです。</p>
            <button class="secondary-button" type="button" id="apply-solution">エディタへ反映（現在の回答を置換）</button>
          </div>
        </aside>
      </article>

    <section class="check-card" aria-labelledby="check-heading">
      <div class="check-heading"><div><span class="overline">03 / VERIFY</span><h3 id="check-heading">クリア条件チェックリスト</h3></div><span class="check-count">${passedCount} / ${checks.length} PASS</span></div>
      <p class="check-intro">チェックは回答の中身を読み取るシミュレーションです。外部APIは使わず、足りない観点を具体的に返します。</p>
      <ol class="workshop-checklist">
        ${checks.map((check, index) => {
          const result = workshopResultFor(state, check);
          const hints = Array.isArray(check.hints) ? check.hints : check.hint ? [check.hint] : [];
          const revealedCount = Math.min(getHintLevel(progress, quest.id, check.id), hints.length);
          const visibleHints = hints.slice(0, revealedCount);
          return `
            <li class="workshop-check ${result.passed ? "workshop-check--passed" : hasRun ? "workshop-check--failed" : ""}">
              <span class="check-icon" aria-hidden="true">${result.passed ? "✓" : hasRun ? "!" : String(index + 1).padStart(2, "0")}</span>
              <div>
                <strong>${escapeHtml(check.label)}</strong>
                <p>${escapeHtml(result.message)}</p>
                ${hints.length ? `
                  <button class="hint-button" type="button" data-reveal-hint data-check-id="${escapeHtml(check.id)}" aria-expanded="${revealedCount > 0}" aria-controls="hints-${escapeHtml(check.id)}" ${revealedCount >= hints.length ? "disabled" : ""}>
                    ${revealedCount >= hints.length ? "ヒントを確認済み" : `ヒントを見る（${revealedCount}/${hints.length}）`}
                  </button>
                  <div class="check-hints ${revealedCount ? "" : "check-hints--hidden"}" id="hints-${escapeHtml(check.id)}" data-hints-for="${escapeHtml(check.id)}" role="region" aria-label="${escapeHtml(check.label)}のヒント" aria-live="polite">
                    ${visibleHints.map((hint, hintIndex) => `<p class="check-hint"><span>${hintIndex + 1}</span>${escapeHtml(hint)}</p>`).join("")}
                  </div>
                ` : ""}
              </div>
            </li>
          `;
        }).join("")}
      </ol>
      <div class="workshop-output ${hasRun ? "workshop-output--visible" : ""}" id="workshop-output" tabindex="-1" aria-live="polite">
        ${hasRun ? `<strong>${checksPassed ? "すべての検証を通過しました" : "もう一歩です。回答を更新して再検証しましょう"}</strong><span>${passedCount} / ${checks.length} の条件が通過</span>` : "実行結果はここに表示されます。"}
      </div>
    </section>
    </div>

    <section class="reflection-card" aria-labelledby="reflection-heading">
      <div><span class="overline">04 / REFLECT</span><h3 id="reflection-heading">学習ノートとふり返り</h3><p>${quest.workshop.reflectionPrompt}</p></div>
      <textarea id="workshop-notes" rows="4" placeholder="仮説・失敗・次の一手を自由に記録…" aria-label="${quest.title}の学習ノート"></textarea>
      <div class="reflection-footer"><span>次に開いたときも、このクエストから続けられます。</span><span class="notes-save-status">自動保存</span></div>
    </section>

    <footer class="workshop-footer">
      <button class="secondary-button" type="button" data-workshop-close>ロードマップへ戻る</button>
      <div><span class="completion-hint">${complete ? "完了済み。必要なら回答をさらに磨けます。" : checksPassed ? "全チェックを通過しました。完了できます。" : "すべての検証を通過すると完了できます。"}</span><button class="primary-button" type="button" id="complete-workshop" ${complete ? "" : checksPassed ? "" : "disabled"}>${complete ? "完了を取り消す" : "クエストを完了"}</button></div>
    </footer>
  `;

  const editor = workshopContent.querySelector("#workshop-response");
  const notes = workshopContent.querySelector("#workshop-notes");
  editor.value = draft;
  notes.value = state.notes;

  const saveField = (field, value, statusSelector) => {
    progress = updateQuestState(progress, quest.id, { [field]: value });
    saveProgress(localStorage, progress);
    const status = workshopContent.querySelector(statusSelector);
    if (status) status.textContent = "自動保存済み";
  };
  editor.addEventListener("input", () => saveField("draft", editor.value, "#autosave-status"));
  notes.addEventListener("input", () => saveField("notes", notes.value, ".notes-save-status"));

  workshopContent.querySelector("#reset-draft").addEventListener("click", () => {
    commit(updateQuestState(progress, quest.id, {
      draft: null,
      checkResults: {},
      lastRunAt: null,
      feedback: "",
    }));
  });

  workshopContent.querySelector("#workshop-run").addEventListener("click", () => {
    const results = runWorkshopChecks(quest, editor.value);
    const passed = results.filter((result) => result.passed).length;
    commit(recordWorkshopRun(progress, quest.id, results, {
      draft: editor.value,
      feedback: `${passed} / ${results.length} checks passed`,
    }));
    workshopContent.querySelector("#workshop-output")?.focus();
  });

  const solutionToggle = workshopContent.querySelector("#show-solution");
  const solutionExample = workshopContent.querySelector("#solution-example");
  solutionToggle.addEventListener("click", () => {
    const willOpen = solutionExample.hidden;
    solutionExample.hidden = !willOpen;
    solutionToggle.setAttribute("aria-expanded", String(willOpen));
    solutionToggle.textContent = willOpen ? "解答例を閉じる" : "解答例を見る";
  });
  workshopContent.querySelector("#apply-solution").addEventListener("click", () => {
    editor.value = modelAnswer;
    saveField("draft", modelAnswer, "#autosave-status");
    editor.focus();
  });

  workshopContent.querySelector("#complete-workshop").addEventListener("click", () => {
    if (complete) {
      commit(reopenQuest(progress, quest.id));
      return;
    }
    if (!hasCompletedChecks(progress, quest.id, checks.map((check) => check.id))) {
      workshopContent.querySelector("#workshop-output")?.focus();
      return;
    }
    commit(completeQuest(progress, quest.id, checks.map((check) => check.id)));
  });

  workshopContent.querySelectorAll("[data-reveal-hint]").forEach((button) => {
    button.addEventListener("click", () => {
      const check = checks.find((item) => item.id === button.dataset.checkId);
      const hintCount = check?.hints?.length || (check?.hint ? 1 : 0);
      if (!check || !hintCount) return;
      commit(revealHint(progress, quest.id, check.id, hintCount), { renderUi: false });
      renderWorkshop();
      requestAnimationFrame(() => {
        [...workshopContent.querySelectorAll("[data-reveal-hint]")]
          .find((item) => item.dataset.checkId === check.id)
          ?.focus();
      });
    });
  });

  const guideImage = workshopContent.querySelector("[data-guide-image]");
  const guideFallback = workshopContent.querySelector("[data-guide-fallback]");
  guideImage.addEventListener("error", () => {
    guideImage.hidden = true;
    guideFallback.hidden = false;
  }, { once: true });
  guideFallback.hidden = true;
  bindAssetFallbacks(workshopContent);
}

function openWorkshop(questId) {
  const quest = allQuests.find((item) => item.id === questId);
  if (!quest?.workshop) return;
  selectedQuestId = questId;
  workshopQuestId = questId;
  workshopReturnFocus = document.activeElement;
  if (!progress.completedQuestIds.includes(questId)) {
    progress = setActiveQuest(progress, questId);
    saveProgress(localStorage, progress);
  }
  workshopRoot.hidden = false;
  document.body.classList.add("workshop-open");
  render();
  requestAnimationFrame(() => workshopContent.querySelector(".workshop-close")?.focus());
}

function closeWorkshop() {
  workshopRoot.hidden = true;
  document.body.classList.remove("workshop-open");
  workshopQuestId = null;
  const returnTarget = workshopReturnFocus;
  workshopReturnFocus = null;
  if (returnTarget && document.contains(returnTarget)) {
    returnTarget.focus();
  } else {
    // Rendering the roadmap while the dialog is open replaces the original
    // trigger node. Return focus to the freshly-rendered quest action instead.
    document.querySelector("#quest-detail #start-workshop")?.focus();
  }
}

function render() {
  renderStats();
  renderRoster();
  renderMap();
  renderDetail();
  if (workshopQuestId) renderWorkshop();
}

workshopRoot.addEventListener("click", (event) => {
  if (event.target.closest("[data-workshop-close]")) closeWorkshop();
});

workshopRoot.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    event.preventDefault();
    closeWorkshop();
    return;
  }
  if (event.key !== "Tab") return;
  const focusable = [...workshopRoot.querySelectorAll("button:not([disabled]), textarea, input, [href]")]
    .filter((element) => !element.hidden);
  if (!focusable.length) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
});

resumeButton.addEventListener("click", () => {
  const target = progress.activeQuestId || getNextQuest()?.id;
  if (!target) return;
  openWorkshop(target);
});

resetButton.addEventListener("click", () => {
  if (!window.confirm("すべてのクエスト進捗をリセットしますか？")) return;
  if (workshopQuestId) closeWorkshop();
  progress = resetProgress(validQuestIds);
  selectedQuestId = allQuests[0].id;
  saveProgress(localStorage, progress);
  render();
});

render();
