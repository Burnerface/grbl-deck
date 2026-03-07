<template>
  <v-card color="surface-variant" rounded="lg" elevation="0">
    <v-card-title class="text-caption text-medium-emphasis py-2 px-3 d-flex align-center">
      <v-icon size="small" class="mr-1">mdi-folder-open</v-icon>
      FICHIERS
      <v-spacer />
      <v-btn icon="mdi-refresh" variant="text" size="x-small" @click="store.chargerFichiers()" />
      <v-btn icon="mdi-upload" variant="text" size="x-small" color="primary" @click="triggerUpload" />
      <input ref="fileInputRef" type="file" accept=".gcode,.nc,.gc,.ngc,.txt" style="display:none" @change="onUpload" />
    </v-card-title>
    <v-divider />

    <v-list density="compact" class="pa-0 file-list" bg-color="transparent">
      <v-list-item
        v-for="file in store.files"
        :key="file.name"
        :class="{ 'file-active': selectedFile === file.name }"
        class="file-item"
        @click="selectFile(file.name)"
      >
        <template #prepend>
          <v-icon size="small" color="primary">mdi-file-code</v-icon>
        </template>

        <v-list-item-title class="text-caption">{{ file.name }}</v-list-item-title>
        <v-list-item-subtitle class="text-caption text-medium-emphasis">
          {{ formatSize(file.size) }}
        </v-list-item-subtitle>

        <template #append>
          <div class="d-flex gap-1">
            <v-btn
              icon="mdi-play"
              size="x-small"
              variant="text"
              color="success"
              :disabled="!store.status.connected || store.status.job.actif"
              @click.stop="lancer(file.name)"
            />
            <v-btn
              icon="mdi-delete"
              size="x-small"
              variant="text"
              color="error"
              @click.stop="supprimer(file.name)"
            />
          </div>
        </template>
      </v-list-item>

      <v-list-item v-if="!store.files.length" class="text-caption text-medium-emphasis pa-3">
        Aucun fichier
      </v-list-item>
    </v-list>
  </v-card>
</template>

<script setup>
import { ref, inject } from 'vue'
import { useMachineStore } from '../stores/machine'

const store = useMachineStore()
const fileInputRef = ref(null)
const selectedFile = ref(null)

// Référence vers le viewer pour charger le GCode
const viewerRef = inject('gcodeViewer', null)

function triggerUpload() {
  fileInputRef.value?.click()
}

async function onUpload(e) {
  const file = e.target.files[0]
  if (!file) return
  await store.uploadFichier(file)
  e.target.value = ''
}

async function selectFile(name) {
  selectedFile.value = name
  // Notifier le viewer
  if (viewerRef?.value) {
    await viewerRef.value.chargerGCode(name)
  }
}

async function lancer(name) {
  await store.lancerFichier(name)
}

async function supprimer(name) {
  await store.supprimerFichier(name)
  if (selectedFile.value === name) selectedFile.value = null
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} o`
  return `${(bytes / 1024).toFixed(1)} Ko`
}
</script>

<style scoped>
.file-list { max-height: 200px; overflow-y: auto; }
.file-item { cursor: pointer; }
.file-item:hover { background: rgba(255,255,255,0.05); }
.file-active { background: rgba(0, 188, 212, 0.1) !important; }
</style>
