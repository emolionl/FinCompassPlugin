<template>
  <div class="dashboard-view">
    <div v-if="loading" class="loading">Loading...</div>
    <div v-else>
      <div v-if="!hasValidServer">
        <div class="warning">
          <h3>Setup Required</h3>
          <p>You must configure at least one server with an API key before using the dashboard.</p>
          <a href="#" @click.prevent="$emit('gotoServers')">Go to Servers</a>
        </div>
      </div>
      <div v-else>
        <h2>Dashboard</h2>
        <p>Welcome to the FinCompass dashboard!</p>
      </div>
    </div>
  </div>
</template>

<script>
import { API_BASE } from '../api';
export default {
  name: 'FinCompassDashboard',
  data() {
    return {
      servers: [],
      loading: true
    }
  },
  computed: {
    hasValidServer() {
      return this.servers.some(s => s.api_key && s.api_key.trim() !== '');
    }
  },
  methods: {
    async fetchServers() {
      this.loading = true;
      try {
        const res = await fetch(`${API_BASE}/servers`);
        if (res.ok) {
          const data = await res.json();
          this.servers = data.servers || [];
        } else {
          this.servers = [];
        }
      } catch (e) {
        this.servers = [];
      }
      this.loading = false;
    }
  },
  mounted() {
    this.fetchServers();
  }
}
</script>

<style scoped>
.dashboard-view {
  padding: 2rem;
  color: #e0e0e0;
}
.loading {
  text-align: center;
  font-size: 1.2rem;
  color: #aaa;
}
.warning {
  background: #333;
  color: #ffb300;
  border-radius: 8px;
  padding: 1.5rem;
  margin: 2rem auto;
  max-width: 500px;
  text-align: center;
}
.warning h3 {
  margin-top: 0;
}
.warning a {
  color: #42b983;
  text-decoration: underline;
  cursor: pointer;
}
</style> 