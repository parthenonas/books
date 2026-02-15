<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from "vue";

import { PGlite } from "@electric-sql/pglite";
import QuestionMultipleChoice from "./QuestionMultipleChoice.vue";
import QuestionSqlSelect from "./QuestionSqlSelect.vue";

const props = defineProps<{
  jsonPath: string;
  requiredIds?: string[];
  count: number;
}>();

const isChrome =
  /Chrome/.test(navigator.userAgent) && /Google Inc/.test(navigator.vendor);

const status = ref<
  | "INIT"
  | "LOADING"
  | "READY"
  | "IN_PROGRESS"
  | "COMPLETED"
  | "BLOCKED"
  | "COMPLETED_VIEW"
>("INIT");

const testData = ref<any>(null);

const state = ref({
  questions: [] as any[],
  answers: {} as Record<string, any>,
  currentIndex: 0,
  startTime: 0,
  endTime: 0,
  questionTimings: {} as Record<string, number>,
  lastQuestionEntryTime: 0,
  cheatAttempts: 0,
  cheatLogs: [] as string[],
  score: 0,
  maxScore: 0,
  grade: 0,
  isBlocked: false,
});

const timeLeft = ref("");
let timerInterval: any = null;

function updateTimer() {
  if (status.value !== "IN_PROGRESS") return;

  const limitMinutes = testData.value.time_limit || 20;
  const limitMs = limitMinutes * 60 * 1000;

  const elapsed = Date.now() - state.value.startTime;
  const remaining = limitMs - elapsed;

  if (remaining <= 0) {
    timeLeft.value = "00:00";
    finishTest();
    alert("Время вышло! Тест завершен принудительно.");
  } else {
    const m = Math.floor(remaining / 60000);
    const s = Math.floor((remaining % 60000) / 1000);
    timeLeft.value = `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  }
}

const fileName = props.jsonPath.replace(/^\//, "");
const storageKey = `quiz_state_${fileName}`;

async function sha256(message: string) {
  const msgBuffer = new TextEncoder().encode(message);
  const hashBuffer = await crypto.subtle.digest("SHA-256", msgBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
}

onMounted(async () => {
  if (!isChrome) return;

  status.value = "LOADING";
  try {
    const fullUrl = `${(import.meta as any).env.BASE_URL}quizzes/${fileName}`;
    const res = await fetch(fullUrl, { cache: "no-store" });
    if (!res.ok) {
      status.value = "INIT";
      return;
    }
    testData.value = await res.json();

    const saved = localStorage.getItem(storageKey);
    if (saved) {
      state.value = JSON.parse(saved);

      if (
        testData.value.max_cheat_attempts &&
        state.value.cheatAttempts >= testData.value.max_cheat_attempts
      ) {
        state.value.isBlocked = true;
      }

      if (state.value.isBlocked) {
        status.value = "COMPLETED";
      } else if (state.value.endTime > 0) {
        status.value = "COMPLETED";
      } else {
        if (state.value.startTime > 0) {
          status.value = "IN_PROGRESS";
          updateTimer();
          timerInterval = setInterval(updateTimer, 1000);
        } else {
          status.value = "READY";
        }
      }
    } else {
      prepareQuestions();
      status.value = "READY";
    }
  } catch (e) {
    status.value = "INIT";
  }
});

watch(
  state,
  (newVal) => {
    localStorage.setItem(storageKey, JSON.stringify(newVal));
  },
  { deep: true },
);

function prepareQuestions() {
  let pool = [...testData.value.questions];
  let selected = [] as any[];

  if (props.requiredIds && props.requiredIds.length > 0) {
    props.requiredIds.forEach((id) => {
      const qIndex = pool.findIndex((q) => q.id === id);
      if (qIndex !== -1) {
        selected.push(pool[qIndex]);
        pool.splice(qIndex, 1);
      }
    });
  }

  pool.sort(() => Math.random() - 0.5);
  const needed = props.count - selected.length;
  if (needed > 0) {
    selected = selected.concat(pool.slice(0, needed));
  }

  selected.sort(() => Math.random() - 0.5);

  state.value.questions = selected;
  selected.forEach((q) => {
    state.value.answers[q.id] = q.type === "sql-select" ? "" : [];
    state.value.questionTimings[q.id] = 0;
    state.value.maxScore += q.points;

    if (q.options) {
      q.options.sort(() => Math.random() - 0.5);
    }
  });
}

function startTest() {
  state.value.startTime = Date.now();
  state.value.lastQuestionEntryTime = Date.now();
  status.value = "IN_PROGRESS";
  addCheatListeners();

  updateTimer();
  timerInterval = setInterval(updateTimer, 1000);
}

function nextQuestion() {
  recordTime();
  if (state.value.currentIndex < state.value.questions.length - 1) {
    state.value.currentIndex++;
    state.value.lastQuestionEntryTime = Date.now();
  }
}

function prevQuestion() {
  recordTime();
  if (state.value.currentIndex > 0) {
    state.value.currentIndex--;
    state.value.lastQuestionEntryTime = Date.now();
  }
}

function recordTime() {
  const currentQId = state.value.questions[state.value.currentIndex].id;
  const spent = Date.now() - state.value.lastQuestionEntryTime;
  state.value.questionTimings[currentQId] += spent;
}

function checkFocus() {
  if (status.value !== "IN_PROGRESS") return;

  if (document.visibilityState === "hidden" || !document.hasFocus()) {
    state.value.cheatAttempts++;
    state.value.cheatLogs.push(
      `Попытка списывания: ${new Date().toLocaleTimeString()}`,
    );

    const maxCheats = testData.value.max_cheat_attempts;
    if (maxCheats && state.value.cheatAttempts >= maxCheats) {
      state.value.isBlocked = true;
      state.value.endTime = Date.now();
      status.value = "BLOCKED";
      removeCheatListeners();
    } else {
      alert(
        `Ахтунг! Попытка списывания зафиксирована. Попытка ${state.value.cheatAttempts} из ${maxCheats || "∞"}`,
      );
    }
  }
}

function addCheatListeners() {
  window.addEventListener("blur", checkFocus);
  document.addEventListener("visibilitychange", checkFocus);
}

function removeCheatListeners() {
  window.removeEventListener("blur", checkFocus);
  document.removeEventListener("visibilitychange", checkFocus);
}

async function finishTest() {
  clearInterval(timerInterval);
  recordTime();
  removeCheatListeners();
  state.value.endTime = Date.now();

  let totalScore = 0;

  for (const q of state.value.questions) {
    if (q.type === "sql-select") {
      try {
        let studentSql = state.value.answers[q.id];
        if (!studentSql || !studentSql.trim()) {
          q.isCorrect = false;
          continue;
        }

        studentSql = studentSql.trim().replace(/;$/, "");

        const db = new PGlite();
        await db.waitReady;

        const initSql = q.init_sql || [];
        for (const sql of initSql) {
          await db.exec(sql);
        }

        try {
          await db.query(studentSql);
        } catch (e) {
          q.isCorrect = false;
          continue;
        }

        let correctQuery = q.correct_query;

        correctQuery = correctQuery.trim().replace(/;$/, "");

        const checkExtra = (await db.query(`
            SELECT count(*) as cnt 
            FROM ((${studentSql}) EXCEPT ALL (${correctQuery})) as diff
        `)) as any;

        const checkMissing = (await db.query(`
            SELECT count(*) as cnt 
            FROM ((${correctQuery}) EXCEPT ALL (${studentSql})) as diff
        `)) as any;

        const extraCount = parseInt(checkExtra.rows[0].cnt as string);
        const missingCount = parseInt(checkMissing.rows[0].cnt as string);

        let dataCorrect = extraCount === 0 && missingCount === 0;

        if (dataCorrect && q.sort_required) {
          const resStudent = await db.query(studentSql);
          const resCorrect = await db.query(correctQuery);
          if (
            JSON.stringify(resStudent.rows) !== JSON.stringify(resCorrect.rows)
          ) {
            dataCorrect = false;
          }
        }

        q.isCorrect = dataCorrect;
      } catch (err) {
        console.error("Ошибка проверки SQL:", err);
        q.isCorrect = false;
      }
    } else {
      const userAnswers = state.value.answers[q.id] || [];
      if (Array.isArray(userAnswers)) {
        userAnswers.sort();
        const hash = await sha256(userAnswers.join(","));
        q.isCorrect = hash === q.correct_hash;
      } else {
        q.isCorrect = false;
      }
    }

    if (q.isCorrect) {
      totalScore += q.points;
    }
  }

  state.value.score = totalScore;

  const percent = (totalScore / state.value.maxScore) * 100;
  let finalGrade = 2;
  const grading = testData.value.grading;
  for (const gradeStr of Object.keys(grading).sort().reverse()) {
    if (percent >= grading[gradeStr]) {
      finalGrade = parseInt(gradeStr);
      break;
    }
  }
  state.value.grade = finalGrade;
  status.value = "COMPLETED_VIEW";
}

const formatTime = (ms: number) => {
  const s = Math.floor(ms / 1000);
  const m = Math.floor(s / 60);
  return `${m}м ${s % 60}с`;
};

function getSelectedOptionTexts(q: any, selectedIds: string[]) {
  if (!q.options) return [];
  return q.options
    .filter((opt: any) => selectedIds.includes(opt.id))
    .map((opt: any) => opt.text)
    .join(", ");
}

onUnmounted(() => {
  removeCheatListeners();
});
</script>

<template>
  <div v-if="status !== 'INIT'" class="quiz-wrapper">
    <div v-if="status === 'READY'" class="quiz-start-box">
      <h3>{{ testData.title }}</h3>
      <button @click="startTest" class="btn primary">Начать тест</button>
    </div>

    <div
      v-if="status === 'COMPLETED'"
      class="quiz-start-box"
      :style="state.isBlocked ? 'border-color: var(--vp-c-danger-1)' : ''"
    >
      <h3>{{ testData.title }}</h3>

      <div v-if="state.isBlocked">
        <p style="color: var(--vp-c-danger-1); font-weight: bold">
          ❌ Тест аннулирован (списывание)
        </p>
        <button @click="status = 'BLOCKED'" class="btn danger">
          Подробнее
        </button>
      </div>

      <div v-else>
        <p>Тест пройден. Оценка: {{ state.grade }}</p>
        <button @click="status = 'COMPLETED_VIEW'" class="btn">
          Показать отчет
        </button>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="status === 'IN_PROGRESS'" class="fullscreen-overlay">
        <div class="quiz-container">
          <div class="quiz-header">
            <span>{{ testData.title }}</span>
            <span
              style="
                font-family: monospace;
                font-size: 1.1em;
                color: var(--vp-c-brand-1);
              "
            >
              ⏳ {{ timeLeft }}
            </span>
            <span
              >{{ state.currentIndex + 1 }} / {{ state.questions.length }}</span
            >
          </div>

          <div class="question-content">
            <QuestionSqlSelect
              v-if="state.questions[state.currentIndex].type === 'sql-select'"
              :question="state.questions[state.currentIndex]"
              :init-sql="testData.init_sql || []"
              v-model="state.answers[state.questions[state.currentIndex].id]"
            />

            <QuestionMultipleChoice
              v-else
              :question="state.questions[state.currentIndex]"
              v-model="state.answers[state.questions[state.currentIndex].id]"
            />
          </div>

          <div class="quiz-footer">
            <button
              class="btn"
              :disabled="state.currentIndex === 0"
              @click="prevQuestion"
            >
              Назад
            </button>
            <button
              v-if="state.currentIndex < state.questions.length - 1"
              class="btn primary"
              @click="nextQuestion"
            >
              Далее
            </button>
            <button v-else class="btn danger" @click="finishTest">
              Завершить тест
            </button>
          </div>
        </div>
      </div>

      <div
        v-if="status === 'COMPLETED_VIEW'"
        class="fullscreen-overlay report-screen"
      >
        <div class="report-container">
          <h1>Итоги: {{ testData.title }}</h1>

          <div class="report-stats">
            <div class="stat-card">
              Оценка: <strong>{{ state.grade }}</strong>
            </div>
            <div class="stat-card">
              Баллы: <strong>{{ state.score }} / {{ state.maxScore }}</strong>
            </div>
            <div class="stat-card">
              Затрачено времени:
              <strong>{{ formatTime(state.endTime - state.startTime) }}</strong>
            </div>
            <div
              class="stat-card"
              :class="{ cheater: state.cheatAttempts > 0 }"
            >
              Списываний: <strong>{{ state.cheatAttempts }}</strong>
            </div>
          </div>

          <div class="questions-report">
            <div
              v-for="(q, idx) in state.questions"
              :key="q.id"
              class="q-report-item"
              :class="q.isCorrect ? 'correct' : 'wrong'"
            >
              <div class="q-header">
                <h4>{{ idx + 1 }}. {{ q.text }}</h4>
                <span class="q-status">{{ q.isCorrect ? "✅" : "❌" }}</span>
              </div>

              <div v-if="q.type === 'sql-select'" class="answer-details">
                <div class="code-block">
                  <strong>Твой запрос:</strong>
                  <pre>{{ state.answers[q.id] || "—" }}</pre>
                </div>
              </div>

              <div v-else class="answer-details">
                <p>
                  <strong>Твой ответ:</strong>
                  {{
                    getSelectedOptionTexts(q, state.answers[q.id] || []) ||
                    "(нет ответа)"
                  }}
                </p>
                <p v-if="!q.isCorrect" style="font-size: 0.8em; opacity: 0.7">
                  (Ответ не совпал с эталоном)
                </p>
              </div>

              <div class="q-footer">
                <small
                  >Время: {{ formatTime(state.questionTimings[q.id]) }}</small
                >
                <small v-if="q.isCorrect" style="color: var(--vp-c-success-1)"
                  >+{{ q.points }} баллов</small
                >
                <small v-else style="color: var(--vp-c-danger-1)"
                  >0 баллов</small
                >
              </div>
            </div>
          </div>

          <button
            @click="status = 'COMPLETED'"
            class="btn"
            style="margin-top: 20px"
          >
            Закрыть отчет
          </button>
        </div>
      </div>

      <div
        v-if="status === 'BLOCKED'"
        class="fullscreen-overlay blocked-screen"
      >
        <h1>🚫 ТЕСТ ЗАБЛОКИРОВАН 🚫</h1>
        <p>Твой результат аннулирован. Признайся в списывании.</p>
        <div class="logs">
          <p v-for="log in state.cheatLogs" :key="log">{{ log }}</p>
        </div>

        <button
          @click="status = 'COMPLETED'"
          class="btn"
          style="margin-top: 20px"
        >
          Закрыть
        </button>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.quiz-wrapper {
  margin: 20px 0;
}

.quiz-start-box {
  border: 1px solid var(--vp-c-border);
  padding: 20px;
  border-radius: 8px;
  background: var(--vp-c-bg-soft);
  text-align: center;
  color: var(--vp-c-text-1);
}

.btn {
  padding: 10px 20px;
  border: 1px solid var(--vp-c-border);
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  background: var(--vp-c-bg-alt);
  color: var(--vp-c-text-1);
  transition:
    background-color 0.2s,
    border-color 0.2s;
}

.btn:hover {
  border-color: var(--vp-c-brand-1);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}

.btn.primary {
  background: var(--vp-c-brand-1);
  color: white;
  border-color: var(--vp-c-brand-1);
}
.btn.primary:hover {
  filter: brightness(1.1);
}

.btn.danger {
  background: var(--vp-c-danger-1);
  color: white;
  border-color: var(--vp-c-danger-1);
}
.btn.danger:hover {
  filter: brightness(1.1);
}

.fullscreen-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  color: var(--vp-c-text-1);
  z-index: 99999;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.quiz-container {
  width: 100%;
  max-width: 800px;
  height: 90vh;
  background: var(--vp-c-bg);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.quiz-header {
  padding: 15px 20px;
  background: var(--vp-c-bg-soft);
  border-bottom: 1px solid var(--vp-c-border);
  display: flex;
  justify-content: space-between;
  font-weight: bold;
  color: var(--vp-c-text-2);
}

.question-content {
  padding: 40px;
  flex-grow: 1;
  overflow-y: auto;
}

.quiz-footer {
  padding: 20px;
  background: var(--vp-c-bg-soft);
  border-top: 1px solid var(--vp-c-border);
  display: flex;
  justify-content: space-between;
}

.report-container {
  width: 100%;
  max-width: 800px;
  max-height: 90vh;
  background: var(--vp-c-bg);
  border-radius: 8px;
  overflow-y: auto;
  padding: 40px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.report-container h1 {
  color: var(--vp-c-text-1);
  margin-bottom: 20px;
}

.report-stats {
  display: flex;
  gap: 20px;
  margin: 30px 0;
  flex-wrap: wrap;
}

.stat-card {
  background: var(--vp-c-bg-soft);
  padding: 20px;
  border-radius: 8px;
  flex: 1;
  min-width: 150px;
  text-align: center;
  border: 1px solid var(--vp-c-border);
  color: var(--vp-c-text-1);
}

.stat-card.cheater {
  border-color: var(--vp-c-danger-1);
  color: var(--vp-c-danger-1);
}

.questions-report {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.q-report-item {
  padding: 15px;
  border-radius: 6px;
  border-left: 5px solid;
  background: var(--vp-c-bg-soft);
  color: var(--vp-c-text-1);
}

.q-report-item h4 {
  margin: 0 0 10px 0;
}

.q-report-item p {
  margin: 5px 0;
  color: var(--vp-c-text-2);
}

.q-report-item.correct {
  border-color: var(--vp-c-success-1);
}

.q-report-item.wrong {
  border-color: var(--vp-c-danger-1);
}

.blocked-screen {
  background: var(--vp-c-bg);
  padding: 40px;
  border-radius: 8px;
  text-align: center;
  color: var(--vp-c-danger-1);
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.2);
}

.blocked-screen h1 {
  color: var(--vp-c-danger-1);
}

.blocked-screen p {
  color: var(--vp-c-text-1);
  margin: 10px 0;
}

.blocked-screen .logs {
  margin-top: 20px;
  color: var(--vp-c-text-2);
  font-family: monospace;
  text-align: left;
  background: var(--vp-c-bg-alt);
  padding: 10px;
  border-radius: 4px;
}

.q-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.q-status {
  font-size: 1.2rem;
}

.answer-details {
  background: var(--vp-c-bg);
  padding: 10px;
  border-radius: 4px;
  margin: 10px 0;
  font-size: 0.9rem;
}

.code-block pre {
  background: var(--vp-c-bg-alt);
  padding: 8px;
  border-radius: 4px;
  overflow-x: auto;
  font-family: monospace;
  margin: 5px 0 10px 0;
  white-space: pre-wrap;
}

.q-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 5px;
  border-top: 1px solid var(--vp-c-border);
  padding-top: 5px;
  opacity: 0.8;
}
</style>
