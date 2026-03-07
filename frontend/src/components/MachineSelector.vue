<template>
  <div class="d-flex align-center gap-2">
    <v-select
      :model-value="store.machineActiveId"
      :items="store.machines"
      item-title="name"
      item-value="id"
      density="compact"
      variant="outlined"
      hide-details
      style="min-width: 200px; max-width: 280px"
      @update:model-value="store.selectionnerMachine($event)"
    >
      <template #item="{ item, props }">
        <v-list-item v-bind="props">
          <template #prepend>
            <v-icon :icon="item.raw.type === 'laser' ? 'mdi-laser-pointer' : 'mdi-router'" size="small" class="mr-1" />
          </template>
          <template #append>
            <v-chip
              :color="item.raw.sim ? 'warning' : 'success'"
              size="x-small"
              variant="tonal"
            >
              {{ item.raw.sim ? 'SIM' : 'REEL' }}
            </v-chip>
          </template>
        </v-list-item>
      </template>
    </v-select>

    <!-- Ajouter machine -->
    <v-btn
      icon="mdi-plus"
      variant="tonal"
      size="small"
      color="primary"
      @click="showMachineDialog = true"
    />
  </div>
</template>

<script setup>
import { inject } from 'vue'
import { useMachineStore } from '../stores/machine'

const store = useMachineStore()
const showMachineDialog = inject('showMachineDialog')
</script>
