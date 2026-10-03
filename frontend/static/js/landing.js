/**
 * MINISOCIAL — MAIN JAVASCRIPT
 * Handles interactivity: Like toggle, Follow/Following toggles,
 * Post creation, Auth modal, Mobile Drawer, and Toast notifications.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const btnLogin = document.getElementById('btn-login');
  const btnSignup = document.getElementById('btn-signup');
  const mobileBtnLogin = document.getElementById('mobile-btn-login');
  const mobileBtnSignup = document.getElementById('mobile-btn-signup');
  const ctaGetStarted = document.getElementById('cta-get-started');
  const ctaLearnMore = document.getElementById('cta-learn-more');
  
  // Auth Modal Elements
  const authModal = document.getElementById('auth-modal');
  const modalCloseBtn = document.getElementById('modal-close-btn');
  const modalTitle = document.getElementById('modal-title');
  const modalSubtitle = document.getElementById('modal-subtitle');
  const modalSubmitBtn = document.getElementById('modal-submit-btn');
  const modalToggleAuth = document.getElementById('modal-toggle-auth');
  const modalSwitchPrompt = document.getElementById('modal-switch-prompt');
  const formNameGroup = document.getElementById('form-name-group');
  const authForm = document.getElementById('auth-form');

  // Mobile Drawer
  const mobileToggle = document.getElementById('mobile-toggle');
  const mobileDrawer = document.getElementById('mobile-drawer');

  // Interactive Mockup Dashboard Elements
  const btnMockupLike = document.getElementById('btn-mockup-like');
  const mockupLikeCount = document.getElementById('mockup-like-count');
  const likeActionLabel = document.getElementById('like-action-label');
  const btnMockupPost = document.getElementById('btn-mockup-post');
  const composerTextInput = document.getElementById('composer-text-input');
  const dashPostsStream = document.getElementById('dash-posts-stream');

  // Profile Card Elements
  const btnFollowBhargavi = document.getElementById('btn-follow-bhargavi');
  const bhargaviFollowers = document.getElementById('bhargavi-followers');

  // Popular People Follow Buttons
  const popFollowButtons = document.querySelectorAll('.btn-pop-follow');

  // Navigation Links
  const navLinks = document.querySelectorAll('.nav-link, .mobile-link');

  // Toast
  const toastNotify = document.getElementById('toast-notify');
  const toastText = document.getElementById('toast-text');
  let toastTimeout = null;

  function showToast(message, icon = '✨') {
    if (!toastNotify || !toastText) return;
    toastText.textContent = message;
    const iconSpan = toastNotify.querySelector('.toast-icon');
    if (iconSpan) iconSpan.textContent = icon;

    toastNotify.classList.add('show');
    clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => {
      toastNotify.classList.remove('show');
    }, 3200);
  }

  /* --------------------------------------------------
     1. LIKE BUTTON INTERACTION
     -------------------------------------------------- */
  let isLiked = false;
  let currentLikes = 12;

  if (btnMockupLike && mockupLikeCount) {
    btnMockupLike.addEventListener('click', () => {
      isLiked = !isLiked;
      if (isLiked) {
        currentLikes++;
        btnMockupLike.classList.add('liked');
        likeActionLabel.textContent = 'Liked';
        showToast('You liked sai_kumar’s post! ❤️', '❤️');
      } else {
        currentLikes = Math.max(0, currentLikes - 1);
        btnMockupLike.classList.remove('liked');
        likeActionLabel.textContent = 'Like';
      }
      mockupLikeCount.textContent = currentLikes;
    });
  }

  /* --------------------------------------------------
     2. FOLLOW / FOLLOWING TOGGLES
     -------------------------------------------------- */
  // Bhargavi profile follow button
  let bhargaviFollowing = false;
  let followerCount = 25;

  if (btnFollowBhargavi && bhargaviFollowers) {
    btnFollowBhargavi.addEventListener('click', () => {
      bhargaviFollowing = !bhargaviFollowing;
      if (bhargaviFollowing) {
        followerCount++;
        btnFollowBhargavi.textContent = '✓ Following';
        btnFollowBhargavi.classList.add('following');
        showToast('You started following @bhargavi', '👤');
      } else {
        followerCount--;
        btnFollowBhargavi.textContent = 'Follow';
        btnFollowBhargavi.classList.remove('following');
        showToast('Unfollowed @bhargavi', '👋');
      }
      bhargaviFollowers.textContent = followerCount;
    });
  }

  // Popular People buttons
  popFollowButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      const isFollowing = btn.classList.contains('following');
      const userName = btn.closest('.popular-user-row')?.querySelector('.pop-name')?.textContent || 'User';

      if (!isFollowing) {
        btn.classList.add('following');
        btn.textContent = 'Following';
        showToast(`You are now following ${userName}!`, '✨');
      } else {
        btn.classList.remove('following');
        btn.textContent = 'Follow';
        showToast(`Unfollowed ${userName}`, '👋');
      }
    });
  });

  /* --------------------------------------------------
     3. POST COMPOSER INTERACTION
     -------------------------------------------------- */
  function handleCreatePost() {
    const text = composerTextInput.value.trim();
    if (!text) {
      composerTextInput.focus();
      return;
    }

    // Create a new post card dynamically
    const newPost = document.createElement('article');
    newPost.className = 'feed-post-card';
    newPost.style.animation = 'heart-pop 0.35s ease-out';
    newPost.innerHTML = `
      <div class="feed-post-header">
        <div class="post-user-info">
          <img src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=70&h=70&fit=crop&crop=faces" alt="You" class="post-avatar">
          <div>
            <h4 class="post-username">bhargavi</h4>
            <span class="post-timestamp">Just now</span>
          </div>
        </div>
        <button class="post-dots" aria-label="Post options">•••</button>
      </div>
      <p class="post-caption">${escapeHtml(text)}</p>
      <div class="post-stats-row">
        <div class="stats-left">
          <span class="stat-bubble heart-bubble">❤️ 1</span>
          <span class="stat-bubble comment-bubble">💬 0</span>
        </div>
      </div>
      <div class="post-actions-row">
        <button type="button" class="post-action-btn liked">
          <svg class="action-icon heart-svg" viewBox="0 0 24 24" fill="#E11D48" stroke="#E11D48" stroke-width="2">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
          </svg>
          <span class="action-label">Liked</span>
        </button>
        <button type="button" class="post-action-btn">
          <svg class="action-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
          </svg>
          <span>Comment</span>
        </button>
      </div>
    `;

    // Insert at top of posts stream
    if (dashPostsStream) {
      dashPostsStream.prepend(newPost);
    }

    composerTextInput.value = '';
    showToast('Your post was shared to the MiniSocial feed! 🚀', '🚀');
  }

  function escapeHtml(string) {
    const div = document.createElement('div');
    div.textContent = string;
    return div.innerHTML;
  }

  if (btnMockupPost && composerTextInput) {
    btnMockupPost.addEventListener('click', handleCreatePost);
    composerTextInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        handleCreatePost();
      }
    });
  }

  /* --------------------------------------------------
     4. AUTH MODAL (LOGIN & SIGN UP)
     -------------------------------------------------- */
  let authMode = 'signup'; // 'signup' or 'login'

  function openModal(mode = 'signup') {
    authMode = mode;
    updateModalView();
    authModal.classList.add('active');
    authModal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  }

  function closeModal() {
    authModal.classList.remove('active');
    authModal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  }

  function updateModalView() {
    if (authMode === 'signup') {
      modalTitle.textContent = 'Welcome to MiniSocial';
      modalSubtitle.textContent = 'Connect, share and grow with your community';
      modalSubmitBtn.textContent = 'Create Account';
      formNameGroup.style.display = 'block';
      modalSwitchPrompt.textContent = 'Already have an account?';
      modalToggleAuth.textContent = 'Log In';
    } else {
      modalTitle.textContent = 'Log in to MiniSocial';
      modalSubtitle.textContent = 'Welcome back! Enter your details to continue';
      modalSubmitBtn.textContent = 'Sign In';
      formNameGroup.style.display = 'none';
      modalSwitchPrompt.textContent = 'Don’t have an account?';
      modalToggleAuth.textContent = 'Sign Up';
    }
  }

  if (btnLogin) btnLogin.addEventListener('click', () => { window.location.href = '/login/'; });
  if (btnSignup) btnSignup.addEventListener('click', () => { window.location.href = '/register/'; });
  if (mobileBtnLogin) mobileBtnLogin.addEventListener('click', () => { window.location.href = '/login/'; });
  if (mobileBtnSignup) mobileBtnSignup.addEventListener('click', () => { window.location.href = '/register/'; });
  if (ctaGetStarted) ctaGetStarted.addEventListener('click', () => { window.location.href = '/register/'; });

  if (modalCloseBtn) modalCloseBtn.addEventListener('click', closeModal);
  if (authModal) {
    authModal.addEventListener('click', (e) => {
      if (e.target === authModal) closeModal();
    });
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && authModal.classList.contains('active')) {
      closeModal();
    }
  });

  if (modalToggleAuth) {
    modalToggleAuth.addEventListener('click', () => {
      authMode = authMode === 'signup' ? 'login' : 'signup';
      updateModalView();
    });
  }

  if (authForm) {
    authForm.addEventListener('submit', (e) => {
      e.preventDefault();
      closeModal();
      showToast(authMode === 'signup' ? 'Welcome aboard! Account created successfully 🎉' : 'Logged in successfully! Welcome back 👋');
    });
  }

  /* --------------------------------------------------
     5. MOBILE DRAWER NAVIGATION
     -------------------------------------------------- */
  function toggleMobileDrawer() {
    const isActive = mobileDrawer.classList.toggle('active');
    mobileToggle.classList.toggle('active', isActive);
  }

  function closeMobileDrawer() {
    mobileDrawer.classList.remove('active');
    mobileToggle.classList.remove('active');
  }

  if (mobileToggle) {
    mobileToggle.addEventListener('click', toggleMobileDrawer);
  }

  // Smooth scroll and active link management
  navLinks.forEach((link) => {
    link.addEventListener('click', (e) => {
      const targetId = link.getAttribute('href');
      if (targetId && targetId.startsWith('#')) {
        const targetElement = document.querySelector(targetId);
        if (targetElement) {
          e.preventDefault();
          closeMobileDrawer();
          
          // Remove active from all nav links
          document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
          
          // Add active to current if it's a main desktop link
          const mainNavLink = document.querySelector(`.nav-menu a[href="${targetId}"]`);
          if (mainNavLink) mainNavLink.classList.add('active');

          targetElement.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
        }
      }
    });
  });

  // Highlight active link on scroll
  const sections = ['home', 'features', 'how-it-works', 'contact'];
  window.addEventListener('scroll', () => {
    const scrollPos = window.scrollY + 100;
    
    sections.forEach((secId) => {
      const secEl = document.getElementById(secId);
      if (secEl) {
        const top = secEl.offsetTop;
        const height = secEl.offsetHeight;
        if (scrollPos >= top && scrollPos < top + height) {
          document.querySelectorAll('.nav-menu .nav-link').forEach(link => {
            link.classList.toggle('active', link.getAttribute('href') === `#${secId}`);
          });
        }
      }
    });
  }, { passive: true });
});
