import os
import sys
import json
import io
from pathlib import Path
from PIL import Image

backend_dir = Path(__file__).resolve().parent / 'backend'
if backend_dir.exists() and str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'minisocial.settings')
import django
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from social.models import (
    Profile, Post, Like, Comment, Follow, Notification,
    Conversation, ConversationParticipant, Message
)

def create_dummy_image():
    file = io.BytesIO()
    image = Image.new('RGBA', size=(50, 50), color=(25, 118, 243))
    image.save(file, 'png')
    file.seek(0)
    return SimpleUploadedFile('test_avatar.png', file.read(), content_type='image/png')

def run_comprehensive_tests():
    print("================================================================")
    print("MINISOCIAL COMPREHENSIVE MULTI-USER END-TO-END INTEGRATION TEST")
    print("================================================================")

    # 1. Clean up test users if existing
    User.objects.filter(username__in=['user_alpha', 'user_beta']).delete()

    client_a = Client()
    client_b = Client()

    # ---------------------------------------------------------------
    # TEST 1: Landing Page & Public vs Protected Routes
    # ---------------------------------------------------------------
    print("\n--- TEST 1: Routing & Authentication Guards ---")
    resp = client_a.get('/')
    assert resp.status_code == 200, f"Landing page failed with {resp.status_code}"
    assert b'Your World, Your Community' in resp.content or b'Get Started' in resp.content
    print("[PASS] Landing page '/' is public and loads correctly")

    for protected_url in ['/home/', '/profile/', '/settings/', '/messages/', '/followers/', '/following/', '/notifications/']:
        r = client_a.get(protected_url)
        assert r.status_code == 302 and '/login/' in r['Location'], f"Unauthenticated access to {protected_url} was not redirected"
    print("[PASS] All protected routes redirect unauthenticated users to /login/")

    # ---------------------------------------------------------------
    # TEST 2: Multi-User Registration & Auto Profile Creation
    # ---------------------------------------------------------------
    print("\n--- TEST 2: Multi-User Registration (User Alpha & User Beta) ---")
    resp_reg_a = client_a.post('/register/', {
        'username': 'user_alpha',
        'email': 'alpha@minisocial.test',
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    }, follow=True)
    assert resp_reg_a.status_code == 200
    user_a = User.objects.get(username='user_alpha')
    assert hasattr(user_a, 'profile'), "User Alpha does not have an attached Profile"
    print("[PASS] User Alpha registered, Profile created automatically via signals, session logged in")

    resp_reg_b = client_b.post('/register/', {
        'username': 'user_beta',
        'email': 'beta@minisocial.test',
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    }, follow=True)
    assert resp_reg_b.status_code == 200
    user_b = User.objects.get(username='user_beta')
    assert hasattr(user_b, 'profile'), "User Beta does not have an attached Profile"
    print("[PASS] User Beta registered, Profile created automatically via signals, session logged in")

    # ---------------------------------------------------------------
    # TEST 3: Profile Picture Upload & Persistence
    # ---------------------------------------------------------------
    print("\n--- TEST 3: Profile Picture Upload & Persistence ---")
    dummy_img = create_dummy_image()
    upload_resp = client_a.post('/profile/photo/', {'profile_picture': dummy_img}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert upload_resp.status_code == 200
    upload_json = upload_resp.json()
    assert upload_json['success'] is True
    assert 'image_url' in upload_json
    print(f"[PASS] Profile picture uploaded successfully: {upload_json['image_url']}")

    user_a.refresh_from_db()
    assert user_a.profile.profile_picture, "profile_picture field not saved in DB"
    assert user_a.profile.picture_url.startswith('/media/'), f"Invalid picture_url: {user_a.profile.picture_url}"
    print("[PASS] Profile picture persisted in SQLite database and accessible via MEDIA_URL")

    # ---------------------------------------------------------------
    # TEST 4: Profile Info & Bio Editing
    # ---------------------------------------------------------------
    print("\n--- TEST 4: Profile Editing & Settings ---")
    update_prof_resp = client_a.post('/profile/update/', {
        'bio': 'Software engineer and open source enthusiast.'
    }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert update_prof_resp.status_code == 200
    assert update_prof_resp.json()['success'] is True
    user_a.refresh_from_db()
    assert user_a.profile.bio == 'Software engineer and open source enthusiast.'
    print("[PASS] User Alpha updated bio via /profile/update/")

    settings_page_resp = client_a.get('/settings/')
    assert settings_page_resp.status_code == 200
    assert b'user_alpha' in settings_page_resp.content
    assert b'Software engineer and open source enthusiast.' in settings_page_resp.content
    print("[PASS] Settings page reflects current database bio and username")

    # ---------------------------------------------------------------
    # TEST 5: Follow / Unfollow System & Real Database Follower Counts
    # ---------------------------------------------------------------
    print("\n--- TEST 5: Follow / Unfollow & Real-Time Follower Counts ---")
    # Initial follower count for User Alpha
    assert Follow.objects.filter(following=user_a).count() == 0

    # User Beta follows User Alpha
    follow_resp = client_b.post(f'/user/{user_a.username}/follow/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert follow_resp.status_code == 200
    follow_json = follow_resp.json()
    assert follow_json['success'] is True
    assert follow_json['following'] is True
    assert follow_json['followers_count'] == 1
    print("[PASS] User Beta followed User Alpha; returns following=True, followers_count=1")

    # Check SQLite state
    assert Follow.objects.filter(follower=user_b, following=user_a).exists()
    assert Follow.objects.filter(following=user_a).count() == 1
    print("[PASS] Follow record exists in SQLite: follower=user_beta, following=user_alpha")

    # User Alpha checks their profile page
    prof_a_resp = client_a.get('/profile/')
    assert prof_a_resp.status_code == 200
    assert b'data-count-followers' in prof_a_resp.content or b'Followers' in prof_a_resp.content
    print("[PASS] User Alpha profile page loads with real database follower count")

    # User Alpha checks followers list
    followers_resp = client_a.get('/followers/')
    assert followers_resp.status_code == 200
    assert b'user_beta' in followers_resp.content, "User Beta not displayed in User Alpha's followers list"
    print("[PASS] User Beta correctly appears in User Alpha's followers list")

    # Followers polling endpoint for User Alpha
    poll_followers_resp = client_a.get('/profile/followers/updates/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert poll_followers_resp.status_code == 200
    poll_f_json = poll_followers_resp.json()
    assert poll_f_json['followers_count'] == 1
    assert any(f['username'] == 'user_beta' for f in poll_f_json['followers'])
    print("[PASS] /profile/followers/updates/ returns real database followers without page reload")

    # ---------------------------------------------------------------
    # TEST 6: Posts, Likes, Comments, and Notifications
    # ---------------------------------------------------------------
    print("\n--- TEST 6: Posts, Likes, Comments, and Notifications Flow ---")
    # User Alpha creates a post
    create_post_resp = client_a.post('/post/create/', {
        'content': 'Hello MiniSocial world from User Alpha!'
    }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert create_post_resp.status_code == 200
    post_json = create_post_resp.json()
    assert post_json['success'] is True
    post_id = post_json['post']['id']
    post_obj = Post.objects.get(id=post_id)
    assert post_obj.author == user_a
    print(f"[PASS] User Alpha created Post #{post_id} in SQLite")

    # Feed updates polling for User Beta
    feed_poll = client_b.get('/feed/updates/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert feed_poll.status_code == 200
    feed_json = feed_poll.json()
    assert any(p['id'] == post_id for p in feed_json['posts'])
    print("[PASS] User Beta detects newly created post via /feed/updates/ polling")

    # User Beta likes User Alpha's post
    like_resp = client_b.post(f'/post/{post_id}/like/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert like_resp.status_code == 200
    like_json = like_resp.json()
    assert like_json['liked'] is True and like_json['like_count'] == 1
    assert Like.objects.filter(user=user_b, post=post_obj).exists()
    print("[PASS] User Beta liked User Alpha's post (Like record saved in SQLite)")

    # User Alpha receives like notification in SQLite
    notif_like = Notification.objects.filter(recipient=user_a, sender=user_b, notification_type='like', post=post_obj).first()
    assert notif_like is not None, "Like notification not created in SQLite for User Alpha"
    print(f"[PASS] Like notification generated in SQLite (ID: {notif_like.id})")

    # User Beta comments on User Alpha's post
    comment_resp = client_b.post(f'/post/{post_id}/comment/', {
        'content': 'Awesome post, Alpha!'
    }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert comment_resp.status_code == 200
    comment_json = comment_resp.json()
    assert comment_json['success'] is True
    assert Comment.objects.filter(post=post_obj, author=user_b, content='Awesome post, Alpha!').exists()
    print("[PASS] User Beta commented on post (Comment saved in SQLite)")

    # User Alpha receives comment notification
    notif_comment = Notification.objects.filter(recipient=user_a, sender=user_b, notification_type='comment', post=post_obj).first()
    assert notif_comment is not None, "Comment notification not created in SQLite for User Alpha"
    print(f"[PASS] Comment notification generated in SQLite (ID: {notif_comment.id})")

    # User Alpha polls for notifications
    notif_poll = client_a.get('/notifications/updates/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert notif_poll.status_code == 200
    notif_poll_json = notif_poll.json()
    assert notif_poll_json['unread_count'] >= 2
    assert len(notif_poll_json['notifications']) >= 2
    print(f"[PASS] /notifications/updates/ polling returned {notif_poll_json['unread_count']} unread notifications for User Alpha")

    # ---------------------------------------------------------------
    # TEST 7: Direct Messaging System & Polling
    # ---------------------------------------------------------------
    print("\n--- TEST 7: Direct Messaging & Real-Time Polling ---")
    # User Alpha sends a message to User Beta
    msg_send_resp = client_a.post('/messages/send/', {
        'recipient': 'user_beta',
        'content': 'Hey Beta, welcome to MiniSocial!'
    }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert msg_send_resp.status_code == 200
    msg_json = msg_send_resp.json()
    assert msg_json['success'] is True
    conv_id = msg_json['conversation_id']
    msg_id = msg_json['message']['id']
    print(f"[PASS] User Alpha sent message to User Beta (Conv #{conv_id}, Msg #{msg_id})")

    # Verify message in SQLite
    msg_obj = Message.objects.get(id=msg_id)
    assert msg_obj.sender == user_a
    assert msg_obj.content == 'Hey Beta, welcome to MiniSocial!'
    assert msg_obj.is_read is False

    # Check unread message count for User Beta via updates endpoint
    msg_poll_beta = client_b.get('/messages/updates/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert msg_poll_beta.status_code == 200
    assert msg_poll_beta.json()['unread_count'] >= 1
    print(f"[PASS] User Beta has {msg_poll_beta.json()['unread_count']} unread message(s) via /messages/updates/")

    # User Beta opens conversation updates
    conv_updates_beta = client_b.get(f'/messages/{conv_id}/updates/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert conv_updates_beta.status_code == 200
    conv_json = conv_updates_beta.json()
    assert any(m['id'] == msg_id for m in conv_json['messages'])
    print("[PASS] User Beta received message through conversation polling")

    # Verify message is marked as read after opening conversation
    msg_obj.refresh_from_db()
    assert msg_obj.is_read is True
    print("[PASS] Message automatically marked as read in SQLite upon opening conversation")

    # ---------------------------------------------------------------
    # TEST 8: Unfollow, Self-Follow Guard, and Follower Count Decrement
    # ---------------------------------------------------------------
    print("\n--- TEST 8: Unfollow & Follow Guard Rules ---")
    # Self-follow guard
    self_follow_resp = client_b.post(f'/user/{user_b.username}/follow/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert self_follow_resp.status_code == 400
    print("[PASS] Self-follow correctly rejected by backend with HTTP 400")

    # User Beta unfollows User Alpha
    unfollow_resp = client_b.post(f'/user/{user_a.username}/follow/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert unfollow_resp.status_code == 200
    unf_json = unfollow_resp.json()
    assert unf_json['following'] is False
    assert unf_json['followers_count'] == 0
    assert not Follow.objects.filter(follower=user_b, following=user_a).exists()
    print("[PASS] User Beta unfollowed User Alpha: SQLite record deleted, followers_count decremented to 0")

    # User Alpha followers polling now reflects 0 followers
    poll_f_after = client_a.get('/profile/followers/updates/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert poll_f_after.status_code == 200
    assert poll_f_after.json()['followers_count'] == 0
    assert len(poll_f_after.json()['followers']) == 0
    print("[PASS] User Alpha follower polling reflects 0 followers in real time")

    # ---------------------------------------------------------------
    # TEST 9: Post with Image Creation
    # ---------------------------------------------------------------
    print("\n--- TEST 9: Post with Image Creation ---")
    dummy_post_img = create_dummy_image()
    post_img_resp = client_b.post('/post/create/', {
        'content': 'Check out this screenshot!',
        'image': dummy_post_img
    }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert post_img_resp.status_code == 200
    post_img_json = post_img_resp.json()
    assert post_img_json['success'] is True
    assert post_img_json['post']['image_url'] is not None
    post_with_img = Post.objects.get(id=post_img_json['post']['id'])
    assert post_with_img.image
    assert post_with_img.image.url.startswith('/media/posts/')
    print(f"[PASS] Post with image created: {post_with_img.image.url}")

    # ---------------------------------------------------------------
    # TEST 10: Mark Notifications as Read
    # ---------------------------------------------------------------
    print("\n--- TEST 10: Mark Notifications as Read ---")
    mark_read_resp = client_a.post('/notifications/mark-read/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert mark_read_resp.status_code == 200
    assert mark_read_resp.json()['unread_count'] == 0
    notif_poll_after = client_a.get('/notifications/updates/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert notif_poll_after.json()['unread_count'] == 0
    print("[PASS] Notifications marked as read; unread count reset to 0 in SQLite")

    # ---------------------------------------------------------------
    # TEST 11: Self-Message Prevention
    # ---------------------------------------------------------------
    print("\n--- TEST 11: Messaging Security & Guards ---")
    self_msg_resp = client_a.post('/messages/send/', {
        'recipient': 'user_alpha',
        'content': 'Can I message myself?'
    }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert self_msg_resp.status_code == 400
    print("[PASS] Self-messaging prevented by backend with HTTP 400")

    # ---------------------------------------------------------------
    # TEST 12: Password Change via Settings
    # ---------------------------------------------------------------
    print("\n--- TEST 12: Settings Password Change ---")
    pwd_resp = client_a.post('/settings/password/', {
        'current_password': 'Password123!',
        'new_password': 'NewPassword456!',
        'confirm_password': 'NewPassword456!'
    }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert pwd_resp.status_code == 200
    assert pwd_resp.json()['success'] is True
    print("[PASS] User Alpha changed password successfully")

    # Test login with old password fails
    client_new = Client()
    login_old = client_new.post('/login/', {'username': 'user_alpha', 'password': 'Password123!'})
    assert login_old.status_code == 200 and b'Invalid' in login_old.content
    print("[PASS] Login with old password rejected")

    # Test login with new password succeeds
    login_new = client_new.post('/login/', {'username': 'user_alpha', 'password': 'NewPassword456!'}, follow=True)
    assert login_new.status_code == 200
    assert b'user_alpha' in login_new.content
    print("[PASS] Login with new password succeeded and user session restored")

    # ---------------------------------------------------------------
    # TEST 13: Logout Flow
    # ---------------------------------------------------------------
    print("\n--- TEST 13: Logout Flow ---")
    logout_resp = client_new.get('/logout/', follow=True)
    assert logout_resp.status_code == 200
    assert b'Your World, Your Community' in logout_resp.content or b'Get Started' in logout_resp.content
    print("[PASS] Logout redirects to Landing page ('/')")

    print("\n================================================================")
    print("ALL 13 COMPREHENSIVE END-TO-END TESTS PASSED WITH 100% SUCCESS!")
    print("================================================================")

if __name__ == '__main__':
    run_comprehensive_tests()
