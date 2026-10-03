/**
 * MINISOCIAL — LOGIN FORM LOGIC
 * Handles input focus styling, client-side validation, error messages,
 * and form submission ready for Django authentication integration.
 */

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('login-form');
  const usernameInput = document.getElementById('id_username');
  const passwordInput = document.getElementById('id_password');
  const rememberCheckbox = document.getElementById('id_remember_me');

  const boxUsername = document.getElementById('box-login-username');
  const boxPassword = document.getElementById('box-login-password');

  const errorUsername = document.getElementById('error-login-username');
  const errorPassword = document.getElementById('error-login-password');

  // Input focus/blur styling handlers
  setupInputFocus(usernameInput, boxUsername, errorUsername);
  setupInputFocus(passwordInput, boxPassword, errorPassword);

  function setupInputFocus(input, box, errorEl) {
    if (!input || !box) return;

    input.addEventListener('focus', () => {
      box.classList.add('focused');
      box.classList.remove('has-error');
      if (errorEl) {
        errorEl.classList.remove('visible');
        errorEl.textContent = '';
      }
    });

    input.addEventListener('blur', () => {
      box.classList.remove('focused');
    });

    input.addEventListener('input', () => {
      if (box.classList.contains('has-error')) {
        box.classList.remove('has-error');
        if (errorEl) {
          errorEl.classList.remove('visible');
          errorEl.textContent = '';
        }
      }
    });
  }

  // Form submit handler
  if (form) {
    form.addEventListener('submit', (e) => {
      let isValid = true;

      // 1. Check Username is not empty
      const usernameVal = usernameInput.value.trim();
      if (!usernameVal) {
        showError(boxUsername, errorUsername, 'Please enter your username');
        isValid = false;
      } else {
        clearError(boxUsername, errorUsername);
      }

      // 2. Check Password is not empty
      const passwordVal = passwordInput.value;
      if (!passwordVal) {
        showError(boxPassword, errorPassword, 'Please enter your password');
        isValid = false;
      } else {
        clearError(boxPassword, errorPassword);
      }

      // 3. If invalid, display message & focus first invalid input
      if (!isValid) {
        e.preventDefault();
        const firstErrorBox = form.querySelector('.input-box.has-error');
        if (firstErrorBox) {
          const inputToFocus = firstErrorBox.querySelector('input');
          if (inputToFocus) inputToFocus.focus();
        }
        return;
      }

      // 4. If valid: If connected to Django with action URL, normal submission proceeds.
      // If frontend demo mode (action is empty or #), provide visual feedback:
      if (!form.getAttribute('action') || form.getAttribute('action') === '') {
        e.preventDefault();
        
        const submitBtn = document.getElementById('btn-login-submit');
        if (submitBtn) {
          submitBtn.textContent = 'Logging in...';
          submitBtn.style.background = '#10B981';
          submitBtn.disabled = true;

          setTimeout(() => {
            submitBtn.textContent = 'Welcome Back! ✓';
            setTimeout(() => {
              submitBtn.textContent = 'Login';
              submitBtn.style.background = '';
              submitBtn.disabled = false;
            }, 1800);
          }, 600);
        }
      }
    });
  }

  function showError(box, errorEl, message) {
    if (box) box.classList.add('has-error');
    if (errorEl) {
      errorEl.textContent = message;
      errorEl.classList.add('visible');
    }
  }

  function clearError(box, errorEl) {
    if (box) box.classList.remove('has-error');
    if (errorEl) {
      errorEl.textContent = '';
      errorEl.classList.remove('visible');
    }
  }
});
