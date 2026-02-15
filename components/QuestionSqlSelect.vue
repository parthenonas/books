<script setup lang="ts">
import { PGlite } from "@electric-sql/pglite";
import { onMounted, onUnmounted, ref, shallowRef, watch } from "vue";

const props = defineProps<{
  question: any;
  modelValue: string;
  initSql: string[];
}>();

const emit = defineEmits(["update:modelValue"]);

const db = shallowRef<PGlite | null>(null);
const resultRows = ref<any[]>([]);
const resultColumns = ref<string[]>([]);
const errorMsg = ref<string | null>(null);
const isDbReady = ref(false);
const successMsg = ref<string | null>(null);

const userQuery = ref(props.modelValue || "");

watch(userQuery, (val) => {
  emit("update:modelValue", val);
});

onMounted(async () => {
  try {
    db.value = new PGlite();

    await db.value.waitReady;

    if (props.initSql && props.initSql.length > 0) {
      for (const sql of props.initSql) {
        await db.value.exec(sql);
      }
    }

    isDbReady.value = true;
  } catch (e: any) {
    errorMsg.value = "Ошибка инициализации БД: " + e.message;
  }
});

async function runQuery() {
  if (!db.value || !userQuery.value.trim()) return;

  errorMsg.value = null;
  successMsg.value = null;
  resultRows.value = [];
  resultColumns.value = [];

  try {
    const res = await db.value.query(userQuery.value);
    if (res.rows) {
      resultRows.value = res.rows;
      if (res.fields) {
        resultColumns.value = res.fields.map((f) => f.name);
      }
      successMsg.value = `Получено строк: ${res.rows.length}`;
    }
  } catch (e: any) {
    errorMsg.value = e.message;
  }
}

onUnmounted(() => {
  if (db.value) {
    db.value = null;
  }
});
</script>

<template>
  <div class="sql-question-container">
    <h2>{{ question.text }}</h2>
    <p class="points-hint">Баллов за вопрос: {{ question.points }}</p>

    <div class="editor-area">
      <textarea
        v-model="userQuery"
        class="code-editor"
        placeholder="SELECT * FROM ..."
        spellcheck="false"
      ></textarea>

      <div class="toolbar">
        <button class="btn-run" @click="runQuery" :disabled="!isDbReady">
          ▶ Выполнить
        </button>
        <span v-if="!isDbReady" class="loading-label">Загрузка БД...</span>
      </div>
    </div>

    <div v-if="errorMsg" class="output-msg error">{{ errorMsg }}</div>

    <div v-if="successMsg" class="output-msg success">{{ successMsg }}</div>

    <div v-if="resultRows.length > 0" class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th v-for="col in resultColumns" :key="col">{{ col }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, idx) in resultRows" :key="idx">
            <td v-for="col in resultColumns" :key="col">
              <span v-if="row[col] === null" class="null-val">NULL</span>
              <span v-else>{{ row[col] }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
h2 {
  margin-bottom: 10px;
  font-size: 1.5rem;
  color: var(--vp-c-text-1);
}

.points-hint {
  color: var(--vp-c-text-2);
  margin-bottom: 20px;
  font-size: 0.9rem;
}

.editor-area {
  margin-bottom: 20px;
  border: 1px solid var(--vp-c-border);
  border-radius: 8px;
  overflow: hidden;
  background: var(--vp-c-bg-alt);
}

.code-editor {
  width: 100%;
  height: 150px;
  background: var(--vp-c-bg-alt);
  color: var(--vp-c-text-1);
  font-family: monospace;
  font-size: 14px;
  padding: 15px;
  border: none;
  resize: vertical;
  outline: none;
}

.toolbar {
  padding: 10px;
  background: var(--vp-c-bg-soft);
  border-top: 1px solid var(--vp-c-border);
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn-run {
  background: var(--vp-c-brand-1);
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  font-size: 0.9rem;
  transition: opacity 0.2s;
}

.btn-run:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading-label {
  font-size: 0.8rem;
  color: var(--vp-c-text-2);
  animation: pulse 1.5s infinite;
}

.output-msg {
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 15px;
  font-family: monospace;
  font-size: 0.9rem;
}
.output-msg.error {
  background: rgba(239, 68, 68, 0.1);
  color: var(--vp-c-danger-1);
  border: 1px solid var(--vp-c-danger-1);
}
.output-msg.success {
  background: rgba(16, 185, 129, 0.1);
  color: var(--vp-c-success-1);
  border: 1px solid var(--vp-c-success-1);
}

.table-wrapper {
  overflow-x: auto;
  border: 1px solid var(--vp-c-border);
  border-radius: 6px;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

th {
  background: var(--vp-c-bg-soft);
  text-align: left;
  padding: 8px 12px;
  border-bottom: 2px solid var(--vp-c-border);
  color: var(--vp-c-text-1);
}

td {
  padding: 8px 12px;
  border-bottom: 1px solid var(--vp-c-border);
  color: var(--vp-c-text-2);
}

.null-val {
  color: var(--vp-c-text-2);
  font-style: italic;
  opacity: 0.7;
}

@keyframes pulse {
  0% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
  100% {
    opacity: 0.5;
  }
}
</style>
