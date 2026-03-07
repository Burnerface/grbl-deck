<template>
  <v-card color="surface-variant" rounded="lg" elevation="0">
    <v-card-title class="text-caption text-medium-emphasis py-2 px-3">
      <v-icon size="small" class="mr-1">mdi-crosshairs-gps</v-icon>
      POSITION
    </v-card-title>
    <v-divider />
    <v-card-text class="pa-3">
      <div class="d-flex flex-column gap-2">
        <div v-for="axis in ['x', 'y', 'z']" :key="axis" class="d-flex align-center justify-space-between">
          <span class="text-overline font-weight-bold" :style="{ color: axisColor(axis) }">
            {{ axis.toUpperCase() }}
          </span>
          <span class="text-h6 font-weight-bold text-mono">
            {{ position[axis].toFixed(3) }}
            <span class="text-caption text-medium-emphasis">mm</span>
          </span>
        </div>
      </div>

      <v-divider class="my-2" />

      <!-- Boutons homing / zéro -->
      <div class="d-flex gap-2">
        <v-btn
          size="small"
          variant="tonal"
          color="primary"
          prepend-icon="mdi-home"
          :disabled="!store.status.connected"
          @click="store.envoyerCommande('$H')"
        >
          Home
        </v-btn>
        <v-btn
          size="small"
          variant="tonal"
          color="secondary"
          prepend-icon="mdi-crosshairs"
          :disabled="!store.status.connected"
          @click="store.envoyerCommande('G92 X0 Y0 Z0')"
        >
          Zéro
        </v-btn>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { computed } from 'vue'
import { useMachineStore } from '../stores/machine'

const store = useMachineStore()
const position = computed(() => store.status.position)

const axisColor = (axis) => {
  return { x: '#FF5252', y: '#00E676', z: '#40C4FF' }[axis]
}
</script>

<style scoped>
.text-mono { font-family: 'Courier New', monospace; }
</style>
