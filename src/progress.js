export const STORAGE_KEY = "llm-roadmap-quest:v1";

export function createQuestState(completed = false) {
  return {
    // null means that the starter has not been edited yet.  It lets the
    // workshop distinguish a fresh quest from a deliberately empty answer.
    draft: null,
    notes: "",
    checkResults: {},
    // Number of hint levels revealed for each check.  It is intentionally
    // stored per quest so revisiting a workshop keeps the learner's pace.
    revealedHints: {},
    lastRunAt: null,
    feedback: "",
    completed,
  };
}

function uniqueStrings(values) {
  return [...new Set(values.filter((value) => typeof value === "string"))];
}

function normalizeCheckResults(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return {};

  return Object.fromEntries(
    Object.entries(value)
      .filter(([id, result]) => typeof id === "string" && result && typeof result === "object")
      .map(([id, result]) => [id, {
        passed: result.passed === true,
        message: typeof result.message === "string" ? result.message : "",
        checkedAt: typeof result.checkedAt === "string" ? result.checkedAt : null,
      }]),
  );
}

function normalizeRevealedHints(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return {};

  return Object.fromEntries(
    Object.entries(value)
      .filter(([id, level]) => typeof id === "string" && Number.isFinite(level))
      .map(([id, level]) => [id, Math.max(0, Math.floor(level))]),
  );
}

export function normalizeQuestState(value, completed = false) {
  const source = value && typeof value === "object" && !Array.isArray(value) ? value : {};
  return {
    draft: typeof source.draft === "string" ? source.draft : null,
    notes: typeof source.notes === "string" ? source.notes : "",
    checkResults: normalizeCheckResults(source.checkResults),
    // `hintLevels` was never part of the public format, but accepting it here
    // makes the additive migration tolerant of an early preview build.
    revealedHints: normalizeRevealedHints(source.revealedHints || source.hintLevels),
    lastRunAt: typeof source.lastRunAt === "string" ? source.lastRunAt : null,
    feedback: typeof source.feedback === "string" ? source.feedback : "",
    // Completion is always derived from the canonical completedQuestIds list;
    // a stale per-quest flag must never resurrect a quest after it is reopened.
    completed: completed === true,
  };
}

export function createInitialProgress(completedQuestIds = [], validQuestIds = []) {
  const completed = uniqueStrings(completedQuestIds);
  const questIds = uniqueStrings([...validQuestIds, ...completed]);
  return {
    completedQuestIds: completed,
    activeQuestId: null,
    questStates: Object.fromEntries(
      questIds.map((questId) => [questId, createQuestState(completed.includes(questId))]),
    ),
    updatedAt: null,
  };
}

export function normalizeProgress(value, validQuestIds) {
  const valid = new Set(validQuestIds);
  // Keep the original empty-save shape for a brand-new or malformed value;
  // questStates are created lazily when a learner opens a workshop.  Existing
  // saves with the old fields still migrate into per-quest records below.
  if (!value || typeof value !== "object") return createInitialProgress();

  const completedQuestIds = Array.isArray(value.completedQuestIds)
    ? [...new Set(value.completedQuestIds.filter((id) => valid.has(id)))]
    : [];
  const activeQuestId = valid.has(value.activeQuestId) ? value.activeQuestId : null;
  // `questStates` is additive so saves from the original roadmap (which only
  // had completedQuestIds/activeQuestId) migrate without losing progress.
  const sourceStates = value.questStates && typeof value.questStates === "object"
    ? value.questStates
    : {};
  const questStates = Object.fromEntries(
    validQuestIds.map((questId) => [
      questId,
      normalizeQuestState(sourceStates[questId], completedQuestIds.includes(questId)),
    ]),
  );

  return {
    completedQuestIds,
    activeQuestId,
    questStates,
    updatedAt: typeof value.updatedAt === "string" ? value.updatedAt : null,
  };
}

export function getQuestState(progress, questId) {
  return normalizeQuestState(
    progress?.questStates?.[questId],
    progress?.completedQuestIds?.includes(questId) === true,
  );
}

export function getHintLevel(progress, questId, checkId) {
  const level = getQuestState(progress, questId).revealedHints?.[checkId];
  return Number.isFinite(level) ? Math.max(0, Math.floor(level)) : 0;
}

