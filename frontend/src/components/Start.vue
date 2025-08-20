<template>
  <div class="start-magic-container">
    <div class="summary-panel">
      <h3>✨ Your Magical Plan ✨</h3>
      <div v-if="fetchingSelections" class="loading-selections">
        <span class="spinner"></span> Loading your selections...
      </div>
      <template v-else>
        <div v-if="selected.intention" class="summary-card intention-card">
          <span class="icon">🪄</span>
          <span class="summary-text">
            I want to <b>{{ selected.intention.intention }}</b>
            <template v-if="selected.intention.amount && selected.intention.amount > 0">
              for <b>{{ selected.intention.amount }}</b> USD
            </template>
            <template v-if="selected.intention.dynamic_sell_timing">
              , holding for <b>most profitable non-linear time</b>
            </template>
            <template v-else-if="selected.intention.hold_minutes && selected.intention.hold_minutes > 0">
              , holding for <b>{{ holdPeriodString(selected.intention.hold_minutes) }}</b>
            </template>.
          </span>
        </div>
        <div v-if="selected.case" class="summary-card">
          <span class="icon">📁</span>
          <span class="summary-text">Case: <b>{{ selected.case.name }}</b></span>
        </div>
        <div v-if="selected.provider" class="summary-card">
          <span class="icon">🔌</span>
          <span class="summary-text">Provider: <b>{{ selected.provider.name }}</b></span>
        </div>
        <div v-if="selected.catalog" class="summary-card">
          <span class="icon">📚</span>
          <span class="summary-text">Catalog: <b>{{ selected.catalog.name }}</b></span>
        </div>
        <div v-if="!selected.intention" class="missing-warning">
          ⚠️ Please select an intention.
          <a href="#/intentions" class="action-link">Take action: Select Intention</a>
        </div>
        <div v-if="!selected.case" class="missing-warning">
          ⚠️ Please select a case.
          <a href="#/cases" class="action-link">Take action: Select Case</a>
        </div>
        <div v-if="!selected.provider" class="missing-warning">
          ⚠️ Please select a provider.
          <a href="#/providers" class="action-link">Take action: Select Provider</a>
        </div>
        <div v-if="!selected.catalog" class="missing-warning">
          ⚠️ Please select a catalog.
          <a href="#/catalogs" class="action-link">Take action: Select Catalog</a>
        </div>
        <div class="magic-desc">All your choices are aligned. When you press <b>Start Magic</b>, your intention will be set in motion with a sprinkle of algorithmic wizardry! ✨</div>
      </template>
    </div>
    <div class="arrow-panel">
      <div class="arrow">→</div>
    </div>
    <div class="action-panel">
      <button
        class="start-magic-btn"
        :disabled="loading || !canStartMagic || fetchingSelections"
        @click="runMagic"
        :title="!canStartMagic ? missingSelectionsText : ''"
      >
        Start Magic
      </button>
      <div v-if="loading" class="loading">Running analysis and scheduling...</div>
      <div v-if="result" class="result">
        <div v-if="result.status === 'success'">
          <h4>Success!</h4>
          <div>Schedule ID (Buy): {{ result.buy_schedule_id }}</div>
          <div>Schedule ID (Sell): {{ result.sell_schedule_id }}</div>
        </div>
        <div v-else class="error">{{ result.error }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import { API_BASE } from '../api';
export default {
  name: 'StartMagic',
  data() {
    return {
      selected: {
        intention: null,
        case: null,
        provider: null,
        catalog: null
      },
      loading: false,
      result: null,
      fetchingSelections: true
    };
  },
  computed: {
    canStartMagic() {
      return (
        this.selected.intention &&
        this.selected.case &&
        this.selected.provider &&
        this.selected.catalog
      );
    },
    missingSelectionsText() {
      const missing = [];
      if (!this.selected.intention) missing.push('intention');
      if (!this.selected.case) missing.push('case');
      if (!this.selected.provider) missing.push('provider');
      if (!this.selected.catalog) missing.push('catalog');
      return 'Please select: ' + missing.join(', ');
    }
  },
  methods: {
    async fetchSelections() {
      this.fetchingSelections = true;
      // Fetch selected intention, case, provider, catalog from API
      const [intentions, cases, providers, catalogs] = await Promise.all([
        fetch(`${API_BASE}/intentions`).then(r => r.json()),
        fetch(`${API_BASE}/cases`).then(r => r.json()),
        fetch(`${API_BASE}/providers`).then(r => r.json()),
        fetch(`${API_BASE}/catalogs`).then(r => r.json())
      ]);
      this.selected.intention = (intentions.find ? intentions.find(i => i.selected) : (intentions.intentions || []).find(i => i.selected)) || null;
      this.selected.case = (cases.cases || []).find(c => c.selected) || null;
      this.selected.provider = (providers.providers || []).find(p => p.selected) || null;
      this.selected.catalog = (catalogs.catalogs || []).find(c => c.selected) || null;
      this.fetchingSelections = false;
    },
    async runMagic() {
      this.loading = true;
      this.result = null;
      try {
        const res = await fetch(`${API_BASE}/start-magic`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            intention_id: this.selected.intention?.id,
            case_id: this.selected.case?.id,
            provider_id: this.selected.provider?.id,
            catalog_id: this.selected.catalog?.id
          })
        });
        const data = await res.json();
        console.log('Full start-magic response:', data);
        if (data.buy_payload) {
          console.log('Buy payload sent to server:', data.buy_payload);
        }
        if (data.sell_payload) {
          console.log('Sell payload sent to server:', data.sell_payload);
        }
        this.result = data;
      } catch (e) {
        this.result = { status: 'error', error: e.message };
      }
      this.loading = false;
    },
    holdPeriodString(minutes) {
      if (!minutes) return '';
      if (minutes % (60 * 24) === 0) return (minutes / (60 * 24)) + ' days';
      if (minutes % 60 === 0) return (minutes / 60) + ' hours';
      return minutes + ' minutes';
    }
  },
  mounted() {
    this.fetchSelections();
  }
};
</script>

