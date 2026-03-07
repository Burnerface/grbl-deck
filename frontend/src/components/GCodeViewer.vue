<template>
  <v-card color="surface-variant" rounded="lg" elevation="0" style="height: 100%;">
    <v-card-title class="text-caption text-medium-emphasis py-2 px-3 d-flex align-center">
      <v-icon size="small" class="mr-1">mdi-vector-polyline</v-icon>
      VISUALISEUR GCODE
      <v-spacer />
      <!-- Info fichier chargé -->
      <span v-if="fichierCharge" class="text-caption text-primary mr-2">{{ fichierCharge }}</span>
      <!-- Progression -->
      <span v-if="store.status.job.actif" class="text-caption text-success mr-2">
        {{ store.status.job.progression }}%
      </span>
      <v-btn icon="mdi-magnify-minus" variant="text" size="x-small" @click="zoom(0.8)" />
      <v-btn icon="mdi-magnify-plus" variant="text" size="x-small" @click="zoom(1.25)" />
      <v-btn icon="mdi-fit-to-screen" variant="text" size="x-small" @click="resetView" />
    </v-card-title>

    <v-divider />

    <!-- Barre progression -->
    <v-progress-linear
      v-if="store.status.job.actif"
      :model-value="store.status.job.progression"
      color="primary"
      height="2"
    />

    <!-- Canvas -->
    <div ref="containerRef" class="canvas-container">
      <canvas
        ref="canvasRef"
        @wheel.prevent="onWheel"
        @mousedown="onMouseDown"
        @mousemove="onMouseMove"
        @mouseup="onMouseUp"
        @mouseleave="onMouseUp"
      />
      <div v-if="!gcodeLines.length" class="canvas-empty text-medium-emphasis text-caption">
        <v-icon size="32" class="mb-2">mdi-file-outline</v-icon>
        <div>Chargez un fichier GCode</div>
      </div>
    </div>
  </v-card>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useMachineStore } from '../stores/machine'

const store = useMachineStore()

// ─── Refs ─────────────────────────────────────────────────────────────────
const canvasRef = ref(null)
const containerRef = ref(null)
const gcodeLines = ref([])
const fichierCharge = ref(null)

// ─── Viewport ─────────────────────────────────────────────────────────────
let scale = 1
let offsetX = 0
let offsetY = 0
let isDragging = false
let dragStart = { x: 0, y: 0 }

// ─── Path parsé ───────────────────────────────────────────────────────────
let parsedPaths = []  // [{ x, y, isMove }]
let bounds = { minX: 0, maxX: 100, minY: 0, maxY: 100 }

// ─── Position tête (depuis WS) ────────────────────────────────────────────
let headPosition = { x: 0, y: 0 }
let rafPending = false

// ─── ResizeObserver ───────────────────────────────────────────────────────
let resizeObserver = null

onMounted(() => {
  resizeObserver = new ResizeObserver(() => redraw())
  if (containerRef.value) resizeObserver.observe(containerRef.value)
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
})

// ─── Charger GCode ────────────────────────────────────────────────────────
async function chargerGCode(filename) {
  fichierCharge.value = filename
  const content = await store.contenuFichier(filename)
  gcodeLines.value = content.split('\n')
  parseGCode(gcodeLines.value)
  resetView()
}

// Exposer pour FileManager
defineExpose({ chargerGCode })

function parseGCode(lines) {
  parsedPaths = []
  let cx = 0, cy = 0
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity

  for (const raw of lines) {
    const line = raw.split(';')[0].trim().toUpperCase()
    if (!line) continue

    const isG0 = line.startsWith('G0') || line.startsWith('G00')
    const isG1 = line.startsWith('G1') || line.startsWith('G01')
    const isG2 = line.startsWith('G2') || line.startsWith('G02')
    const isG3 = line.startsWith('G3') || line.startsWith('G03')

    if (isG0 || isG1 || isG2 || isG3) {
      const mx = line.match(/X([-\d.]+)/)
      const my = line.match(/Y([-\d.]+)/)
      if (mx) cx = parseFloat(mx[1])
      if (my) cy = parseFloat(my[1])

      parsedPaths.push({ x: cx, y: cy, isMove: isG0 })
      minX = Math.min(minX, cx)
      maxX = Math.max(maxX, cx)
      minY = Math.min(minY, cy)
      maxY = Math.max(maxY, cy)
    }
  }

  if (parsedPaths.length) {
    bounds = { minX, maxX, minY, maxY }
  }
}

