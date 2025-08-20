<template>
  <div class="intentions-view">
    <h2>Manage Intentions</h2>

    <div class="toolbar">
      <button @click="openCreateModal">Add New Intention</button>
    </div>

    <!-- Intentions List -->
    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <ul v-else class="intentions-list">
      <li v-for="intention in intentions" :key="intention.id" class="intention-item">
        <div class="view-mode">
          <div class="intention-details">
            <strong>{{ intention.intention }}</strong>
            <p v-if="intention.description">{{ intention.description }}</p>
          </div>
          <div class="intention-actions">
            <button @click="selectIntention(intention)" :class="{ 'selected-btn': intention.selected }">
              {{ intention.selected ? 'Selected' : 'Select' }}
            </button>
            <button @click="openEditModal(intention)">Edit</button>
            <button @click="deleteIntention(intention.id)" class="danger">Delete</button>
          </div>
        </div>
      </li>
    </ul>

    <!-- Modal for Create/Edit -->
    <div v-if="showModal" class="modal-overlay">
      <div class="modal-content">
        <h3>{{ modalForm.isEdit ? 'Edit Intention' : 'Create New Intention' }}</h3>
        <form @submit.prevent="handleModalSubmit">
          <div class="form-group">
            <label for="intention">Intention</label>
            <input id="intention" v-model="modalForm.intention" placeholder="e.g., 'Financial Growth'" required />
          </div>
          <div class="form-group">
            <label for="description">Description</label>
            <input id="description" v-model="modalForm.description" placeholder="Optional details" />
          </div>
          <div class="form-group checkbox-group">
            <input type="checkbox" id="selected" v-model="modalForm.selected" />
            <label for="selected">Set as selected</label>
          </div>
          <div class="form-group">
            <label for="amount">Amount to Invest</label>
            <input type="number" min="0" step="any" id="amount" v-model.number="modalForm.amount" placeholder="e.g. 1000" />
            <small>Default amount to invest for this intention (can be overridden per schedule).</small>
          </div>
          <div class="form-group">
            <label for="holdMinutes">Hold Period</label>
            <div class="hold-period-inputs">
              <input type="number" min="0" v-model.number="holdValue" id="holdMinutes" style="width: 80px;" />
              <select v-model="holdUnit">
                <option value="minutes">Minutes</option>
                <option value="hours">Hours</option>
                <option value="days">Days</option>
              </select>
            </div>
            <small>How long to hold before selling (used as default for schedules).</small>
          </div>
          <div class="form-group">
            <label for="stopLoss">Stop Loss Percentage</label>
            <input type="number" min="0" max="100" step="0.1" id="stopLoss" v-model.number="modalForm.stop_loss_percentage" placeholder="e.g. 5.0" />
            <small>Percentage loss at which to sell (e.g., 5.0 for 5%).</small>
          </div>
          <div class="form-group">
            <label for="takeProfit">Take Profit Percentage</label>
            <input type="number" min="0" max="1000" step="0.1" id="takeProfit" v-model.number="modalForm.take_profit_percentage" placeholder="e.g. 15.0" />
            <small>Percentage gain at which to sell (e.g., 15.0 for 15%).</small>
          </div>
          <div class="modal-actions">
            <button type="submit">{{ modalForm.isEdit ? 'Save Changes' : 'Create' }}</button>
            <button type="button" @click="closeModal">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { API_BASE } from '../api';