export function revealHint(progress, questId, checkId, hintCount = Number.POSITIVE_INFINITY) {
  if (typeof checkId !== "string" || !checkId) return progress;
  const current = getHintLevel(progress, questId, checkId);
  const maximum = Number.isFinite(hintCount)
    ? Math.max(0, Math.floor(hintCount))
    : Number.POSITIVE_INFINITY;
  if (current >= maximum) return progress;

  const state = getQuestState(progress, questId);
  return updateQuestState(progress, questId, {
    revealedHints: {
      ...(state.revealedHints || {}),
      [checkId]: Math.min(current + 1, maximum),
    },
  });
}

export function updateQuestState(progress, questId, patch = {}) {
  const current = getQuestState(progress, questId);
  const nextCompleted = typeof patch.completed === "boolean" ? patch.completed : current.completed;
  const nextState = normalizeQuestState({ ...current, ...patch }, nextCompleted);
  return {
    ...progress,
    questStates: {
      ...(progress.questStates || {}),
      [questId]: nextState,
    },
    updatedAt: new Date().toISOString(),
  };
}

export function recordWorkshopRun(progress, questId, results, options = {}) {
  const resultList = Array.isArray(results) ? results : [];
  const checkResults = Object.fromEntries(
    resultList
      .filter((result) => result && typeof result.id === "string")
      .map((result) => [result.id, {
        passed: result.passed === true,
        message: typeof result.message === "string" ? result.message : "",
        checkedAt: new Date().toISOString(),
      }]),
  );

  return updateQuestState(progress, questId, {
    ...(typeof options.draft === "string" ? { draft: options.draft } : {}),
    checkResults,
    lastRunAt: new Date().toISOString(),
    feedback: typeof options.feedback === "string" ? options.feedback : "",
  });
}

export function hasCompletedChecks(progress, questId, requiredCheckIds = []) {
  const state = getQuestState(progress, questId);
  return requiredCheckIds.length > 0 && requiredCheckIds.every((checkId) =>
    state.checkResults?.[checkId]?.passed === true,
  );
}

export function completeQuest(progress, questId, requiredCheckIds = []) {
  if (!hasCompletedChecks(progress, questId, requiredCheckIds)) return progress;

  const completedQuestIds = [...new Set([...progress.completedQuestIds, questId])];
  return updateQuestState({
    ...progress,
    completedQuestIds,
    activeQuestId: progress.activeQuestId === questId ? null : progress.activeQuestId,
  }, questId, { completed: true });
}

export function reopenQuest(progress, questId) {
  return updateQuestState({
    ...progress,
    completedQuestIds: progress.completedQuestIds.filter((id) => id !== questId),
  }, questId, { completed: false });
}

export function toggleQuest(progress, questId) {
  const completed = new Set(progress.completedQuestIds);
  completed.has(questId) ? completed.delete(questId) : completed.add(questId);

  return {
    ...progress,
    completedQuestIds: [...completed],
    questStates: {
      ...(progress.questStates || {}),
      [questId]: normalizeQuestState(progress.questStates?.[questId], completed.has(questId)),
    },
    activeQuestId: completed.has(questId) && progress.activeQuestId === questId
      ? null
      : progress.activeQuestId,
    updatedAt: new Date().toISOString(),
  };
}

export function setActiveQuest(progress, questId) {
  return {
    ...progress,
    activeQuestId: progress.completedQuestIds.includes(questId) ? null : questId,
    updatedAt: new Date().toISOString(),
  };
}

export function resetProgress(validQuestIds = []) {
  return createInitialProgress([], validQuestIds);
}

export function getStats(progress, quests) {
  const completed = new Set(progress.completedQuestIds);
  const completedQuests = quests.filter((quest) => completed.has(quest.id));
  return {
    completedCount: completedQuests.length,
    totalCount: quests.length,
    earnedXp: completedQuests.reduce((sum, quest) => sum + quest.xp, 0),
    totalXp: quests.reduce((sum, quest) => sum + quest.xp, 0),
    percent: quests.length ? Math.round((completedQuests.length / quests.length) * 100) : 0,
  };
}

export function isPhaseUnlocked(phaseIndex, phases, progress) {
  if (phaseIndex === 0) return true;
  return phases[phaseIndex - 1].quests.every((quest) =>
    progress.completedQuestIds.includes(quest.id),
  );
}

export function loadProgress(storage, validQuestIds) {
  try {
    const raw = storage.getItem(STORAGE_KEY);
    return normalizeProgress(raw ? JSON.parse(raw) : null, validQuestIds);
  } catch {
    return createInitialProgress();
  }
}

export function saveProgress(storage, progress) {
  storage.setItem(STORAGE_KEY, JSON.stringify(progress));
}
