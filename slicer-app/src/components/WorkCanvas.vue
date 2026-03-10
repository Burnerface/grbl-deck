<template>
  <div class="canvas-wrap" ref="wrapRef"
    @dragover.prevent="isDragging = true"
    @dragleave="isDragging = false"
    @drop.prevent="onDrop"
    @wheel.prevent="onWheel"
    @contextmenu.prevent="showCtxMenu"
  >
    <!-- Toolbar outils -->
    <div class="tools-bar">
      <div class="tool-grp">
        <button v-for="t in tools" :key="t.id"
          class="tool-btn" :class="{ active: activeTool === t.id }"
          :title="t.label + ' (' + t.key + ')'"
          @click="setTool(t.id)">
          {{ t.icon }}
        </button>
      </div>
      <div class="tool-sep"></div>
      <div class="tool-grp">
        <button class="tool-btn" title="Annuler (Ctrl+Z)" @click="undo">↩</button>
        <button class="tool-btn" title="Refaire (Ctrl+Y)" @click="redo">↪</button>
        <button class="tool-btn" title="Tout sélectionner" @click="selectAll">⊞</button>
        <button class="tool-btn" title="Supprimer" @click="deleteSelected">🗑</button>
      </div>
      <div class="tool-sep"></div>
      <!-- Coords objet -->
      <div class="coords-bar">
        <div class="coord-field" v-for="f in coordFields" :key="f.k">
          <span class="coord-lbl">{{ f.label }}</span>
          <input class="coord-inp" type="number" :step="f.step || 0.1"
            :value="coords[f.k]"
            @change="onCoordChange(f.k, $event.target.value)"/>
          <span class="coord-unit">{{ f.unit }}</span>
        </div>
      </div>
      <div class="tool-sep"></div>
      <div class="tool-grp" style="margin-left:auto">
        <button class="tool-btn" title="Ajuster la vue" @click="fitView">⊡</button>
        <div class="zoom-display" @click="resetZoom">{{ zoomPct }}%</div>
      </div>
    </div>

    <!-- Canvas Fabric.js -->
    <div class="canvas-inner" ref="innerRef">
      <canvas ref="canvasEl"></canvas>
    </div>

    <!-- Drag overlay -->
    <Transition name="fade">
      <div v-if="isDragging" class="drop-overlay">
        <div class="drop-card">
          <span class="drop-icon">📂</span>
          <p class="drop-title">Déposer ici</p>
          <p class="drop-sub">SVG · PNG · JPG</p>
        </div>
      </div>
    </Transition>

    <!-- Badge plateau -->
    <div class="bed-badge">Plateau 600 × 400 mm</div>

    <!-- Zoom FAB -->
    <div class="zoom-fab">
      <button @click="zoomIn">+</button>
      <button @click="zoomOut">−</button>
      <button @click="fitView">⊡</button>
    </div>

    <!-- Modes vue -->
    <div class="view-modes">
      <button v-for="m in viewModes" :key="m.id"
        :class="{ active: viewMode === m.id }"
        @click="viewMode = m.id">
        {{ m.icon }} {{ m.label }}
      </button>
    </div>

    <!-- Context menu -->
    <div v-if="ctxVisible" class="ctx-menu"
      :style="{ left: ctxX + 'px', top: ctxY + 'px' }"
      @mouseleave="ctxVisible = false">
      <div class="ctx-item" @click="duplicateSelected">⧉ Dupliquer</div>
      <div class="ctx-item" @click="assignLayer">🏷 Assigner couche</div>
      <div class="ctx-sep"></div>
      <div class="ctx-item" @click="bringFront">⬆ Premier plan</div>
      <div class="ctx-item" @click="sendBack">⬇ Arrière-plan</div>
      <div class="ctx-sep"></div>
      <div class="ctx-item danger" @click="deleteSelected">🗑 Supprimer</div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import * as fabric from 'fabric'

