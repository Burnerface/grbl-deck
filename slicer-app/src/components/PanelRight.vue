<template>
  <div class="panel-right">

    <AccordionSection title="Machine" icon="⚙" icon-class="machine" :value="'Laser 40W'">
      <div class="field-row">
        <span class="field-label">Type</span>
        <select class="field-select">
          <option>Laser CO₂</option>
          <option>Laser diode</option>
          <option>CNC fraisage</option>
        </select>
      </div>
      <div class="field-row">
        <span class="field-label">Largeur</span>
        <input class="field-input" type="number" value="600"/>
        <span class="field-unit">mm</span>
      </div>
      <div class="field-row">
        <span class="field-label">Hauteur</span>
        <input class="field-input" type="number" value="400"/>
        <span class="field-unit">mm</span>
      </div>
    </AccordionSection>

    <AccordionSection title="Matériau" icon="🪵" icon-class="material" :value="selectedMat">
      <div class="mat-presets">
        <button v-for="m in matPresets" :key="m"
          class="mat-chip" :class="{ active: selectedMat === m }"
          @click="selectedMat = m">{{ m }}</button>
      </div>
      <div class="field-row" style="margin-top:8px">
        <span class="field-label">Épaisseur</span>
        <input class="field-input" type="number" :value="matThickness" @change="matThickness = +$event.target.value"/>
        <span class="field-unit">mm</span>
      </div>
    </AccordionSection>

    <AccordionSection v-if="activeLayer" :title="`Process — ${activeLayer.name}`" icon="🔥" icon-class="process">
      <div class="field-col">
        <span class="field-label">Mode</span>
        <div class="mode-chips">
          <button v-for="m in modes" :key="m.id"
            class="mode-chip" :class="[{ active: activeLayer.mode === m.id }, m.id]"
            @click="emit('update-layer', { id: activeLayer.id, mode: m.id })">
            {{ m.label }}
          </button>
        </div>
      </div>
      <div class="acc-sep"></div>
      <SliderField label="Puissance" :value="activeLayer.power" :min="0" :max="100" unit="%" color="var(--accent)" @input="v => emit('update-layer', { id: activeLayer.id, power: v })"/>
      <SliderField label="Vitesse" :value="activeLayer.speed" :min="100" :max="10000" unit="mm/min" color="#4A90E2" @input="v => emit('update-layer', { id: activeLayer.id, speed: v })"/>
      <SliderField label="Fréquence" :value="activeLayer.frequency" :min="1" :max="100" unit="kHz" color="var(--teal)" @input="v => emit('update-layer', { id: activeLayer.id, frequency: v })"/>
      <div class="acc-sep"></div>
      <div class="field-row">
        <span class="field-label">Passes</span>
        <div class="passes-row">
          <button class="pass-btn" @click="changePasses(-1)">−</button>
          <span class="pass-count">{{ activeLayer.passes }}</span>
          <button class="pass-btn" @click="changePasses(1)">＋</button>
        </div>
      </div>
      <div class="field-row" v-if="activeLayer.mode === 'fill'">
        <span class="field-label">Intervalle</span>
        <input class="field-input" type="number" step="0.05" :value="activeLayer.interval"
          @change="emit('update-layer', { id: activeLayer.id, interval: +$event.target.value })"/>
        <span class="field-unit">mm</span>
      </div>
    </AccordionSection>

    <div class="gcode-section">
      <div class="gcode-header">
        <span class="gcode-title">Aperçu GCode</span>
        <div class="gcode-stats">
          <div class="stat"><span class="stat-val">{{ gcodeStats.lines }}</span><span class="stat-lbl">lignes</span></div>
          <div class="stat"><span class="stat-val">{{ gcodeStats.time }}</span><span class="stat-lbl">durée</span></div>
          <div class="stat"><span class="stat-val">{{ gcodeStats.dist }}</span><span class="stat-lbl">dist.</span></div>
        </div>
      </div>
      <div class="gcode-box">
        <div v-for="line in gcodePreview" :key="line.n" class="gc-line" :class="{ highlight: line.cmd === 'M3' && line.args && !line.args.includes('S0') }">
          <span class="gc-n">{{ line.n }}</span>
          <span class="gc-cmd">{{ line.cmd }}</span>
          <span class="gc-arg">{{ line.args }}</span>
          <span class="gc-comment">{{ line.comment }}</span>
        </div>
      </div>
      <SendPanel :gcode-lines="gcodePreview"/>
    </div>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import AccordionSection from './AccordionSection.vue'
import SliderField from './SliderField.vue'
import SendPanel from './SendPanel.vue'

const props = defineProps({
  activeLayer: Object,
  selectedCoords: Object,
  gcodePreview: Array,
  gcodeStats: Object,
})
const emit = defineEmits(['update-layer', 'update-coords', 'send'])

