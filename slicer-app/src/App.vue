<template>
  <div class="app" :data-theme="theme">
    <TopBar
      :theme="theme"
      @toggle-theme="toggleTheme"
      @import-file="triggerImport"
      @generate="generateGcode"
    />
    <div class="app-body">
      <PanelLeft
        :objects="objects"
        :layers="layers"
        :selected-id="selectedId"
        @select="selectObject"
        @delete="deleteObject"
        @add-layer="addLayer"
        @select-layer="selectLayer"
      />
      <WorkCanvas
        ref="canvasRef"
        :active-tool="activeTool"
        :active-layer="activeLayer"
        :theme="theme"
        @objects-changed="onObjectsChanged"
        @selection-changed="onSelectionChanged"
        @coords-changed="onCoordsChanged"
      />
      <PanelRight
        :active-layer="activeLayer"
        :selected-coords="selectedCoords"
        :gcode-preview="gcodePreview"
        :gcode-stats="gcodeStats"
        @update-layer="updateLayer"
        @update-coords="updateCoords"
        @send="sendToGrblDeck"
      />
    </div>
    <StatusBar
      :cursor="cursor"
      :zoom="zoom"
      :selected-info="selectedInfo"
      :objects-count="objects.length"
      :layers-count="layers.length"
    />
    <input
      ref="fileInput"
      type="file"
      accept=".svg,.png,.jpg,.jpeg,.dxf"
      style="display:none"
      @change="onFileSelected"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import TopBar from './components/TopBar.vue'
import PanelLeft from './components/PanelLeft.vue'
import WorkCanvas from './components/WorkCanvas.vue'
import PanelRight from './components/PanelRight.vue'
import StatusBar from './components/StatusBar.vue'

// ── Thème ──────────────────────────────────────────────────
const theme = ref('dark')
function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
}

// ── Outil actif ────────────────────────────────────────────
const activeTool = ref('select')

// ── Canvas ref ─────────────────────────────────────────────
const canvasRef = ref(null)

// ── Objets sur le canvas ───────────────────────────────────
const objects = ref([])
const selectedId = ref(null)
const selectedCoords = ref({ x: 0, y: 0, w: 0, h: 0, r: 0 })
const cursor = ref({ x: 0, y: 0 })
const zoom = ref(100)
const selectedInfo = ref('')

function onObjectsChanged(objs) { objects.value = objs }
function onSelectionChanged(obj) {
  selectedId.value = obj?.id || null
  selectedInfo.value = obj ? `${obj.w}×${obj.h} mm` : ''
}
function onCoordsChanged(c) {
  if (c.cursor) cursor.value = c.cursor
  if (c.zoom)   zoom.value   = Math.round(c.zoom * 100)
  if (c.selection) selectedCoords.value = c.selection
}
function updateCoords(coords) {
  canvasRef.value?.applyCoords(coords)
}

// ── Couches ────────────────────────────────────────────────
const layers = ref([
  { id: 'l1', name: 'Gravure',   color: '#E8590C', mode: 'fill', power: 75, speed: 3000, passes: 1, interval: 0.1, frequency: 20 },
  { id: 'l2', name: 'Score',     color: '#F59E0B', mode: 'line', power: 40, speed: 5000, passes: 1, interval: 0.1, frequency: 20 },
  { id: 'l3', name: 'Découpe',   color: '#EF4444', mode: 'cut',  power: 95, speed: 800,  passes: 3, interval: 0.1, frequency: 20 },
])
const activeLayerId = ref('l1')
const activeLayer = computed(() => layers.value.find(l => l.id === activeLayerId.value))

function selectLayer(id) { activeLayerId.value = id }
function addLayer() {
  const id = `l${Date.now()}`
  layers.value.push({ id, name: `Couche ${layers.value.length + 1}`, color: '#0BBFA8', mode: 'line', power: 50, speed: 3000, passes: 1, interval: 0.1, frequency: 20 })
  activeLayerId.value = id
}
function updateLayer(updated) {
  const idx = layers.value.findIndex(l => l.id === updated.id)
  if (idx !== -1) layers.value[idx] = { ...layers.value[idx], ...updated }
}

// ── Objets ─────────────────────────────────────────────────
function selectObject(id) { canvasRef.value?.selectById(id) }
function deleteObject(id) { canvasRef.value?.deleteById(id) }