// ── Props & Emits ──────────────────────────────────────────
const props = defineProps({
  activeTool: { type: String, default: 'select' },
  activeLayer: { type: Object, default: null },
  theme: { type: String, default: 'dark' },
})

const emit = defineEmits(['objects-changed', 'selection-changed', 'coords-changed'])

// ── Constantes ─────────────────────────────────────────────
const PX = 1.5        // px par mm
const BED_W_MM = 600
const BED_H_MM = 400
const BED_W = BED_W_MM * PX
const BED_H = BED_H_MM * PX

// ── Refs DOM ───────────────────────────────────────────────
const wrapRef   = ref(null)
const innerRef  = ref(null)
const canvasEl  = ref(null)

// ── État ───────────────────────────────────────────────────
let fc = null
let bed = null
const isDragging = ref(false)
const viewMode   = ref('design')
const zoomLevel  = ref(1)
const zoomPct    = computed(() => Math.round(zoomLevel.value * 100))
const coords     = ref({ x: 0, y: 0, w: 0, h: 0, r: 0 })

// Undo/Redo
const undoStack = []
const redoStack = []

// Dessin
let isDrawing = false, drawObj = null, drawStart = { x: 0, y: 0 }
let isPanning = false, lastPt = { x: 0, y: 0 }

// Context menu
const ctxVisible = ref(false)
const ctxX = ref(0), ctxY = ref(0)

// ── Outils ─────────────────────────────────────────────────
const activeTool = ref('select')
const tools = [
  { id: 'select', icon: '↖', label: 'Sélectionner', key: 'V' },
  { id: 'rect',   icon: '▭', label: 'Rectangle',    key: 'R' },
  { id: 'circle', icon: '○', label: 'Ellipse',       key: 'E' },
  { id: 'line',   icon: '╱', label: 'Ligne',         key: 'L' },
  { id: 'text',   icon: 'T', label: 'Texte',         key: 'T' },
  { id: 'pan',    icon: '✋', label: 'Déplacer vue',  key: 'Space' },
]

const coordFields = [
  { k: 'x', label: 'X', unit: 'mm', step: 0.1 },
  { k: 'y', label: 'Y', unit: 'mm', step: 0.1 },
  { k: 'w', label: 'W', unit: 'mm', step: 0.1 },
  { k: 'h', label: 'H', unit: 'mm', step: 0.1 },
  { k: 'r', label: '∠', unit: '°',  step: 1   },
]

const viewModes = [
  { id: 'design',  icon: '🎨', label: 'Design' },
  { id: 'preview', icon: '👁',  label: 'Aperçu' },
  { id: 'gcode',   icon: '⚡', label: 'GCode'  },
]

// ── Init ───────────────────────────────────────────────────
onMounted(() => {
  initCanvas()
  window.addEventListener('resize', onResize)
  window.addEventListener('keydown', onKey)
  document.addEventListener('click', hideCtx)
})

onUnmounted(() => {
  fc?.dispose()
  window.removeEventListener('resize', onResize)
  window.removeEventListener('keydown', onKey)
  document.removeEventListener('click', hideCtx)
})

function initCanvas() {
  const wrap = wrapRef.value
  fc = new fabric.Canvas(canvasEl.value, {
    width:  wrap.clientWidth,
    height: wrap.clientHeight - 40, // moins toolbar
    selection: true,
    preserveObjectStacking: true,
    backgroundColor: 'transparent',
    fireMiddleClick: true,
  })

  // Plateau
  bed = new fabric.Rect({
    left: 0, top: 0, width: BED_W, height: BED_H,
    fill: props.theme === 'dark' ? '#1E1F22' : '#F8F8FA',
    stroke: '#E8590C', strokeWidth: 1.5,
    selectable: false, evented: false, id: '__bed__',
  })
  fc.add(bed)
  drawGrid()
  bindEvents()
  fitView()

  // Objets de démo
  addDemo()
}

