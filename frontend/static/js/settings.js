/**
 * MINISOCIAL — SETTINGS PAGE SCRIPT
 * Handles Profile Picture Upload, Profile Info updates, and Password Change.
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
  // Elements
  const photoInput = document.getElementById('settings-photo-file');
  const photoPreviewWrap = document.getElementById('settings-photo-preview');
  const profileForm = document.getElementById('profile-info-form');
  const bioInput = document.getElementById('settings-bio-input');
  const colorInput = document.getElementById('settings-color-input');
  const profileAlert = document.getElementById('profile-status-alert');
  const btnSaveProfile = document.getElementById('btn-save-profile');

  const passwordForm = document.getElementById('password-change-form');
  const currentPasswordInput = document.getElementById('input-current-password');
  const newPasswordInput = document.getElementById('input-new-password');
  const confirmPasswordInput = document.getElementById('input-confirm-password');
  const passwordAlert = document.getElementById('password-status-alert');
  const btnChangePassword = document.getElementById('btn-change-password-submit');

  function showAlert(el, msg, isSuccess) {
    if (!el) return;
    el.textContent = msg;
    el.className = 'status-alert ' + (isSuccess ? 'success' : 'error');
    el.style.display = 'block';
    setTimeout(() => {
      el.style.display = 'none';
    }, 4500);
  }

  function updateAvatarsOnPage(imageUrl) {
    if (!imageUrl) return;
    // Update settings preview
    if (photoPreviewWrap) {
      photoPreviewWrap.innerHTML = `<img src="${imageUrl}" alt="Profile photo" class="avatar-img" id="settings-avatar-img">`;
    }
    // Update topbar avatar
    const topbarWrap = document.querySelector('.topbar-user-area .user-avatar-wrap');
    if (topbarWrap) {
      topbarWrap.innerHTML = `<img src="${imageUrl}" alt="Avatar" class="avatar-img" id="topbar-avatar-img">`;
    }
  }

  /* --------------------------------------------------
     1. PHOTO UPLOAD VIA AJAX
     -------------------------------------------------- */
  if (photoInput) {
    photoInput.addEventListener('change', () => {
      const file = photoInput.files[0];
      if (!file) return;

      const formData = new FormData();
      formData.append('profile_picture', file);

      if (profileAlert) {
        profileAlert.textContent = 'Uploading photo...';
        profileAlert.className = 'status-alert';
        profileAlert.style.display = 'block';
      }

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
        if (data.success) {
          updateAvatarsOnPage(data.image_url);
          showAlert(profileAlert, 'Profile picture updated successfully!', true);
        } else {
          showAlert(profileAlert, data.message || 'Failed to update photo.', false);
        }
      })
      .catch(err => {
        console.error('Photo upload error:', err);
        showAlert(profileAlert, 'Network error while uploading photo.', false);
      });
    });
  }

  /* --------------------------------------------------
     2. PROFILE INFO UPDATE
     -------------------------------------------------- */
  if (profileForm) {
    profileForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const bio = bioInput ? bioInput.value.trim() : '';
      const color = colorInput ? colorInput.value : '';

      if (btnSaveProfile) {
        btnSaveProfile.disabled = true;
        btnSaveProfile.textContent = 'Saving...';
      }

      fetch('/profile/update/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
          bio: bio,
          avatar_color: color
        })
      })
      .then(res => res.json())
      .then(data => {
        if (btnSaveProfile) {
          btnSaveProfile.disabled = false;
          btnSaveProfile.textContent = 'Save Profile';
        }
        if (data.success) {
          showAlert(profileAlert, 'Profile details saved successfully!', true);
        } else {
          showAlert(profileAlert, data.message || 'Failed to save profile.', false);
        }
      })
      .catch(err => {
        console.error('Profile update error:', err);
        if (btnSaveProfile) {
          btnSaveProfile.disabled = false;
          btnSaveProfile.textContent = 'Save Profile';
        }
        showAlert(profileAlert, 'Network error updating profile.', false);
      });
    });
  }

  /* --------------------------------------------------
     3. PASSWORD CHANGE
     -------------------------------------------------- */
  if (passwordForm) {
    passwordForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const currentPassword = currentPasswordInput ? currentPasswordInput.value : '';
      const newPassword = newPasswordInput ? newPasswordInput.value : '';
      const confirmPassword = confirmPasswordInput ? confirmPasswordInput.value : '';

      if (!currentPassword || !newPassword || !confirmPassword) {
        showAlert(passwordAlert, 'Please fill in all password fields.', false);
        return;
      }

      if (newPassword !== confirmPassword) {
        showAlert(passwordAlert, 'New passwords do not match.', false);
        return;
      }

      if (newPassword.length < 4) {
        showAlert(passwordAlert, 'Password must be at least 4 characters long.', false);
        return;
      }

      if (btnChangePassword) {
        btnChangePassword.disabled = true;
        btnChangePassword.textContent = 'Updating...';
      }

      fetch('/settings/password/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
          confirm_password: confirmPassword
        })
      })
      .then(res => res.json())
      .then(data => {
        if (btnChangePassword) {
          btnChangePassword.disabled = false;
          btnChangePassword.textContent = 'Change Password';
        }
        if (data.success) {
          showAlert(passwordAlert, 'Password changed successfully!', true);
          if (currentPasswordInput) currentPasswordInput.value = '';
          if (newPasswordInput) newPasswordInput.value = '';
          if (confirmPasswordInput) confirmPasswordInput.value = '';
        } else {
          showAlert(passwordAlert, data.message || 'Failed to change password.', false);
        }
      })
      .catch(err => {
        console.error('Password change error:', err);
        if (btnChangePassword) {
          btnChangePassword.disabled = false;
          btnChangePassword.textContent = 'Change Password';
        }
        showAlert(passwordAlert, 'Network error changing password.', false);
      });
    });
  }

  /* --------------------------------------------------
     4. FEED PREFERENCES UPDATE
     -------------------------------------------------- */
  const feedPrefForm = document.getElementById('feed-preferences-form');
  const prefCleanFeed = document.getElementById('pref-clean-feed');
  const prefPreferredMood = document.getElementById('pref-preferred-mood');
  const prefShowExpired = document.getElementById('pref-show-expired');
  const prefAlert = document.getElementById('pref-status-alert');
  const btnSavePref = document.getElementById('btn-save-preferences');

  if (feedPrefForm) {
    feedPrefForm.addEventListener('submit', (e) => {
      e.preventDefault();

      if (btnSavePref) {
        btnSavePref.disabled = true;
        btnSavePref.textContent = 'Saving...';
      }

      const payload = {
        clean_feed: prefCleanFeed ? prefCleanFeed.checked : false,
        preferred_mood: prefPreferredMood ? prefPreferredMood.value : '',
        show_expired_posts: prefShowExpired ? prefShowExpired.checked : false
      };

      fetch('/preferences/update/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(payload)
      })
      .then(res => res.json())
      .then(data => {
        if (btnSavePref) {
          btnSavePref.disabled = false;
          btnSavePref.textContent = 'Save Feed Preferences';
        }
        if (data.success) {
          showAlert(prefAlert, 'Feed preferences updated successfully!', true);
        } else {
          showAlert(prefAlert, data.message || 'Failed to update preferences.', false);
        }
      })
      .catch(err => {
        console.error('Preferences update error:', err);
        if (btnSavePref) {
          btnSavePref.disabled = false;
          btnSavePref.textContent = 'Save Feed Preferences';
        }
        showAlert(prefAlert, 'Network error updating preferences.', false);
      });
    });
  }
});

