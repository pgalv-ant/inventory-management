<template>
  <div class="reports">
    <div class="page-header">
      <h2>{{ t('reports.title', 'Performance Reports') }}</h2>
      <p>{{ t('reports.description', 'View quarterly performance metrics and monthly trends') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Quarterly Performance -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.quarterly', 'Quarterly Performance') }}</h3>
        </div>
        <div class="table-container">
          <table class="reports-table">
            <thead>
              <tr>
                <th>{{ t('reports.quarter', 'Quarter') }}</th>
                <th>{{ t('reports.totalOrders', 'Total Orders') }}</th>
                <th>{{ t('reports.totalRevenue', 'Total Revenue') }}</th>
                <th>{{ t('reports.avgOrderValue', 'Avg Order Value') }}</th>
                <th>{{ t('reports.fulfillmentRate', 'Fulfillment Rate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in quarterlyData" :key="q.quarter">
                <td><strong>{{ q.quarter }}</strong></td>
                <td>{{ q.total_orders }}</td>
                <td>{{ currencySymbol }}{{ formatNumber(q.total_revenue) }}</td>
                <td>{{ currencySymbol }}{{ formatNumber(q.avg_order_value) }}</td>
                <td>
                  <span :class="getFulfillmentClass(q.fulfillment_rate)">
                    {{ q.fulfillment_rate }}%
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Monthly Trends Chart -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.monthlyTrend', 'Monthly Revenue Trend') }}</h3>
        </div>
        <div class="chart-container">
          <div class="bar-chart">
            <div v-for="month in monthlyData" :key="month.month" class="bar-wrapper">
              <div class="bar-container">
                <div
                  class="bar"
                  :style="{ height: getBarHeight(month.revenue) + 'px' }"
                  :title="currencySymbol + formatNumber(month.revenue)"
                ></div>
              </div>
              <div class="bar-label">{{ formatMonth(month.month) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Month-over-Month Comparison -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.monthOverMonth', 'Month-over-Month Analysis') }}</h3>
        </div>
        <div class="table-container">
          <table class="reports-table">
            <thead>
              <tr>
                <th>{{ t('reports.month', 'Month') }}</th>
                <th>{{ t('reports.orders', 'Orders') }}</th>
                <th>{{ t('reports.revenue', 'Revenue') }}</th>
                <th>{{ t('reports.change', 'Change') }}</th>
                <th>{{ t('reports.growthRate', 'Growth Rate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(month, index) in monthlyData" :key="month.month">
                <td><strong>{{ formatMonth(month.month) }}</strong></td>
                <td>{{ month.order_count }}</td>
                <td>{{ currencySymbol }}{{ formatNumber(month.revenue) }}</td>
                <td>
                  <span v-if="index > 0" :class="getChangeClass(month.revenue, monthlyData[index - 1].revenue)">
                    {{ getChangeValue(month.revenue, monthlyData[index - 1].revenue) }}
                  </span>
                  <span v-else>-</span>
                </td>
                <td>
                  <span v-if="index > 0" :class="getChangeClass(month.revenue, monthlyData[index - 1].revenue)">
                    {{ getGrowthRate(month.revenue, monthlyData[index - 1].revenue) }}
                  </span>
                  <span v-else>-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Summary Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.totalRevenueYTD', 'Total Revenue (YTD)') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ formatNumber(totalRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.avgMonthlyRevenue', 'Avg Monthly Revenue') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ formatNumber(avgMonthlyRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.totalOrdersYTD', 'Total Orders (YTD)') }}</div>
          <div class="stat-value">{{ totalOrders }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.bestQuarter', 'Best Performing Quarter') }}</div>
          <div class="stat-value">{{ bestQuarter }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Reports',
  setup() {
    const { t, currentCurrency, currentLocale } = useI18n()
    const { selectedLocation, selectedCategory, selectedStatus, getCurrentFilters } = useFilters()

    const currencySymbol = computed(() => currentCurrency.value === 'JPY' ? '¥' : '$')

    const loading = ref(true)
    const error = ref(null)
    const quarterlyData = ref([])
    const monthlyData = ref([])

    // Summary stats derived from raw data — auto-update when data refetches
    const totalRevenue = computed(() =>
      monthlyData.value.reduce((sum, m) => sum + m.revenue, 0)
    )
    const avgMonthlyRevenue = computed(() =>
      monthlyData.value.length ? totalRevenue.value / monthlyData.value.length : 0
    )
    const totalOrders = computed(() =>
      monthlyData.value.reduce((sum, m) => sum + m.order_count, 0)
    )
    const bestQuarter = computed(() =>
      quarterlyData.value.reduce(
        (best, q) => q.total_revenue > (best?.total_revenue ?? 0) ? q : best,
        null
      )?.quarter ?? '—'
    )
    // Cache max once per dataset instead of recomputing per bar
    const maxMonthlyRevenue = computed(() =>
      Math.max(...monthlyData.value.map(m => m.revenue), 0)
    )

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
        const filters = getCurrentFilters()
        const [quarterly, monthly] = await Promise.all([
          api.getQuarterlyReports(filters),
          api.getMonthlyTrends(filters)
        ])
        quarterlyData.value = quarterly
        monthlyData.value = monthly
      } catch (err) {
        console.error('Failed to load reports:', err)
        error.value = 'Failed to load reports: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Reports aggregate across time, so the period filter doesn't apply — only refetch on the others
    watch([selectedLocation, selectedCategory, selectedStatus], loadData)
    onMounted(loadData)

    const formatNumber = (num) =>
      num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })

    const formatMonth = (monthStr) => {
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      // Noon UTC keeps the date stable across all timezones (avoids UTC-midnight rolling back a day)
      return new Date(monthStr + '-01T12:00:00Z').toLocaleDateString(locale, { year: 'numeric', month: 'short' })
    }

    const getBarHeight = (revenue) =>
      maxMonthlyRevenue.value === 0 ? 0 : (revenue / maxMonthlyRevenue.value) * 200

    const getFulfillmentClass = (rate) => {
      if (rate >= 90) return 'badge success'
      if (rate >= 75) return 'badge warning'
      return 'badge danger'
    }

    const getChangeValue = (current, previous) => {
      const change = current - previous
      if (change > 0) return '+' + currencySymbol.value + formatNumber(change)
      if (change < 0) return '-' + currencySymbol.value + formatNumber(Math.abs(change))
      return currencySymbol.value + '0.00'
    }

    const getChangeClass = (current, previous) => {
      const change = current - previous
      if (change > 0) return 'positive-change'
      if (change < 0) return 'negative-change'
      return ''
    }

    const getGrowthRate = (current, previous) => {
      if (previous === 0) return 'N/A'
      const rate = ((current - previous) / previous) * 100
      return (rate > 0 ? '+' : '') + rate.toFixed(1) + '%'
    }

    return {
      t, currencySymbol, loading, error,
      quarterlyData, monthlyData,
      totalRevenue, avgMonthlyRevenue, totalOrders, bestQuarter,
      formatNumber, formatMonth, getBarHeight,
      getFulfillmentClass, getChangeValue, getChangeClass, getGrowthRate
    }
  }
}
</script>

<style scoped>
.reports-table {
  width: 100%;
  border-collapse: collapse;
}

.reports-table th {
  text-align: left;
  padding: 0.75rem 1rem;
  font-size: 0.813rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--color-border);
}

.reports-table td {
  padding: 0.875rem 1rem;
  font-size: 0.875rem;
  border-bottom: 1px solid var(--color-border);
}

.reports-table tr:last-child td {
  border-bottom: none;
}

.chart-container {
  padding: 1rem 0;
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  gap: 0.5rem;
  height: 240px;
  padding: 0 1rem;
}

.bar-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.bar-container {
  width: 100%;
  height: 200px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.bar {
  width: 70%;
  background: var(--color-link);
  border-radius: 4px 4px 0 0;
  transition: height 0.3s ease;
}

.bar-label {
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  text-align: center;
}

.positive-change {
  color: #059669;
  font-weight: 500;
}

.negative-change {
  color: #dc2626;
  font-weight: 500;
}

.stats-grid {
  margin-top: 1.5rem;
}
</style>
