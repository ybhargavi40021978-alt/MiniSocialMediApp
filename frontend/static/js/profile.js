/**
 * MINISOCIAL — PROFILE PAGE LOGIC
 * Handles tab switching, like toggling on profile posts, direct photo upload,
 * and real-time polling for follower counts.
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
  // Tabs
  const tabBtns = document.querySelectorAll('.profile-tabs-nav .tab-btn');
  const postsTabContent = document.getElementById('posts-tab-content');
  const aboutTabContent = document.getElementById('about-tab-content');
  const followersCountEl = document.getElementById('followers-count');
  const followingCountEl = document.getElementById('following-count');
  const photoUploadInput = document.getElementById('profile-photo-direct-upload');
  const mainAvatarContainer = document.getElementById('main-avatar-container');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.getAttribute('data-tab');
      if (!tab) return;

      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      if (tab === 'posts') {
        if (postsTabContent) postsTabContent.style.display = 'block';
        if (aboutTabContent) aboutTabContent.style.display = 'none';
      } else if (tab === 'about') {
        if (postsTabContent) postsTabContent.style.display = 'none';
        if (aboutTabContent) aboutTabContent.style.display = 'block';
      }
    });
  });

  /* --------------------------------------------------
     1. DIRECT PROFILE PHOTO UPLOAD
     -------------------------------------------------- */
  if (photoUploadInput) {
    photoUploadInput.addEventListener('change', () => {
      const file = photoUploadInput.files[0];
      if (!file) return;

      const formData = new FormData();
      formData.append('profile_picture', file);

      fetch('/profile/photo/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData
      })
      .then(res => res.json())
      .then(data => {
        if (data.success && data.image_url) {
          if (mainAvatarContainer) {
            mainAvatarContainer.innerHTML = `<img src="${data.image_url}" alt="Profile" class="avatar-img" id="profile-avatar-img" style="width: 100%; height: 100%; object-fit: cover;">`;
          }
        } else {
          alert(data.message || 'Failed to update photo.');
        }
      })
      .catch(err => {
        console.error('Profile photo upload error:', err);
      });
    });
  }

  /* --------------------------------------------------
     2. POST LIKES (AJAX)
     -------------------------------------------------- */
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

  /* --------------------------------------------------
     3. LIVE FOLLOWER COUNT POLLING
     -------------------------------------------------- */
  let isPolling = false;
  function syncFollowers() {
    if (isPolling) return;
    isPolling = true;

    fetch('/profile/followers/updates/', {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(res => res.json())
    .then(data => {
      isPolling = false;
      if (data.success) {
        if (followersCountEl) followersCountEl.textContent = data.followers_count;
        if (followingCountEl) followingCountEl.textContent = data.following_count;
      }
    })
    .catch(() => {
      isPolling = false;
    });
  }

  setInterval(syncFollowers, 3500);
});
