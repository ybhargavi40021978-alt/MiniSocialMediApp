/**
 * MiniSocial — Screen 10: Like / Unlike (UI State) JavaScript
 * Demonstrates functional side-by-side like state toggling.
 */

document.addEventListener('DOMContentLoaded', () => {
  const likeButtons = document.querySelectorAll('.action-like');

  likeButtons.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();

      // Find the card containing this button
      const card = btn.closest('.post-card');
      if (!card) return;

      const likesCountSpan = card.querySelector('.likes-count');
      const textSpan = btn.querySelector('.btn-text');
      const isCurrentlyLiked = btn.getAttribute('data-liked') === 'true';

      let currentLikes = likesCountSpan ? parseInt(likesCountSpan.textContent, 10) || 0 : 0;

      if (isCurrentlyLiked) {
        // Toggle to UNLIKED state
        btn.setAttribute('data-liked', 'false');
        btn.setAttribute('aria-label', 'Like post');
        btn.classList.remove('liked');
        if (textSpan) textSpan.textContent = 'Like';
        if (likesCountSpan) {
          likesCountSpan.textContent = Math.max(0, currentLikes - 1);
        }
      } else {
        // Toggle to LIKED state
        btn.setAttribute('data-liked', 'true');
        btn.setAttribute('aria-label', 'Unlike post');
        btn.classList.add('liked');
        if (textSpan) textSpan.textContent = 'Liked';
        if (likesCountSpan) {
          likesCountSpan.textContent = currentLikes + 1;
        }
      }
    });
  });
});
