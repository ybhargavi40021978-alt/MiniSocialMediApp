/**
 * MINISOCIAL — FOLLOWERS & FOLLOWING PAGE SCRIPT
 * Handles live follow/unfollow toggling via Django AJAX, tab switching,
 * and live background polling to reflect followers/following updates in real time.
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
  const followersStream = document.getElementById('followers-stream');
  const sectionTitle = document.getElementById('followers-section-title');
  const tabBtns = document.querySelectorAll('.profile-tabs-nav .tab-btn');
  const headerFollowersCount = document.getElementById('header-followers-count');
  const headerFollowingCount = document.getElementById('header-following-count');

  let currentTab = 'followers';

  function attachFollowRowListeners() {
    const buttons = document.querySelectorAll('.btn-follow-toggle');
    buttons.forEach((btn) => {
      // Prevent attaching duplicate listeners
      if (btn.dataset.listenerAttached) return;
      btn.dataset.listenerAttached = 'true';

      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const username = btn.getAttribute('data-username');
        if (!username) return;

        btn.disabled = true;

        fetch(`/user/${username}/follow/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
          }
        })
        .then(res => res.json())
        .then(data => {
          btn.disabled = false;
          if (data.success) {
            if (data.following) {
              btn.setAttribute('data-following', 'true');
              btn.textContent = 'Following';
              btn.classList.remove('follow');
              btn.classList.add('following');
            } else {
              btn.setAttribute('data-following', 'false');
              btn.textContent = 'Follow';
              btn.classList.remove('following');
              btn.classList.add('follow');
            }
          }
        })
        .catch(err => {
          btn.disabled = false;
          console.error("Follow toggle error:", err);
        });
      });
    });
  }

  attachFollowRowListeners();

  // Tab switching
  tabBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      const tab = btn.getAttribute('data-tab');
      if (!tab) return;
      currentTab = tab;

      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      if (tab === 'followers') {
        syncFollowersList(true);
      } else if (tab === 'following') {
        renderFollowingList();
      } else if (tab === 'about') {
        if (sectionTitle) sectionTitle.textContent = "About";
        if (followersStream) {
          followersStream.innerHTML = `
            <div style="padding: 16px; font-size: 11.5px; color: #475569; line-height: 1.4;">
              MiniSocial is a clean social community to share your thoughts, follow friends, and stay inspired.
            </div>
          `;
        }
      }
    });
  });

  function renderFollowingList() {
    if (!followersStream || !window.followingData) return;
    if (sectionTitle) sectionTitle.textContent = `Following (${window.followingData.length})`;

    if (window.followingData.length === 0) {
      followersStream.innerHTML = `
        <div style="text-align: center; padding: 24px 14px; font-size: 11px; color: #64748B;">
          You are not following anyone yet.
        </div>
      `;
    } else {
      followersStream.innerHTML = window.followingData.map(item => {
        const avatarHtml = item.avatar 
          ? `<img src="${item.avatar}" alt="${item.username}" class="avatar-img" style="width: 100%; height: 100%; object-fit: cover;">`
          : `<svg class="avatar-svg" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><circle cx="16" cy="16" r="16" fill="${item.color || '#1976F3'}"/></svg>`;

        return `
          <div class="follower-row" id="following-${item.id}">
            <div class="follower-avatar-wrap" aria-hidden="true" style="overflow: hidden; border-radius: 50%;">
              ${avatarHtml}
            </div>
            <div class="follower-meta">
              <a href="${item.profile_url}" class="follower-username" style="text-decoration: none; color: inherit;">
                ${item.username}
              </a>
              <span class="follower-handle">@${item.username}</span>
            </div>
            <div class="follower-btn-wrap">
              <button 
                type="button" 
                class="btn-follow-toggle following" 
                data-username="${item.username}"
                data-following="true"
              >
                Following
              </button>
            </div>
          </div>
        `;
      }).join('');
      attachFollowRowListeners();
    }
  }

  /* --------------------------------------------------
     LIVE REAL-TIME POLLING FOR FOLLOWERS / FOLLOWING
     -------------------------------------------------- */
  let isPolling = false;

  function syncFollowersList(forceRender = false) {
    if (isPolling) return;
    isPolling = true;

    fetch('/profile/followers/updates/', {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(res => res.json())
    .then(data => {
      isPolling = false;
      if (!data.success) return;

      if (headerFollowersCount) headerFollowersCount.textContent = data.followers_count;
      if (headerFollowingCount) headerFollowingCount.textContent = data.following_count;

      if (currentTab === 'followers' && followersStream) {
        if (sectionTitle) sectionTitle.textContent = `Followers (${data.followers_count})`;

        const serverFollowerIds = new Set(data.followers.map(f => f.id));

        // 1. Remove rows of users who unfollowed
        const existingRows = followersStream.querySelectorAll('.follower-row[data-user-id]');
        existingRows.forEach(row => {
          const uid = parseInt(row.getAttribute('data-user-id'), 10);
          if (!serverFollowerIds.has(uid)) {
            row.remove();
          }
        });

        // 2. Add newly followed users if not in DOM
        data.followers.forEach(f => {
          if (!document.getElementById(`follower-${f.id}`)) {
            const emptyMsg = document.getElementById('empty-followers-msg');
            if (emptyMsg) emptyMsg.remove();

            const row = document.createElement('div');
            row.className = 'follower-row';
            row.id = `follower-${f.id}`;
            row.setAttribute('data-user-id', f.id);

            const avatarHtml = f.avatar 
              ? `<img src="${f.avatar}" alt="${f.username}" class="avatar-img" style="width: 100%; height: 100%; object-fit: cover;">`
              : `<svg class="avatar-svg" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><circle cx="16" cy="16" r="16" fill="${f.color || '#1976F3'}"/></svg>`;

            row.innerHTML = `
              <div class="follower-avatar-wrap" aria-hidden="true" style="overflow: hidden; border-radius: 50%;">
                ${avatarHtml}
              </div>
              <div class="follower-meta">
                <a href="${f.profile_url}" class="follower-username" style="text-decoration: none; color: inherit;">
                  ${f.username}
                </a>
                <span class="follower-handle">@${f.username}</span>
              </div>
              <div class="follower-btn-wrap">
                <button 
                  type="button" 
                  class="btn-follow-toggle ${f.is_following ? 'following' : 'follow'}" 
                  data-username="${f.username}"
                  data-following="${f.is_following ? 'true' : 'false'}"
                >
                  ${f.is_following ? 'Following' : 'Follow'}
                </button>
              </div>
            `;

            followersStream.prepend(row);
          }
        });

        // If list is empty
        if (data.followers.length === 0 && !document.getElementById('empty-followers-msg')) {
          followersStream.innerHTML = `
            <div style="text-align: center; padding: 24px 14px; font-size: 11px; color: #64748B;" id="empty-followers-msg">
              No followers yet.
            </div>
          `;
        }

        attachFollowRowListeners();
      }
    })
    .catch(err => {
      isPolling = false;
      console.warn('Followers sync error:', err);
    });
  }

  // Poll every 3.5s
  setInterval(() => {
    syncFollowersList(false);
  }, 3500);
});
