<!-- ═══════════════════ StatusBar.vue ═══════════════════ -->
<template>
  <div class="statusbar">
    <div class="sb-item"><div class="sb-dot ok"></div> GRBLDeck connecté</div>
    <div class="sb-sep"></div>
    <div class="sb-item">X: {{ cursor.x }}  Y: {{ cursor.y }} mm</div>
    <div class="sb-sep"></div>
    <div class="sb-item">{{ selectedInfo || 'Aucune sélection' }}</div>
    <div class="sb-right">
      <div class="sb-item">{{ objectsCount }} objets · {{ layersCount }} couches</div>
      <div class="sb-sep"></div>
      <div class="sb-item">Zoom: {{ zoom }}%</div>
      <div class="sb-sep"></div>
      <div class="sb-item">Mode: Laser</div>
    </div>
  </div>
</template>
<script setup>
defineProps({ cursor: Object, zoom: Number, selectedInfo: String, objectsCount: Number, layersCount: Number })
</script>
<style scoped>
.statusbar {
  height: 24px; background: var(--bg-panel); border-top: 1px solid var(--border);
  display: flex; align-items: center; padding: 0 14px; gap: 14px;
  flex-shrink: 0; font-size: 10.5px; color: var(--txt2); font-family: var(--ffm);
}
.sb-item { display: flex; align-items: center; gap: 5px; }
.sb-sep  { width: 1px; height: 13px; background: var(--border); }
.sb-right { margin-left: auto; display: flex; gap: 14px; }
.sb-dot { width: 6px; height: 6px; border-radius: 50%; }
.sb-dot.ok { background: var(--green); box-shadow: 0 0 5px var(--green); }
</style>
