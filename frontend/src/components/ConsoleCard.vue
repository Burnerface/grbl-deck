<template>
  <v-card color="surface-variant" rounded="lg" elevation="0">
    <v-card-title class="text-caption text-medium-emphasis py-2 px-3 d-flex align-center">
      <v-icon size="small" class="mr-1">mdi-console</v-icon>
      CONSOLE
      <v-spacer />
      <v-btn icon="mdi-delete-sweep" variant="text" size="x-small" @click="store.logs = []" />
    </v-card-title>
    <v-divider />

    <!-- Logs -->
    <div ref="logsRef" class="console-logs pa-2">
      <div
        v-for="(log, i) in store.logs"
        :key="i"
        class="log-line text-caption"
        :class="logClass(log.message)"
      >
        <span class="text-medium-emphasis mr-1">{{ log.time }}</span>
        <span>{{ log.message }}</span>
      </div>
      <div v-if="store.logs.length === 0" class="text-caption text-medium-emphasis pa-2">
        Aucun log...
      </div>
    </div>

    <v-divider />

    <!-- Input commande -->
    <div class="pa-2 d-flex gap-2">
      <v-text-field
        v-model="cmd"
        density="compact"
        variant="outlined"
        hide-details
        placeholder="Commande GRBL..."
        :disabled="!store.status.connected"
        class="text-mono"
        @keydown.enter="envoyer"
        @keydown.up="historyUp"
        @keydown.down="historyDown"
      />
      <v-btn
        icon="mdi-send"
        color="primary"
        size="small"
        :disabled="!store.status.connected || !cmd"
        @click="envoyer"
      />
    </div>
  </v-card>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { useMachineStore } from '../stores/machine'

const store = useMachineStore()
const cmd = ref('')
const logsRef = ref(null)
const history = ref([])
const historyIndex = ref(-1)

async function envoyer() {
  if (!cmd.value.trim()) return
  history.value.unshift(cmd.value)
  if (history.value.length > 50) history.value.pop()
  historyIndex.value = -1
  await store.envoyerCommande(cmd.value)
  cmd.value = ''
}

function historyUp() {
  if (historyIndex.value < history.value.length - 1) {
    historyIndex.value++
    cmd.value = history.value[historyIndex.value]
  }
}

function historyDown() {
  if (historyIndex.value > 0) {
    historyIndex.value--
    cmd.value = history.value[historyIndex.value]
  } else {
    historyIndex.value = -1
    cmd.value = ''
  }
}

function logClass(msg) {
  if (msg.startsWith('>')) return 'log-cmd'
  if (msg.startsWith('⚠') || msg.includes('error') || msg.includes('ALARM')) return 'log-error'
  if (msg.startsWith('<')) return 'log-status'
  return 'log-response'
}

// Auto-scroll
watch(() => store.logs.length, async () => {
  await nextTick()
  if (logsRef.value) {
    logsRef.value.scrollTop = logsRef.value.scrollHeight
  }
})
</script>

<style scoped>
.console-logs {
  height: 160px;
  overflow-y: auto;
  font-family: 'Courier New', monospace;
  background: rgba(0, 0, 0, 0.3);
}
.log-line { line-height: 1.4; padding: 1px 0; }
.log-cmd { color: #40C4FF; }
.log-error { color: #FF5252; }
.log-status { color: #aaa; }
.log-response { color: #e0e0e0; }
.text-mono { font-family: 'Courier New', monospace; }
</style>
