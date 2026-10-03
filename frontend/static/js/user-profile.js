/**
 * MINISOCIAL — USER PROFILE SCRIPT
 * Handles Follow/Following toggle via AJAX, tab switching, and live follower sync.
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
  const followBtn = document.getElementById('btn-follow-user');
  const followersCountEl = document.getElementById('user-followers-count');

  if (followBtn) {
    followBtn.addEventListener('click', (e) => {
      e.preventDefault();
      const username = followBtn.getAttribute('data-username');
      if (!username) return;

      followBtn.disabled = true;

      fetch(`/user/${username}/follow/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
      .then(res => res.json())
      .then(data => {
        followBtn.disabled = false;
        if (data.success) {
          if (data.following) {
            followBtn.classList.add('following');
            followBtn.setAttribute('data-following', 'true');
            followBtn.textContent = 'Following';
          } else {
            followBtn.classList.remove('following');
            followBtn.setAttribute('data-following', 'false');
            followBtn.textContent = 'Follow';
          }
          const count = data.followers_count !== undefined ? data.followers_count : data.follower_count;
          if (followersCountEl && count !== undefined) {
            followersCountEl.textContent = count;
          }
        }
      })
      .catch(err => {
        followBtn.disabled = false;
        console.error("Follow error:", err);
      });
    });
  }

  // Tabs
  const tabBtns = document.querySelectorAll('.profile-tabs-nav .tab-btn');
  const postsTabContent = document.getElementById('posts-tab-content');
  const aboutTabContent = document.getElementById('about-tab-content');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const tab = btn.getAttribute('data-tab');
      if (tab === 'posts') {
        if (postsTabContent) postsTabContent.style.display = 'block';
        if (aboutTabContent) aboutTabContent.style.display = 'none';
      } else if (tab === 'about') {
        if (postsTabContent) postsTabContent.style.display = 'none';
        if (aboutTabContent) aboutTabContent.style.display = 'block';
      }
    });
  });

  // Like buttons in profile posts
  document.querySelectorAll('.action-like-btn').forEach(btn => {
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      const postId = this.dataset.postId;
      if (!postId) return;

      this.disabled = true;

      const likeNumberSpan = this.closest('.post-card').querySelector('.like-number');
      const actionTextSpan = this.querySelector('.action-text');
      const svgIcon = this.querySelector('svg');

      fetch(`/post/${postId}/like/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
      .then(res => res.json())
      .then(data => {
        this.disabled = false;
        if (data.success) {
          if (data.liked) {
            this.classList.add('active');
            this.dataset.liked = 'true';
            if (actionTextSpan) actionTextSpan.textContent = 'Liked';
            if (svgIcon) {
              svgIcon.setAttribute('fill', '#FF4D67');
              svgIcon.setAttribute('stroke', '#FF4D67');
            }
          } else {
            this.classList.remove('active');
            this.dataset.liked = 'false';
            if (actionTextSpan) actionTextSpan.textContent = 'Like';
            if (svgIcon) {
              svgIcon.setAttribute('fill', 'none');
              svgIcon.setAttribute('stroke', 'currentColor');
            }
          }
          if (likeNumberSpan) likeNumberSpan.textContent = data.like_count;
        }
      })
      .catch(err => {
        this.disabled = false;
        console.error("Like error:", err);
      });
    });
  });

  // Polling for live follower count of this user
  if (followBtn && followersCountEl) {
    const username = followBtn.getAttribute('data-username');
    setInterval(() => {
      fetch(`/profile/followers/updates/?user=${username}`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      })
      .then(res => res.json())
      .then(data => {
        if (data.success && data.followers_count !== undefined) {
          followersCountEl.textContent = data.followers_count;
        }
      })
      .catch(() => {});
    }, 3500);
  }
});