<style scoped>
.start-magic-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
}
.summary-panel {
  background: linear-gradient(135deg, #23272a 80%, #42b983 100%);
  color: #fff;
  padding: 2.5rem 2.5rem 2rem 2.5rem;
  border-radius: 16px;
  min-width: 320px;
  box-shadow: 0 8px 32px #0006, 0 1.5px 8px #42b98344;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  position: relative;
  perspective: 900px;
}
.summary-panel h3 {
  font-size: 1.5rem;
  margin-bottom: 1.5rem;
  color: #ffe066;
  letter-spacing: 1px;
  text-shadow: 0 2px 8px #0008, 0 0.5px 0 #fff8;
}
.summary-card {
  background: linear-gradient(120deg, #23272a 80%, #42b98322 100%);
  border-radius: 12px;
  padding: 1rem 1.5rem;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  box-shadow: 0 4px 18px #0004, 0 1.5px 8px #42b98333;
  font-size: 1.1rem;
  transform: translateZ(10px) scale(1.01);
  transition: box-shadow 0.2s, transform 0.2s;
}
.summary-card:hover {
  box-shadow: 0 8px 32px #42b98366, 0 2px 12px #0006;
  transform: translateZ(20px) scale(1.03) rotateY(-2deg);
}
.intention-card {
  border: 2.5px solid #42b983;
  background: linear-gradient(100deg, #42b98344 0%, #fff0 100%);
  font-size: 1.25rem;
  font-weight: 700;
  color: #ffe066;
  text-shadow: 0 1px 4px #0008, 0 0.5px 0 #fff8;
  box-shadow: 0 8px 32px #42b98377, 0 2px 12px #0008;
  transform: translateZ(30px) scale(1.04) rotateY(-3deg);
  z-index: 2;
}
.icon {
  font-size: 1.5rem;
  margin-right: 0.7rem;
  filter: drop-shadow(0 2px 4px #0006);
}
.summary-text b {
  color: #fff;
  font-weight: 700;
  text-shadow: 0 1px 4px #0008;
}
.magic-desc {
  margin-top: 1.5rem;
  font-size: 1.05rem;
  color: #b2f7ef;
  font-style: italic;
  text-shadow: 0 1px 4px #0008, 0 0.5px 0 #fff8;
}
.arrow-panel {
  font-size: 3rem;
  margin: 0 2rem;
  color: #42b983;
  display: flex;
  align-items: center;
}
.arrow {
  font-size: 4rem;
  font-weight: bold;
}
.action-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.start-magic-btn {
  background: linear-gradient(270deg, #42b983, #6a82fb, #fc5c7d, #f7971e, #42b983);
  background-size: 1000% 1000%;
  animation: magic-gradient 6s ease-in-out infinite;
  color: #fff;
  font-size: 2.5rem;
  width: 150px;
  height: 150px;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  font-weight: bold;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 8px 32px #42b98355,
    0 2px 16px #0008,
    0 0 0 6px #fff2 inset,
    0 0 24px 4px #ffe06655;
  position: relative;
  z-index: 1;
  transition: box-shadow 0.15s, transform 0.15s;
  overflow: hidden;
}
.start-magic-btn::before {
  content: '';
  position: absolute;
  top: 18px;
  left: 30px;
  width: 90px;
  height: 30px;
  background: linear-gradient(120deg, #fff8 0%, #fff2 100%);
  border-radius: 50%;
  opacity: 0.7;
  filter: blur(2px);
  pointer-events: none;
  z-index: 2;
}
.start-magic-btn:active {
  box-shadow:
    0 2px 8px #42b98377,
    0 1px 4px #0008,
    0 0 0 3px #fff2 inset,
    0 0 12px 2px #ffe06655;
  transform: scale(0.97);
}
@keyframes magic-gradient {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}
.start-magic-btn:disabled {
  background: #888;
  cursor: not-allowed;
}
.loading {
  color: #aaa;
  margin-bottom: 1rem;
}
.result {
  margin-top: 1rem;
  background: #23272a;
  color: #fff;
  padding: 1rem 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px #0002;
}
.result .error {
  color: #ff7675;
}
.missing-warning {
  color: #ff7675;
  background: #4d2d2d;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  margin-bottom: 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.75em;
}
.action-link {
  color: #42b983;
  background: #fff1;
  border-radius: 4px;
  padding: 0.2em 0.7em;
  margin-left: 0.5em;
  font-size: 0.98em;
  font-weight: 600;
  text-decoration: underline;
  transition: background 0.2s, color 0.2s;
}
.action-link:hover {
  background: #42b983;
  color: #fff;
}
.loading-selections {
  color: #ffe066;
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
}
.spinner {
  width: 1.5em;
  height: 1.5em;
  border: 3px solid #ffe066;
  border-top: 3px solid #42b983;
  border-radius: 50%;
  margin-right: 0.75em;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style> 