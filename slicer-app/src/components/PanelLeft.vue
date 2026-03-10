<template>
  <div class="panel-left">
    <!-- Import rapide -->
    <div class="import-bar">
      <button class="import-btn" @click="$emit('import-file')">＋ Importer</button>
    </div>

    <!-- Liste objets -->
    <div class="section-hd">
      Objets
      <span class="count-badge">{{ objects.length }}</span>
    </div>

    <div class="obj-list">
      <div v-if="objects.length === 0" class="empty-hint">
        Importe un fichier ou dessine une forme
      </div>
      <div v-for="obj in objects" :key="obj.id"
        class="obj-item" :class="{ selected: selectedId === obj.id }"
        @click="$emit('select', obj.id)">
        <div class="obj-thumb">{{ typeIcon(obj.type) }}</div>
        <div class="obj-info">
          <div class="obj-name">{{ typeName(obj.type) }}</div>
          <div class="obj-meta">{{ obj.w }} × {{ obj.h }} mm</div>
        </div>
        <div class="obj-acts">
          <button class="obj-act" @click.stop="$emit('delete', obj.id)" title="Supprimer">✕</button>
        </div>
      </div>
    </div>

    <!-- Couches -->
    <div class="layers-section">
      <div class="section-hd">
        Couches
        <button class="add-layer-btn" @click="$emit('add-layer')" title="Ajouter une couche">＋</button>
      </div>
      <div class="layer-list">
        <div v-for="layer in layers" :key="layer.id"
          class="layer-item" :class="{ active: selectedLayerId === layer.id }"
          @click="$emit('select-layer', layer.id)">
          <div class="layer-color" :style="{ background: layer.color }"></div>
          <div class="layer-label">{{ layer.name }}</div>
          <span class="layer-badge" :class="layer.mode">{{ layer.mode.toUpperCase() }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  objects: Array,
  layers: Array,
  selectedId: String,
})
defineEmits(['select', 'delete', 'add-layer', 'select-layer', 'import-file'])

const selectedLayerId = ref(props.layers?.[0]?.id)
watch(() => props.layers, l => { if (l?.length) selectedLayerId.value = l[0].id }, { immediate: true })

function typeIcon(type) {
  return { rect:'▭', ellipse:'○', line:'╱', 'i-text':'T', text:'T', group:'⊡', image:'🖼' }[type] || '◻'
}
function typeName(type) {
  return { rect:'Rectangle', ellipse:'Ellipse', line:'Ligne', 'i-text':'Texte', text:'Texte', group:'Groupe', image:'Image' }[type] || type
}
</script>

<style scoped>
.panel-left {
  width: 215px;
  background: var(--bg-panel);
  border-right: 1px solid var(--border);
  display: flex; flex-direction: column;
  flex-shrink: 0; overflow: hidden;
}

.import-bar {
  padding: 10px;
  border-bottom: 1px solid var(--border);
}
.import-btn {
  width: 100%; height: 32px;
  background: var(--accent-soft); border: 1px solid rgba(232,89,12,.25);
  color: var(--accent); border-radius: 6px;
  font-size: 12.5px; font-weight: 600;
  transition: all .15s;
}
.import-btn:hover { background: var(--accent); color: white; }

.section-hd {
  padding: 10px 12px 6px;
  font-size: 10px; font-weight: 700;
  letter-spacing: .10em; text-transform: uppercase;
  color: var(--txt2);
  display: flex; align-items: center; justify-content: space-between;
}
.count-badge {
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: 4px; padding: 1px 6px;
  font-size: 11px; color: var(--txt0); font-family: var(--ffm);
}
.add-layer-btn {
  width: 20px; height: 20px;
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: 4px; color: var(--txt1); font-size: 14px;
  display: flex; align-items: center; justify-content: center;
  transition: all .15s;
}
.add-layer-btn:hover { border-color: var(--accent); color: var(--accent); }

.obj-list {
  flex: 1; overflow-y: auto; padding: 0 8px 8px;
  min-height: 80px;
}
.obj-list::-webkit-scrollbar { width: 3px; }
.obj-list::-webkit-scrollbar-thumb { background: var(--border-lit); border-radius: 4px; }

.empty-hint {
  font-size: 11px; color: var(--txt2);
  text-align: center; padding: 20px 12px;
  line-height: 1.5;
}

.obj-item {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 8px; border-radius: 6px;
  cursor: pointer; border: 1px solid transparent;
  transition: all .12s; margin-bottom: 2px;
}
.obj-item:hover { background: var(--bg-hover); }
.obj-item.selected { background: var(--accent-soft); border-color: rgba(232,89,12,.2); }

.obj-thumb {
  width: 30px; height: 30px;
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: 5px; display: flex; align-items: center; justify-content: center;
  font-size: 14px; flex-shrink: 0;
}
.obj-info { flex: 1; min-width: 0; }
.obj-name { font-size: 12px; font-weight: 500; color: var(--txt0); }
.obj-meta { font-size: 10px; color: var(--txt2); font-family: var(--ffm); margin-top: 1px; }

.obj-acts { opacity: 0; transition: opacity .15s; }
.obj-item:hover .obj-acts { opacity: 1; }
.obj-act {
  width: 22px; height: 22px; border-radius: 4px;
  background: none; color: var(--txt2); font-size: 12px;
  display: flex; align-items: center; justify-content: center;
  transition: all .12s;
}
.obj-act:hover { background: rgba(239,68,68,.1); color: var(--red); }

/* Couches */
.layers-section { border-top: 1px solid var(--border); }
.layer-list { padding: 0 8px 10px; }

.layer-item {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 8px; border-radius: 6px;
  cursor: pointer; border: 1px solid transparent;
  transition: all .12s; margin-bottom: 2px;
}
.layer-item:hover { background: var(--bg-hover); }
.layer-item.active { background: var(--bg-card); border-color: var(--border); }

.layer-color { width: 10px; height: 10px; border-radius: 2px; flex-shrink: 0; }
.layer-label { flex: 1; font-size: 12px; font-weight: 500; color: var(--txt0); }

.layer-badge {
  font-size: 9px; font-weight: 600; padding: 2px 6px; border-radius: 10px;
}
.layer-badge.fill  { background: rgba(232,89,12,.15); color: var(--accent); }
.layer-badge.line  { background: rgba(11,191,168,.15); color: var(--teal); }
.layer-badge.cut   { background: rgba(239,68,68,.15);  color: var(--red); }
.layer-badge.score { background: rgba(245,158,11,.15); color: var(--yellow); }
</style>