// ─── Dessin ───────────────────────────────────────────────────────────────
function redraw() {
  const canvas = canvasRef.value
  const container = containerRef.value
  if (!canvas || !container) return

  const w = container.clientWidth
  const h = container.clientHeight
  canvas.width = w
  canvas.height = h

  const ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, w, h)

  // Fond grille
  drawGrid(ctx, w, h)

  if (!parsedPaths.length) return

  // GCode paths
  ctx.save()
  ctx.translate(offsetX, offsetY)
  ctx.scale(scale, scale)

  const toCanvas = (x, y) => ({
    cx: x - bounds.minX,
    cy: (bounds.maxY - y),  // Inverser Y (GRBL = Y vers haut, canvas = Y vers bas)
  })

  ctx.lineWidth = 1 / scale
  ctx.lineCap = 'round'

  let inMove = true
  ctx.beginPath()

  for (let i = 0; i < parsedPaths.length; i++) {
    const p = parsedPaths[i]
    const { cx, cy } = toCanvas(p.x, p.y)

    if (p.isMove) {
      if (!inMove) {
        ctx.strokeStyle = '#00BCD4'
        ctx.stroke()
        ctx.beginPath()
      }
      ctx.strokeStyle = 'rgba(255,255,255,0.15)'
      ctx.moveTo(cx, cy)
      inMove = true
    } else {
      if (inMove) {
        ctx.stroke()
        ctx.beginPath()
        ctx.strokeStyle = '#00E676'
        inMove = false
      }
      ctx.lineTo(cx, cy)
    }
  }
  ctx.stroke()

  // Tête de gravure
  drawHead(ctx, headPosition.x, headPosition.y)

  ctx.restore()
}

function drawGrid(ctx, w, h) {
  ctx.strokeStyle = 'rgba(255,255,255,0.04)'
  ctx.lineWidth = 1
  const step = 50
  for (let x = 0; x < w; x += step) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke()
  }
  for (let y = 0; y < h; y += step) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke()
  }
}

function drawHead(ctx, x, y) {
  if (!store.status.connected) return
  const { cx, cy } = { cx: x - bounds.minX, cy: bounds.maxY - y }
  const r = 6 / scale

  ctx.beginPath()
  ctx.arc(cx, cy, r, 0, Math.PI * 2)
  ctx.fillStyle = '#FF6B35'
  ctx.fill()

  ctx.beginPath()
  ctx.moveTo(cx - r * 2, cy)
  ctx.lineTo(cx + r * 2, cy)
  ctx.moveTo(cx, cy - r * 2)
  ctx.lineTo(cx, cy + r * 2)
  ctx.strokeStyle = '#FF6B35'
  ctx.lineWidth = 1 / scale
  ctx.stroke()
}

// ─── Watch position WS (non-bloquant via RAF) ─────────────────────────────
watch(() => store.status.position, (pos) => {
  headPosition = { x: pos.x, y: pos.y }
  if (rafPending) return
  rafPending = true
  requestAnimationFrame(() => {
    redraw()
    rafPending = false
  })
}, { deep: true })

// ─── Zoom / Pan ───────────────────────────────────────────────────────────
function zoom(factor) {
  const canvas = canvasRef.value
  if (!canvas) return
  const cx = canvas.width / 2
  const cy = canvas.height / 2
  offsetX = cx - (cx - offsetX) * factor
  offsetY = cy - (cy - offsetY) * factor
  scale *= factor
  redraw()
}

function onWheel(e) {
  const factor = e.deltaY < 0 ? 1.1 : 0.9
  const rect = canvasRef.value.getBoundingClientRect()
  const mx = e.clientX - rect.left
  const my = e.clientY - rect.top
  offsetX = mx - (mx - offsetX) * factor
  offsetY = my - (my - offsetY) * factor
  scale *= factor
  redraw()
}

function onMouseDown(e) {
  isDragging = true
  dragStart = { x: e.clientX - offsetX, y: e.clientY - offsetY }
}

function onMouseMove(e) {
  if (!isDragging) return
  offsetX = e.clientX - dragStart.x
  offsetY = e.clientY - dragStart.y
  redraw()
}

function onMouseUp() {
  isDragging = false
}

function resetView() {
  const canvas = canvasRef.value
  const container = containerRef.value
  if (!canvas || !container) return

  const w = container.clientWidth
  const h = container.clientHeight
  const bw = bounds.maxX - bounds.minX || 100
  const bh = bounds.maxY - bounds.minY || 100
  const margin = 40

  scale = Math.min((w - margin * 2) / bw, (h - margin * 2) / bh)
  offsetX = margin
  offsetY = margin
  redraw()
}
</script>

<style scoped>
.canvas-container {
  position: relative;
  height: calc(100% - 48px);
  min-height: 400px;
  overflow: hidden;
}

canvas {
  display: block;
  width: 100%;
  height: 100%;
  cursor: grab;
}

canvas:active { cursor: grabbing; }

.canvas-empty {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}
</style>
