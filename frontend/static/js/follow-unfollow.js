/**
 * MiniSocial — Screen 11: Follow / Unfollow (UI State) JavaScript
 * Demonstrates functional side-by-side follow/unfollow state toggling.
 */

document.addEventListener('DOMContentLoaded', () => {
  const followButtons = document.querySelectorAll('.btn-follow');

  followButtons.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();

      // Find the parent profile card
      const card = btn.closest('.profile-card');
      if (!card) return;

      const followersCountSpan = card.querySelector('.followers-count');
      const isCurrentlyFollowing = btn.getAttribute('data-following') === 'true';

      let currentCount = followersCountSpan ? parseInt(followersCountSpan.textContent, 10) || 0 : 8;

      if (isCurrentlyFollowing) {
        // Toggle to NOT-FOLLOWING state ("Follow")
        btn.setAttribute('data-following', 'false');
        btn.setAttribute('aria-label', 'Follow Priya');
        btn.classList.remove('following');
        btn.classList.add('follow');
        btn.textContent = 'Follow';

        if (followersCountSpan) {
          followersCountSpan.textContent = Math.max(0, currentCount - 1);
        }
      } else {
        // Toggle to FOLLOWING state ("Following")
        btn.setAttribute('data-following', 'true');
        btn.setAttribute('aria-label', 'Unfollow Priya');
        btn.classList.remove('follow');
        btn.classList.add('following');
        btn.textContent = 'Following';

        if (followersCountSpan) {
          followersCountSpan.textContent = currentCount + 1;
        }
      }
    });
  });

  // Tab switching for both cards
  const allTabs = document.querySelectorAll('.card-tabs-nav .tab-btn');
  allTabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      const parentNav = tab.closest('.card-tabs-nav');
      if (parentNav) {
        parentNav.querySelectorAll('.tab-btn').forEach((t) => t.classList.remove('active'));
        tab.classList.add('active');
      }
    });
  });
});