const selectedMat = ref('Bois 3mm')
const matThickness = ref(3)
const matPresets = ['Bois 3mm', 'Acrylique', 'Carton', 'Cuir', '+ Perso']
const modes = [
  { id: 'fill', label: 'Fill' }, { id: 'line', label: 'Line' },
  { id: 'cut',  label: 'Cut'  }, { id: 'score', label: 'Score' },
]
function changePasses(d) {
  if (!props.activeLayer) return
  emit('update-layer', { id: props.activeLayer.id, passes: Math.max(1, Math.min(10, props.activeLayer.passes + d)) })
}
</script>

<style scoped>
.panel-right { width: 255px; background: var(--bg-panel); border-left: 1px solid var(--border); display: flex; flex-direction: column; flex-shrink: 0; overflow-y: auto !important; overflow-x: hidden; min-height: 0; }
.panel-right::-webkit-scrollbar { width: 3px; }
.panel-right::-webkit-scrollbar-thumb { background: var(--border-lit); border-radius: 4px; }
.field-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.field-row:last-child { margin-bottom: 0; }
.field-col { display: flex; flex-direction: column; gap: 6px; margin-bottom: 8px; }
.field-label { font-size: 11.5px; color: var(--txt1); flex: 1; }
.field-input { width: 80px; height: 27px; background: var(--bg-input); border: 1px solid var(--border); border-radius: 4px; color: var(--txt0); font-size: 12px; padding: 0 8px; }
.field-select { flex: 1; height: 27px; background: var(--bg-input); border: 1px solid var(--border); border-radius: 4px; color: var(--txt0); font-size: 12px; padding: 0 6px; }
.field-unit { font-size: 10.5px; color: var(--txt2); font-family: var(--ffm); min-width: 22px; }
.mat-presets { display: flex; flex-wrap: wrap; gap: 5px; }
.mat-chip { padding: 4px 10px; border-radius: 20px; background: var(--bg-input); border: 1px solid var(--border); font-size: 11px; color: var(--txt1); cursor: pointer; transition: all .12s; }
.mat-chip.active { background: var(--teal-soft); border-color: var(--teal); color: var(--teal); }
.mode-chips { display: flex; gap: 4px; }
.mode-chip { flex: 1; height: 27px; border-radius: 4px; background: var(--bg-input); border: 1px solid var(--border); font-size: 11px; font-weight: 500; color: var(--txt1); cursor: pointer; transition: all .12s; }
.mode-chip.active.fill  { background: var(--accent-soft); border-color: var(--accent); color: var(--accent); }
.mode-chip.active.line  { background: var(--teal-soft); border-color: var(--teal); color: var(--teal); }
.mode-chip.active.cut   { background: rgba(239,68,68,.15); border-color: var(--red); color: var(--red); }
.mode-chip.active.score { background: rgba(245,158,11,.15); border-color: var(--yellow); color: var(--yellow); }
.passes-row { display: flex; align-items: center; gap: 8px; flex: 1; }
.pass-btn { width: 27px; height: 27px; background: var(--bg-input); border: 1px solid var(--border); border-radius: 4px; color: var(--txt0); font-size: 16px; display: flex; align-items: center; justify-content: center; transition: all .12s; cursor: pointer; }
.pass-count { flex: 1; text-align: center; font-size: 16px; font-weight: 700; color: var(--txt0); }
.acc-sep { height: 1px; background: var(--border); margin: 8px 0; }
.gcode-section { display: flex; flex-direction: column; min-height: 200px; border-top: 1px solid var(--border); }
.gcode-header { padding: 10px 14px; display: flex; align-items: center; justify-content: space-between; }
.gcode-title { font-size: 10px; font-weight: 700; letter-spacing: .10em; text-transform: uppercase; color: var(--txt2); }
.gcode-stats { display: flex; gap: 10px; }
.stat { display: flex; flex-direction: column; align-items: center; }
.stat-val { font-size: 12px; font-weight: 700; color: var(--txt0); font-family: var(--ffm); }
.stat-lbl { font-size: 9px; color: var(--txt2); text-transform: uppercase; letter-spacing: .08em; }
.gcode-box { flex: 1; overflow-y: auto; padding: 8px 10px; background: var(--bg); font-family: var(--ffm); font-size: 10.5px; line-height: 1.8; }
.gcode-box::-webkit-scrollbar { width: 3px; }
.gcode-box::-webkit-scrollbar-thumb { background: var(--border-lit); }
.gc-line { display: flex; gap: 8px; }
.gc-n { color: var(--txt2); min-width: 22px; text-align: right; }
.gc-cmd { color: #4A90E2; font-weight: 500; min-width: 28px; }
.gc-arg { color: var(--txt1); }
.gc-comment { color: var(--txt2); }
.gc-line.highlight .gc-cmd { color: var(--accent); }
</style>
