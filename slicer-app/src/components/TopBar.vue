<template>
  <div class="topbar">
    <!-- Logo -->
    <div class="tb-logo">
      <div class="tb-logo-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="3"/>
          <path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>
          <path d="M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M5.6 18.4l2.1-2.1M16.3 7.7l2.1-2.1"/>
        </svg>
      </div>
      <div class="tb-logo-text">
        <span class="tb-logo-name">GRBLDeck</span>
        <span class="tb-logo-sub">Slicer v0.1</span>
      </div>
    </div>

    <!-- Étapes workflow -->
    <div class="tb-steps">
      <button v-for="(step, i) in steps" :key="step.id"
        class="tb-step" :class="{ active: activeStep === step.id }"
        @click="activeStep = step.id">
        <span class="step-num">{{ i + 1 }}</span>
        {{ step.label }}
      </button>
      <span v-if="i < steps.length - 1" class="step-arrow">›</span>
    </div>

    <!-- Actions droite -->
    <div class="tb-actions">
      <!-- Machine -->
      <div class="machine-pill">
        <span class="machine-dot"></span>
        <span class="machine-name">Laser Pro 40W</span>
        <span class="machine-port">:8086</span>
      </div>

      <!-- Import -->
      <button class="tb-btn" @click="$emit('import-file')">
        📂 Importer
      </button>

      <!-- Theme toggle -->
      <button class="tb-btn-icon" @click="$emit('toggle-theme')" :title="theme === 'dark' ? 'Mode clair' : 'Mode sombre'">
        {{ theme === 'dark' ? '☀️' : '🌙' }}
      </button>

      <!-- Générer GCode -->
      <button class="tb-btn-secondary" @click="$emit('generate')">
        ⚡ Générer GCode
      </button>

      <!-- Envoyer -->
      <button class="tb-btn-primary" @click="$emit('send')">
        ▶ Envoyer
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({ theme: String })
defineEmits(['toggle-theme', 'import-file', 'generate', 'send'])

const activeStep = ref('prepare')
const steps = [
  { id: 'prepare',   label: 'Préparer'   },
  { id: 'parametrer', label: 'Paramétrer' },
  { id: 'generer',   label: 'Générer'    },
  { id: 'envoyer',   label: 'Envoyer'    },
]
</script>

<style scoped>
.topbar {
  height: 52px;
  background: var(--bg-panel);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  flex-shrink: 0;
  z-index: 100;
}

.tb-logo {
  width: 190px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-right: 1px solid var(--border);
  flex-shrink: 0;
}
.tb-logo-icon {
  width: 30px; height: 30px;
  background: var(--accent);
  border-radius: 7px;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 0 14px var(--accent-glow);
  flex-shrink: 0;
}
.tb-logo-icon svg { width: 17px; height: 17px; }
.tb-logo-text { display: flex; flex-direction: column; line-height: 1; }
.tb-logo-name { font-size: 13px; font-weight: 600; color: var(--txt0); }
.tb-logo-sub  { font-size: 10px; color: var(--txt2); font-family: var(--ffm); margin-top: 2px; }

.tb-steps {
  display: flex;
  align-items: center;
  height: 100%;
  padding: 0 12px;
  gap: 2px;
}
.tb-step {
  height: 36px; padding: 0 14px;
  border-radius: 6px;
  background: none; color: var(--txt1);
  font-size: 13px; font-weight: 500;
  display: flex; align-items: center; gap: 7px;
  transition: all .15s;
}
.tb-step:hover { background: var(--bg-hover); color: var(--txt0); }
.tb-step.active { background: var(--accent-soft); color: var(--accent); }
.step-num {
  width: 18px; height: 18px; border-radius: 50%;
  background: var(--bg-card); font-size: 10px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  color: var(--txt2); font-family: var(--ffm);
}
.tb-step.active .step-num { background: var(--accent); color: white; }
.step-arrow { color: var(--txt2); font-size: 14px; padding: 0 2px; }

.tb-actions {
  margin-left: auto;
  display: flex; align-items: center; gap: 8px;
  padding: 0 16px;
}

.machine-pill {
  display: flex; align-items: center; gap: 7px;
  background: var(--bg-card); border: 1px solid var(--border-lit);
  border-radius: 6px; padding: 5px 12px;
  cursor: pointer; transition: all .15s;
}
.machine-pill:hover { border-color: var(--accent); }
.machine-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--green); box-shadow: 0 0 5px var(--green); }
.machine-name { font-size: 12.5px; color: var(--txt0); font-weight: 500; }
.machine-port { font-size: 10px; color: var(--txt2); font-family: var(--ffm); }

.tb-btn {
  height: 34px; padding: 0 14px;
  background: var(--bg-card); border: 1px solid var(--border);
  color: var(--txt1); font-size: 12.5px; border-radius: 6px;
  transition: all .15s;
}
.tb-btn:hover { border-color: var(--border-lit); color: var(--txt0); }

.tb-btn-icon {
  width: 34px; height: 34px;
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: 6px; font-size: 15px;
  display: flex; align-items: center; justify-content: center;
  transition: all .15s;
}
.tb-btn-icon:hover { border-color: var(--border-lit); }

.tb-btn-secondary {
  height: 34px; padding: 0 14px;
  background: var(--bg-card); border: 1px solid var(--border-lit);
  color: var(--txt0); font-size: 12.5px; font-weight: 500; border-radius: 6px;
  transition: all .15s;
}
.tb-btn-secondary:hover { border-color: var(--teal); color: var(--teal); }

.tb-btn-primary {
  height: 34px; padding: 0 18px;
  background: var(--accent); color: white;
  font-size: 13px; font-weight: 600; border-radius: 6px;
  box-shadow: 0 0 16px var(--accent-glow);
  transition: all .15s;
}
.tb-btn-primary:hover { background: #F06A20; box-shadow: 0 0 24px var(--accent-glow); transform: translateY(-1px); }
</style>
