/**
 * Plant Analytics Dashboard Module
 * Chemical Plant Equipment Analytics
 */

import { ApiClient } from './api.js';
import { CONFIG } from './config.js';
import { UI } from './ui.js';

export class DashboardManager {
  static rangeChart = null;
  static typeChart = null;
  static correlationChart = null;

  static init() {
    this.bindEvents();
    this.initCharts();
  }

  static bindEvents() {
    const refreshBtn = document.getElementById('btn-refresh-dashboard');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => {
        const activeUid = localStorage.getItem(CONFIG.STORAGE_KEYS.ACTIVE_DATASET_UID);
        if (activeUid) {
          this.loadDatasetAnalytics(activeUid);
          UI.showToast('Telemetry Refreshed', 'Dashboard metrics updated.', 'info');
        } else {
          UI.showToast('No Dataset Active', 'Please select or upload a dataset first.', 'warning');
        }
      });
    }
  }

  static initCharts() {
    // 1. Parameter Ranges Chart (Min, Avg, Max)
    const rangeCtx = document.getElementById('chart-parameter-ranges')?.getContext('2d');
    if (rangeCtx && window.Chart) {
      this.rangeChart = new Chart(rangeCtx, {
        type: 'bar',
        data: {
          labels: ['Flowrate (m³/h)', 'Pressure (bar)', 'Temperature (°C)'],
          datasets: [
            {
              label: 'Minimum',
              data: [0, 0, 0],
              backgroundColor: 'rgba(6, 182, 212, 0.4)',
              borderColor: '#06b6d4',
              borderWidth: 1,
              borderRadius: 4
            },
            {
              label: 'Average',
              data: [0, 0, 0],
              backgroundColor: 'rgba(14, 165, 233, 0.7)',
              borderColor: '#0ea5e9',
              borderWidth: 1,
              borderRadius: 4
            },
            {
              label: 'Maximum',
              data: [0, 0, 0],
              backgroundColor: 'rgba(244, 63, 94, 0.6)',
              borderColor: '#f43f5e',
              borderWidth: 1,
              borderRadius: 4
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              labels: { color: '#94a3b8', font: { family: 'Inter', size: 12 } }
            }
          },
          scales: {
            x: {
              grid: { color: 'rgba(51, 65, 85, 0.3)' },
              ticks: { color: '#94a3b8' }
            },
            y: {
              grid: { color: 'rgba(51, 65, 85, 0.3)' },
              ticks: { color: '#94a3b8' }
            }
          }
        }
      });
    }

    // 2. Equipment Type Breakdown Doughnut Chart
    const typeCtx = document.getElementById('chart-type-distribution')?.getContext('2d');
    if (typeCtx && window.Chart) {
      this.typeChart = new Chart(typeCtx, {
        type: 'doughnut',
        data: {
          labels: ['Pump', 'Heat Exchanger', 'Reactor', 'Column', 'Compressor', 'Valve', 'Storage Tank'],
          datasets: [{
            data: [0, 0, 0, 0, 0, 0, 0],
            backgroundColor: [
              '#06b6d4',
              '#0ea5e9',
              '#6366f1',
              '#10b981',
              '#f59e0b',
              '#f43f5e',
              '#8b5cf6'
            ],
            borderColor: '#111827',
            borderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'right',
              labels: { color: '#94a3b8', font: { family: 'Inter', size: 11 }, boxWidth: 12 }
            }
          }
        }
      });
    }

    // 3. Pressure vs Flowrate Scatter Plot
    const corrCtx = document.getElementById('chart-correlation')?.getContext('2d');
    if (corrCtx && window.Chart) {
      this.correlationChart = new Chart(corrCtx, {
        type: 'scatter',
        data: {
          datasets: [{
            label: 'Operating Units',
            data: [],
            backgroundColor: '#06b6d4',
            borderColor: '#38bdf8',
            pointRadius: 6,
            pointHoverRadius: 8
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { labels: { color: '#94a3b8' } },
            tooltip: {
              callbacks: {
                label: (ctx) => `Flow: ${ctx.raw.x} m³/h, Press: ${ctx.raw.y} bar (${ctx.raw.name || 'Unit'})`
              }
            }
          },
          scales: {
            x: {
              title: { display: true, text: 'Flowrate (m³/h)', color: '#94a3b8' },
              grid: { color: 'rgba(51, 65, 85, 0.3)' },
              ticks: { color: '#94a3b8' }
            },
            y: {
              title: { display: true, text: 'Pressure (bar)', color: '#94a3b8' },
              grid: { color: 'rgba(51, 65, 85, 0.3)' },
              ticks: { color: '#94a3b8' }
            }
          }
        }
      });
    }
  }

  /**
   * Load and render analytics for a specific dataset UID
   */
  static async loadDatasetAnalytics(datasetUid) {
    if (!datasetUid) return;

    try {
      const data = await ApiClient.get(CONFIG.ENDPOINTS.DATASET_DETAIL(datasetUid));
      if (!data) return;

      // Update KPI Cards
      document.getElementById('kpi-equipment-count').textContent = data.equipment_count || 0;
      
      const stats = data.statistics || {};
      const flow = stats.flowrate || {};
      const press = stats.pressure || {};
      const temp = stats.temperature || {};

      document.getElementById('kpi-avg-flowrate').textContent = UI.formatNum(flow.average, '', 1);
      document.getElementById('kpi-flowrate-range').textContent = `${flow.min ?? 0} - ${flow.max ?? 0}`;

      document.getElementById('kpi-avg-pressure').textContent = UI.formatNum(press.average, '', 1);
      document.getElementById('kpi-pressure-range').textContent = `${press.min ?? 0} - ${press.max ?? 0}`;

      document.getElementById('kpi-avg-temperature').textContent = UI.formatNum(temp.average, '', 1);
      document.getElementById('kpi-temp-range').textContent = `${temp.min ?? 0} - ${temp.max ?? 0}`;

      // Update Parameter Range Bar Chart
      if (this.rangeChart) {
        this.rangeChart.data.datasets[0].data = [flow.min || 0, press.min || 0, temp.min || 0];
        this.rangeChart.data.datasets[1].data = [flow.average || 0, press.average || 0, temp.average || 0];
        this.rangeChart.data.datasets[2].data = [flow.max || 0, press.max || 0, temp.max || 0];
        this.rangeChart.update();
      }

      // Update Type Distribution Chart
      if (this.typeChart && data.equipment_summary) {
        const types = Object.keys(data.equipment_summary);
        const counts = Object.values(data.equipment_summary);
        this.typeChart.data.labels = types;
        this.typeChart.data.datasets[0].data = counts;
        this.typeChart.update();
      }

      // Update Alerts and Inactive Equipment Feed
      const alertsContainer = document.getElementById('dashboard-alerts-list');
      if (alertsContainer) {
        const inactives = data.inactive_equipment || [];
        const missing = data.missing_data || [];

        if (inactives.length === 0 && missing.length === 0) {
          alertsContainer.innerHTML = `
            <div class="empty-state">
              <i data-lucide="check-circle" class="empty-state-icon" style="color: var(--accent-emerald);"></i>
              <p>All operating equipment telemetry reporting normally.</p>
            </div>
          `;
        } else {
          let html = '';
          inactives.forEach(item => {
            html += `
              <div class="alert-item">
                <div class="alert-info">
                  <span class="alert-name">${item.equipment_name} (${item.equipment_type || 'Unknown'})</span>
                  <span class="alert-desc">${item.reason || 'All parameters missing'}</span>
                </div>
                <span class="badge badge-rose">Offline</span>
              </div>
            `;
          });

          missing.forEach(item => {
            html += `
              <div class="alert-item warning">
                <div class="alert-info">
                  <span class="alert-name">${item.equipment_name} (${item.equipment_type || 'Unit'})</span>
                  <span class="alert-desc">Missing columns: ${(item.missing_columns || []).join(', ')}</span>
                </div>
                <span class="badge badge-amber">Partial Data</span>
              </div>
            `;
          });
          alertsContainer.innerHTML = html;
        }
      }

      // Also load equipment items to populate scatter correlation plot
      this.loadCorrelationScatter(datasetUid);

      if (window.lucide) window.lucide.createIcons();

    } catch (err) {
      console.error('Failed to load dataset analytics:', err);
    }
  }

  static async loadCorrelationScatter(datasetUid) {
    try {
      const equipments = await ApiClient.get(CONFIG.ENDPOINTS.EQUIPMENT_BY_DATASET(datasetUid));
      if (Array.isArray(equipments) && this.correlationChart) {
        const points = equipments.map(eq => ({
          x: eq.flowrate,
          y: eq.pressure,
          name: eq.equipment_name
        }));
        this.correlationChart.data.datasets[0].data = points;
        this.correlationChart.update();
      }
    } catch (_) {}
  }
}
