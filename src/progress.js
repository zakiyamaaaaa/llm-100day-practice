export const STORAGE_KEY = "llm-roadmap-quest:v1";

export function createInitialProgress(completedQuestIds = []) {
  return {
    completedQuestIds: [...new Set(completedQuestIds)],
    activeQuestId: null,
    updatedAt: null,
  };
}

export function normalizeProgress(value, validQuestIds) {
  const valid = new Set(validQuestIds);
  if (!value || typeof value !== "object") return createInitialProgress();

  const completedQuestIds = Array.isArray(value.completedQuestIds)
    ? [...new Set(value.completedQuestIds.filter((id) => valid.has(id)))]
    : [];
  const activeQuestId = valid.has(value.activeQuestId) ? value.activeQuestId : null;

  return {
    completedQuestIds,
    activeQuestId,
    updatedAt: typeof value.updatedAt === "string" ? value.updatedAt : null,
  };
}

export function toggleQuest(progress, questId) {
  const completed = new Set(progress.completedQuestIds);
  completed.has(questId) ? completed.delete(questId) : completed.add(questId);

  return {
    ...progress,
    completedQuestIds: [...completed],
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

export function resetProgress() {
  return createInitialProgress();
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
