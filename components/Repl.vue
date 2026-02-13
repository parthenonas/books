<script setup lang="ts">
import { PGlite } from "@electric-sql/pglite";
import "@electric-sql/pglite-repl/webcomponent";
import { vector } from "@electric-sql/pglite/vector";
import { onMounted, ref } from "vue";

interface ReplProps {
  initialQueries: string[];
}

const { initialQueries = [] } = defineProps<ReplProps>();
const opened = ref(false);

const pg = new PGlite({
  extensions: { vector },
});

onMounted(async () => {
  await pg.waitReady;
  for (const query of initialQueries) {
    await pg.exec(query).catch((e) => console.error(e));
  }
});

const toggle = () => {
  opened.value = !opened.value;
  if (opened.value) {
    setTimeout(() => document.querySelector("pglite-repl")?.focus(), 100);
  }
};
</script>

<template>
  <div class="terminal-container" :class="{ 'is-open': opened }">
    <div class="terminal-header" @click="toggle">
      <span class="terminal-title">
        <span class="icon">💻</span> SQL Terminal
      </span>
      <span class="terminal-toggle-icon">{{
        opened ? "▼ Свернуть" : "▲ Открыть консоль"
      }}</span>
    </div>

    <div class="terminal-body">
      <pglite-repl :pg="pg" theme="dark" class="repl-component" />
    </div>
  </div>
</template>

<style scoped>
.terminal-container {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  z-index: 9999;
  background-color: #1e1e20;
  border-top: 1px solid #444;
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.5);
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  transform: translateY(calc(100% - 40px));
}

.terminal-container.is-open {
  transform: translateY(0);
}

.terminal-header {
  height: 40px;
  background-color: #2d2d30;
  color: #cccccc;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  cursor: pointer;
  user-select: none;
  font-family: monospace;
  font-size: 14px;
}

.terminal-header:hover {
  background-color: #3e3e42;
  color: #ffffff;
}

.terminal-body {
  height: 40vh;
  width: 100%;
  background-color: #0d0d0d;
  overflow: hidden;
}

.repl-component {
  width: 100%;
  height: 100%;
  display: block;
  --repl-bg: #0d0d0d;
}
</style>
