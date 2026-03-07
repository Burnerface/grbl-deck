import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const API = '/api'
const WS_BASE = `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/api/ws`

export const useMachineStore = defineStore('machine', () => {
  // ─── State ───────────────────────────────────────────────────────────────
  const machines = ref([])
  const machineActiveId = ref(null)
  const ws = ref(null)

  // État machine active (mis à jour par WebSocket)
  const status = ref({
    connected: false,
    state: 'Disconnected',
    position: { x: 0, y: 0, z: 0 },
    job: { actif: false, fichier: null, progression: 0 },
  })
  const logs = ref([])
  const files = ref([])

  // ─── Computed ─────────────────────────────────────────────────────────────
  const machineActive = computed(() =>
    machines.value.find(m => m.id === machineActiveId.value) || null
  )

  const mode = computed(() => machineActive.value?.type || 'cnc')

  // ─── WebSocket ────────────────────────────────────────────────────────────
  function connectWS(machineId) {
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }

    const socket = new WebSocket(`${WS_BASE}/${machineId}`)

    socket.onopen = () => {
      console.log(`[WS] Connecté à ${machineId}`)
    }

    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        handleWsMessage(msg)
      } catch (e) {
        console.error('[WS] Parse error', e)
      }
    }

    socket.onclose = () => {
      console.log('[WS] Déconnecté')
      // Reconnecter après 2s si la machine est toujours active
      if (machineActiveId.value === machineId) {
        setTimeout(() => connectWS(machineId), 2000)
      }
    }

    socket.onerror = (e) => {
      console.error('[WS] Erreur', e)
    }

    ws.value = socket
  }

  function handleWsMessage(msg) {
    switch (msg.type) {
      case 'status':
        status.value = { ...status.value, ...msg.data }
        break

      case 'log':
        logs.value.push(msg.data)
        if (logs.value.length > 500) logs.value.shift()
        break

      case 'error':
        logs.value.push({ time: new Date().toLocaleTimeString(), message: `⚠ ${msg.message}` })
        break
    }
  }

  function sendWsCommand(command) {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify({ type: 'command', command }))
    }
  }

  // ─── Machines ─────────────────────────────────────────────────────────────
  async function chargerMachines() {
    const res = await fetch(`${API}/machines`)
    machines.value = await res.json()

    if (!machineActiveId.value && machines.value.length > 0) {
      await selectionnerMachine(machines.value[0].id)
    }
  }

  async function selectionnerMachine(id) {
    machineActiveId.value = id
    logs.value = []
    status.value = {
      connected: false,
      state: 'Disconnected',
      position: { x: 0, y: 0, z: 0 },
      job: { actif: false, fichier: null, progression: 0 },
    }
    connectWS(id)
    await chargerFichiers()
  }

  async function ajouterMachine(config) {
    const res = await fetch(`${API}/machines`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    })
    const machine = await res.json()
    machines.value.push(machine)
    return machine
  }

  async function modifierMachine(id, config) {
    const res = await fetch(`${API}/machines/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    })
    const updated = await res.json()
    const idx = machines.value.findIndex(m => m.id === id)
    if (idx !== -1) machines.value[idx] = updated
    return updated
  }

  async function supprimerMachine(id) {
    await fetch(`${API}/machines/${id}`, { method: 'DELETE' })
    machines.value = machines.value.filter(m => m.id !== id)
    if (machineActiveId.value === id && machines.value.length > 0) {
      await selectionnerMachine(machines.value[0].id)
    }
  }

  // ─── Connexion ────────────────────────────────────────────────────────────
  async function connecter() {
    await fetch(`${API}/machines/${machineActiveId.value}/connect`, { method: 'POST' })
  }

  async function deconnecter() {
    await fetch(`${API}/machines/${machineActiveId.value}/disconnect`, { method: 'POST' })
  }

  // ─── Commandes ───────────────────────────────────────────────────────────
  async function envoyerCommande(command) {
    // Via WebSocket si disponible, sinon REST
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      sendWsCommand(command)
    } else {
      await fetch(`${API}/machines/${machineActiveId.value}/command`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command }),
      })
    }
  }

  async function stopper() {
    await fetch(`${API}/machines/${machineActiveId.value}/stop`, { method: 'POST' })
  }

  // ─── Fichiers ─────────────────────────────────────────────────────────────
  async function chargerFichiers() {
    if (!machineActiveId.value) return
    const res = await fetch(`${API}/machines/${machineActiveId.value}/files`)
    files.value = await res.json()
  }

  async function uploadFichier(file) {
    const form = new FormData()
    form.append('file', file)
    await fetch(`${API}/machines/${machineActiveId.value}/upload`, {
      method: 'POST',
      body: form,
    })
    await chargerFichiers()
  }

  async function contenuFichier(filename) {
    const res = await fetch(`${API}/machines/${machineActiveId.value}/files/${encodeURIComponent(filename)}/content`)
    const data = await res.json()
    return data.content
  }

  async function supprimerFichier(filename) {
    await fetch(`${API}/machines/${machineActiveId.value}/files/${encodeURIComponent(filename)}`, {
      method: 'DELETE',
    })
    await chargerFichiers()
  }

  async function lancerFichier(filename) {
    await fetch(`${API}/machines/${machineActiveId.value}/run/${encodeURIComponent(filename)}`, {
      method: 'POST',
    })
  }

  // ─── Settings GRBL ────────────────────────────────────────────────────────
  async function chargerSettings() {
    await fetch(`${API}/machines/${machineActiveId.value}/settings/load`, { method: 'POST' })
  }

  async function envoyerSetting(key, value) {
    await fetch(`${API}/machines/${machineActiveId.value}/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key, value }),
    })
  }

  async function chargerPorts() {
    const res = await fetch(`${API}/ports`)
    return await res.json()
  }

  // ─── Return ───────────────────────────────────────────────────────────────
  return {
    // State
    machines,
    machineActiveId,
    status,
    logs,
    files,
    // Computed
    machineActive,
    mode,
    // Actions
    chargerMachines,
    selectionnerMachine,
    ajouterMachine,
    modifierMachine,
    supprimerMachine,
    connecter,
    deconnecter,
    envoyerCommande,
    stopper,
    chargerFichiers,
    uploadFichier,
    contenuFichier,
    supprimerFichier,
    lancerFichier,
    chargerSettings,
    envoyerSetting,
    chargerPorts,
  }
})
