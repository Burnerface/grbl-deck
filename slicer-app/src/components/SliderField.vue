<template>
  <div class="slider-field">
    <div class="slider-top">
      <span class="slider-label">{{ label }}</span>
      <div class="slider-val-wrap">
        <input class="slider-val" type="number" :min="min" :max="max" :value="value"
          @change="emit('input', +$event.target.value)"/>
        <span class="slider-unit">{{ unit }}</span>
      </div>
    </div>
    <div class="slider-track-wrap">
      <input class="slider-track" type="range" :min="min" :max="max" :value="value"
        :style="{ '--fill': fillPct, '--color': color }"
        @input="emit('input', +$event.target.value)"/>
    </div>
  </div>
</template>
<script setup>
import { computed } from 'vue'
const props = defineProps({
  label: String, value: Number, min: Number, max: Number, unit: String, color: String,
})
const emit = defineEmits(['input'])
const fillPct = computed(() => `${((props.value - props.min) / (props.max - props.min)) * 100}%`)
</script>
<style scoped>
.slider-field { margin-bottom: 10px; }
.slider-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 5px; }
.slider-label { font-size: 11.5px; color: var(--txt1); }
.slider-val-wrap { display: flex; align-items: center; gap: 4px; }
.slider-val { width: 55px; height: 24px; background: var(--bg-input); border: 1px solid var(--border); border-radius: 4px; color: var(--txt0); font-size: 11.5px; padding: 0 6px; text-align: right; font-family: var(--ffm); }
.slider-unit { font-size: 10px; color: var(--txt2); font-family: var(--ffm); min-width: 28px; }
.slider-track { -webkit-appearance: none; appearance: none; width: 100%; height: 4px; border-radius: 2px; outline: none; cursor: pointer; background: linear-gradient(to right, v-bind(color) 0%, v-bind(color) var(--fill), var(--border-lit) var(--fill), var(--border-lit) 100%); }
.slider-track::-webkit-slider-thumb { -webkit-appearance: none; width: 14px; height: 14px; border-radius: 50%; background: v-bind(color); border: 2px solid var(--bg-panel); cursor: pointer; }
</style>
