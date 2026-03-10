<template>
  <div class="acc-section" :class="{ open }">
    <button class="acc-header" @click="open = !open">
      <div class="acc-icon" :class="iconClass">{{ icon }}</div>
      <span class="acc-title">{{ title }}</span>
      <span v-if="value" class="acc-value">{{ value }}</span>
      <span class="acc-arrow">▾</span>
    </button>
    <div class="acc-body">
      <div class="acc-content">
        <slot />
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref } from 'vue'
defineProps({ title: String, icon: String, iconClass: String, value: String })
const open = ref(true)
</script>
<style scoped>
.acc-section { border-bottom: 1px solid var(--border); overflow: hidden; }
.acc-header {
  height: 40px; padding: 0 14px;
  display: flex; align-items: center; gap: 10px;
  cursor: pointer; width: 100%; background: none;
  color: var(--txt0); transition: background .12s;
}
.acc-header:hover { background: var(--bg-hover); }
.acc-icon {
  width: 26px; height: 26px; border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; flex-shrink: 0;
}
.acc-icon.machine  { background: rgba(74,144,226,.15); color: #4A90E2; }
.acc-icon.material { background: var(--teal-soft); color: var(--teal); }
.acc-icon.process  { background: var(--accent-soft); color: var(--accent); }
.acc-title { flex: 1; text-align: left; font-size: 12.5px; font-weight: 600; }
.acc-value { font-size: 11px; color: var(--txt2); font-family: var(--ffm); }
.acc-arrow { font-size: 10px; color: var(--txt2); transition: transform .2s; }
.acc-section.open .acc-arrow { transform: rotate(180deg); }
.acc-body { overflow: hidden; max-height: 0; transition: max-height .25s ease; background: var(--bg-card); }
.acc-section.open .acc-body { max-height: 800px; }
.acc-content { padding: 12px 14px; }
</style>
