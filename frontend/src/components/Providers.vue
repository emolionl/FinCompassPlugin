<template>
  <div class="providers-view">
    <h2>Available Providers</h2>
    <div v-if="loading" class="loading">Loading providers...</div>
    <div v-else-if="error">
      <div class="error-message">
        {{ error }}
        <template v-if="error && error.toLowerCase().includes('no server selected')">
          <a href="#/servers" class="action-link">Action: Select Server</a>
        </template>
      </div>
    </div>
    <div v-else>
      <div v-if="!providers.length" class="no-providers">No providers found for the selected server.</div>
      <div v-else>
        <ul class="providers-list">
          <li v-for="provider in providers" :key="provider.id" class="provider-item" :class="{ 'selected': provider.selected }">
            <span class="provider-name">{{ provider.name || provider.id }}</span>
            <button 
              @click="toggleProvider(provider)"
              :class="{ 'selected-btn': provider.selected }"
            >
              {{ provider.selected ? 'Selected (click to deselect)' : 'Select' }}
            </button>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import { API_BASE } from '../api';
export default {
  name: 'FinCompassProviders',
  data() {
    return {
      providers: [],
      loading: true,
      error: ''
    }
  },
  methods: {
    async fetchProviders() {
      this.loading = true;
      this.error = '';
      try {
        const res = await fetch(`${API_BASE}/providers`);
        const data = await res.json();
        if (res.ok && data.status === 'success') {
          // The API might return providers nested under a 'results' key or directly
          this.providers = Array.isArray(data.providers) ? data.providers : (data.providers.results || []);
        } else {
          this.error = data.error || 'Failed to load providers.';
        }
      } catch (e) {
        this.error = 'Network error or could not fetch providers.';
      }
      this.loading = false;
    },
    async toggleProvider(provider) {
      this.error = '';
      try {
        if (provider.selected) {
          // Deselect this provider
          const res = await fetch(`${API_BASE}/providers/${provider.id}/deselect`, { method: 'POST' });
          const data = await res.json();
          if (!res.ok || data.status !== 'success') {
            throw new Error(data.error || 'Failed to deselect provider.');
          }
        } else {
          // Select this provider
          const res = await fetch(`${API_BASE}/providers/${provider.id}/select`, { method: 'POST' });
          const data = await res.json();
          if (!res.ok || data.status !== 'success') {
            throw new Error(data.error || 'Failed to select provider.');
          }
        }
        await this.fetchProviders();
      } catch (e) {
        this.error = e.message;
      }
    }
  },
  mounted() {
    this.fetchProviders();
  }
}
</script>

<style scoped>
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
.providers-view {
  color: #e0e0e0;
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
.no-providers {
  text-align: center;
  padding: 2rem;
  color: #888;
}
.providers-list {
  list-style: none;
  padding: 0;
}
.provider-item {
  background: #2c2f33;
  border-radius: 6px;
  padding: 1rem 1.5rem;
  margin-bottom: 0.75rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background-color 0.2s;
  border-left: 4px solid transparent;
}
.provider-item.selected {
  background-color: #36393f;
  border-left-color: #42b983;
}
.provider-name {
  font-weight: 600;
}
.provider-item button {
  background-color: #40444b;
  color: #fff;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}
.provider-item button:hover {
  background-color: #52575e;
}
.provider-item button.selected-btn {
  background-color: #42b983;
  cursor: default;
  font-weight: bold;
}
.provider-item button:disabled {
  opacity: 0.7;
}
</style> 