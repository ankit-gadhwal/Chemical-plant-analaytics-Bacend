/**
 * UI Utilities, Modals, Toasts & Formatters
 * Chemical Plant Equipment Analytics
 */

export class UI {
  /**
   * Display a floating toast alert
   */
  static showToast(title, message, type = 'info', duration = 4000) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    let iconName = 'info';
    if (type === 'success') iconName = 'check-circle';
    if (type === 'error') iconName = 'alert-octagon';
    if (type === 'warning') iconName = 'alert-triangle';

    toast.innerHTML = `
      <div style="color: var(--accent-${type === 'error' ? 'rose' : type === 'success' ? 'emerald' : type === 'warning' ? 'amber' : 'cyan'});">
        <i data-lucide="${iconName}"></i>
      </div>
      <div class="toast-content">
        <div class="toast-title">${title}</div>
        <div class="toast-msg">${message}</div>
      </div>
      <button class="toast-close" title="Close"><i data-lucide="x"></i></button>
    `;

    container.appendChild(toast);

    if (window.lucide) {
      window.lucide.createIcons({ root: toast });
    }

    const removeToast = () => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(40px)';
      toast.style.transition = 'all 0.25s ease';
      setTimeout(() => toast.remove(), 250);
    };

    toast.querySelector('.toast-close').addEventListener('click', removeToast);

    if (duration > 0) {
      setTimeout(removeToast, duration);
    }
  }

  /**
   * Modal Show / Hide Helper
   */
  static openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add('active');
      if (window.lucide) window.lucide.createIcons({ root: modal });
    }
  }

  static closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove('active');
    }
  }

  /**
   * Status Pill / Badge HTML Generator
   */
  static getStatusBadge(flowrate, pressure, temperature) {
    if (flowrate === 0 && pressure === 0) {
      return `<span class="badge badge-rose"><i data-lucide="alert-circle"></i> Inactive</span>`;
    }
    if (pressure > 50 || temperature > 200) {
      return `<span class="badge badge-amber"><i data-lucide="alert-triangle"></i> High Load</span>`;
    }
    return `<span class="badge badge-emerald"><i data-lucide="check"></i> Optimal</span>`;
  }

  /**
   * Format numbers to 2 decimal places with fallback
   */
  static formatNum(val, unit = '', decimals = 2) {
    if (val === null || val === undefined || isNaN(val)) return `— ${unit}`.trim();
    return `${Number(val).toFixed(decimals)} ${unit}`.trim();
  }

  /**
   * Format ISO timestamps
   */
  static formatDate(dateStr) {
    if (!dateStr) return '—';
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (_) {
      return dateStr;
    }
  }
}
