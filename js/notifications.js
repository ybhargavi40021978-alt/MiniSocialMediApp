/**
 * MINISOCIAL — NOTIFICATIONS PAGE SCRIPT
 * Handles marking notifications as read, individual dismiss/delete,
 * tab filtering (All vs Unread), and background live polling.
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
  const notifItemsList = document.getElementById('notification-items-list');
  const btnMarkAll = document.getElementById('btn-mark-all-read');
  const sidebarNotifBadge = document.getElementById('sidebar-notif-badge');
  const headerUnreadPill = document.getElementById('header-unread-pill');
  const unreadTabBadge = document.getElementById('unread-tab-badge');
  const sidebarMessagesBadge = document.getElementById('sidebar-messages-badge');

  const tabAll = document.getElementById('tab-all');
  const tabUnread = document.getElementById('tab-unread');
  let currentFilter = 'all'; // 'all' or 'unread'

  function updateBadge(count) {
    if (sidebarNotifBadge) {
      if (count > 0) {
        sidebarNotifBadge.textContent = count;
        sidebarNotifBadge.style.display = 'inline-block';
      } else {
        sidebarNotifBadge.style.display = 'none';
      }
    }
    if (headerUnreadPill) {
      if (count > 0) {
        headerUnreadPill.textContent = `${count} new`;
        headerUnreadPill.style.display = 'inline-block';
      } else {
        headerUnreadPill.style.display = 'none';
      }
    }
    if (unreadTabBadge) {
      if (count > 0) {
        unreadTabBadge.textContent = count;
        unreadTabBadge.style.display = 'inline-block';
      } else {
        unreadTabBadge.style.display = 'none';
      }
    }
  }

  function applyFilter() {
    if (!notifItemsList) return;
    const rows = notifItemsList.querySelectorAll('.notification-row');
    let visibleCount = 0;

    rows.forEach(row => {
      const isUnread = row.classList.contains('unread');
      if (currentFilter === 'unread') {
        if (isUnread) {
          row.style.display = 'flex';
          visibleCount++;
        } else {
          row.style.display = 'none';
        }
      } else {
        row.style.display = 'flex';
        visibleCount++;
      }
    });

    let emptyFilterBox = document.getElementById('empty-filter-box');
    if (visibleCount === 0 && rows.length > 0) {
      if (!emptyFilterBox) {
        emptyFilterBox = document.createElement('div');
        emptyFilterBox.id = 'empty-filter-box';
        emptyFilterBox.style.cssText = 'text-align: center; padding: 48px 16px; color: #64748B; font-size: 13px;';
        emptyFilterBox.innerHTML = `
          <div style="font-size: 24px; margin-bottom: 8px;">🎉</div>
          <strong>No unread notifications!</strong><br>
          <span style="color: #94A3B8; font-size: 12px;">You are all caught up with community updates.</span>
        `;
        notifItemsList.appendChild(emptyFilterBox);
      }
      emptyFilterBox.style.display = 'block';
    } else if (emptyFilterBox) {
      emptyFilterBox.style.display = 'none';
    }
  }

  // Filter tab buttons
  if (tabAll) {
    tabAll.addEventListener('click', () => {
      currentFilter = 'all';
      tabAll.style.background = 'var(--primary-blue)';
      tabAll.style.color = '#fff';
      tabAll.style.border = 'none';

      if (tabUnread) {
        tabUnread.style.background = '#fff';
        tabUnread.style.color = 'var(--text-gray)';
        tabUnread.style.border = '1px solid var(--border-light)';
      }
      applyFilter();
    });
  }

  if (tabUnread) {
    tabUnread.addEventListener('click', () => {
      currentFilter = 'unread';
      tabUnread.style.background = 'var(--primary-blue)';
      tabUnread.style.color = '#fff';
      tabUnread.style.border = 'none';

      if (tabAll) {
        tabAll.style.background = '#fff';
        tabAll.style.color = 'var(--text-gray)';
        tabAll.style.border = '1px solid var(--border-light)';
      }
      applyFilter();
    });
  }

  function attachRowListener(row) {
    if (!row || row.dataset.listenerAttached) return;
    row.dataset.listenerAttached = 'true';

    // Click anywhere on row -> Mark read and open target URL
    row.addEventListener('click', (e) => {
      // If clicking avatar link or dismiss button, don't trigger row navigation
      if (e.target.closest('a') || e.target.closest('.btn-dismiss-notif')) return;

      const isUnread = row.classList.contains('unread');
      const notifId = row.getAttribute('data-id');
      const targetUrl = row.getAttribute('data-target-url');

      if (isUnread && notifId) {
        fetch(`/notification/${notifId}/read/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
          }
        })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            row.classList.remove('unread');
            row.setAttribute('data-read', 'true');
            const blueDot = row.querySelector('.unread-blue-dot');
            if (blueDot) blueDot.remove();
            updateBadge(data.unread_count);
            if (currentFilter === 'unread') applyFilter();
            if (targetUrl && targetUrl !== '#' && targetUrl !== 'None') {
              window.location.href = targetUrl;
            }
          }
        })
        .catch(() => {
          if (targetUrl && targetUrl !== '#' && targetUrl !== 'None') {
            window.location.href = targetUrl;
          }
        });
      } else if (targetUrl && targetUrl !== '#' && targetUrl !== 'None') {
        window.location.href = targetUrl;
      }
    });

    // Dismiss / Delete button
    const btnDismiss = row.querySelector('.btn-dismiss-notif');
    if (btnDismiss) {
      btnDismiss.addEventListener('click', (e) => {
        e.stopPropagation();
        const notifId = btnDismiss.getAttribute('data-id');
        if (!notifId) return;

        btnDismiss.disabled = true;
        fetch(`/notification/${notifId}/delete/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
          }
        })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            row.style.opacity = '0';
            row.style.transform = 'translateX(20px)';
            row.style.transition = 'all 0.25s ease';
            setTimeout(() => {
              row.remove();
              updateBadge(data.unread_count);
              applyFilter();
            }, 250);
          } else {
            btnDismiss.disabled = false;
          }
        })
        .catch(() => {
          btnDismiss.disabled = false;
        });
      });
    }
  }

  document.querySelectorAll('.notification-row').forEach(row => {
    attachRowListener(row);
  });

  // Mark all as read
  if (btnMarkAll) {
    btnMarkAll.addEventListener('click', () => {
      fetch('/notification/read-all/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          document.querySelectorAll('.notification-row').forEach(row => {
            row.classList.remove('unread');
            row.setAttribute('data-read', 'true');
            const blueDot = row.querySelector('.unread-blue-dot');
            if (blueDot) blueDot.remove();
          });
          updateBadge(0);
          if (currentFilter === 'unread') applyFilter();
        }
      })
      .catch(err => console.error("Mark all read error:", err));
    });
  }

  function getLatestNotifId() {
    if (!notifItemsList) return 0;
    const rows = notifItemsList.querySelectorAll('.notification-row[data-id]');
    let maxId = 0;
    rows.forEach(r => {
      const id = parseInt(r.getAttribute('data-id'), 10);
      if (id > maxId) maxId = id;
    });
    return maxId;
  }

  /* --------------------------------------------------
     LIVE BACKGROUND POLLING FOR NOTIFICATIONS
     -------------------------------------------------- */
  let isPolling = false;

  function pollNotifications() {
    if (isPolling) return;
    const afterId = getLatestNotifId();
    isPolling = true;

    fetch(`/notifications/updates/?after=${afterId}`, {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(res => res.json())
    .then(data => {
      isPolling = false;
      if (data.success) {
        updateBadge(data.unread_count);

        if (data.notifications && data.notifications.length > 0 && notifItemsList) {
          const noNotifsBox = document.getElementById('no-notifs-box');
          if (noNotifsBox) noNotifsBox.remove();

          data.notifications.reverse().forEach(n => {
            if (document.getElementById(`notif-${n.id}`)) return; // Prevent duplicates

            const row = document.createElement('div');
            row.className = `notification-row ${n.is_read ? '' : 'unread'}`;
            row.id = `notif-${n.id}`;
            row.setAttribute('data-id', n.id);
            row.setAttribute('data-read', n.is_read ? 'true' : 'false');
            row.setAttribute('data-type', n.notification_type);
            row.setAttribute('data-target-url', n.target_url || '#');

            const avatarHtml = n.sender_avatar 
              ? `<img src="${n.sender_avatar}" alt="${n.sender}" style="width: 100%; height: 100%; object-fit: cover;">`
              : `<svg viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg" style="width: 100%; height: 100%;">
                  <circle cx="16" cy="16" r="16" fill="${n.sender_color || '#1976F3'}"/>
                  <circle cx="16" cy="12" r="6" fill="#FCD5B5"/>
                  <path d="M10 11C10 6 22 6 22 11C22 13 20 12 18 10C16 9 14 9 12 10C10 12 10 13 10 11Z" fill="#1E293B"/>
                  <path d="M8 26C8 21 12 19 16 19C20 19 24 21 24 26H8Z" fill="${n.sender_color || '#1976F3'}"/>
                </svg>`;

            let badgeSvg = '';
            if (n.notification_type === 'like') {
              badgeSvg = `<svg viewBox="0 0 24 24" fill="#FF4F70" stroke="#FF4F70" width="10" height="10"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>`;
            } else if (n.notification_type === 'comment') {
              badgeSvg = `<svg viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5" width="10" height="10"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>`;
            } else if (n.notification_type === 'follow') {
              badgeSvg = `<svg viewBox="0 0 24 24" fill="none" stroke="#1976F3" stroke-width="2.5" width="10" height="10"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/></svg>`;
            } else {
              badgeSvg = `<svg viewBox="0 0 24 24" fill="none" stroke="#6366F1" stroke-width="2.5" width="10" height="10"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`;
            }

            row.innerHTML = `
              <div class="notif-avatar-wrapper">
                <a href="/user/${n.sender}/" style="display: block; width: 100%; height: 100%; border-radius: 50%; overflow: hidden;" onclick="event.stopPropagation();">
                  ${avatarHtml}
                </a>
                <span class="mini-type-badge icon-${n.notification_type}">
                  ${badgeSvg}
                </span>
              </div>
              <div class="notif-text-content">
                <p class="notif-message-text">
                  <a href="/user/${n.sender}/" class="notif-user-bold" onclick="event.stopPropagation();">
                    ${n.sender}
                  </a>
                  <span style="color: #475569;">${n.text}</span>
                </p>
                <span class="notif-time-ago">Just now</span>
              </div>
              <div class="notif-row-actions" style="display: flex; align-items: center; gap: 10px; margin-left: auto;">
                ${n.is_read ? '' : '<span class="unread-blue-dot" style="width: 8px; height: 8px; border-radius: 50%; background: #1976F3; display: inline-block;"></span>'}
                <button type="button" class="btn-dismiss-notif" data-id="${n.id}" title="Dismiss notification" style="background: none; border: none; color: #CBD5E1; cursor: pointer; padding: 4px; font-size: 16px; line-height: 1; border-radius: 4px; transition: color 0.15s;" onclick="event.stopPropagation();">
                  &times;
                </button>
              </div>
            `;

            notifItemsList.prepend(row);
            attachRowListener(row);
          });

          applyFilter();
        }
      }
    })
    .catch(() => {
      isPolling = false;
    });

    // Sync messages badge
    fetch('/messages/updates/', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
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
    }).catch(() => {});
  }

  setInterval(pollNotifications, 3500);
});
