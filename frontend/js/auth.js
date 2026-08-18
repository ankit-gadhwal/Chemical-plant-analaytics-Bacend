/**
 * Authentication Module & User Session Management
 * Chemical Plant Equipment Analytics
 */

import { ApiClient } from './api.js';
import { CONFIG } from './config.js';
import { UI } from './ui.js';

export class AuthManager {
  static currentUser = null;

  static init() {
    this.bindEvents();
    this.restoreSession();
  }

  static bindEvents() {
    // Open auth modal button
    const openAuthBtn = document.getElementById('btn-open-auth');
    if (openAuthBtn) {
      openAuthBtn.addEventListener('click', () => UI.openModal('auth-modal'));
    }

    // Close auth modal
    const closeAuthBtn = document.getElementById('btn-close-auth-modal');
    if (closeAuthBtn) {
      closeAuthBtn.addEventListener('click', () => UI.closeModal('auth-modal'));
    }

    // Auth modal backdrop click
    const authModal = document.getElementById('auth-modal');
    if (authModal) {
      authModal.addEventListener('click', (e) => {
        if (e.target === authModal) UI.closeModal('auth-modal');
      });
    }

    // Toggle Login vs Signup tabs
    const tabLogin = document.getElementById('tab-login-btn');
    const tabSignup = document.getElementById('tab-signup-btn');
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');
    const modalTitle = document.getElementById('auth-modal-title');

    if (tabLogin && tabSignup) {
      tabLogin.addEventListener('click', () => {
        tabLogin.classList.add('active');
        tabSignup.classList.remove('active');
        loginForm.style.display = 'block';
        signupForm.style.display = 'none';
        modalTitle.textContent = 'Sign In to ChemPulse';
      });

      tabSignup.addEventListener('click', () => {
        tabSignup.classList.add('active');
        tabLogin.classList.remove('active');
        signupForm.style.display = 'block';
        loginForm.style.display = 'none';
        modalTitle.textContent = 'Create Plant Engineer Account';
      });
    }

    // Login Form Submit
    if (loginForm) {
      loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value.trim();
        const password = document.getElementById('login-password').value;
        const submitBtn = document.getElementById('btn-submit-login');

        try {
          submitBtn.disabled = true;
          submitBtn.innerHTML = 'Signing In...';

          const res = await ApiClient.post(CONFIG.ENDPOINTS.LOGIN, { email, password });
          if (res.access_token) {
            ApiClient.setTokens(res.access_token, res.refresh_token);
            this.setCurrentUser(res.user || { email });
            UI.closeModal('auth-modal');
            UI.showToast('Authentication Successful', `Welcome back, ${email}`, 'success');
            window.dispatchEvent(new CustomEvent('chempulse:auth-changed'));
          }
        } catch (err) {
          UI.showToast('Login Failed', err.message, 'error');
        } finally {
          submitBtn.disabled = false;
          submitBtn.innerHTML = 'Sign In';
        }
      });
    }

    // Signup Form Submit
    if (signupForm) {
      signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('signup-username').value.trim();
        const first_name = document.getElementById('signup-firstname').value.trim();
        const last_name = document.getElementById('signup-lastname').value.trim();
        const email = document.getElementById('signup-email').value.trim();
        const password = document.getElementById('signup-password').value;
        const submitBtn = document.getElementById('btn-submit-signup');

        if (!username || !first_name || !last_name || !email || !password) {
          UI.showToast('Missing Fields', 'Please fill out all required fields.', 'warning');
          return;
        }

        if (username.length > 8) {
          UI.showToast('Invalid Username', 'Username must be at most 8 characters.', 'warning');
          return;
        }

        if (password.length < 6) {
          UI.showToast('Invalid Password', 'Password must be at least 6 characters long.', 'warning');
          return;
        }

        try {
          submitBtn.disabled = true;
          submitBtn.innerHTML = 'Creating Account...';

          const res = await ApiClient.post(CONFIG.ENDPOINTS.SIGNUP, {
            username,
            first_name,
            last_name,
            email,
            password
          });

          UI.showToast('Account Created', res.message || 'Please log in with your credentials.', 'success');
          // Switch to login tab
          tabLogin.click();
          document.getElementById('login-email').value = email;
        } catch (err) {
          if (err.message && err.message.toLowerCase().includes('already exists')) {
            UI.showToast('Account Exists', 'An account with this email already exists. Switched to Sign In.', 'info');
            tabLogin.click();
            document.getElementById('login-email').value = email;
            document.getElementById('login-password').focus();
          } else {
            UI.showToast('Signup Failed', err.message, 'error');
          }
        } finally {
          submitBtn.disabled = false;
          submitBtn.innerHTML = 'Create Account';
        }
      });
    }

    // Logout button
    const logoutBtn = document.getElementById('btn-logout');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', async () => {
        try {
          await ApiClient.get(CONFIG.ENDPOINTS.LOGOUT);
        } catch (_) {}
        this.logout();
      });
    }

    // Listen for auth expired event
    window.addEventListener('chempulse:auth-expired', () => {
      this.logout();
      UI.showToast('Session Expired', 'Please sign in again.', 'warning');
    });
  }

  static setCurrentUser(user) {
    this.currentUser = user;
    if (user) {
      localStorage.setItem(CONFIG.STORAGE_KEYS.USER, JSON.stringify(user));
    }
    this.updateUserUI();
  }

  static restoreSession() {
    const savedUser = localStorage.getItem(CONFIG.STORAGE_KEYS.USER);
    if (savedUser && ApiClient.getAccessToken()) {
      try {
        this.currentUser = JSON.parse(savedUser);
      } catch (_) {}
    }
    this.updateUserUI();
  }

  static logout() {
    ApiClient.clearTokens();
    this.currentUser = null;
    this.updateUserUI();
    UI.showToast('Signed Out', 'You have been logged out.', 'info');
    window.dispatchEvent(new CustomEvent('chempulse:auth-changed'));
  }

  static updateUserUI() {
    const openAuthBtn = document.getElementById('btn-open-auth');
    const userPill = document.getElementById('user-profile-pill');
    const userEmailDisplay = document.getElementById('user-email-display');
    const userAvatar = document.getElementById('user-avatar-initial');

    if (this.currentUser) {
      if (openAuthBtn) openAuthBtn.style.display = 'none';
      if (userPill) userPill.style.display = 'flex';
      if (userEmailDisplay) userEmailDisplay.textContent = this.currentUser.email || 'Plant Engineer';
      if (userAvatar) userAvatar.textContent = (this.currentUser.email || 'U')[0].toUpperCase();
    } else {
      if (openAuthBtn) openAuthBtn.style.display = 'inline-flex';
      if (userPill) userPill.style.display = 'none';
    }

    if (window.lucide) window.lucide.createIcons();
  }

  static isAuthenticated() {
    return !!ApiClient.getAccessToken();
  }
}
