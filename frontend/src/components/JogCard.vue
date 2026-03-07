<template>
  <v-card color="surface-variant" rounded="lg" elevation="0">
    <v-card-title class="text-caption text-medium-emphasis py-2 px-3">
      <v-icon size="small" class="mr-1">mdi-gamepad-variant</v-icon>
      JOG
    </v-card-title>
    <v-divider />
    <v-card-text class="pa-3">
      <!-- Grille de déplacement XY -->
      <div class="jog-grid mb-3">
        <div />
        <v-btn :disabled="!connected" icon variant="tonal" size="small" @click="jog('Y', step)">
          <v-icon>mdi-arrow-up</v-icon>
        </v-btn>
        <div />

        <v-btn :disabled="!connected" icon variant="tonal" size="small" @click="jog('X', -step)">
          <v-icon>mdi-arrow-left</v-icon>
        </v-btn>
        <v-btn :disabled="!connected" icon variant="tonal" color="primary" size="small" @click="store.envoyerCommande('G0 X0 Y0')">
          <v-icon>mdi-crosshairs</v-icon>
        </v-btn>
        <v-btn :disabled="!connected" icon variant="tonal" size="small" @click="jog('X', step)">
          <v-icon>mdi-arrow-right</v-icon>
        </v-btn>

        <div />
        <v-btn :disabled="!connected" icon variant="tonal" size="small" @click="jog('Y', -step)">
          <v-icon>mdi-arrow-down</v-icon>
        </v-btn>
        <div />
      </div>

      <!-- Z -->
      <div class="d-flex align-center justify-center gap-2 mb-3">
        <v-btn :disabled="!connected" icon variant="tonal" size="small" color="info" @click="jog('Z', step)">
          <v-icon>mdi-arrow-collapse-up</v-icon>
        </v-btn>
        <span class="text-caption text-medium-emphasis">Z</span>
        <v-btn :disabled="!connected" icon variant="tonal" size="small" color="info" @click="jog('Z', -step)">
          <v-icon>mdi-arrow-collapse-down</v-icon>
        </v-btn>
      </div>

      <!-- Step selector -->
      <v-btn-toggle v-model="stepIndex" mandatory density="compact" color="primary" class="w-100">
        <v-btn v-for="s in steps" :key="s" size="x-small" class="flex-grow-1">
          {{ s }}
        </v-btn>
      </v-btn-toggle>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useMachineStore } from '../stores/machine'

const store = useMachineStore()
const connected = computed(() => store.status.connected)

const steps = [0.1, 1, 5, 10, 50]
const stepIndex = ref(1)
const step = computed(() => steps[stepIndex.value])

function jog(axis, distance) {
  store.envoyerCommande(`$J=G91 G21 ${axis}${distance} F1000`)
}
</script>

<style scoped>
.jog-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 4px;
  place-items: center;
}
</style>
