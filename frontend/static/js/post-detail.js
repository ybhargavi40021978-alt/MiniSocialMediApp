/**
 * MINISOCIAL — POST DETAIL PAGE LOGIC
 * Connects Like toggle and Comment submission to Django backend via AJAX.
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
  /* --------------------------------------------------
     1. LIKE / UNLIKE INTERACTION
     -------------------------------------------------- */
  const btnLike = document.getElementById('btn-like-detail');
  const likesCountEl = document.getElementById('metric-likes-count');
  const actionLikeText = document.getElementById('detail-like-text');

  if (btnLike) {
    btnLike.addEventListener('click', () => {
      const postId = btnLike.getAttribute('data-post-id');
      if (!postId) return;

      const svg = btnLike.querySelector('svg');

      fetch(`/post/${postId}/like/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          if (data.liked) {
            btnLike.classList.add('liked');
            btnLike.setAttribute('data-liked', 'true');
            if (actionLikeText) actionLikeText.textContent = 'Liked';
            if (svg) {
              svg.setAttribute('fill', '#FF4D67');
              svg.setAttribute('stroke', '#FF4D67');
            }
          } else {
            btnLike.classList.remove('liked');
            btnLike.setAttribute('data-liked', 'false');
            if (actionLikeText) actionLikeText.textContent = 'Like';
            if (svg) {
              svg.setAttribute('fill', 'none');
              svg.setAttribute('stroke', 'currentColor');
            }
          }
          if (likesCountEl) likesCountEl.textContent = data.like_count;
        }
      })
      .catch(err => console.error("Like error:", err));
    });
  }

  /* --------------------------------------------------
     2. COMMENT SUBMISSION (AJAX)
     -------------------------------------------------- */
  const commentForm = document.getElementById('comment-composer-form');
  const commentInput = document.getElementById('comment-input-field');
  const commentsStream = document.getElementById('comments-stream-container');
  const commentsCountEl = document.getElementById('metric-comments-count');
  const noCommentsMsg = document.getElementById('no-comments-msg');
  const btnFocusComment = document.getElementById('btn-focus-comment');

  if (btnFocusComment && commentInput) {
    btnFocusComment.addEventListener('click', () => {
      commentInput.focus();
    });
  }

  if (commentForm && commentInput) {
    commentForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const content = commentInput.value.trim();
      if (!content) {
        commentInput.focus();
        return;
      }

      const actionUrl = commentForm.getAttribute('action');

      fetch(actionUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ content: content })
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          const c = data.comment;
          if (noCommentsMsg) noCommentsMsg.remove();

          const commentDiv = document.createElement('div');
          commentDiv.className = 'comment-item';
          commentDiv.id = `comment-${c.id}`;

          const avatarHtml = c.avatar_url 
            ? `<img src="${c.avatar_url}" alt="${escapeHtml(c.author)}" class="avatar-img" style="width: 100%; height: 100%; object-fit: cover;">`
            : `<svg class="avatar-svg" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="12" fill="${c.avatar_color || '#1976F3'}"/>
                <circle cx="12" cy="9" r="4.5" fill="#FCD5B5"/>
                <path d="M8 8C8 5 16 5 16 8C16 9 14.5 7 12 7C9.5 7 8 9 8 8Z" fill="#1E293B"/>
                <path d="M6 20C6 16 9 14.5 12 14.5C15 14.5 18 16 18 20H6Z" fill="${c.avatar_color || '#1976F3'}"/>
              </svg>`;

          commentDiv.innerHTML = `
            <div class="comment-avatar-wrap" style="overflow: hidden; border-radius: 50%;">
              ${avatarHtml}
            </div>
            <div class="comment-content-box">
              <div class="comment-header-row">
                <a href="${c.author_url}" class="comment-author" style="text-decoration: none; color: inherit;">
                  ${escapeHtml(c.author)}
                </a>
                <span class="comment-timestamp">${c.created_at}</span>
              </div>
              <p class="comment-text-body">${escapeHtml(c.content)}</p>
            </div>
          `;

          if (commentsStream) {
            commentsStream.appendChild(commentDiv);
          }

          if (commentsCountEl) {
            commentsCountEl.textContent = data.comment_count;
          }

          commentInput.value = '';
        }
      })
      .catch(err => console.error("Comment error:", err));
    });
  }

  function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
});