function addDemo() {
  const r = new fabric.Rect({
    left: 60, top: 80, width: 180, height: 120,
    fill: 'rgba(232,89,12,0.08)', stroke: '#E8590C', strokeWidth: 1.5,
    id: `obj_${Date.now()}`,
  })
  const t = new fabric.IText('Texte gravure', {
    left: 60, top: 230, fontSize: 22,
    fill: '#0BBFA8', fontFamily: 'DM Sans, sans-serif',
    id: `obj_${Date.now() + 1}`,
  })
  const e = new fabric.Ellipse({
    left: 320, top: 100, rx: 60, ry: 40,
    fill: 'rgba(11,191,168,0.08)', stroke: '#0BBFA8', strokeWidth: 1.5,
    id: `obj_${Date.now() + 2}`,
  })
  fc.add(r, t, e)
  fc.renderAll()
  emitObjects()
}

// ── Grille ─────────────────────────────────────────────────
function drawGrid() {
  fc.getObjects().filter(o => o.isGrid).forEach(o => fc.remove(o))
  const minor = 10 * PX, major = 50 * PX
  const dark = props.theme === 'dark'
  const cm = dark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.05)'
  const cM = dark ? 'rgba(255,255,255,0.09)' : 'rgba(0,0,0,0.09)'
  for (let x = 0; x <= BED_W; x += minor)
    fc.add(new fabric.Line([x,0,x,BED_H], { stroke: x%major===0?cM:cm, strokeWidth:1, selectable:false, evented:false, isGrid:true }))
  for (let y = 0; y <= BED_H; y += minor)
    fc.add(new fabric.Line([0,y,BED_W,y], { stroke: y%major===0?cM:cm, strokeWidth:1, selectable:false, evented:false, isGrid:true }))
  fc.sendToBack(bed)
  fc.renderAll()
}

// ── Events Fabric ──────────────────────────────────────────
function bindEvents() {
  fc.on('mouse:down', e => {
    const me = e.e
    if (me.altKey || activeTool.value === 'pan') {
      isPanning = true; lastPt = { x: me.clientX, y: me.clientY }
      fc.defaultCursor = 'grabbing'; return
    }
    if (['rect','circle','line'].includes(activeTool.value)) {
      isDrawing = true
      drawStart = fc.getPointer(me)
      const col = props.activeLayer?.color || '#E8590C'
      if (activeTool.value === 'rect') {
        drawObj = new fabric.Rect({ left:drawStart.x, top:drawStart.y, width:0, height:0, fill:col+'18', stroke:col, strokeWidth:1.5, selectable:false })
      } else if (activeTool.value === 'circle') {
        drawObj = new fabric.Ellipse({ left:drawStart.x, top:drawStart.y, rx:0, ry:0, fill:col+'18', stroke:col, strokeWidth:1.5, selectable:false })
      } else if (activeTool.value === 'line') {
        drawObj = new fabric.Line([drawStart.x,drawStart.y,drawStart.x,drawStart.y], { stroke:col, strokeWidth:2, selectable:false })
      }
      if (drawObj) fc.add(drawObj)
    }
  })

  fc.on('mouse:move', e => {
    const me = e.e
    const pt = fc.getPointer(me)
    emit('coords-changed', { cursor: { x: +(pt.x/PX).toFixed(1), y: +(pt.y/PX).toFixed(1) } })

    if (isPanning) {
      const vpt = fc.viewportTransform
      vpt[4] += me.clientX - lastPt.x
      vpt[5] += me.clientY - lastPt.y
      lastPt = { x: me.clientX, y: me.clientY }
      fc.renderAll(); return
    }
    if (!isDrawing || !drawObj) return
    const dx = pt.x - drawStart.x, dy = pt.y - drawStart.y
    if (drawObj.type === 'rect') drawObj.set({ left:Math.min(pt.x,drawStart.x), top:Math.min(pt.y,drawStart.y), width:Math.abs(dx), height:Math.abs(dy) })
    else if (drawObj.type === 'ellipse') drawObj.set({ left:Math.min(pt.x,drawStart.x), top:Math.min(pt.y,drawStart.y), rx:Math.abs(dx)/2, ry:Math.abs(dy)/2 })
    else if (drawObj.type === 'line') drawObj.set({ x2:pt.x, y2:pt.y })
    fc.renderAll()
  })

  fc.on('mouse:up', () => {
    if (isPanning) { isPanning = false; fc.defaultCursor = 'default' }
    if (isDrawing && drawObj) {
      drawObj.set({ selectable: true })
      drawObj.id = `obj_${Date.now()}`
      fc.setActiveObject(drawObj)
      pushUndo()
      setTool('select')
      isDrawing = false; drawObj = null
    }
  })

  fc.on('mouse:dblclick', e => {
    if (activeTool.value !== 'text') return
    const pt = fc.getPointer(e.e)
    const t = new fabric.IText('Texte', {
      left: pt.x, top: pt.y, fontSize: 20,
      fill: props.activeLayer?.color || '#E8590C',
      fontFamily: 'DM Sans, sans-serif',
      id: `obj_${Date.now()}`,
    })
    fc.add(t); fc.setActiveObject(t); t.enterEditing()
    setTool('select')
  })

  fc.on('selection:created', syncSelection)
  fc.on('selection:updated', syncSelection)
  fc.on('selection:cleared', () => {
    emit('selection-changed', null)
    coords.value = { x:0, y:0, w:0, h:0, r:0 }
  })
  fc.on('object:modified', () => { pushUndo(); emitObjects(); syncSelection() })
}

