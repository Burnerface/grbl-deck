<template>
  <v-dialog :model-value="modelValue" max-width="700" @update:model-value="$emit('update:modelValue', $event)">
    <v-card color="surface" rounded="lg">
      <v-card-title class="d-flex align-center py-3 px-4">
        <v-icon class="mr-2">mdi-cog</v-icon>
        Paramètres GRBL — {{ store.machineActive?.name }}
        <v-spacer />
        <v-btn icon="mdi-close" variant="text" size="small" @click="$emit('update:modelValue', false)" />
      </v-card-title>

      <v-divider />

      <v-card-text class="pa-4">
        <v-alert v-if="!store.status.connected" type="warning" variant="tonal" density="compact" class="mb-3">
          Connectez la machine pour charger les paramètres GRBL
        </v-alert>

        <div class="d-flex gap-2 mb-3">
          <v-btn
            color="primary"
            variant="tonal"
            prepend-icon="mdi-download"
            size="small"
            :disabled="!store.status.connected"
            :loading="loading"
            @click="charger"
          >
            Charger depuis machine
          </v-btn>
        </div>

        <!-- Liste des settings parsés depuis les logs -->
        <v-table density="compact" class="settings-table">
          <thead>
            <tr>
              <th style="width:80px">Paramètre</th>
              <th>Valeur</th>
              <th style="width:80px">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(val, key) in settings" :key="key">
              <td class="text-caption font-weight-bold text-primary">{{ key }}</td>
              <td>
                <v-text-field
                  v-model="settings[key]"
                  density="compact"
                  variant="plain"
                  hide-details
                  class="text-caption"
                />
              </td>
              <td>
                <v-btn
                  icon="mdi-send"
                  size="x-small"
                  variant="text"
                  color="success"
                  :disabled="!store.status.connected"
                  @click="store.envoyerSetting(key, settings[key])"
                />
              </td>
            </tr>
          </tbody>
        </v-table>

        <div v-if="!Object.keys(settings).length && store.status.connected" class="text-caption text-medium-emphasis pa-3 text-center">
          Cliquez "Charger depuis machine" pour afficher les paramètres
        </div>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useMachineStore } from '../stores/machine'

defineProps({ modelValue: Boolean })
defineEmits(['update:modelValue'])

const store = useMachineStore()
const settings = ref({})
const loading = ref(false)

async function charger() {
  loading.value = true
  settings.value = {}
  // Écouter les logs pour récupérer les $xx=yyy
  await store.chargerSettings()
  // Attendre 2s pour recevoir la réponse via WS
  setTimeout(() => {
    parseSettingsFromLogs()
    loading.value = false
  }, 2000)
}

function parseSettingsFromLogs() {
  const parsed = {}
  for (const log of store.logs) {
    const match = log.message?.match(/^\$(\d+)=([\d.]+)/)
    if (match) {
      parsed[`$${match[1]}`] = match[2]
    }
  }
  if (Object.keys(parsed).length) {
    settings.value = parsed
  }
}
</script>

<style scoped>
.settings-table { max-height: 400px; overflow-y: auto; }
</style>
