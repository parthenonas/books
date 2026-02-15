<script setup lang="ts">
const props = defineProps<{
  question: any;
  modelValue: string[];
}>();

const emit = defineEmits(["update:modelValue"]);

function toggleOption(optId: string) {
  const newAnswers = [...props.modelValue];
  const idx = newAnswers.indexOf(optId);

  if (idx === -1) {
    newAnswers.push(optId);
  } else {
    newAnswers.splice(idx, 1);
  }

  emit("update:modelValue", newAnswers);
}
</script>

<template>
  <div class="mc-container">
    <h2>{{ question.text }}</h2>
    <p class="points-hint">Баллов за вопрос: {{ question.points }}</p>

    <div class="options-list">
      <label
        v-for="opt in question.options"
        :key="opt.id"
        class="option-item"
        :class="{ selected: modelValue.includes(opt.id) }"
      >
        <input
          type="checkbox"
          :checked="modelValue.includes(opt.id)"
          @change="toggleOption(opt.id)"
        />
        <span class="opt-text">{{ opt.text }}</span>
      </label>
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
  margin-bottom: 30px;
  font-size: 0.9rem;
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.option-item {
  display: flex;
  align-items: center;
  padding: 15px;
  background: var(--vp-c-bg-alt);
  border-radius: 6px;
  cursor: pointer;
  border: 1px solid var(--vp-c-border);
  transition: 0.2s;
  color: var(--vp-c-text-1);
}

.option-item:hover {
  border-color: var(--vp-c-brand-1);
  background: var(--vp-c-bg-soft);
}

.option-item.selected {
  border-color: var(--vp-c-brand-1);
  background: var(--vp-c-bg-soft);
}

.option-item input {
  margin-right: 15px;
  transform: scale(1.3);
  cursor: pointer;
}
</style>
