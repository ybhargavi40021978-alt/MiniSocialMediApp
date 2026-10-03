/**
 * MINISOCIAL — REAL-TIME MESSAGING JAVASCRIPT
 * Handles real-time chat sending, background polling, and DOM updates without duplication.
 */

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  if (!cookieValue) {
    const inputToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (inputToken) cookieValue = inputToken.value;
  }
  return cookieValue;
}

document.addEventListener('DOMContentLoaded', () => {
  const activeChatPane = document.getElementById('active-chat-pane');
  const chatMessagesStream = document.getElementById('chat-messages-stream');
  const chatForm = document.getElementById('chat-composer-form');
  const chatInput = document.getElementById('chat-msg-input');
  const sidebarMessagesBadge = document.getElementById('sidebar-messages-badge');

  function scrollToBottom() {
    if (chatMessagesStream) {
      chatMessagesStream.scrollTop = chatMessagesStream.scrollHeight;
    }
  }

  scrollToBottom();

  function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function getLatestMessageId() {
    if (!chatMessagesStream) return 0;
    const msgEls = chatMessagesStream.querySelectorAll('[data-msg-id]');
    let maxId = 0;
    msgEls.forEach(el => {
      const id = parseInt(el.getAttribute('data-msg-id'), 10);
      if (id > maxId) maxId = id;
    });
    return maxId;
  }

  function appendMessage(msg) {
    if (!chatMessagesStream) return;
    if (document.getElementById(`msg-${msg.id}`)) return; // Duplicate prevention

    const row = document.createElement('div');
    row.className = `msg-row ${msg.is_me ? 'me' : 'other'}`;
    row.id = `msg-${msg.id}`;
    row.setAttribute('data-msg-id', msg.id);

    const avatarHtml = msg.sender_avatar 
      ? `<img src="${msg.sender_avatar}" alt="${escapeHtml(msg.sender)}" class="avatar-img">`
      : `<svg viewBox="0 0 32 32" class="avatar-svg"><circle cx="16" cy="16" r="16" fill="${msg.sender_color || '#1976F3'}"/></svg>`;

    row.innerHTML = `
      <div class="msg-avatar" aria-hidden="true">
        ${avatarHtml}
      </div>
      <div class="msg-bubble">
        <p class="msg-text">${escapeHtml(msg.content)}</p>
        <span class="msg-time">${msg.created_at}</span>
      </div>
    `;

    chatMessagesStream.appendChild(row);
    scrollToBottom();
  }

  /* --------------------------------------------------
     1. SEND MESSAGE VIA AJAX
     -------------------------------------------------- */
  if (chatForm && activeChatPane && chatInput) {
    const convId = activeChatPane.getAttribute('data-conv-id');

    chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const content = chatInput.value.trim();
      if (!content) return;

      const btnSubmit = document.getElementById('btn-chat-send');
      if (btnSubmit) btnSubmit.disabled = true;

      fetch('/messages/send/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
          conversation_id: convId,
          content: content
        })
      })
      .then(res => res.json())
      .then(data => {
        if (btnSubmit) btnSubmit.disabled = false;
        if (data.success && data.message) {
          appendMessage(data.message);
          chatInput.value = '';
          chatInput.focus();

          // Update snippet in conversations list
          const activeConvEl = document.querySelector(`.conv-item[data-conv-id="${convId}"] .conv-last-msg`);
          if (activeConvEl) {
            activeConvEl.textContent = `You: ${content}`;
          }
        }
      })
      .catch(err => {
        console.error('Send message error:', err);
        if (btnSubmit) btnSubmit.disabled = false;
      });
    });
  }

  /* --------------------------------------------------
     2. BACKGROUND POLLING FOR REAL-TIME CHAT UPDATES
     -------------------------------------------------- */
  let isPolling = false;

  function pollChatUpdates() {
    if (isPolling) return;
    if (!activeChatPane) {
      // Global badge polling only
      pollGlobalUnread();
      return;
    }

    const convId = activeChatPane.getAttribute('data-conv-id');
    if (!convId) return;

    const afterId = getLatestMessageId();
    isPolling = true;

    fetch(`/messages/${convId}/updates/?after=${afterId}`, {
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
    .then(res => res.json())
    .then(data => {
      isPolling = false;
      if (data.success) {
        if (data.messages && data.messages.length > 0) {
          data.messages.forEach(msg => {
            appendMessage(msg);
          });
        }
        if (sidebarMessagesBadge) {
          if (data.unread_count > 0) {
            sidebarMessagesBadge.textContent = data.unread_count;
            sidebarMessagesBadge.style.display = 'inline-block';
          } else {
            sidebarMessagesBadge.style.display = 'none';
          }
        }
      }
    })
    .catch(err => {
      isPolling = false;
      console.warn('Chat polling error:', err);
    });
  }

  function pollGlobalUnread() {
    fetch('/messages/updates/', {
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
    .then(res => res.json())
    .then(data => {
      if (data.success && sidebarMessagesBadge) {
        if (data.unread_count > 0) {
          sidebarMessagesBadge.textContent = data.unread_count;
          sidebarMessagesBadge.style.display = 'inline-block';
        } else {
          sidebarMessagesBadge.style.display = 'none';
        }
      }
    })
    .catch(() => {});
  }

  // Run polling every 2.5s
  setInterval(pollChatUpdates, 2500);
});
