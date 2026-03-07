<template>
  <v-card color="surface-variant" rounded="lg" elevation="0">
    <v-card-title class="text-caption text-medium-emphasis py-2 px-3 d-flex align-center">
      <v-icon size="small" class="mr-1">mdi-camera</v-icon>
      CAMÉRA
      <v-spacer />
      <v-btn icon="mdi-cog" variant="text" size="x-small" @click="showConfig = !showConfig" />
    </v-card-title>
    <v-divider />

    <!-- Config URL caméra -->
    <div v-if="showConfig" class="pa-2">
      <v-text-field
        v-model="cameraUrl"
        density="compact"
        variant="outlined"
        hide-details
        placeholder="http://ip:port/stream"
        label="URL flux caméra"
        class="mb-2"
      />
      <v-btn size="small" color="primary" block @click="appliquer">Appliquer</v-btn>
    </div>

    <!-- Flux vidéo -->
    <div class="camera-container">
      <img
        v-if="activeUrl"
        :src="activeUrl"
        class="camera-feed"
        alt="Caméra"
        @error="onError"
      />
      <div v-else class="camera-empty text-medium-emphasis text-caption">
        <v-icon size="32" class="mb-2">mdi-camera-off</v-icon>
        <div>Aucune caméra configurée</div>
      </div>
    </div>
  </v-card>
</template>

<script setup>
import { ref } from 'vue'

const cameraUrl = ref('')
const activeUrl = ref('')
const showConfig = ref(false)

function appliquer() {
  activeUrl.value = cameraUrl.value
  showConfig.value = false
}

function onError() {
  activeUrl.value = ''
}
</script>

<style scoped>
.camera-container {
  position: relative;
  width: 100%;
  aspect-ratio: 4/3;
  background: #000;
  overflow: hidden;
}

.camera-feed {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.camera-empty {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
</style>
