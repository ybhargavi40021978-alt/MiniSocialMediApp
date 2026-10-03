/**
 * MINISOCIAL — HOME / FEED PAGE SCRIPT
 * Connects feed interactions to Django backend via AJAX / Fetch.
 * Includes background polling for live feed synchronization, real avatars, and badge updates.
 */

// Helper to get CSRF token
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
  const postsStreamContainer = document.getElementById('posts-stream-container');
  const composerTrigger = document.getElementById('composer-card-trigger');
  const modalOverlay = document.getElementById('modal-overlay');
  const createPostModal = document.getElementById('create-post-modal');
  const btnCloseModal = document.querySelector('.btn-close-modal');
  const createPostForm = document.getElementById('create-post-form');
  const postTextInput = document.getElementById('post-text-input');
  const validationMsg = document.getElementById('validation-msg');
  const btnTriggerImage = document.getElementById('btn-trigger-image');
  const postImageFile = document.getElementById('post-image-file');
  const imagePreviewContainer = document.getElementById('image-preview-container');
  const imagePreviewImg = document.getElementById('image-preview-img');
  const btnRemoveImage = document.getElementById('btn-remove-image');

  const sidebarNotifBadge = document.getElementById('sidebar-notif-badge');
  const topbarNotifBadge = document.getElementById('topbar-notif-badge');
  const sidebarMessagesBadge = document.getElementById('sidebar-messages-badge');

  function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function getLatestPostId() {
    if (!postsStreamContainer) return 0;
    const postEls = postsStreamContainer.querySelectorAll('[data-post-id]');
    let maxId = 0;
    postEls.forEach(el => {
      const id = parseInt(el.getAttribute('data-post-id'), 10);
      if (id > maxId) maxId = id;
    });
    return maxId;
  }

  /* --------------------------------------------------
     1. MODAL OPEN / CLOSE CONTROLS
     -------------------------------------------------- */
  function openModal() {
    if (createPostModal) createPostModal.classList.remove('hidden');
    if (modalOverlay) modalOverlay.classList.remove('hidden');
    if (postTextInput) setTimeout(() => postTextInput.focus(), 60);
  }

  function closeModal() {
    if (createPostModal) createPostModal.classList.add('hidden');
    if (modalOverlay) modalOverlay.classList.add('hidden');
    if (validationMsg) validationMsg.style.display = 'none';
  }

  if (composerTrigger) {
    composerTrigger.addEventListener('click', (e) => {
      e.preventDefault();
      openModal();
    });
  }

  if (btnCloseModal) {
    btnCloseModal.addEventListener('click', (e) => {
      e.preventDefault();
      closeModal();
    });
  }

  if (modalOverlay) {
    modalOverlay.addEventListener('click', () => {
      closeModal();
    });
  }

  /* --------------------------------------------------
     2. IMAGE PREVIEW CONTROLS
     -------------------------------------------------- */
  if (btnTriggerImage && postImageFile) {
    btnTriggerImage.addEventListener('click', () => {
      postImageFile.click();
    });

    postImageFile.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (event) => {
          if (imagePreviewImg) imagePreviewImg.src = event.target.result;
          if (imagePreviewContainer) imagePreviewContainer.style.display = 'block';
          if (validationMsg) validationMsg.style.display = 'none';
        };
        reader.readAsDataURL(file);
      }
    });
  }

  if (btnRemoveImage) {
    btnRemoveImage.addEventListener('click', (e) => {
      e.stopPropagation();
      if (postImageFile) postImageFile.value = '';
      if (imagePreviewImg) imagePreviewImg.src = '';
      if (imagePreviewContainer) imagePreviewContainer.style.display = 'none';
    });
  }

  /* --------------------------------------------------
     3. CREATE / PREPEND POST ELEMENT
     -------------------------------------------------- */
  function renderPostArticle(p) {
    if (document.getElementById(`post-${p.id}`)) return null;

    const article = document.createElement('article');
    article.className = 'post-card';
    article.id = `post-${p.id}`;
    article.dataset.postId = p.id;

    const imageSnippet = p.image_url ? `
      <div class="post-media-wrap" style="margin-top: 8px; border-radius: 6px; overflow: hidden; max-height: 220px;">
        <img src="${p.image_url}" alt="Post image" style="width: 100%; height: 100%; object-fit: cover; display: block;">
      </div>
    ` : '';

    const avatarSnippet = p.author_avatar ? `
      <img src="${p.author_avatar}" alt="${escapeHtml(p.author)}" class="avatar-img" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">
    ` : `
      <svg class="avatar-svg" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
        <circle cx="16" cy="16" r="16" fill="${p.author_color || '#1976F3'}"/>
        <circle cx="16" cy="12" r="6" fill="#FCD5B5"/>
        <path d="M11 10C11 6 21 6 21 10C21 11 19 8 16 8C13 8 11 11 11 10Z" fill="#1E293B"/>
        <path d="M8 26C8 21 12 19 16 19C20 19 24 21 24 26H8Z" fill="${p.author_color || '#1976F3'}"/>
      </svg>
    `;

    // Badges
    let badgesHtml = '<div class="post-badges-row">';
    if (p.mood) {
      badgesHtml += `<span class="post-pill-badge badge-mood">${escapeHtml(p.mood)}</span>`;
    }
    if (p.circle_name) {
      badgesHtml += `<a href="/circle/${p.circle_id}/" class="post-pill-badge badge-circle" style="text-decoration:none;">👥 ${escapeHtml(p.circle_name)}</a>`;
    } else if (p.visibility === 'followers') {
      badgesHtml += `<span class="post-pill-badge badge-visibility">👥 Followers</span>`;
    } else if (p.visibility === 'private') {
      badgesHtml += `<span class="post-pill-badge badge-visibility">🔒 Private</span>`;
    }
    if (p.expires_in_seconds !== null && p.expires_in_seconds !== undefined) {
      badgesHtml += `<span class="post-pill-badge badge-expiry expiry-countdown" data-post-id="${p.id}" data-remaining="${p.expires_in_seconds}">⏳ Expires in <span class="timer-display">...</span></span>`;
    }
    if (p.version_count > 1) {
      badgesHtml += `<span class="post-pill-badge badge-version" onclick="openEvolutionModal(${p.id})">v${p.version_count} • View Evolution</span>`;
    }
    badgesHtml += '</div>';

    // Poll
    let pollHtml = '';
    if (p.poll) {
      pollHtml = `<div class="poll-container" id="poll-box-${p.poll.id}"><h4 class="poll-question">📊 ${escapeHtml(p.poll.question)}</h4><div class="poll-options-list">`;
      p.poll.options.forEach(opt => {
        pollHtml += `
          <div class="poll-option-row">
            <button type="button" class="poll-option-btn" onclick="votePoll(${p.poll.id}, ${opt.id})" ${p.poll.has_voted ? 'disabled' : ''}>
              <div class="poll-option-progress" style="width: ${opt.percentage}%;"></div>
              <div class="poll-option-content">
                <span>${escapeHtml(opt.text)}</span>
                <span style="font-weight: 700;">${opt.percentage}% (${opt.votes})</span>
              </div>
            </button>
          </div>
        `;
      });
      pollHtml += `</div><span class="poll-total-votes">${p.poll.total_votes} total votes</span></div>`;
    }

    // Topics
    let topicsHtml = '';
    if (p.topics && p.topics.length > 0) {
      topicsHtml = '<div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 10px;">';
      p.topics.forEach(t => {
        topicsHtml += `<a href="/explore/?topic=${encodeURIComponent(t)}" style="font-size: 11.5px; color: #1976F3; text-decoration: none; font-weight: 600;">#${escapeHtml(t)}</a>`;
      });
      topicsHtml += '</div>';
    }

    // Reaction breakdown
    let breakdownHtml = '';
    if (p.reaction_breakdown && Object.keys(p.reaction_breakdown).length > 0) {
      breakdownHtml = '<div class="reaction-breakdown-bar">';
      for (const [reason, count] of Object.entries(p.reaction_breakdown)) {
        breakdownHtml += `<span class="reaction-reason-pill">${escapeHtml(reason)} ${count}</span>`;
      }
      breakdownHtml += '</div>';
    }

    const isLiked = p.is_liked || false;
    const likeCount = p.like_count !== undefined ? p.like_count : (p.likes_count || 0);

    article.innerHTML = `
      <div class="post-header">
        <div class="post-author-box">
          <a href="${p.author_url}" class="post-avatar-link" style="text-decoration: none;">
            <div class="post-avatar" aria-hidden="true">
              ${avatarSnippet}
            </div>
          </a>
          <div class="author-meta">
            <a href="${p.author_url}" class="author-username" style="text-decoration: none; color: inherit;">${escapeHtml(p.author)}</a>
            <span class="post-time">${p.created_at}</span>
          </div>
        </div>
        <div class="post-options-wrap">
          ${p.is_author ? `<button type="button" class="post-options-btn" onclick="openEditPostModal(${p.id}, '${escapeHtml(p.content).replace(/'/g, "\\'")}')" title="Edit Post">✏️</button>` : ''}
        </div>
      </div>
      ${badgesHtml}
      <div class="post-body">
        <a href="${p.detail_url}" style="text-decoration: none; color: inherit;">
          <p class="post-text">${escapeHtml(p.content)}</p>
        </a>
        ${imageSnippet}
        ${pollHtml}
        ${topicsHtml}
      </div>
      <div class="post-metadata">
        <span class="stat-likes-count"><span class="like-number">${likeCount}</span> Likes</span>
        <span class="stat-comments-count"><span class="comment-number">${p.comment_count || 0}</span> Comments</span>
      </div>
      ${breakdownHtml}
      <div class="post-actions-bar">
        <div class="reactions-wrapper" onmouseenter="showReactionsPopover(${p.id})" onmouseleave="hideReactionsPopover(${p.id})">
          <div class="reactions-popover hidden" id="reaction-popover-${p.id}">
            <button type="button" class="reaction-btn-icon" title="Like" onclick="reactToPost(${p.id}, '')">❤️</button>
            <button type="button" class="reaction-btn-icon" title="Helpful" onclick="reactToPost(${p.id}, 'Helpful')">👍</button>
            <button type="button" class="reaction-btn-icon" title="Funny" onclick="reactToPost(${p.id}, 'Funny')">😂</button>
            <button type="button" class="reaction-btn-icon" title="Inspiring" onclick="reactToPost(${p.id}, 'Inspiring')">🌟</button>
            <button type="button" class="reaction-btn-icon" title="Interesting" onclick="reactToPost(${p.id}, 'Interesting')">💡</button>
            <button type="button" class="reaction-btn-icon" title="Supportive" onclick="reactToPost(${p.id}, 'Supportive')">🤝</button>
          </div>
          <button 
            type="button" 
            class="action-btn action-like-btn ${isLiked ? 'active' : ''}" 
            id="like-btn-${p.id}"
            data-post-id="${p.id}"
            data-liked="${isLiked ? 'true' : 'false'}"
            onclick="toggleLikePost(${p.id})"
          >
            <span class="action-icon heart-icon">
              <svg viewBox="0 0 24 24" fill="${isLiked ? '#FF4D67' : 'none'}" stroke="${isLiked ? '#FF4D67' : 'currentColor'}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
              </svg>
            </span>
            <span class="action-text">${p.user_reaction_reason || (isLiked ? 'Liked' : 'Like')}</span>
          </button>
        </div>
        <a href="${p.detail_url}" class="action-btn action-comment-btn" style="text-decoration: none; color: inherit;">
          <span class="action-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
            </svg>
          </span>
          <span class="action-text">Comment</span>
        </a>
        <button type="button" class="action-btn action-share-btn" onclick="navigator.clipboard.writeText(window.location.origin + '${p.detail_url}'); alert('Post link copied to clipboard!');">
          <span class="action-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/>
              <polyline points="16 6 12 2 8 6"/>
              <line x1="12" y1="2" x2="12" y2="15"/>
            </svg>
          </span>
          <span class="action-text">Share</span>
        </button>
      </div>
    `;

    return article;
  }

  /* --------------------------------------------------
     4. CREATE POST SUBMISSION (AJAX)
     -------------------------------------------------- */
  if (createPostForm) {
    createPostForm.addEventListener('submit', (e) => {
      e.preventDefault();

      const content = postTextInput ? postTextInput.value.trim() : '';
      const hasImage = postImageFile && postImageFile.files.length > 0;
      const pollQuestion = document.getElementById('poll-question-input')?.value.trim();

      if (!content && !hasImage && !pollQuestion) {
        if (validationMsg) {
          validationMsg.textContent = "Please write something or create a poll.";
          validationMsg.style.display = 'block';
        }
        if (postTextInput) postTextInput.focus();
        return;
      }

      const btnSubmit = document.getElementById('btn-modal-post-submit');
      if (btnSubmit) {
        btnSubmit.disabled = true;
        btnSubmit.textContent = 'Posting...';
      }

      const formData = new FormData(createPostForm);
      const visVal = formData.get('visibility');
      if (visVal && visVal.startsWith('circle:')) {
        formData.set('circle_id', visVal.split(':')[1]);
        formData.set('visibility', 'circle');
      }

      fetch('/post/create/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData
      })
      .then(res => res.json())
      .then(data => {
        if (btnSubmit) {
          btnSubmit.disabled = false;
          btnSubmit.textContent = 'Post';
        }

        if (data.success) {
          const article = renderPostArticle(data.post);
          if (article && postsStreamContainer) {
            postsStreamContainer.prepend(article);
          }

          // Reset inputs and close modal
          if (postTextInput) postTextInput.value = '';
          if (postImageFile) postImageFile.value = '';
          if (imagePreviewContainer) imagePreviewContainer.style.display = 'none';
          createPostForm.reset();
          const pollContainer = document.getElementById('poll-fields-container');
          if (pollContainer) pollContainer.style.display = 'none';
          closeModal();
        } else {
          if (validationMsg) {
            validationMsg.textContent = data.message || "Failed to create post.";
            validationMsg.style.display = 'block';
          }
        }
      })
      .catch(err => {
        console.error("Post creation error:", err);
        if (btnSubmit) {
          btnSubmit.disabled = false;
          btnSubmit.textContent = 'Post';
        }
      });
    });
  }

  /* --------------------------------------------------
     5. LIKE / UNLIKE INTERACTION (AJAX)
     -------------------------------------------------- */
  function attachLikeListener(button) {
    if (!button) return;
    button.addEventListener('click', function(e) {
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
  }

  document.querySelectorAll('.action-like-btn').forEach(btn => {
    attachLikeListener(btn);
  });

  /* --------------------------------------------------
     6. BACKGROUND FEED & BADGE POLLING
     -------------------------------------------------- */
  let isFeedPolling = false;

  function pollFeedUpdates() {
    if (isFeedPolling) return;
    const afterId = getLatestPostId();
    isFeedPolling = true;

    fetch(`/feed/updates/?after=${afterId}`, {
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
    .then(res => res.json())
    .then(data => {
      isFeedPolling = false;
      if (data.success && data.posts && data.posts.length > 0) {
        // Prepend new posts in ascending order of arrival (or reversed if array is newest first)
        data.posts.reverse().forEach(p => {
          const article = renderPostArticle(p);
          if (article && postsStreamContainer) {
            postsStreamContainer.prepend(article);
          }
        });
      }
    })
    .catch(err => {
      isFeedPolling = false;
    });

    // Check message & notification badges
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

    fetch('/notifications/updates/', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        if (sidebarNotifBadge) {
          if (data.unread_count > 0) {
            sidebarNotifBadge.textContent = data.unread_count;
            sidebarNotifBadge.style.display = 'inline-block';
          } else {
            sidebarNotifBadge.style.display = 'none';
          }
        }
        if (topbarNotifBadge) {
          if (data.unread_count > 0) {
            topbarNotifBadge.textContent = data.unread_count;
            topbarNotifBadge.style.display = 'flex';
          } else {
            topbarNotifBadge.style.display = 'none';
          }
        }
      }
    }).catch(() => {});
  }

  // Poll every 4 seconds
  setInterval(pollFeedUpdates, 4000);
});