// ── Import ─────────────────────────────────────────────────
const fileInput = ref(null)
function triggerImport() { fileInput.value?.click() }
function onFileSelected(e) {
  const file = e.target.files[0]
  if (file) canvasRef.value?.importFile(file)
  e.target.value = ''
}

// ── GCode ──────────────────────────────────────────────────
const gcodePreview = ref([
  { n: 1,  cmd: '',    args: '',                    comment: '; GRBLDeck Slicer' },
  { n: 2,  cmd: 'G21', args: '',                    comment: '; unités mm' },
  { n: 3,  cmd: 'G90', args: '',                    comment: '; coordonnées absolues' },
  { n: 4,  cmd: 'M3',  args: ' S0',                 comment: '; laser ON' },
  { n: 5,  cmd: 'G0',  args: ' X0.00 Y0.00',        comment: '' },
  { n: 6,  cmd: 'M3',  args: ' S191',               comment: '; 75%' },
  { n: 7,  cmd: 'G1',  args: ' X120.00 Y0.00 F3000', comment: '' },
  { n: 8,  cmd: 'G1',  args: ' X120.00 Y80.00',     comment: '' },
  { n: 9,  cmd: 'M5',  args: '',                    comment: '; laser OFF' },
  { n: 10, cmd: 'G0',  args: ' X0.00 Y0.00',        comment: '; retour origine' },
])
const gcodeStats = ref({ lines: 2847, time: '14:23', dist: '48.2m' })

function generateGcode() {
  gcodeStats.value = {
    lines: Math.floor(Math.random() * 3000) + 500,
    time: `${Math.floor(Math.random() * 20) + 2}:${String(Math.floor(Math.random() * 60)).padStart(2,'0')}`,
    dist: `${(Math.random() * 60 + 10).toFixed(1)}m`,
  }
}

function sendToGrblDeck() {
  fetch('http://192.168.1.168:8086/api/files/upload', {
    method: 'POST',
    body: JSON.stringify({ gcode: gcodePreview.value }),
    headers: { 'Content-Type': 'application/json' },
  })
  .then(() => alert('✅ Envoyé vers GRBLDeck !'))
  .catch(() => alert('❌ Erreur de connexion au backend'))
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

:root {
  --ff: 'DM Sans', sans-serif;
  --ffm: 'DM Mono', monospace;
  --accent: #E8590C;
  --accent-soft: rgba(232,89,12,0.12);
  --accent-glow: rgba(232,89,12,0.30);
  --teal: #0BBFA8;
  --teal-soft: rgba(11,191,168,0.12);
  --green: #22C55E;
  --yellow: #F59E0B;
  --red: #EF4444;
}

[data-theme="dark"] {
  --bg: #1A1B1E; --bg-panel: #222327; --bg-card: #2A2B2F;
  --bg-input: #1A1B1E; --bg-hover: rgba(255,255,255,.05);
  --border: rgba(255,255,255,.08); --border-lit: rgba(255,255,255,.14);
  --txt0: #F1F2F5; --txt1: #A8AAB2; --txt2: #5E6070;
  --canvas-bg: #141517; --bed-fill: #1E1F22;
  --grid-minor: rgba(255,255,255,0.04); --grid-major: rgba(255,255,255,0.09);
}

[data-theme="light"] {
  --bg: #F0F0F2; --bg-panel: #FAFAFA; --bg-card: #FFFFFF;
  --bg-input: #F4F4F6; --bg-hover: rgba(0,0,0,.04);
  --border: rgba(0,0,0,.09); --border-lit: rgba(0,0,0,.16);
  --txt0: #1A1B1E; --txt1: #5E6070; --txt2: #9EA0AC;
  --canvas-bg: #E4E4E8; --bed-fill: #F8F8FA;
  --grid-minor: rgba(0,0,0,0.05); --grid-major: rgba(0,0,0,0.09);
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, #app { height: 100%; overflow: hidden; }

.app {
  font-family: var(--ff);
  font-size: 13px;
  background: var(--bg);
  color: var(--txt0);
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: background .2s, color .2s;
}

.app-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

button { font-family: var(--ff); cursor: pointer; border: none; outline: none; }
input, select { font-family: var(--ffm); outline: none; }
</style>
