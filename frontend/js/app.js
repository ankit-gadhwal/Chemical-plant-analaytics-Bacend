/**
 * Main Application Bootstrap & Router
 * Chemical Plant Equipment Analytics
 */

import { CONFIG } from './config.js';
import { ApiClient } from './api.js';
import { UI } from './ui.js';
import { AuthManager } from './auth.js';
import { DatasetManager } from './datasets.js';
import { DashboardManager } from './dashboard.js';
import { EquipmentManager } from './equipment.js';
import { DocumentManager } from './documents.js';
import { ChatManager } from './chat.js';

class App {
  static activeView = 'dashboard';

  static async init() {
    console.log('Initializing ChemPulse Plant Analytics Web App...');

    // 1. Initialize Core Managers
    AuthManager.init();
    DashboardManager.init();
    EquipmentManager.init();
    DatasetManager.init();
    DocumentManager.init();
    ChatManager.init();

    // 2. Setup Navigation & Routing
    this.setupNavigation();

    // 3. Setup Global Event Listeners
    this.setupGlobalEvents();

    // 4. Check Backend Connectivity
    this.checkBackendHealth();

    // 5. Initial Render
    if (window.lucide) window.lucide.createIcons();
  }

  static setupNavigation() {
    const navItems = document.querySelectorAll('.sidebar-nav .nav-item');
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const sidebar = document.getElementById('app-sidebar');

    navItems.forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        const targetView = item.getAttribute('data-view');
        this.switchView(targetView);

        // Close mobile sidebar if open
        if (sidebar && sidebar.classList.contains('mobile-open')) {
          sidebar.classList.remove('mobile-open');
        }
      });
    });

    if (mobileMenuBtn && sidebar) {
      mobileMenuBtn.addEventListener('click', () => {
        sidebar.classList.toggle('mobile-open');
      });
    }
  }

  static switchView(viewName) {
    if (!viewName) return;
    this.activeView = viewName;

    // Update Nav Active State
    document.querySelectorAll('.sidebar-nav .nav-item').forEach(item => {
      if (item.getAttribute('data-view') === viewName) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });

    // Update Views Visibility
    document.querySelectorAll('.app-view').forEach(view => {
      if (view.id === `view-${viewName}`) {
        view.classList.add('active-view');
      } else {
        view.classList.remove('active-view');
      }
    });

    // View-specific reloads
    const activeUid = localStorage.getItem(CONFIG.STORAGE_KEYS.ACTIVE_DATASET_UID);

    if (viewName === 'dashboard' && activeUid) {
      DashboardManager.loadDatasetAnalytics(activeUid);
    } else if (viewName === 'equipment') {
      EquipmentManager.loadEquipmentList();
    } else if (viewName === 'documents' && activeUid) {
      DocumentManager.loadDocuments(activeUid);
    } else if (viewName === 'chat') {
      ChatManager.loadSessions();
    }

    if (window.lucide) window.lucide.createIcons();
  }

  static setupGlobalEvents() {
    // When active dataset changes
    window.addEventListener('chempulse:dataset-changed', (e) => {
      const { uid } = e.detail;
      if (this.activeView === 'dashboard') {
        DashboardManager.loadDatasetAnalytics(uid);
      } else if (this.activeView === 'equipment') {
        EquipmentManager.loadEquipmentList();
      } else if (this.activeView === 'documents') {
        DocumentManager.loadDocuments(uid);
      }
    });

    // When a dataset is modified or equipment updated
    window.addEventListener('chempulse:dataset-updated', (e) => {
      const { uid } = e.detail;
      if (uid) DashboardManager.loadDatasetAnalytics(uid);
    });

    // When auth state changes (login or logout)
    window.addEventListener('chempulse:auth-changed', () => {
      DatasetManager.loadDatasets();
      ChatManager.loadSessions();
      if (this.activeView === 'equipment') EquipmentManager.loadEquipmentList();
    });
  }

  static async checkBackendHealth() {
    const dot = document.getElementById('system-status-dot');
    const text = document.getElementById('system-status-text');

    try {
      // Test ping to /dataset/
      await fetch(`${CONFIG.API_BASE_URL}/dataset/?page=1&page_size=1`, { method: 'GET' });
      if (dot) dot.classList.remove('offline');
      if (text) text.textContent = 'API Live';
    } catch (_) {
      if (dot) dot.classList.add('offline');
      if (text) text.textContent = 'API Offline';
    }
  }
}

// Bootstrap once DOM is loaded
document.addEventListener('DOMContentLoaded', () => App.init());