function syncSelection() {
  const obj = fc.getActiveObject()
  if (!obj || obj.id === '__bed__') return
  const c = {
    x: +(obj.left/PX).toFixed(2),
    y: +(obj.top/PX).toFixed(2),
    w: +(obj.getScaledWidth()/PX).toFixed(2),
    h: +(obj.getScaledHeight()/PX).toFixed(2),
    r: +(obj.angle||0).toFixed(1),
  }
  coords.value = c
  emit('selection-changed', { id: obj.id, ...c })
  emit('coords-changed', { selection: c })
}

function emitObjects() {
  const objs = fc.getObjects()
    .filter(o => o.id && o.id !== '__bed__' && !o.isGrid)
    .map(o => ({
      id: o.id,
      type: o.type,
      w: +(o.getScaledWidth()/PX).toFixed(1),
      h: +(o.getScaledHeight()/PX).toFixed(1),
    }))
  emit('objects-changed', objs)
}

// ── Outils ─────────────────────────────────────────────────
function setTool(t) {
  activeTool.value = t
  if (t === 'select') {
    fc.selection = true; fc.defaultCursor = 'default'
    fc.getObjects().forEach(o => { if (o.id !== '__bed__' && !o.isGrid) o.selectable = true })
  } else {
    fc.selection = false; fc.defaultCursor = 'crosshair'
    fc.discardActiveObject(); fc.renderAll()
  }
}

// ── Zoom ───────────────────────────────────────────────────
function zoomIn()  { applyZoom(zoomLevel.value * 1.15) }
function zoomOut() { applyZoom(zoomLevel.value / 1.15) }
function resetZoom() { applyZoom(1) }

function applyZoom(z, center) {
  z = Math.max(0.05, Math.min(10, z))
  zoomLevel.value = z
  if (center) fc.zoomToPoint(new fabric.Point(center.x, center.y), z)
  else {
    const w = wrapRef.value.clientWidth, h = wrapRef.value.clientHeight
    fc.zoomToPoint(new fabric.Point(w/2, (h-40)/2), z)
  }
  emit('coords-changed', { zoom: z })
  fc.renderAll()
}

function onWheel(e) {
  applyZoom(zoomLevel.value * (e.deltaY > 0 ? 0.9 : 1.1), { x: e.offsetX, y: e.offsetY - 40 })
}

