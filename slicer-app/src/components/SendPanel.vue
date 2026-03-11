<template>
  <div class="send-panel">

    <!-- Header -->
    <div class="sp-header">
      <span class="sp-title">Envoyer vers GRBLDeck</span>
      <button class="sp-refresh" @click="loadMachines" :class="{ spinning: loading }">↻</button>
    </div>

    <!-- Erreur -->
    <div v-if="error" class="sp-error">{{ error }}</div>

    <!-- Liste machines -->
    <div v-if="machines.length === 0 && !loading" class="sp-empty">
      Aucune machine trouvée
    </div>

    <div v-for="m in machines" :key="m.id"
      class="sp-machine" :class="{ selected: selectedId === m.id }"
      @click="selectedId = m.id">
      <div class="sp-machine-left">
        <div class="sp-dot" :class="m.connected ? 'online' : 'offline'"></div>
        <div class="sp-machine-info">
          <div class="sp-machine-name">{{ m.name }}</div>
          <div class="sp-machine-meta">{{ m.type }} · {{ m.state }}</div>
        </div>
      </div>
      <span class="sp-check" v-if="selectedId === m.id">✓</span>
    </div>

    <!-- Nom du fichier -->
    <div class="sp-field">
      <span class="sp-field-label">Nom fichier</span>
      <input class="sp-input" v-model="filename" placeholder="job.nc"/>
    </div>

    <!-- Bouton -->
    <button class="sp-btn"
      :class="{ sending: status === 'sending', done: status === 'done', error: status === 'error' }"
      :disabled="!selectedId || status === 'sending'"
      @click="send">
      <span v-if="status === 'idle'">▶ Envoyer le GCode</span>
      <span v-else-if="status === 'sending'">⏳ Envoi en cours…</span>
      <span v-else-if="status === 'done'">✅ Envoyé ! Lancer ?</span>
      <span v-else-if="status === 'error'">❌ Erreur — Réessayer</span>
    </button>

    <!-- Lancer -->
    <button v-if="status === 'done'" class="sp-btn-run" @click="run">
      ▶▶ Lancer l'usinage
    </button>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({ gcodeLines: Array })

const API = 'http://192.168.1.168:8086'
const machines  = ref([])
const selectedId = ref(null)
const filename  = ref('slicer-job.nc')
const loading   = ref(false)
const error     = ref('')
const status    = ref('idle') // idle | sending | done | error

async function loadMachines() {
  loading.value = true
  error.value = ''
  try {
    const r = await fetch(`${API}/machines`)
    machines.value = await r.json()
    if (machines.value.length > 0) selectedId.value = machines.value[0].id
  } catch (e) {
    error.value = 'Impossible de joindre le backend'
  } finally {
    loading.value = false
  }
}

async function send() {
  if (!selectedId.value) return
  status.value = 'sending'
  error.value  = ''
  try {
    // Construire le contenu GCode
    const gcodeText = props.gcodeLines
      .map(l => `${l.cmd}${l.args} ${l.comment}`.trim())
      .join('\n')

    // Créer un FormData avec le fichier
    const blob = new Blob([gcodeText], { type: 'text/plain' })
    const fd   = new FormData()
    fd.append('file', blob, filename.value)

    const r = await fetch(`${API}/machines/${selectedId.value}/upload`, {
      method: 'POST',
      body: fd,
    })
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    status.value = 'done'
  } catch (e) {
    error.value  = e.message
    status.value = 'error'
  }
}

async function run() {
  try {
    const r = await fetch(`${API}/machines/${selectedId.value}/run/${encodeURIComponent(filename.value)}`, {
      method: 'POST'
    })
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    status.value = 'idle'
    alert(`✅ Usinage lancé sur "${machines.value.find(m=>m.id===selectedId.value)?.name}"`)
  } catch (e) {
    error.value  = e.message
    status.value = 'error'
  }
}

onMounted(loadMachines)
</script>

<style scoped>
.send-panel {
  padding: 10px;
  border-top: 1px solid var(--border);
  display: flex; flex-direction: column; gap: 7px;
}

.sp-header {
  display: flex; align-items: center; justify-content: space-between;
}
.sp-title { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .10em; color: var(--txt2); }
.sp-refresh {
  width: 24px; height: 24px; border-radius: 4px;
  background: var(--bg-card); border: 1px solid var(--border);
  color: var(--txt1); font-size: 14px;
  display: flex; align-items: center; justify-content: center;
  transition: all .2s; cursor: pointer;
}
.sp-refresh:hover { color: var(--txt0); }
.sp-refresh.spinning { animation: spin .6s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.sp-error { font-size: 11px; color: var(--red); background: rgba(239,68,68,.1); border-radius: 4px; padding: 5px 8px; }
.sp-empty { font-size: 11px; color: var(--txt2); text-align: center; padding: 8px; }

.sp-machine {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 10px; background: var(--bg-card);
  border: 1px solid var(--border); border-radius: 7px;
  cursor: pointer; transition: all .12s;
}
.sp-machine:hover { border-color: var(--border-lit); }
.sp-machine.selected { border-color: var(--accent); background: var(--accent-soft); }
.sp-machine-left { display: flex; align-items: center; gap: 9px; }
.sp-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.sp-dot.online  { background: var(--green); box-shadow: 0 0 5px var(--green); }
.sp-dot.offline { background: var(--txt2); }
.sp-machine-name { font-size: 12px; font-weight: 500; color: var(--txt0); }
.sp-machine-meta { font-size: 10px; color: var(--txt2); font-family: var(--ffm); margin-top: 1px; }
.sp-check { color: var(--accent); font-size: 14px; font-weight: 700; }

.sp-field { display: flex; align-items: center; gap: 8px; }
.sp-field-label { font-size: 11px; color: var(--txt1); min-width: 70px; }
.sp-input {
  flex: 1; height: 27px; padding: 0 8px;
  background: var(--bg-input); border: 1px solid var(--border);
  border-radius: 4px; color: var(--txt0); font-size: 11.5px; font-family: var(--ffm);
  transition: border-color .12s;
}
.sp-input:focus { border-color: var(--accent); }

.sp-btn {
  height: 38px; border-radius: 6px;
  background: var(--accent); color: white;
  font-size: 13px; font-weight: 600;
  box-shadow: 0 0 16px var(--accent-glow);
  transition: all .15s; cursor: pointer; border: none;
}
.sp-btn:hover:not(:disabled) { background: #F06A20; transform: translateY(-1px); box-shadow: 0 0 24px var(--accent-glow); }
.sp-btn:disabled { opacity: .5; cursor: not-allowed; }
.sp-btn.done  { background: var(--green); box-shadow: 0 0 16px rgba(34,197,94,.3); }
.sp-btn.error { background: var(--red);   box-shadow: 0 0 16px rgba(239,68,68,.3); }

.sp-btn-run {
  height: 34px; border-radius: 6px;
  background: var(--teal-soft); border: 1px solid var(--teal);
  color: var(--teal); font-size: 12.5px; font-weight: 600;
  transition: all .15s; cursor: pointer;
}
.sp-btn-run:hover { background: var(--teal); color: white; }
</style>
