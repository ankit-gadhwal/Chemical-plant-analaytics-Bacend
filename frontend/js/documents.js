/**
 * Technical Documents & Manuals Module (RAG Knowledge Ingestion)
 * Chemical Plant Equipment Analytics
 */

import { ApiClient } from './api.js';
import { CONFIG } from './config.js';
import { UI } from './ui.js';
import { AuthManager } from './auth.js';

export class DocumentManager {
  static documents = [];

  static init() {
    this.bindEvents();
  }

  static bindEvents() {
    const uploadForm = document.getElementById('doc-upload-form');
    const fileInput = document.getElementById('doc-file-input');

    if (uploadForm && fileInput) {
      uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const activeUid = localStorage.getItem(CONFIG.STORAGE_KEYS.ACTIVE_DATASET_UID);

        if (!activeUid) {
          UI.showToast('No Active Dataset', 'Please select a dataset to associate this document with.', 'warning');
          return;
        }

        if (!AuthManager.isAuthenticated()) {
          UI.showToast('Authentication Required', 'Please sign in to upload technical manuals.', 'warning');
          UI.openModal('auth-modal');
          return;
        }

        if (!fileInput.files || fileInput.files.length === 0) {
          UI.showToast('No File', 'Please choose a document to upload.', 'error');
          return;
        }

        const file = fileInput.files[0];
        const submitBtn = document.getElementById('btn-upload-doc');

        try {
          submitBtn.disabled = true;
          submitBtn.innerHTML = '<i data-lucide="loader" class="spin"></i> Indexing Manual...';

          const formData = new FormData();
          formData.append('file', file);

          await ApiClient.post(`${CONFIG.ENDPOINTS.DOCUMENTS_UPLOAD}?dataset_uid=${encodeURIComponent(activeUid)}`, formData);

          UI.showToast('Document Indexed', `"${file.name}" uploaded and indexed for AI RAG knowledge.`, 'success');
          fileInput.value = '';
          this.loadDocuments(activeUid);

        } catch (err) {
          UI.showToast('Upload Failed', err.message, 'error');
        } finally {
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<i data-lucide="upload"></i> <span>Upload & Index</span>';
          if (window.lucide) window.lucide.createIcons({ root: submitBtn });
        }
      });
    }
  }

  /**
   * Load indexed documents for active dataset
   */
  static async loadDocuments(datasetUid) {
    const tableBody = document.getElementById('documents-table-body');
    if (!tableBody) return;

    if (!datasetUid) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="3" class="empty-state">
            <p>Please select or upload a dataset to view attached manuals.</p>
          </td>
        </tr>
      `;
      return;
    }

    try {
      const docs = await ApiClient.get(CONFIG.ENDPOINTS.DOCUMENTS_BY_DATASET(datasetUid));
      this.documents = Array.isArray(docs) ? docs : [];

      if (this.documents.length === 0) {
        tableBody.innerHTML = `
          <tr>
            <td colspan="3" class="empty-state">
              <i data-lucide="file-question" class="empty-state-icon"></i>
              <p>No engineering manuals or SOPs indexed for this dataset yet.</p>
            </td>
          </tr>
        `;
        if (window.lucide) window.lucide.createIcons({ root: tableBody });
        return;
      }

      tableBody.innerHTML = this.documents.map(doc => `
        <tr>
          <td>
            <div style="display: flex; align-items: center; gap: 0.6rem;">
              <i data-lucide="file-text" class="text-cyan"></i>
              <strong>${doc.original_filename}</strong>
            </div>
          </td>
          <td>${UI.formatDate(doc.created_at)}</td>
          <td style="text-align: right;">
            <button class="btn btn-ghost btn-sm btn-icon text-rose btn-delete-doc" title="Delete Manual" data-uid="${doc.uid}" data-name="${doc.original_filename}">
              <i data-lucide="trash-2"></i>
            </button>
          </td>
        </tr>
      `).join('');

      if (window.lucide) window.lucide.createIcons({ root: tableBody });

      // Delete buttons
      tableBody.querySelectorAll('.btn-delete-doc').forEach(btn => {
        btn.addEventListener('click', async () => {
          const uid = btn.getAttribute('data-uid');
          const name = btn.getAttribute('data-name');
          if (confirm(`Remove document "${name}"?`)) {
            try {
              await ApiClient.delete(CONFIG.ENDPOINTS.DOCUMENT_DETAIL(uid));
              UI.showToast('Removed', `Document "${name}" removed.`, 'info');
              this.loadDocuments(datasetUid);
            } catch (err) {
              UI.showToast('Error', err.message, 'error');
            }
          }
        });
      });

    } catch (err) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="3" class="empty-state" style="color: var(--accent-rose);">
            <p>${err.message || 'Failed to load documents.'}</p>
          </td>
        </tr>
      `;
    }
  }
}
