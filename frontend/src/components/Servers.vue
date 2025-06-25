<template>
  <div class="servers-view">
    <h2>Servers</h2>
    <form class="add-server-form" @submit.prevent="addServer">
      <input v-model="newServerUrl" placeholder="Server URL (e.g. https://fincompass.emolio.nl)" required />
      <input v-model="newServerDescription" placeholder="Description (optional)" />
      <input v-model="newServerApiKey" placeholder="API Key (optional)" />
      <button type="submit">Add Server</button>
    </form>
    <div v-if="loading" class="loading">Loading...</div>
    <div v-else>
      <div v-if="!servers.length">No servers found.</div>
      <ul v-else class="server-list">
        <li v-for="server in servers" :key="server.url" class="server-item" :class="{ selected: server.selected }">
          <div style="display: flex; align-items: center; flex: 1; min-width: 0;">
            <span class="server-name">{{ server.url }}</span>
            <span v-if="server.description" class="server-desc">- {{ server.description }}</span>
          </div>
          <div class="server-actions">
            <button
              @click="toggleServer(server)"
              :class="{ 'selected-btn': server.selected }"
            >
              {{ server.selected ? 'Selected (click to deselect)' : 'Select' }}
            </button>
            <button @click="editServer(server)" class="edit-btn">Edit</button>
            <button @click="deleteServer(server)" class="danger">Delete</button>
          </div>
          <div v-if="editingUrl === server.url" class="edit-form">
            <input v-model="editDescription" placeholder="Description" />
            <input v-model="editApiKey" placeholder="API Key" />
            <button @click="saveEdit(server)">Save</button>
            <button @click="cancelEdit">Cancel</button>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FinCompassServers',
  data() {
    return {
      servers: [],
      loading: true,
      newServerUrl: '',
      newServerDescription: '',
      newServerApiKey: '',
      editingUrl: null,
      editDescription: '',
      editApiKey: ''
    }
  },
  methods: {
    async fetchServers() {
      this.loading = true;
      try {
        const res = await fetch('/fincompass/api/servers');
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
    },
    async addServer() {
      if (!this.newServerUrl) return;
      const payload = {
        url: this.newServerUrl,
        description: this.newServerDescription,
        api_key: this.newServerApiKey
      };
      const res = await fetch('/fincompass/api/servers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        this.newServerUrl = '';
        this.newServerDescription = '';
        this.newServerApiKey = '';
        await this.fetchServers();
      }
    },
    editServer(server) {
      this.editingUrl = server.url;
      this.editDescription = server.description || '';
      this.editApiKey = server.api_key || '';
    },
    cancelEdit() {
      this.editingUrl = null;
      this.editDescription = '';
      this.editApiKey = '';
    },
    async saveEdit(server) {
      // Update description
      if (server.description !== this.editDescription) {
        await fetch(`/fincompass/api/servers/${encodeURIComponent(server.url)}/description`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ description: this.editDescription })
        });
      }
      // Update API key
      if (server.api_key !== this.editApiKey) {
        await fetch(`/fincompass/api/servers/${encodeURIComponent(server.url)}/api_key`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ api_key: this.editApiKey })
        });
      }
      this.cancelEdit();
      await this.fetchServers();
    },
    async deleteServer(server) {
      if (!confirm('Delete this server?')) return;
      await fetch(`/fincompass/api/servers/${encodeURIComponent(server.url)}`, {
        method: 'DELETE'
      });
      await this.fetchServers();
    },
    async toggleServer(server) {
      if (server.selected) {
        // Deselect all
        await fetch('/fincompass/api/servers/deselect', { method: 'POST' });
      } else {
        // Select this server
        await fetch(`/fincompass/api/servers/${encodeURIComponent(server.url)}/select`, { method: 'POST' });
      }
      await this.fetchServers();
    }
  },
  mounted() {
    this.fetchServers();
  }
}
</script>

<style scoped>
.servers-view {
  /* max-width: 600px; */
  margin: 1.5rem auto;
  background: #23272a;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 16px rgba(0,0,0,0.3);
  color: #e0e0e0;
}
.add-server-form {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 2rem;
}
.add-server-form input {
  flex: 1;
  padding: 0.4rem;
  border-radius: 4px;
  border: 1px solid #444;
  background: #181a1b;
  color: #e0e0e0;
}
.add-server-form button {
  background: #42b983;
  color: #fff;
  border: none;
  padding: 0.4rem 1rem;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}
.add-server-form button:hover {
  background: #369870;
}
.server-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.server-item {
  background: #2c2f33;
  border-radius: 6px;
  padding: 1rem 1.5rem;
  margin-bottom: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  box-sizing: border-box;
  transition: background-color 0.2s, border-left-color 0.2s;
  border-left: 4px solid transparent;
}
.server-item.selected {
  background-color: #36393f;
  border-left-color: #42b983;
}
.server-name {
  font-weight: 600;
  font-size: 1.08rem;
  word-break: break-all;
}
.server-desc {
  color: #aaa;
  margin-left: 0.5em;
  font-size: 0.98em;
}
.server-actions {
  display: flex;
  gap: 0.7rem;
}
.selected-btn {
  background: #42b983 !important;
  color: #fff !important;
  font-weight: bold;
  border: none;
  border-radius: 4px;
  padding: 0.5rem 1.2rem;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}
.selected-btn:hover {
  background: #369870 !important;
}
.server-actions button {
  border: none;
  border-radius: 4px;
  padding: 0.5rem 1.2rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}
.server-actions button:not(.selected-btn):not(.danger):not(.edit-btn) {
  background: #eee;
  color: #222;
}
.server-actions .edit-btn {
  background: #2196f3;
  color: #fff;
}
.server-actions .edit-btn:hover {
  background: #1769aa;
}
.server-actions .danger {
  background: #e74c3c;
  color: #fff;
}
.server-actions .danger:hover {
  background: #c0392b;
}
.edit-form {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}
.edit-form input {
  flex: 1;
  padding: 0.4rem;
  border-radius: 4px;
  border: 1px solid #444;
  background: #181a1b;
  color: #e0e0e0;
}
.edit-form button {
  background: #42b983;
  color: #fff;
  border: none;
  padding: 0.4rem 1rem;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}
.edit-form button:hover {
  background: #369870;
}
.loading {
  text-align: center;
  font-size: 1.2rem;
  color: #aaa;
}
</style> 