export default {
  name: 'FinCompassIntentions',
  data() {
    return {
      intentions: [],
      loading: true,
      error: '',
      showModal: false,
      modalForm: {
        isEdit: false,
        data: {
          id: null,
          intention: '',
          description: '',
          selected: false,
          buy_datetime: '',
          sell_datetime: '',
          hold_minutes: 0,
          amount: 0,
          stop_loss_percentage: 0,
          take_profit_percentage: 0
        }
      },
      holdValue: 0,
      holdUnit: 'minutes',
    };
  },
  watch: {
    'modalForm': {
      handler(newVal) {
        // When editing, convert hold_minutes to value/unit
        if (newVal && typeof newVal.hold_minutes === 'number') {
          if (newVal.hold_minutes % (60 * 24) === 0) {
            this.holdValue = newVal.hold_minutes / (60 * 24);
            this.holdUnit = 'days';
          } else if (newVal.hold_minutes % 60 === 0) {
            this.holdValue = newVal.hold_minutes / 60;
            this.holdUnit = 'hours';
          } else {
            this.holdValue = newVal.hold_minutes;
            this.holdUnit = 'minutes';
          }
        } else {
          this.holdValue = 0;
          this.holdUnit = 'minutes';
        }
      },
      immediate: true,
      deep: true
    }
  },
  methods: {
    async fetchIntentions() {
      this.loading = true;
      try {
        const response = await fetch(`${API_BASE}/intentions`);
        if (!response.ok) throw new Error('Failed to fetch intentions');
        this.intentions = await response.json();
      } catch (err) {
        this.error = err.message;
      } finally {
        this.loading = false;
      }
    },
    openCreateModal() {
      this.modalForm = {
        id: null,
        intention: '',
        description: '',
        selected: false,
        hold_minutes: 0,
        amount: 0,
        stop_loss_percentage: 0,
        take_profit_percentage: 0
      };
      this.showModal = true;
    },
    openEditModal(intention) {
      this.modalForm = {
        id: intention.id,
        intention: intention.intention,
        description: intention.description,
        selected: intention.selected,
        hold_minutes: intention.hold_minutes || 0,
        amount: intention.amount || 0,
        stop_loss_percentage: intention.stop_loss_percentage || 0,
        take_profit_percentage: intention.take_profit_percentage || 0
      };
      this.showModal = true;
    },
    closeModal() {
      this.showModal = false;
    },
    async handleModalSubmit() {
      if (this.modalForm.isEdit) {
        await this.saveEdit();
      } else {
        await this.createIntention();
      }
    },
    async createIntention() {
      await this.saveIntention();
    },
    async saveEdit() {
      // If we are setting an intention to 'selected', we should unselect the currently selected one first.
      if (this.modalForm.data.selected) {
        const currentlySelected = this.intentions.find(i => i.selected && i.id !== this.modalForm.data.id);
        if (currentlySelected) {
           await fetch(`${API_BASE}/intentions/${currentlySelected.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ...currentlySelected, selected: false })
            });
        }
      }

      await this.saveIntention();
    },
    async deleteIntention(id) {
      if (!confirm('Are you sure you want to delete this intention?')) return;
      await fetch(`${API_BASE}/intentions/${id}`, {
        method: 'DELETE'
      });
      await this.fetchIntentions();
    },
    async selectIntention(intentionToSelect) {
      // Unselect all others, then select the new one
      const updates = this.intentions.map(i => {
          const shouldBeSelected = i.id === intentionToSelect.id;
          if (i.selected !== shouldBeSelected) {
              return fetch(`${API_BASE}/intentions/${i.id}`, {
                  method: 'PUT',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ ...i, selected: shouldBeSelected })
              });
          }
          return Promise.resolve();
      });
      
      await Promise.all(updates);
      await this.fetchIntentions();
    },
    async saveIntention() {
      this.error = '';
      try {
        let hold_minutes = 0;
        if (this.holdUnit === 'days') hold_minutes = this.holdValue * 24 * 60;
        else if (this.holdUnit === 'hours') hold_minutes = this.holdValue * 60;
        else hold_minutes = this.holdValue;
        const payload = {
          intention: this.modalForm.intention,
          description: this.modalForm.description,
          selected: this.modalForm.selected,
          hold_minutes,
          amount: this.modalForm.amount,
          stop_loss_percentage: this.modalForm.stop_loss_percentage,
          take_profit_percentage: this.modalForm.take_profit_percentage
        };
        let res;
        if (this.modalForm.id) {
          res = await fetch(`${API_BASE}/intentions/${this.modalForm.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
        } else {
          res = await fetch(`${API_BASE}/intentions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
        }
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Failed to save intention.');
        this.showModal = false;
        await this.fetchIntentions();
      } catch (e) {
        this.error = e.message;
      }
    }
  },
  mounted() {
    this.fetchIntentions();
  }
};
</script>

<style scoped>
.intentions-view {
  color: #e0e0e0;
  padding: 1rem;
}
.toolbar {
  margin-bottom: 1.5rem;
}
.toolbar button {
  background: #42b983;
  color: #fff;
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}
.intentions-list {
  list-style: none;
  padding: 0;
}
.intention-item {
  background: #2c2f33;
  border-radius: 6px;
  padding: 1rem 1.5rem;
  margin-bottom: 1rem;
  border-left: 4px solid transparent;
}
.intention-item.selected {
  border-left-color: #42b983;
}
.view-mode {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.intention-details p {
  margin: 0.25rem 0 0;
  color: #aaa;
  font-size: 0.9rem;
}
.intention-actions {
  display: flex;
  gap: 0.5rem;
}
.intention-actions button {
  background: #40444b;
  color: #fff;
  border: none;
  padding: 0.4rem 0.8rem;
  border-radius: 4px;
  cursor: pointer;
}
.intention-actions button.danger {
  background: #992e2e;
}
.intention-actions button.selected-btn {
  background: #42b983;
  font-weight: bold;
}
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
}
.modal-content {
  background-color: #2c2f33;
  padding: 2rem;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
}
.modal-content h3 {
  margin-top: 0;
  margin-bottom: 1.5rem;
}
.form-group {
  margin-bottom: 1rem;
}
.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #b0b0b0;
}
.form-group input[type="text"], 
.form-group input[type="password"],
.form-group input[type="number"] {
  width: 100%;
  padding: 0.75rem;
  border-radius: 4px;
  border: 1px solid #40444b;
  background: #181a1b;
  color: #e0e0e0;
  box-sizing: border-box; /* Added */
}
.checkbox-group {
    display: flex;
    align-items: center;
}
.checkbox-group input {
    margin-right: 0.5rem;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 2rem;
}
.modal-actions button {
  padding: 0.6rem 1.2rem;
  border-radius: 4px;
  border: none;
  cursor: pointer;
}
.modal-actions button[type="submit"] {
  background-color: #42b983;
  color: white;
}
.modal-actions button[type="button"] {
  background-color: #40444b;
  color: white;
}
.hold-period-inputs {
  display: flex;
  align-items: center;
}
.hold-period-inputs input {
  margin-right: 0.5rem;
}
.hold-period-inputs select {
  margin-right: 1rem;
}
</style> 