<template>
  <div class="cases-view">
    <h2>Cases</h2>
    <p class="subtitle">Select the case to use for analysis.</p>
    <div v-if="loading" class="loading">Loading cases...</div>
    <div v-else-if="error" class="error-message">{{ error }}</div>
    <div v-else>
      <div v-if="!cases.length" class="no-cases">
        No cases found. Create a case first.
      </div>
      <ul v-else class="cases-list">
        <li 
          v-for="caseObj in cases" 
          :key="caseObj.id" 
          class="case-item" 
          :class="{ 'selected': caseObj.selected }"
        >
          <span class="case-name">{{ caseObj.name }}</span>
          <button 
            @click="toggleCase(caseObj)"
            :class="{ 'selected-btn': caseObj.selected }"
          >
            {{ caseObj.selected ? 'Selected (click to deselect)' : 'Select' }}
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import { API_BASE } from '../api';
export default {
  name: 'FinCompassCases',
  data() {
    return {
      cases: [],
      loading: true,
      error: ''
    };
  },
  methods: {
    async fetchCases() {
      this.loading = true;
      this.error = '';
      try {
        const res = await fetch(`${API_BASE}/cases`);
        const data = await res.json();
        if (res.ok && data.status === 'success') {
          this.cases = data.cases || [];
        } else {
          this.error = data.error || 'Failed to load cases.';
        }
      } catch (e) {
        this.error = 'Network error or could not fetch cases.';
      }
      this.loading = false;
    },
    async toggleCase(caseObj) {
      this.error = '';
      try {
        if (caseObj.selected) {
          // Deselect all
          const res = await fetch(`${API_BASE}/cases/deselect`, { method: 'POST' });
          const data = await res.json();
          if (!res.ok || data.status !== 'success') {
            throw new Error(data.error || 'Failed to deselect.');
          }
        } else {
          // Select this case
          const res = await fetch(`${API_BASE}/cases/${caseObj.id}/select`, { method: 'POST' });
          const data = await res.json();
          if (!res.ok || data.status !== 'success') {
            throw new Error(data.error || 'Failed to select the case.');
          }
        }
        await this.fetchCases();
      } catch (e) {
        this.error = e.message;
      }
    }
  },
  mounted() {
    this.fetchCases();
  }
};
</script>

<style scoped>
.cases-view {
  color: #e0e0e0;
}
.subtitle {
  color: #aaa;
  margin-top: -1rem;
  margin-bottom: 2rem;
}
.loading {
  text-align: center;
  padding: 2rem;
  color: #aaa;
}
.error-message {
  color: #ff7675;
  background-color: #4d2d2d;
  padding: 1rem;
  border-radius: 6px;
  text-align: center;
}
.no-cases {
  text-align: center;
  padding: 2rem;
  color: #888;
}
.cases-list {
  list-style: none;
  padding: 0;
}
.case-item {
  background: #2c2f33;
  border-radius: 6px;
  padding: 1rem 1.5rem;
  margin-bottom: 0.75rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background-color 0.2s, border-left-color 0.2s;
  border-left: 4px solid transparent;
}
.case-item.selected {
  background-color: #36393f;
  border-left-color: #42b983;
}
.case-name {
  font-weight: 600;
}
.case-item button {
  background-color: #40444b;
  color: #fff;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
  font-weight: 600;
}
.case-item button:hover {
  background-color: #52575e;
}
.case-item button.selected-btn {
  background-color: #42b983;
  cursor: pointer;
}
.case-item button:disabled {
  opacity: 0.7;
}
.case-item button:disabled:hover {
  background-color: #42b983;
}
</style> 