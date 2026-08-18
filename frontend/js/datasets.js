/**
 * Datasets & Ingestion Hub Module
 * Chemical Plant Equipment Analytics
 */

import { ApiClient } from './api.js';
import { CONFIG } from './config.js';
import { UI } from './ui.js';
import { AuthManager } from './auth.js';

export class DatasetManager {
  static datasets = [];
  static activeDataset = null;

  static init() {
    this.bindEvents();
    this.loadDatasets();
  }

  static bindEvents() {
    // Dropzone elements
    const dropzone = document.getElementById('csv-dropzone');
    const fileInput = document.getElementById('csv-file-input');

    if (dropzone && fileInput) {
      dropzone.addEventListener('click', () => fileInput.click());

      dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('drag-over');
      });

      dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('drag-over');
      });

      dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('drag-over');
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
          this.uploadFile(e.dataTransfer.files[0]);
        }
      });

      fileInput.addEventListener('change', () => {
        if (fileInput.files && fileInput.files.length > 0) {
          this.uploadFile(fileInput.files[0]);
        }
      });
    }

    // Download Sample CSV
    const downloadSampleBtn = document.getElementById('btn-download-sample-csv');
    const quickSampleBtn = document.getElementById('btn-quick-sample');

    const triggerSampleDownload = () => {
      const link = document.createElement('a');
      link.href = 'assets/sample_equipment_data.csv';
      link.download = 'sample_chemical_equipment.csv';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      UI.showToast('Downloaded', 'Sample CSV template downloaded.', 'info');
    };

    if (downloadSampleBtn) downloadSampleBtn.addEventListener('click', triggerSampleDownload);
    if (quickSampleBtn) quickSampleBtn.addEventListener('click', triggerSampleDownload);

    // Refresh Datasets list
    const refreshBtn = document.getElementById('btn-refresh-datasets');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => this.loadDatasets());
    }

    // Active dataset dropdown in header
    const datasetSelect = document.getElementById('active-dataset-select');
    if (datasetSelect) {
      datasetSelect.addEventListener('change', (e) => {
        const uid = e.target.value;
        this.setActiveDataset(uid);
      });
    }
  }

  /**
   * Upload CSV file to backend
   */
  static async uploadFile(file) {
    if (!AuthManager.isAuthenticated()) {
      UI.showToast('Authentication Required', 'Please sign in to upload datasets.', 'warning');
      UI.openModal('auth-modal');
      return;
    }

    if (!file.name.endsWith('.csv')) {
      UI.showToast('Invalid File', 'Only .csv files are supported.', 'error');
      return;
    }

    const progressContainer = document.getElementById('upload-progress-container');
    const filenameLabel = document.getElementById('upload-filename');
    const percentLabel = document.getElementById('upload-percent');
    const progressBar = document.getElementById('upload-progress-bar');

    try {
      if (progressContainer) progressContainer.style.display = 'block';
      if (filenameLabel) filenameLabel.textContent = file.name;
      if (percentLabel) percentLabel.textContent = 'Processing...';
      if (progressBar) progressBar.style.width = '70%';

      const formData = new FormData();
      formData.append('file', file);

      const res = await ApiClient.post(CONFIG.ENDPOINTS.DATASET_UPLOAD, formData);

      if (progressBar) progressBar.style.width = '100%';
      if (percentLabel) percentLabel.textContent = '100%';

      UI.showToast('Upload Complete', res.message || 'Dataset uploaded and processed successfully.', 'success');
      
      // Reload datasets and set as active
      await this.loadDatasets();
      if (res.uid) {
        this.setActiveDataset(res.uid);
      }

    } catch (err) {
      UI.showToast('Upload Failed', err.message, 'error');
    } finally {
      setTimeout(() => {
        if (progressContainer) progressContainer.style.display = 'none';
        if (progressBar) progressBar.style.width = '0%';
        const fileInput = document.getElementById('csv-file-input');
        if (fileInput) fileInput.value = '';
      }, 1500);
    }
  }

  /**
   * Load list of datasets for current user
   */
  static async loadDatasets() {
    const tableBody = document.getElementById('datasets-table-body');
    const datasetSelect = document.getElementById('active-dataset-select');

    try {
      const res = await ApiClient.get(CONFIG.ENDPOINTS.DATASETS, { page: 1, page_size: 50 });
      this.datasets = res.items || [];

      // Update header dropdown
      if (datasetSelect) {
        if (this.datasets.length === 0) {
          datasetSelect.innerHTML = '<option value="">No Dataset Available</option>';
        } else {
          datasetSelect.innerHTML = this.datasets.map(d => `
            <option value="${d.uid}">${d.original_filename} (${d.equipment_count || 0} units)</option>
          `).join('');
        }
      }

      // Check saved active dataset
      const savedActiveUid = localStorage.getItem(CONFIG.STORAGE_KEYS.ACTIVE_DATASET_UID);
      if (savedActiveUid && this.datasets.some(d => d.uid === savedActiveUid)) {
        this.setActiveDataset(savedActiveUid, false);
      } else if (this.datasets.length > 0) {
        this.setActiveDataset(this.datasets[0].uid, false);
      }

      // Render Table Body
      if (tableBody) {
        if (this.datasets.length === 0) {
          tableBody.innerHTML = `
            <tr>
              <td colspan="8" class="empty-state">
                <i data-lucide="folder" class="empty-state-icon"></i>
                <p>No datasets uploaded yet. Upload a CSV above or click "Sample CSV".</p>
              </td>
            </tr>
          `;
          if (window.lucide) window.lucide.createIcons({ root: tableBody });
          return;
        }

        tableBody.innerHTML = this.datasets.map(d => {
          const isActive = d.uid === this.activeDataset?.uid;
          return `
            <tr style="${isActive ? 'background-color: rgba(6, 182, 212, 0.08);' : ''}">
              <td>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                  <i data-lucide="file-spreadsheet" class="text-cyan"></i>
                  <strong>${d.original_filename}</strong>
                  ${isActive ? '<span class="badge badge-cyan">Active</span>' : ''}
                </div>
              </td>
              <td class="mono-num">${d.equipment_count || 0}</td>
              <td class="mono-num">${UI.formatNum(d.average_flowrate, 'm³/h')}</td>
              <td class="mono-num">${UI.formatNum(d.average_pressure, 'bar')}</td>
              <td class="mono-num">${UI.formatNum(d.average_temperature, '°C')}</td>
              <td><span class="badge ${d.status === 'COMPLETED' ? 'badge-emerald' : 'badge-amber'}">${d.status}</span></td>
              <td>${UI.formatDate(d.created_at)}</td>
              <td style="text-align: right;">
                <button class="btn btn-secondary btn-sm btn-select-dataset" data-uid="${d.uid}">
                  ${isActive ? 'Selected' : 'Select'}
                </button>
                <button class="btn btn-ghost btn-sm btn-icon text-rose btn-delete-dataset" title="Delete Dataset" data-uid="${d.uid}" data-name="${d.original_filename}">
                  <i data-lucide="trash-2"></i>
                </button>
              </td>
            </tr>
          `;
        }).join('');

        if (window.lucide) window.lucide.createIcons({ root: tableBody });

        // Bind buttons
        tableBody.querySelectorAll('.btn-select-dataset').forEach(btn => {
          btn.addEventListener('click', () => {
            const uid = btn.getAttribute('data-uid');
            this.setActiveDataset(uid);
            this.loadDatasets();
          });
        });

        tableBody.querySelectorAll('.btn-delete-dataset').forEach(btn => {
          btn.addEventListener('click', async () => {
            const uid = btn.getAttribute('data-uid');
            const name = btn.getAttribute('data-name');
            if (confirm(`Are you sure you want to delete dataset "${name}"? This will also remove its equipment and chat sessions.`)) {
              try {
                await ApiClient.delete(CONFIG.ENDPOINTS.DATASET_DETAIL(uid));
                UI.showToast('Deleted', `Dataset "${name}" deleted.`, 'info');
                if (this.activeDataset?.uid === uid) {
                  localStorage.removeItem(CONFIG.STORAGE_KEYS.ACTIVE_DATASET_UID);
                  this.activeDataset = null;
                }
                this.loadDatasets();
              } catch (err) {
                UI.showToast('Delete Failed', err.message, 'error');
              }
            }
          });
        });
      }

    } catch (err) {
      if (tableBody) {
        tableBody.innerHTML = `
          <tr>
            <td colspan="8" class="empty-state" style="color: var(--accent-rose);">
              <p>${err.message || 'Failed to load datasets.'}</p>
            </td>
          </tr>
        `;
      }
    }
  }

  /**
   * Set active dataset and broadcast change
   */
  static setActiveDataset(uid, notify = true) {
    if (!uid) return;
    localStorage.setItem(CONFIG.STORAGE_KEYS.ACTIVE_DATASET_UID, uid);
    this.activeDataset = this.datasets.find(d => d.uid === uid) || { uid };

    const datasetSelect = document.getElementById('active-dataset-select');
    if (datasetSelect) datasetSelect.value = uid;

    // Dispatch global event for other components (Dashboard, Equipment, Docs, Chat)
    window.dispatchEvent(new CustomEvent('chempulse:dataset-changed', {
      detail: { uid, dataset: this.activeDataset }
    }));

    if (notify) {
      UI.showToast('Active Dataset Changed', `Dataset set to ${this.activeDataset.original_filename || uid}`, 'info');
    }
  }
}
