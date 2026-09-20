import test from "node:test";
import assert from "node:assert/strict";

import { allQuests, phases } from "../src/game-data.js";
import {
  STORAGE_KEY,
  createInitialProgress,
  getHintLevel,
  getStats,
  isPhaseUnlocked,
  loadProgress,
  normalizeProgress,
  revealHint,
  setActiveQuest,
  toggleQuest,
} from "../src/progress.js";

const questIds = allQuests.map((quest) => quest.id);

test("初期状態は最初のフェーズだけ解放される", () => {
  const progress = createInitialProgress();
  assert.equal(isPhaseUnlocked(0, phases, progress), true);
  assert.equal(isPhaseUnlocked(1, phases, progress), false);
});

test("前フェーズの全クエスト完了で次を解放する", () => {
  const progress = createInitialProgress(phases[0].quests.map((quest) => quest.id));
  assert.equal(isPhaseUnlocked(1, phases, progress), true);
  assert.equal(isPhaseUnlocked(2, phases, progress), false);
});

test("クエスト完了の切り替えとXP集計が一致する", () => {
  const first = allQuests[0];
  const completed = toggleQuest(createInitialProgress(), first.id);
  assert.deepEqual(completed.completedQuestIds, [first.id]);
  assert.equal(getStats(completed, allQuests).earnedXp, first.xp);
  assert.equal(getStats(completed, allQuests).completedCount, 1);

  const reverted = toggleQuest(completed, first.id);
  assert.deepEqual(reverted.completedQuestIds, []);
});

test("完了済みクエストは進行中に設定しない", () => {
  const progress = createInitialProgress([allQuests[0].id]);
  assert.equal(setActiveQuest(progress, allQuests[0].id).activeQuestId, null);
  assert.equal(setActiveQuest(progress, allQuests[1].id).activeQuestId, allQuests[1].id);
});

test("保存データから未知IDと重複を除去する", () => {
  const result = normalizeProgress(
    {
      completedQuestIds: [questIds[0], "unknown", questIds[0]],
      activeQuestId: "unknown",
      updatedAt: "2026-09-16T00:00:00.000Z",
    },
    questIds,
  );
  assert.deepEqual(result.completedQuestIds, [questIds[0]]);
  assert.equal(result.activeQuestId, null);
});

test("壊れたlocalStorageデータでは安全に初期化する", () => {
  const storage = {
    getItem(key) {
      assert.equal(key, STORAGE_KEY);
      return "{invalid";
    },
  };
  assert.deepEqual(loadProgress(storage, questIds), createInitialProgress());
});

test("ヒントの開示レベルはクエストごとに一段ずつ保存される", () => {
  const questId = allQuests[0].id;
  const initial = createInitialProgress([], questIds);
  const firstHint = revealHint(initial, questId, "safe-env", 2);
  assert.equal(getHintLevel(firstHint, questId, "safe-env"), 1);

  const secondHint = revealHint(firstHint, questId, "safe-env", 2);
  assert.equal(getHintLevel(secondHint, questId, "safe-env"), 2);
  assert.equal(getHintLevel(secondHint, allQuests[1].id, "safe-env"), 0);

  const reloaded = normalizeProgress(JSON.parse(JSON.stringify(secondHint)), questIds);
  assert.equal(getHintLevel(reloaded, questId, "safe-env"), 2);
  assert.deepEqual(revealHint(secondHint, questId, "safe-env", 2), secondHint);
});
