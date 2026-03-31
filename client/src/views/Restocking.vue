<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking</h2>
      <p>Set a budget and get restock recommendations from demand forecasts</p>
    </div>

    <div class="card budget-card">
      <div class="budget-control">
        <label class="budget-label">Available Budget</label>
        <div class="slider-row">
          <input
            type="range"
            min="1000"
            max="50000"
            step="500"
            :value="budget"
            @input="onBudgetInput"
            class="budget-slider"
          />
          <span class="budget-value">${{ budget.toLocaleString() }}</span>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading recommendations...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="recommendations.length === 0" class="empty-state">
      No items need restocking within this budget
    </div>
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Recommendations ({{ recommendations.length }})</h3>
        </div>
        <div class="table-container">
          <table class="restock-table">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Item</th>
                <th>Category</th>
                <th>Shortfall</th>
                <th>Qty</th>
                <th>Unit Cost</th>
                <th>Line Total</th>
                <th>Lead Time</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rec in recommendations" :key="rec.sku">
                <td><strong>{{ rec.sku }}</strong></td>
                <td>{{ rec.name }}</td>
                <td>{{ rec.category }}</td>
                <td>{{ rec.shortfall.toLocaleString() }}</td>
                <td>{{ rec.recommended_quantity.toLocaleString() }}</td>
                <td>${{ rec.unit_cost.toLocaleString() }}</td>
                <td><strong>${{ rec.line_total.toLocaleString() }}</strong></td>
                <td>{{ rec.lead_time_days }} days</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="summary-row">
          <span class="summary-text">
            Total: <strong>${{ totalCost.toLocaleString() }}</strong>
            &mdash;
            Remaining budget: <strong>${{ remainingBudget.toLocaleString() }}</strong>
          </span>
          <button
            class="place-order-btn"
            :disabled="recommendations.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? 'Placing Order...' : 'Place Order' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="successMessage" class="success-banner">
      {{ successMessage }}
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { api } from '../api'

export default {
  name: 'Restocking',
  setup() {
    const budget = ref(15000)
    const recommendations = ref([])
    const totalCost = ref(0)
    const remainingBudget = ref(0)
    const loading = ref(false)
    const error = ref(null)
    const submitting = ref(false)
    const successMessage = ref('')

    let debounceTimer = null

    const loadRecommendations = async () => {
      loading.value = true
      error.value = null
      try {
        const data = await api.getRestockingRecommendations(budget.value)
        recommendations.value = data.recommendations
        totalCost.value = data.total_cost
        remainingBudget.value = data.remaining_budget
      } catch (err) {
        error.value = 'Failed to load recommendations'
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    const onBudgetInput = (e) => {
      budget.value = Number(e.target.value)
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        loadRecommendations()
      }, 300)
    }

    const placeOrder = async () => {
      if (recommendations.value.length === 0 || submitting.value) return
      submitting.value = true
      error.value = null
      try {
        const items = recommendations.value.map(rec => ({
          sku: rec.sku,
          name: rec.name,
          quantity: rec.recommended_quantity,
          unit_price: rec.unit_cost,
          category: rec.category,
          lead_time_days: rec.lead_time_days
        }))
        const order = await api.placeRestockingOrder(items)
        successMessage.value = `Order ${order.order_number} placed. View it in the Orders tab.`
        recommendations.value = []
        totalCost.value = 0
        remainingBudget.value = budget.value
        setTimeout(() => {
          successMessage.value = ''
        }, 5000)
      } catch (err) {
        error.value = 'Failed to place order'
        console.error(err)
      } finally {
        submitting.value = false
      }
    }

    onMounted(() => loadRecommendations())

    return {
      budget,
      recommendations,
      totalCost,
      remainingBudget,
      loading,
      error,
      submitting,
      successMessage,
      onBudgetInput,
      placeOrder
    }
  }
}
</script>

<style scoped>
.restocking {
  padding: 0;
}

.budget-card {
  margin-bottom: 1.25rem;
}

.budget-control {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.budget-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.slider-row {
  display: flex;
  align-items: center;
  gap: 1.25rem;
}

.budget-slider {
  flex: 1;
  height: 6px;
  accent-color: #2563eb;
  cursor: pointer;
}

.budget-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  min-width: 90px;
  text-align: right;
  letter-spacing: -0.025em;
}

.restock-table {
  table-layout: auto;
  width: 100%;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #64748b;
  font-size: 0.938rem;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 0.75rem 0.25rem;
  border-top: 1px solid #e2e8f0;
  margin-top: 0.5rem;
}

.summary-text {
  font-size: 0.938rem;
  color: #334155;
}

.place-order-btn {
  padding: 0.625rem 1.5rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.success-banner {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 1rem 1.25rem;
  border-radius: 8px;
  font-size: 0.938rem;
  font-weight: 500;
  margin-top: 1rem;
}
</style>
