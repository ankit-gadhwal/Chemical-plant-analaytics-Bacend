/**
 * Equipment Telemetry Explorer Module
 * Chemical Plant Equipment Analytics
 */

import { ApiClient } from './api.js';
import { CONFIG } from './config.js';
import { UI } from './ui.js';

export class EquipmentManager {
  static currentPage = 1;
  static pageSize = 10;
  static totalPages = 1;
  static totalItems = 0;

  static init() {
    this.bindEvents();
  }

  static bindEvents() {
    // Search & Filter inputs
    const searchInput = document.getElementById('filter-search');
    const typeSelect = document.getElementById('filter-type');
    const sortBySelect = document.getElementById('filter-sort-by');
    const orderSelect = document.getElementById('filter-order');
    const minPressInput = document.getElementById('filter-min-pressure');
    const maxPressInput = document.getElementById('filter-max-pressure');
    const minTempInput = document.getElementById('filter-min-temp');
    const maxTempInput = document.getElementById('filter-max-temp');
    const minFlowInput = document.getElementById('filter-min-flowrate');
    const maxFlowInput = document.getElementById('filter-max-flowrate');

    const triggerReload = () => {
      this.currentPage = 1;
      this.loadEquipmentList();
    };

    if (searchInput) searchInput.addEventListener('input', this.debounce(triggerReload, 350));
    if (typeSelect) typeSelect.addEventListener('change', triggerReload);
    if (sortBySelect) sortBySelect.addEventListener('change', triggerReload);
    if (orderSelect) orderSelect.addEventListener('change', triggerReload);
    if (minPressInput) minPressInput.addEventListener('change', triggerReload);
    if (maxPressInput) maxPressInput.addEventListener('change', triggerReload);
    if (minTempInput) minTempInput.addEventListener('change', triggerReload);
    if (maxTempInput) maxTempInput.addEventListener('change', triggerReload);
    if (minFlowInput) minFlowInput.addEventListener('change', triggerReload);
    if (maxFlowInput) maxFlowInput.addEventListener('change', triggerReload);

    // Reset Filters
    const resetBtn = document.getElementById('btn-clear-equipment-filters');
    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        if (searchInput) searchInput.value = '';
        if (typeSelect) typeSelect.value = '';
        if (sortBySelect) sortBySelect.value = 'created_at';
        if (orderSelect) orderSelect.value = 'desc';
        if (minPressInput) minPressInput.value = '';
        if (maxPressInput) maxPressInput.value = '';
        if (minTempInput) minTempInput.value = '';
        if (maxTempInput) maxTempInput.value = '';
        if (minFlowInput) minFlowInput.value = '';
        if (maxFlowInput) maxFlowInput.value = '';
        this.currentPage = 1;
        this.loadEquipmentList();
      });
    }

    // Pagination buttons
    const prevBtn = document.getElementById('btn-prev-page');
    const nextBtn = document.getElementById('btn-next-page');

    if (prevBtn) {
      prevBtn.addEventListener('click', () => {
        if (this.currentPage > 1) {
          this.currentPage--;
          this.loadEquipmentList();
        }
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        if (this.currentPage < this.totalPages) {
          this.currentPage++;
          this.loadEquipmentList();
        }
      });
    }

    // Equipment Edit Modal Form
    const editForm = document.getElementById('equipment-edit-form');
    if (editForm) {
      editForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const uid = document.getElementById('edit-equipment-id').value;
        const equipment_name = document.getElementById('edit-equipment-name').value.trim();
        const equipment_type = document.getElementById('edit-equipment-type').value.trim();
        const flowrate = parseFloat(document.getElementById('edit-equipment-flowrate').value);
        const pressure = parseFloat(document.getElementById('edit-equipment-pressure').value);
        const temperature = parseFloat(document.getElementById('edit-equipment-temp').value);

        try {
          await ApiClient.patch(CONFIG.ENDPOINTS.EQUIPMENT_DETAIL(uid), {
            equipment_name,
            equipment_type,
            flowrate,
            pressure,
            temperature
          });

          UI.closeModal('equipment-modal');
          UI.showToast('Updated', 'Equipment parameters updated successfully.', 'success');
          this.loadEquipmentList();
          
          // Also refresh dashboard if active
          const activeUid = localStorage.getItem(CONFIG.STORAGE_KEYS.ACTIVE_DATASET_UID);
          if (activeUid) window.dispatchEvent(new CustomEvent('chempulse:dataset-updated', { detail: { uid: activeUid } }));

        } catch (err) {
          UI.showToast('Update Failed', err.message, 'error');
        }
      });
    }

    // Close modal buttons
    const closeModalBtn = document.getElementById('btn-close-equipment-modal');
    const cancelModalBtn = document.getElementById('btn-cancel-equipment-edit');
    if (closeModalBtn) closeModalBtn.addEventListener('click', () => UI.closeModal('equipment-modal'));
    if (cancelModalBtn) cancelModalBtn.addEventListener('click', () => UI.closeModal('equipment-modal'));
  }

  /**
   * Fetch equipment from backend with all active filters
   */
  static async loadEquipmentList() {
    const tableBody = document.getElementById('equipment-table-body');
    if (!tableBody) return;

    const activeDatasetUid = localStorage.getItem(CONFIG.STORAGE_KEYS.ACTIVE_DATASET_UID);

    const params = {
      page: this.currentPage,
      page_size: this.pageSize,
      search: document.getElementById('filter-search')?.value.trim() || undefined,
      equipment_type: document.getElementById('filter-type')?.value || undefined,
      dataset_uid: activeDatasetUid || undefined,
      sort_by: document.getElementById('filter-sort-by')?.value || 'created_at',
      order: document.getElementById('filter-order')?.value || 'desc',
      min_pressure: document.getElementById('filter-min-pressure')?.value || undefined,
      max_pressure: document.getElementById('filter-max-pressure')?.value || undefined,
      min_temperature: document.getElementById('filter-min-temp')?.value || undefined,
      max_temperature: document.getElementById('filter-max-temp')?.value || undefined,
      min_flowrate: document.getElementById('filter-min-flowrate')?.value || undefined,
      max_flowrate: document.getElementById('filter-max-flowrate')?.value || undefined,
    };

    try {
      tableBody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align: center; padding: 2rem; color: var(--text-muted);">
            <i data-lucide="loader" class="spin" style="margin-right: 0.5rem;"></i> Loading equipment telemetry...
          </td>
        </tr>
      `;
      if (window.lucide) window.lucide.createIcons({ root: tableBody });

      const res = await ApiClient.get(CONFIG.ENDPOINTS.EQUIPMENT, params);
      const items = res.items || [];
      const pagination = res.pagination || {};

      this.currentPage = pagination.page || 1;
      this.totalPages = pagination.total_pages || 1;
      this.totalItems = pagination.total_items || 0;

      this.updatePaginationUI();

      if (items.length === 0) {
        tableBody.innerHTML = `
          <tr>
            <td colspan="7" class="empty-state">
              <i data-lucide="inbox" class="empty-state-icon"></i>
              <p>No equipment matching your filter criteria.</p>
            </td>
          </tr>
        `;
        if (window.lucide) window.lucide.createIcons({ root: tableBody });
        return;
      }

      tableBody.innerHTML = items.map(eq => `
        <tr data-uid="${eq.uid}">
          <td>
            <strong>${eq.equipment_name}</strong>
          </td>
          <td><span class="badge badge-muted">${eq.equipment_type}</span></td>
          <td class="mono-num">${UI.formatNum(eq.flowrate, 'm³/h')}</td>
          <td class="mono-num">${UI.formatNum(eq.pressure, 'bar')}</td>
          <td class="mono-num">${UI.formatNum(eq.temperature, '°C')}</td>
          <td>${UI.getStatusBadge(eq.flowrate, eq.pressure, eq.temperature)}</td>
          <td style="text-align: right;">
            <button class="btn btn-ghost btn-sm btn-icon btn-edit-eq" title="Edit Parameters" data-eq='${JSON.stringify(eq)}'>
              <i data-lucide="edit-3"></i>
            </button>
            <button class="btn btn-ghost btn-sm btn-icon text-rose btn-delete-eq" title="Delete Equipment" data-uid="${eq.uid}" data-name="${eq.equipment_name}">
              <i data-lucide="trash-2"></i>
            </button>
          </td>
        </tr>
      `).join('');

      if (window.lucide) window.lucide.createIcons({ root: tableBody });

      // Bind action buttons
      tableBody.querySelectorAll('.btn-edit-eq').forEach(btn => {
        btn.addEventListener('click', () => {
          const eq = JSON.parse(btn.getAttribute('data-eq'));
          this.openEditModal(eq);
        });
      });

      tableBody.querySelectorAll('.btn-delete-eq').forEach(btn => {
        btn.addEventListener('click', async () => {
          const uid = btn.getAttribute('data-uid');
          const name = btn.getAttribute('data-name');
          if (confirm(`Are you sure you want to delete equipment "${name}"?`)) {
            try {
              await ApiClient.delete(CONFIG.ENDPOINTS.EQUIPMENT_DETAIL(uid));
              UI.showToast('Deleted', `Equipment "${name}" removed.`, 'info');
              this.loadEquipmentList();
            } catch (err) {
              UI.showToast('Delete Failed', err.message, 'error');
            }
          }
        });
      });

    } catch (err) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="7" class="empty-state" style="color: var(--accent-rose);">
            <i data-lucide="alert-circle" class="empty-state-icon"></i>
            <p>${err.message || 'Failed to fetch equipment data.'}</p>
          </td>
        </tr>
      `;
      if (window.lucide) window.lucide.createIcons({ root: tableBody });
    }
  }

  static openEditModal(eq) {
    document.getElementById('edit-equipment-id').value = eq.uid;
    document.getElementById('edit-equipment-name').value = eq.equipment_name;
    document.getElementById('edit-equipment-type').value = eq.equipment_type;
    document.getElementById('edit-equipment-flowrate').value = eq.flowrate;
    document.getElementById('edit-equipment-pressure').value = eq.pressure;
    document.getElementById('edit-equipment-temp').value = eq.temperature;
    UI.openModal('equipment-modal');
  }

  static updatePaginationUI() {
    const metaDisplay = document.getElementById('equipment-pagination-meta');
    const pageDisplay = document.getElementById('current-page-display');
    const prevBtn = document.getElementById('btn-prev-page');
    const nextBtn = document.getElementById('btn-next-page');

    if (metaDisplay) metaDisplay.textContent = `Showing ${(this.currentPage - 1) * this.pageSize + 1} - ${Math.min(this.currentPage * this.pageSize, this.totalItems)} of ${this.totalItems} units`;
    if (pageDisplay) pageDisplay.textContent = `${this.currentPage} / ${this.totalPages || 1}`;
    if (prevBtn) prevBtn.disabled = this.currentPage <= 1;
    if (nextBtn) nextBtn.disabled = this.currentPage >= this.totalPages;
  }

  static debounce(func, wait) {
    let timeout;
    return (...args) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(this, args), wait);
    };
  }
}