function fitView() {
  const w = wrapRef.value.clientWidth - 80
  const h = wrapRef.value.clientHeight - 80 - 40
  const z = Math.min(w/BED_W, h/BED_H, 1)
  zoomLevel.value = z
  fc.setZoom(z)
  fc.viewportTransform = [z,0,0,z,(wrapRef.value.clientWidth-BED_W*z)/2,(wrapRef.value.clientHeight-40-BED_H*z)/2]
  emit('coords-changed', { zoom: z })
  fc.renderAll()
}

// ── Undo/Redo ──────────────────────────────────────────────
function pushUndo() {
  undoStack.push(JSON.stringify(fc.toJSON(['id','isGrid'])))
  redoStack.length = 0
}
function undo() {
  if (!undoStack.length) return
  redoStack.push(JSON.stringify(fc.toJSON(['id','isGrid'])))
  fc.loadFromJSON(undoStack.pop(), () => { fc.renderAll(); emitObjects() })
}
function redo() {
  if (!redoStack.length) return
  undoStack.push(JSON.stringify(fc.toJSON(['id','isGrid'])))
  fc.loadFromJSON(redoStack.pop(), () => { fc.renderAll(); emitObjects() })
}

// ── Actions ────────────────────────────────────────────────
function selectAll() { fc.discardActiveObject(); fc.renderAll() }

function deleteSelected() {
  const obj = fc.getActiveObject()
  if (!obj || obj.id === '__bed__') return
  if (obj.type === 'activeSelection') obj.getObjects().forEach(o => fc.remove(o))
  else fc.remove(obj)
  fc.discardActiveObject(); fc.renderAll()
  pushUndo(); emitObjects()
  ctxVisible.value = false
}

function duplicateSelected() {
  const obj = fc.getActiveObject()
  if (!obj) return
  obj.clone(clone => {
    clone.set({ left: obj.left+20, top: obj.top+20, id: `obj_${Date.now()}` })
    fc.add(clone); fc.setActiveObject(clone); fc.renderAll()
    pushUndo(); emitObjects()
  })
  ctxVisible.value = false
}

function bringFront() { fc.getActiveObject()?.bringToFront(); fc.renderAll(); ctxVisible.value = false }
function sendBack()   { fc.getActiveObject()?.sendToBack();   fc.renderAll(); ctxVisible.value = false }
function assignLayer() { ctxVisible.value = false }

// ── Context menu ───────────────────────────────────────────
function showCtxMenu(e) {
  ctxX.value = e.clientX; ctxY.value = e.clientY
  ctxVisible.value = true
}
function hideCtx() { ctxVisible.value = false }

// ── Keyboard ───────────────────────────────────────────────
function onKey(e) {
  if (e.target.tagName === 'INPUT') return
  const k = e.key.toLowerCase()
  if (k === 'delete' || k === 'backspace') deleteSelected()
  if (k === 'escape') setTool('select')
  if (k === 'v') setTool('select')
  if (k === 'r') setTool('rect')
  if (k === 'e') setTool('circle')
  if (k === 'l') setTool('line')
  if (k === 't') setTool('text')
  if (k === '+') zoomIn()
  if (k === '-') zoomOut()
  if (e.ctrlKey && k === 'z') undo()
  if (e.ctrlKey && k === 'y') redo()
  if (e.ctrlKey && k === 'd') { e.preventDefault(); duplicateSelected() }
}

// ── Import ─────────────────────────────────────────────────
function onDrop(e) {
  isDragging.value = false
  importFile(e.dataTransfer?.files[0])
}

