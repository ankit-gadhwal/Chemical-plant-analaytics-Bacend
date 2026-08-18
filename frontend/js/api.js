/**
 * API Client & Network Service
 * Chemical Plant Equipment Analytics
 */

import { CONFIG } from './config.js';

export class ApiClient {
  static getAccessToken() {
    return localStorage.getItem(CONFIG.STORAGE_KEYS.ACCESS_TOKEN);
  }

  static getRefreshToken() {
    return localStorage.getItem(CONFIG.STORAGE_KEYS.REFRESH_TOKEN);
  }

  static setTokens(accessToken, refreshToken) {
    if (accessToken) localStorage.setItem(CONFIG.STORAGE_KEYS.ACCESS_TOKEN, accessToken);
    if (refreshToken) localStorage.setItem(CONFIG.STORAGE_KEYS.REFRESH_TOKEN, refreshToken);
  }

  static clearTokens() {
    localStorage.removeItem(CONFIG.STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(CONFIG.STORAGE_KEYS.REFRESH_TOKEN);
    localStorage.removeItem(CONFIG.STORAGE_KEYS.USER);
  }

  /**
   * Main request method with token injection & automatic refresh retry
   */
  static async request(endpoint, options = {}) {
    const url = endpoint.startsWith('http') ? endpoint : `${CONFIG.API_BASE_URL}${endpoint}`;
    
    const headers = {
      ...(options.headers || {})
    };

    // If body is not FormData and not already Content-Type specified, default to application/json
    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    // Attach Bearer Access Token if present
    const token = this.getAccessToken();
    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      let response = await fetch(url, {
        ...options,
        headers
      });

      // Handle 401 Unauthorized -> Attempt token refresh
      if (response.status === 401 && !options._retry && this.getRefreshToken()) {
        options._retry = true;
        const refreshed = await this.refreshAccessToken();
        if (refreshed) {
          return await this.request(endpoint, options);
        }
      }

      // Check if response is successful
      if (!response.ok) {
        let errorDetails = `HTTP Error ${response.status}`;
        try {
          const errorJson = await response.json();
          if (Array.isArray(errorJson.detail)) {
            errorDetails = errorJson.detail.map(d => {
              const field = d.loc ? d.loc.slice(-1)[0] : '';
              return field ? `${field}: ${d.msg}` : d.msg;
            }).join(' | ');
          } else {
            errorDetails = errorJson.detail || errorJson.message || errorJson.error || JSON.stringify(errorJson);
          }
        } catch (_) {
          errorDetails = await response.text();
        }
        throw new Error(errorDetails || `Request failed with status ${response.status}`);
      }

      // Parse JSON response if available
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }
      return await response.text();

    } catch (err) {
      console.error(`API Request Error [${endpoint}]:`, err);
      throw err;
    }
  }

  /**
   * Refresh the access token using the stored refresh token
   */
  static async refreshAccessToken() {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) return false;

    try {
      const response = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.REFRESH_TOKEN}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${refreshToken}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.access_token) {
          localStorage.setItem(CONFIG.STORAGE_KEYS.ACCESS_TOKEN, data.access_token);
          return true;
        }
      }
    } catch (e) {
      console.warn('Failed to refresh token:', e);
    }

    this.clearTokens();
    window.dispatchEvent(new CustomEvent('chempulse:auth-expired'));
    return false;
  }

  // Convenience methods
  static get(endpoint, params = {}) {
    let url = endpoint;
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== '') {
        query.append(key, val);
      }
    });
    const queryString = query.toString();
    if (queryString) {
      url += (url.includes('?') ? '&' : '?') + queryString;
    }
    return this.request(url, { method: 'GET' });
  }

  static post(endpoint, body) {
    const isForm = body instanceof FormData;
    return this.request(endpoint, {
      method: 'POST',
      body: isForm ? body : JSON.stringify(body)
    });
  }

  static patch(endpoint, body) {
    return this.request(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(body)
    });
  }

  static delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }
}
