/**
 * AI Plant Copilot Module (Text-to-SQL & Document RAG)
 * Chemical Plant Equipment Analytics
 */

import { ApiClient } from './api.js';
import { CONFIG } from './config.js';
import { UI } from './ui.js';
import { AuthManager } from './auth.js';

export class ChatManager {
  static currentMode = 'sql'; // 'sql' or 'rag'
  static currentSessionUid = null;
  static sessions = [];

  static init() {
    this.bindEvents();
    this.loadSessions();
  }

  static bindEvents() {
    // Mode toggles
    const sqlBtn = document.getElementById('mode-sql-btn');
    const ragBtn = document.getElementById('mode-rag-btn');
    const modeDesc = document.getElementById('chat-active-mode-desc');

    if (sqlBtn && ragBtn) {
      sqlBtn.addEventListener('click', () => {
        this.currentMode = 'sql';
        sqlBtn.classList.add('active');
        ragBtn.classList.remove('active');
        if (modeDesc) modeDesc.textContent = 'Mode: Querying live equipment metrics with Text-to-SQL';
      });

      ragBtn.addEventListener('click', () => {
        this.currentMode = 'rag';
        ragBtn.classList.add('active');
        sqlBtn.classList.remove('active');
        if (modeDesc) modeDesc.textContent = 'Mode: Searching engineering manuals & SOP documents with RAG';
      });
    }

    // New Chat Button
    const newChatBtn = document.getElementById('btn-new-chat');
    if (newChatBtn) {
      newChatBtn.addEventListener('click', () => {
        this.currentSessionUid = null;
        this.clearMessagesFeed();
        this.renderGreetingMessage();
        this.highlightActiveSession(null);
        UI.showToast('New Chat', 'Started a new conversational session.', 'info');
      });
    }

    // Chat Form Submit
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('chat-send-btn');

    if (chatForm && chatInput) {
      chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const question = chatInput.value.trim();
        if (!question) return;

        const activeDatasetUid = localStorage.getItem(CONFIG.STORAGE_KEYS.ACTIVE_DATASET_UID);
        if (!activeDatasetUid) {
          UI.showToast('No Active Dataset', 'Please select a dataset to chat with.', 'warning');
          return;
        }

        if (!AuthManager.isAuthenticated()) {
          UI.showToast('Authentication Required', 'Please sign in to use the AI Copilot.', 'warning');
          UI.openModal('auth-modal');
          return;
        }

        // Append user message
        this.appendMessage('User', question);
        chatInput.value = '';

        // Add loading assistant placeholder
        const placeholderId = 'temp-msg-' + Date.now();
        this.appendLoadingMessage(placeholderId);

        try {
          if (sendBtn) sendBtn.disabled = true;

          let response;
          if (this.currentMode === 'sql') {
            response = await ApiClient.post(CONFIG.ENDPOINTS.CHAT_SQL, {
              dataset_uid: activeDatasetUid,
              session_uid: this.currentSessionUid || undefined,
              question
            });
            this.replaceLoadingMessage(placeholderId, response.answer, 'sql');
          } else {
            response = await ApiClient.post(CONFIG.ENDPOINTS.CHAT_RAG, {
              dataset_uid: activeDatasetUid,
              session_uid: this.currentSessionUid || undefined,
              question
            });
            this.replaceLoadingMessage(placeholderId, response.answer, 'rag', response.sources);
          }

          // Reload session list to show updated/new session
          this.loadSessions();

        } catch (err) {
          this.replaceLoadingMessage(placeholderId, `⚠️ **Error**: ${err.message || 'Failed to generate answer. Please try again.'}`, 'error');
        } finally {
          if (sendBtn) sendBtn.disabled = false;
        }
      });
    }
  }

  /**
   * Load previous chat sessions for current user
   */
  static async loadSessions() {
    const listContainer = document.getElementById('chat-sessions-list');
    if (!listContainer) return;

    if (!AuthManager.isAuthenticated()) {
      listContainer.innerHTML = '<div style="font-size: 0.8rem; color: var(--text-muted); padding: 0.5rem;">Sign in to view chat history</div>';
      return;
    }

    try {
      const sessions = await ApiClient.get(CONFIG.ENDPOINTS.CHAT_SESSIONS);
      this.sessions = Array.isArray(sessions) ? sessions : [];

      if (this.sessions.length === 0) {
        listContainer.innerHTML = '<div style="font-size: 0.8rem; color: var(--text-muted); padding: 0.5rem;">No previous sessions</div>';
        return;
      }

      listContainer.innerHTML = this.sessions.map(s => `
        <div class="chat-session-item ${s.session_uid === this.currentSessionUid ? 'active' : ''}" data-uid="${s.session_uid}">
          <span class="chat-session-title" title="${s.title || 'Chat Session'}">${s.title || 'Equipment Analysis'}</span>
          <button class="chat-session-del-btn" title="Delete Session" data-uid="${s.session_uid}">
            <i data-lucide="trash"></i>
          </button>
        </div>
      `).join('');

      if (window.lucide) window.lucide.createIcons({ root: listContainer });

      // Session click
      listContainer.querySelectorAll('.chat-session-item').forEach(item => {
        item.addEventListener('click', (e) => {
          if (e.target.closest('.chat-session-del-btn')) return;
          const uid = item.getAttribute('data-uid');
          this.loadSessionHistory(uid);
        });
      });

      // Delete session click
      listContainer.querySelectorAll('.chat-session-del-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          e.stopPropagation();
          const uid = btn.getAttribute('data-uid');
          if (confirm('Delete this chat session history?')) {
            try {
              await ApiClient.delete(CONFIG.ENDPOINTS.CHAT_SESSION_DETAIL(uid));
              if (this.currentSessionUid === uid) {
                this.currentSessionUid = null;
                this.clearMessagesFeed();
                this.renderGreetingMessage();
              }
              this.loadSessions();
            } catch (err) {
              UI.showToast('Error', err.message, 'error');
            }
          }
        });
      });

    } catch (err) {
      console.warn('Failed to load chat sessions:', err);
    }
  }

  /**
   * Load history for a given session UID
   */
  static async loadSessionHistory(sessionUid) {
    this.currentSessionUid = sessionUid;
    this.highlightActiveSession(sessionUid);

    const feed = document.getElementById('chat-messages-feed');
    if (!feed) return;

    try {
      feed.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 2rem;">Loading chat history...</div>';
      const history = await ApiClient.get(CONFIG.ENDPOINTS.CHAT_SESSION_DETAIL(sessionUid));
      const messages = history.messages || [];

      this.clearMessagesFeed();

      if (messages.length === 0) {
        this.renderGreetingMessage();
        return;
      }

      messages.forEach(m => {
        this.appendMessage(m.role, m.message);
      });

    } catch (err) {
      feed.innerHTML = `<div style="color: var(--accent-rose); padding: 1rem;">Failed to load history: ${err.message}</div>`;
    }
  }

  static highlightActiveSession(sessionUid) {
    document.querySelectorAll('.chat-session-item').forEach(el => {
      if (el.getAttribute('data-uid') === sessionUid) {
        el.classList.add('active');
      } else {
        el.classList.remove('active');
      }
    });
  }

  static clearMessagesFeed() {
    const feed = document.getElementById('chat-messages-feed');
    if (feed) feed.innerHTML = '';
  }

  static renderGreetingMessage() {
    const feed = document.getElementById('chat-messages-feed');
    if (!feed) return;
    feed.innerHTML = `
      <div class="chat-message assistant-message">
        <div class="message-avatar"><i data-lucide="bot"></i></div>
        <div class="message-bubble">
          Hello! I'm your <strong>ChemPulse AI Copilot</strong>. I can analyze your equipment parameters, generate SQL queries to find operational anomalies, or search your attached engineering manuals for SOPs.<br><br>
          <em>Try asking: "Which pumps are operating with temperature above 100°C?" or "What is the average pressure across all reactors?"</em>
        </div>
      </div>
    `;
    if (window.lucide) window.lucide.createIcons({ root: feed });
  }

  static appendMessage(role, text, sources = []) {
    const feed = document.getElementById('chat-messages-feed');
    if (!feed) return;

    const isUser = (role === 'User' || role === 'user');
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-message ${isUser ? 'user-message' : 'assistant-message'}`;

    const formattedText = this.formatMarkdown(text);

    let sourcesHtml = '';
    if (sources && sources.length > 0) {
      sourcesHtml = `
        <div class="sources-container">
          <div class="sources-label">Citations & Source Manuals</div>
          <div class="sources-chips-list">
            ${sources.map(s => `
              <span class="source-chip" title="Document UID: ${s.document_uid}">
                <i data-lucide="file-text"></i> ${s.document_name} ${s.page ? `(p. ${s.page})` : ''} [Chunk #${s.chunk_index}]
              </span>
            `).join('')}
          </div>
        </div>
      `;
    }

    msgDiv.innerHTML = `
      <div class="message-avatar"><i data-lucide="${isUser ? 'user' : 'bot'}"></i></div>
      <div class="message-bubble">
        ${formattedText}
        ${sourcesHtml}
      </div>
    `;

    feed.appendChild(msgDiv);
    if (window.lucide) window.lucide.createIcons({ root: msgDiv });
    feed.scrollTop = feed.scrollHeight;
  }

  static appendLoadingMessage(tempId) {
    const feed = document.getElementById('chat-messages-feed');
    if (!feed) return;

    const msgDiv = document.createElement('div');
    msgDiv.className = 'chat-message assistant-message';
    msgDiv.id = tempId;

    msgDiv.innerHTML = `
      <div class="message-avatar"><i data-lucide="bot"></i></div>
      <div class="message-bubble" style="display: flex; align-items: center; gap: 0.5rem; color: var(--text-secondary);">
        <i data-lucide="loader" class="spin"></i> AI Copilot is analyzing equipment data...
      </div>
    `;

    feed.appendChild(msgDiv);
    if (window.lucide) window.lucide.createIcons({ root: msgDiv });
    feed.scrollTop = feed.scrollHeight;
  }

  static replaceLoadingMessage(tempId, text, mode, sources = []) {
    const loadingDiv = document.getElementById(tempId);
    if (!loadingDiv) return;

    const bubble = loadingDiv.querySelector('.message-bubble');
    if (bubble) {
      let html = this.formatMarkdown(text);
      if (sources && sources.length > 0) {
        html += `
          <div class="sources-container">
            <div class="sources-label">Citations & Source Manuals</div>
            <div class="sources-chips-list">
              ${sources.map(s => `
                <span class="source-chip" title="Document: ${s.document_uid}">
                  <i data-lucide="file-text"></i> ${s.document_name} ${s.page ? `(p. ${s.page})` : ''} [Chunk #${s.chunk_index}]
                </span>
              `).join('')}
            </div>
          </div>
        `;
      }
      bubble.innerHTML = html;
      bubble.style.color = '';
      if (window.lucide) window.lucide.createIcons({ root: loadingDiv });
    }

    const feed = document.getElementById('chat-messages-feed');
    if (feed) feed.scrollTop = feed.scrollHeight;
  }

  static formatMarkdown(text) {
    if (!text) return '';
    // Basic markdown conversion for bold, code blocks, bullet points, and newlines
    let formatted = text
      .replace(/```sql([\s\S]*?)```/gi, '<pre class="sql-query-block"><code>$1</code></pre>')
      .replace(/```([\s\S]*?)```/gi, '<pre class="sql-query-block"><code>$1</code></pre>')
      .replace(/`([^`]+)`/g, '<code style="background: rgba(255,255,255,0.1); padding: 0.1rem 0.35rem; border-radius: 4px; font-family: var(--font-mono); font-size: 0.85em;">$1</code>')
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/\*([^*]+)\*/g, '<em>$1</em>')
      .replace(/\n\n/g, '<br><br>')
      .replace(/\n/g, '<br>');
    return formatted;
  }
}