function importFile(file) {
  if (!file) return
  const ext = file.name.split('.').pop().toLowerCase()
  const reader = new FileReader()

  if (['png','jpg','jpeg','webp'].includes(ext)) {
    reader.onload = ev => {
      fabric.Image.fromURL(ev.target.result, img => {
        img.scaleToWidth(Math.min(BED_W * 0.5, img.width))
        img.set({ left: 40, top: 40, id: `img_${Date.now()}` })
        fc.add(img); fc.setActiveObject(img); fc.renderAll()
        pushUndo(); emitObjects()
      })
    }
    reader.readAsDataURL(file)
  } else if (ext === 'svg') {
    reader.onload = ev => {
      fabric.loadSVGFromString(ev.target.result, (objs, opts) => {
        const g = fabric.util.groupSVGElements(objs, opts)
        if (g.width > BED_W * 0.6) g.scaleToWidth(BED_W * 0.6)
        g.set({ left: 40, top: 40, id: `svg_${Date.now()}` })
        fc.add(g); fc.setActiveObject(g); fc.renderAll()
        pushUndo(); emitObjects()
      })
    }
    reader.readAsText(file)
  }
}

// ── Resize ─────────────────────────────────────────────────
function onResize() {
  if (!fc || !wrapRef.value) return
  fc.setWidth(wrapRef.value.clientWidth)
  fc.setHeight(wrapRef.value.clientHeight - 40)
  fc.renderAll()
}

// ── Watchers ───────────────────────────────────────────────
watch(() => props.theme, () => {
  if (!fc || !bed) return
  bed.set({ fill: props.theme === 'dark' ? '#1E1F22' : '#F8F8FA' })
  fc.backgroundColor = props.theme === 'dark' ? '#141517' : '#E4E4E8'
  drawGrid()
})

// ── Expose ─────────────────────────────────────────────────
function applyCoords(c) {
  const obj = fc.getActiveObject()
  if (!obj) return
  if (c.x !== undefined) obj.set('left', c.x * PX)
  if (c.y !== undefined) obj.set('top',  c.y * PX)
  if (c.w !== undefined) obj.scaleToWidth(c.w * PX)
  if (c.h !== undefined) obj.scaleToHeight(c.h * PX)
  if (c.r !== undefined) obj.set('angle', c.r)
  fc.renderAll(); pushUndo()
}
function selectById(id) {
  const obj = fc.getObjects().find(o => o.id === id)
  if (obj) { fc.setActiveObject(obj); fc.renderAll() }
}
function deleteById(id) {
  const obj = fc.getObjects().find(o => o.id === id)
  if (obj) { fc.remove(obj); fc.renderAll(); pushUndo(); emitObjects() }
}
function onCoordChange(k, v) {
  const c = { ...coords.value, [k]: parseFloat(v) }
  coords.value = c
  applyCoords(c)
}

defineExpose({ fitView, zoomIn, zoomOut, importFile, applyCoords, selectById, deleteById })
</script>

<style scoped>
.canvas-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  background-color: var(--canvas-bg);
  background-image:
    linear-gradient(var(--grid-minor) 1px, transparent 1px),
    linear-gradient(90deg, var(--grid-minor) 1px, transparent 1px),
    linear-gradient(var(--grid-major) 1px, transparent 1px),
    linear-gradient(90deg, var(--grid-major) 1px, transparent 1px);
  background-size: 10px 10px, 10px 10px, 50px 50px, 50px 50px;
}

/* Toolbar outils */
.tools-bar {
  height: 40px;
  background: var(--bg-panel);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 10px;
  gap: 3px;
  flex-shrink: 0;
  z-index: 10;
}

.tool-grp { display: flex; align-items: center; gap: 2px; }
.tool-sep { width: 1px; height: 20px; background: var(--border); margin: 0 6px; }

.tool-btn {
  width: 30px; height: 30px;
  border-radius: 5px;
  background: none;
  color: var(--txt1);
  font-size: 14px;
  display: flex; align-items: center; justify-content: center;
  transition: all .12s;
  position: relative;
}
.tool-btn:hover { background: var(--bg-hover); color: var(--txt0); }
.tool-btn.active { background: var(--accent-soft); color: var(--accent); }

