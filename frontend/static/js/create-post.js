/**
 * MiniSocial — Screen 9: Create Post (Modal/Inline) JavaScript
 * Handles modal open/close, image attachment preview, validation, and post creation.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const modalOverlay = document.getElementById('modal-overlay');
  const createPostModal = document.getElementById('create-post-modal');
  const btnCloseModal = document.getElementById('btn-close-modal');
  const createPostForm = document.getElementById('create-post-form');
  const postTextInput = document.getElementById('post-text-input');
  const validationMsg = document.getElementById('validation-msg');

  // Image upload elements
  const btnTriggerImage = document.getElementById('btn-trigger-image');
  const postImageFile = document.getElementById('post-image-file');
  const imagePreviewContainer = document.getElementById('image-preview-container');
  const imagePreviewImg = document.getElementById('image-preview-img');
  const btnRemoveImage = document.getElementById('btn-remove-image');

  // Background feed container & composer trigger
  const postsStreamContainer = document.getElementById('posts-stream-container');
  const feedComposerTrigger = document.getElementById('feed-composer-trigger');

  let selectedImageBase64 = null;

  // 1. Close Modal
  function closeModal() {
    if (createPostModal) createPostModal.classList.add('hidden');
    if (modalOverlay) modalOverlay.classList.add('hidden');
    if (validationMsg) validationMsg.style.display = 'none';
  }

  // 2. Open Modal
  function openModal() {
    if (createPostModal) createPostModal.classList.remove('hidden');
    if (modalOverlay) modalOverlay.classList.remove('hidden');
    if (postTextInput) {
      setTimeout(() => postTextInput.focus(), 50);
    }
  }

  if (btnCloseModal) {
    btnCloseModal.addEventListener('click', (e) => {
      e.preventDefault();
      closeModal();
    });
  }

  // Click on darkened overlay to dismiss
  if (modalOverlay) {
    modalOverlay.addEventListener('click', () => {
      closeModal();
    });
  }

  // Click background composer to reopen modal if dismissed
  if (feedComposerTrigger) {
    feedComposerTrigger.addEventListener('click', () => {
      openModal();
    });
  }

  // 3. Image Selection & Preview
  if (btnTriggerImage && postImageFile) {
    btnTriggerImage.addEventListener('click', () => {
      postImageFile.click();
    });

    postImageFile.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (event) => {
          selectedImageBase64 = event.target.result;
          imagePreviewImg.src = selectedImageBase64;
          imagePreviewContainer.style.display = 'block';
          if (validationMsg) validationMsg.style.display = 'none';
        };
        reader.readAsDataURL(file);
      }
    });
  }

  // Remove attached image
  if (btnRemoveImage) {
    btnRemoveImage.addEventListener('click', (e) => {
      e.stopPropagation();
      selectedImageBase64 = null;
      postImageFile.value = '';
      imagePreviewImg.src = '';
      imagePreviewContainer.style.display = 'none';
    });
  }

  // 4. Create Post Submission & Validation
  if (createPostForm) {
    createPostForm.addEventListener('submit', (e) => {
      e.preventDefault();
      submitPost();
    });
  }

  function submitPost() {
    const textContent = postTextInput ? postTextInput.value.trim() : '';

    // Empty validation
    if (!textContent && !selectedImageBase64) {
      if (validationMsg) {
        validationMsg.textContent = 'Please write something before posting.';
        validationMsg.style.display = 'block';
      }
      if (postTextInput) postTextInput.focus();
      return;
    }

    // Hide validation
    if (validationMsg) validationMsg.style.display = 'none';

    // Create new post card in background feed
    if (postsStreamContainer) {
      const newPostArticle = document.createElement('article');
      newPostArticle.className = 'post-card';
      
      const imageSnippet = selectedImageBase64 ? `
        <div class="post-media-wrap" style="margin-top: 8px; border-radius: 6px; overflow: hidden; max-height: 180px;">
          <img src="${selectedImageBase64}" alt="User post image" style="width: 100%; height: 100%; object-fit: cover; display: block;">
        </div>
      ` : '';

      newPostArticle.innerHTML = `
        <div class="post-header">
          <div class="post-author-box">
            <div class="post-avatar">
              <svg class="avatar-svg" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
                <circle cx="16" cy="16" r="16" fill="#6366F1"/>
                <circle cx="16" cy="12" r="6" fill="#FEEAA1"/>
                <path d="M11 11C11 7 21 7 21 11C21 12 19 12 18 10C17 9 15 9 14 10C13 12 11 12 11 11Z" fill="#3D405B"/>
                <path d="M8 26C8 21 12 19 16 19C20 19 24 21 24 26H8Z" fill="#818CF8"/>
              </svg>
            </div>
            <div class="author-meta">
              <span class="author-username">Bhargavi</span>
              <span class="post-time">Just now</span>
            </div>
          </div>
        </div>
        <div class="post-body">
          <p class="post-text-content">${escapeHTML(textContent)}</p>
          ${imageSnippet}
        </div>
        <div class="post-actions-bar">
          <div class="action-btn-group">
            <button type="button" class="post-action-btn like-btn">
              <span class="action-icon">♥</span>
              <span class="action-count">0</span>
            </button>
            <button type="button" class="post-action-btn">
              <span class="action-icon">💬</span>
              <span class="action-count">0</span>
            </button>
          </div>
        </div>
      `;

      // Prepend to top of feed
      postsStreamContainer.prepend(newPostArticle);

      // Add simple like toggle for the newly created post
      const newLikeBtn = newPostArticle.querySelector('.like-btn');
      if (newLikeBtn) {
        newLikeBtn.addEventListener('click', function() {
          const countSpan = this.querySelector('.action-count');
          const isLiked = this.classList.toggle('active');
          let count = parseInt(countSpan.textContent, 10) || 0;
          countSpan.textContent = isLiked ? count + 1 : Math.max(0, count - 1);
        });
      }
    }

    // Reset form inputs
    if (postTextInput) postTextInput.value = '';
    selectedImageBase64 = null;
    if (postImageFile) postImageFile.value = '';
    if (imagePreviewContainer) {
      imagePreviewImg.src = '';
      imagePreviewContainer.style.display = 'none';
    }

    // Close modal
    closeModal();
  }

  // Security helper to escape HTML
  function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
});
