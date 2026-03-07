<template>
  <v-dialog :model-value="modelValue" max-width="480" @update:model-value="$emit('update:modelValue', $event)">
    <v-card color="surface" rounded="lg">
      <v-card-title class="d-flex align-center py-3 px-4">
        <v-icon class="mr-2">mdi-plus-circle</v-icon>
        Ajouter une machine
        <v-spacer />
        <v-btn icon="mdi-close" variant="text" size="small" @click="$emit('update:modelValue', false)" />
      </v-card-title>

      <v-divider />

      <v-card-text class="pa-4">
        <v-text-field
          v-model="form.name"
          label="Nom de la machine"
          density="compact"
          variant="outlined"
          class="mb-3"
        />

        <v-select
          v-model="form.type"
          label="Type"
          :items="[{ title: 'CNC', value: 'cnc' }, { title: 'Laser', value: 'laser' }]"
          density="compact"
          variant="outlined"
          class="mb-3"
        />

        <v-switch
          v-model="form.sim"
          label="Mode simulateur (sans machine physique)"
          color="warning"
          density="compact"
          class="mb-3"
        />

        <template v-if="!form.sim">
          <v-select
            v-model="form.port"
            label="Port série"
            :items="ports"
            density="compact"
            variant="outlined"
            class="mb-3"
            @click:prepend-inner="chargerPorts"
          >
            <template #append-inner>
              <v-btn icon="mdi-refresh" variant="text" size="x-small" @click.stop="chargerPorts" />
            </template>
          </v-select>

          <v-select
            v-model="form.baudrate"
            label="Baudrate"
            :items="[9600, 19200, 38400, 57600, 115200]"
            density="compact"
            variant="outlined"
          />
        </template>
      </v-card-text>

      <v-card-actions class="px-4 pb-4">
        <v-spacer />
        <v-btn variant="text" @click="$emit('update:modelValue', false)">Annuler</v-btn>
        <v-btn color="primary" variant="flat" :loading="saving" @click="sauvegarder">
          Ajouter
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useMachineStore } from '../stores/machine'

const props = defineProps({ modelValue: Boolean })
const emit = defineEmits(['update:modelValue'])

const store = useMachineStore()
const saving = ref(false)
const ports = ref([])

const form = ref({
  name: '',
  type: 'cnc',
  port: '',
  baudrate: 115200,
  sim: false,
})

watch(() => props.modelValue, (val) => {
  if (val) chargerPorts()
})

async function chargerPorts() {
  ports.value = await store.chargerPorts()
}

async function sauvegarder() {
  saving.value = true
  try {
    await store.ajouterMachine(form.value)
    emit('update:modelValue', false)
    form.value = { name: '', type: 'cnc', port: '', baudrate: 115200, sim: false }
  } finally {
    saving.value = false
  }
}
</script>