.tool-btn[title]:hover::after {
  content: attr(title);
  position: absolute;
  top: calc(100% + 6px);
  left: 50%; transform: translateX(-50%);
  background: var(--bg-card);
  border: 1px solid var(--border-lit);
  color: var(--txt0);
  font-size: 11px; padding: 3px 8px;
  border-radius: 4px; white-space: nowrap;
  z-index: 100; pointer-events: none;
}

/* Coords */
.coords-bar { display: flex; align-items: center; gap: 5px; }
.coord-field {
  display: flex; align-items: center; gap: 3px;
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: 4px; padding: 0 7px; height: 28px;
}
.coord-lbl  { font-size: 10px; color: var(--txt2); font-family: var(--ffm); min-width: 10px; }
.coord-inp  { width: 52px; background: none; border: none; color: var(--txt0); font-size: 11.5px; text-align: right; font-family: var(--ffm); }
.coord-unit { font-size: 10px; color: var(--txt2); }
.zoom-display {
  font-family: var(--ffm); font-size: 11px; color: var(--txt1);
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: 4px; padding: 4px 10px; min-width: 52px; text-align: center; cursor: pointer;
}

/* Canvas inner */
.canvas-inner { flex: 1; position: relative; overflow: hidden; }

/* Drop overlay */
.drop-overlay {
  position: absolute; inset: 0;
  background: rgba(232,89,12,0.06);
  border: 2px dashed var(--accent);
  display: flex; align-items: center; justify-content: center;
  z-index: 50; pointer-events: none;
}
.drop-card { background: var(--bg-card); border: 1px solid var(--border-lit); border-radius: 12px; padding: 28px 48px; text-align: center; }
.drop-icon { font-size: 36px; display: block; margin-bottom: 10px; }
.drop-title { font-size: 15px; font-weight: 600; color: var(--txt0); }
.drop-sub   { font-size: 12px; color: var(--txt2); margin-top: 4px; }

/* Badge + FAB */
.bed-badge {
  position: absolute; bottom: 12px; left: 50%; transform: translateX(-50%);
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: 20px; padding: 4px 14px;
  font-size: 11px; color: var(--txt2); font-family: var(--ffm);
  pointer-events: none; z-index: 10;
}
.zoom-fab { position: absolute; bottom: 16px; right: 16px; display: flex; flex-direction: column; gap: 3px; z-index: 20; }
.zoom-fab button {
  width: 32px; height: 32px; border-radius: 7px;
  background: var(--bg-card); border: 1px solid var(--border);
  color: var(--txt1); font-size: 16px;
  display: flex; align-items: center; justify-content: center;
  transition: all .12s;
}
.zoom-fab button:hover { border-color: var(--border-lit); color: var(--txt0); }

/* Vue modes */
.view-modes { position: absolute; bottom: 16px; left: 16px; display: flex; gap: 4px; z-index: 20; }
.view-modes button {
  height: 28px; padding: 0 12px; border-radius: 5px;
  background: var(--bg-card); border: 1px solid var(--border);
  color: var(--txt1); font-size: 11.5px; transition: all .12s;
}
.view-modes button:hover { border-color: var(--border-lit); color: var(--txt0); }
.view-modes button.active { background: var(--accent-soft); border-color: var(--accent); color: var(--accent); }

/* Context menu */
.ctx-menu {
  position: fixed; background: var(--bg-card); border: 1px solid var(--border-lit);
  border-radius: 8px; padding: 5px; box-shadow: 0 8px 32px rgba(0,0,0,.4);
  z-index: 9999; min-width: 170px;
}
.ctx-item { padding: 7px 12px; border-radius: 4px; font-size: 12.5px; color: var(--txt1); cursor: pointer; transition: all .1s; }
.ctx-item:hover { background: var(--bg-hover); color: var(--txt0); }
.ctx-item.danger:hover { background: rgba(239,68,68,.1); color: var(--red); }
.ctx-sep { height: 1px; background: var(--border); margin: 4px 0; }

/* Transitions */
.fade-enter-active, .fade-leave-active { transition: opacity .2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
