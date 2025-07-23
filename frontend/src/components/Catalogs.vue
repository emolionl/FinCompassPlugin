<template>
  <div class="catalogs-view">
    <h2>Analysis Catalogs</h2>
    <p class="subtitle">Select the catalog to use for analysis.</p>
    
    <div v-if="loading" class="loading">Loading catalogs...</div>
    <div v-else-if="error" class="error-message">{{ error }}</div>
    <div v-else>
      <div v-if="!catalogs.length" class="no-catalogs">
        No catalogs found. Ensure AetherOnePy core is running.
      </div>
      <ul v-else class="catalogs-list">
        <li 
          v-for="catalog in catalogs" 
          :key="catalog.id" 
          class="catalog-item" 
          :class="{ 'selected': catalog.selected }"
        >
          <span class="catalog-name">{{ catalog.name }}</span>
          <button 
            @click="toggleCatalog(catalog)"
            :class="{ 'selected-btn': catalog.selected }"
          >
            {{ catalog.selected ? 'Selected (click to deselect)' : 'Select' }}
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import { API_BASE } from '../api';
export default {
  name: 'FinCompassCatalogs',
  data() {
    return {
      catalogs: [],
      loading: true,
      error: ''
    };
  },
  methods: {
    async fetchCatalogs() {
      this.loading = true;
      this.error = '';
      try {
        const res = await fetch(`${API_BASE}/catalogs`);
        const data = await res.json();
        if (res.ok && data.status === 'success') {
          this.catalogs = data.catalogs || [];
        } else {
          this.error = data.error || 'Failed to load catalogs.';
        }
      } catch (e) {
        this.error = 'Network error or could not fetch catalogs.';
      }
      this.loading = false;
    },
    async toggleCatalog(catalog) {
      this.error = '';
      try {
        if (catalog.selected) {
          // Deselect all
          const res = await fetch(`${API_BASE}/catalogs/deselect`, { method: 'POST' });
          const data = await res.json();
          if (!res.ok || data.status !== 'success') {
            throw new Error(data.error || 'Failed to deselect.');
          }
        } else {
          // Select this catalog
          const res = await fetch(`${API_BASE}/catalogs/${catalog.id}/select`, { method: 'POST' });
          const data = await res.json();
          if (!res.ok || data.status !== 'success') {
            throw new Error(data.error || 'Failed to select the catalog.');
          }
        }
        await this.fetchCatalogs();
      } catch (e) {
        this.error = e.message;
      }
    }
  },
  mounted() {
    this.fetchCatalogs();
  }
};
</script>

<style scoped>
.catalogs-view {
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
.no-catalogs {
  text-align: center;
  padding: 2rem;
  color: #888;
}
.catalogs-list {
  list-style: none;
  padding: 0;
}
.catalog-item {
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
.catalog-item.selected {
  background-color: #36393f;
  border-left-color: #42b983;
}
.catalog-name {
  font-weight: 600;
}
.catalog-item button {
  background-color: #40444b;
  color: #fff;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
  font-weight: 600;
}
.catalog-item button:hover {
  background-color: #52575e;
}
.catalog-item button.selected-btn {
  background-color: #42b983;
  cursor: pointer;
}
.catalog-item button:disabled {
  opacity: 0.7;
}
.catalog-item button:disabled:hover {
  background-color: #42b983;
}
</style> 