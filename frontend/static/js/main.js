/**
 * MINISOCIAL — REGISTRATION FORM LOGIC
 * Handles input focus styling, client-side validation, error messages,
 * and form submission for Django.
 */

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('registration-form');
  const usernameInput = document.getElementById('id_username');
  const emailInput = document.getElementById('id_email');
  const passwordInput = document.getElementById('id_password');
  const confirmPasswordInput = document.getElementById('id_confirm_password');

  const boxUsername = document.getElementById('box-username');
  const boxEmail = document.getElementById('box-email');
  const boxPassword = document.getElementById('box-password');
  const boxConfirmPassword = document.getElementById('box-confirm-password');

  const errorUsername = document.getElementById('error-username');
  const errorEmail = document.getElementById('error-email');
  const errorPassword = document.getElementById('error-password');
  const errorConfirmPassword = document.getElementById('error-confirm-password');

  setupInputFocus(usernameInput, boxUsername, errorUsername);
  setupInputFocus(emailInput, boxEmail, errorEmail);
  setupInputFocus(passwordInput, boxPassword, errorPassword);
  setupInputFocus(confirmPasswordInput, boxConfirmPassword, errorConfirmPassword);

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

  function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  }

  if (form) {
    form.addEventListener('submit', (e) => {
      let isValid = true;

      // 1. Username
      const usernameVal = usernameInput ? usernameInput.value.trim() : '';
      if (!usernameVal) {
        showError(boxUsername, errorUsername, 'Please enter a username');
        isValid = false;
      } else {
        clearError(boxUsername, errorUsername);
      }

      // 2. Email
      const emailVal = emailInput ? emailInput.value.trim() : '';
      if (!emailVal) {
        showError(boxEmail, errorEmail, 'Please enter your email address');
        isValid = false;
      } else if (!isValidEmail(emailVal)) {
        showError(boxEmail, errorEmail, 'Please enter a valid email address');
        isValid = false;
      } else {
        clearError(boxEmail, errorEmail);
      }

      // 3. Password
      const passwordVal = passwordInput ? passwordInput.value : '';
      if (!passwordVal) {
        showError(boxPassword, errorPassword, 'Please enter a password');
        isValid = false;
      } else {
        clearError(boxPassword, errorPassword);
      }

      // 4. Confirm Password
      if (confirmPasswordInput) {
        const confirmVal = confirmPasswordInput.value;
        if (!confirmVal) {
          showError(boxConfirmPassword, errorConfirmPassword, 'Please confirm your password');
          isValid = false;
        } else if (passwordVal !== confirmVal) {
          showError(boxConfirmPassword, errorConfirmPassword, 'Passwords do not match');
          isValid = false;
        } else {
          clearError(boxConfirmPassword, errorConfirmPassword);
        }
      }

      if (!isValid) {
        e.preventDefault();
        const firstErrorBox = form.querySelector('.input-box.has-error');
        if (firstErrorBox) {
          const inputToFocus = firstErrorBox.querySelector('input');
          if (inputToFocus) inputToFocus.focus();
        }
        return;
      }

      // If action is empty or #, preventDefault for demo:
      if (!form.getAttribute('action') || form.getAttribute('action') === '' || form.getAttribute('action') === '#') {
        e.preventDefault();
        const submitBtn = document.getElementById('btn-register-submit');
        if (submitBtn) {
          submitBtn.textContent = 'Account Created! ✓';
          submitBtn.style.background = '#10B981';
          submitBtn.disabled = true;
          setTimeout(() => {
            submitBtn.textContent = 'Register';
            submitBtn.style.background = '';
            submitBtn.disabled = false;
          }, 2500);
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
