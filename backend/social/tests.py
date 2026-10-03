import io
from PIL import Image
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from social.models import (
    Profile, Post, Like, Comment, Follow, Notification,
    Conversation, ConversationParticipant, Message
)

def create_test_image(name='avatar.png'):
    file = io.BytesIO()
    img = Image.new('RGB', (40, 40), color=(25, 118, 243))
    img.save(file, 'PNG')
    file.seek(0)
    return SimpleUploadedFile(name, file.read(), content_type='image/png')

class MiniSocialIntegrationTests(TestCase):
    def setUp(self):
        self.client_a = Client()
        self.client_b = Client()

        self.user_a = User.objects.create_user(username='alice', email='alice@example.com', password='Password123!')
        self.user_b = User.objects.create_user(username='bob', email='bob@example.com', password='Password123!')

    def test_profile_auto_creation_signal(self):
        """User registration automatically creates a Profile."""
        self.assertTrue(hasattr(self.user_a, 'profile'))
        self.assertTrue(hasattr(self.user_b, 'profile'))
        self.assertEqual(self.user_a.profile.user, self.user_a)

    def test_landing_page_public(self):
        """Root URL loads the public landing page."""
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)

    def test_protected_routes_redirect_to_login(self):
        """Unauthenticated requests to protected endpoints redirect to login."""
        for path in ['/home/', '/profile/', '/settings/', '/messages/', '/followers/', '/notifications/']:
            resp = self.client.get(path)
            self.assertEqual(resp.status_code, 302)
            self.assertIn('/login/', resp['Location'])

    def test_follow_and_real_time_follower_count(self):
        """Bob follows Alice -> Alice follower count is 1 in DB, Bob in follower list."""
        self.client_b.force_login(self.user_b)
        self.client_a.force_login(self.user_a)

        # Follow action
        resp = self.client_b.post(f'/user/{self.user_a.username}/follow/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['following'])
        self.assertEqual(data['followers_count'], 1)

        # SQLite relationship check
        self.assertTrue(Follow.objects.filter(follower=self.user_b, following=self.user_a).exists())
        self.assertEqual(Follow.objects.filter(following=self.user_a).count(), 1)

        # Follower updates endpoint for Alice
        f_poll = self.client_a.get('/profile/followers/updates/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(f_poll.status_code, 200)
        f_data = f_poll.json()
        self.assertEqual(f_data['followers_count'], 1)
        self.assertTrue(any(f['username'] == 'bob' for f in f_data['followers']))

        # Bob unfollows Alice
        unf_resp = self.client_b.post(f'/user/{self.user_a.username}/follow/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(unf_resp.status_code, 200)
        self.assertFalse(unf_resp.json()['following'])
        self.assertEqual(unf_resp.json()['followers_count'], 0)
        self.assertFalse(Follow.objects.filter(follower=self.user_b, following=self.user_a).exists())

    def test_self_follow_rejected(self):
        """User cannot follow themselves."""
        self.client_a.force_login(self.user_a)
        resp = self.client_a.post(f'/user/{self.user_a.username}/follow/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 400)

    def test_profile_photo_upload_and_persistence(self):
        """User uploads a real profile picture and it saves to media/."""
        self.client_a.force_login(self.user_a)
        img = create_test_image('alice_avatar.png')
        resp = self.client_a.post('/profile/photo/', {'profile_picture': img}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['success'])

        self.user_a.refresh_from_db()
        self.assertTrue(bool(self.user_a.profile.profile_picture))
        self.assertTrue(self.user_a.profile.picture_url.startswith('/media/profile_pictures/'))

    def test_post_creation_like_comment_and_notification(self):
        """Alice creates post, Bob likes and comments -> Notifications generated in SQLite."""
        self.client_a.force_login(self.user_a)
        self.client_b.force_login(self.user_b)

        # Alice creates post
        post_resp = self.client_a.post('/post/create/', {'content': 'Integration test post'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(post_resp.status_code, 200)
        post_id = post_resp.json()['post']['id']
        post = Post.objects.get(id=post_id)

        # Bob likes Alice's post
        like_resp = self.client_b.post(f'/post/{post_id}/like/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(like_resp.status_code, 200)
        self.assertTrue(like_resp.json()['liked'])
        self.assertEqual(like_resp.json()['like_count'], 1)
        self.assertTrue(Like.objects.filter(user=self.user_b, post=post).exists())

        # Notification for like exists in SQLite
        like_notif = Notification.objects.filter(recipient=self.user_a, sender=self.user_b, notification_type='like', post=post)
        self.assertTrue(like_notif.exists())

        # Bob comments on Alice's post
        comment_resp = self.client_b.post(f'/post/{post_id}/comment/', {'content': 'Nice post!'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(comment_resp.status_code, 200)
        self.assertEqual(comment_resp.json()['comment_count'], 1)
        self.assertTrue(Comment.objects.filter(author=self.user_b, post=post, content='Nice post!').exists())

        # Notification for comment exists in SQLite
        comment_notif = Notification.objects.filter(recipient=self.user_a, sender=self.user_b, notification_type='comment', post=post)
        self.assertTrue(comment_notif.exists())

        # Alice checks notification updates
        notif_poll = self.client_a.get('/notifications/updates/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(notif_poll.status_code, 200)
        self.assertGreaterEqual(notif_poll.json()['unread_count'], 2)

    def test_direct_messaging_and_polling(self):
        """Alice messages Bob -> Message in SQLite -> Bob polls updates -> Marked read."""
        self.client_a.force_login(self.user_a)
        self.client_b.force_login(self.user_b)

        send_resp = self.client_a.post('/messages/send/', {
            'recipient': 'bob',
            'content': 'Hello Bob!'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(send_resp.status_code, 200)
        data = send_resp.json()
        self.assertTrue(data['success'])
        conv_id = data['conversation_id']
        msg_id = data['message']['id']

        msg = Message.objects.get(id=msg_id)
        self.assertEqual(msg.sender, self.user_a)
        self.assertEqual(msg.content, 'Hello Bob!')
        self.assertFalse(msg.is_read)

        # Bob polls conversation updates
        updates_resp = self.client_b.get(f'/messages/{conv_id}/updates/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(updates_resp.status_code, 200)
        self.assertTrue(any(m['id'] == msg_id for m in updates_resp.json()['messages']))

        # Message is now marked as read
        msg.refresh_from_db()
        self.assertTrue(msg.is_read)

    def test_settings_bio_update_and_password_change(self):
        """Alice updates bio and changes password via settings."""
        self.client_a.force_login(self.user_a)

        # Bio update
        bio_resp = self.client_a.post('/profile/update/', {'bio': 'Updated bio via settings'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(bio_resp.status_code, 200)
        self.user_a.refresh_from_db()
        self.assertEqual(self.user_a.profile.bio, 'Updated bio via settings')

        # Password change
        pwd_resp = self.client_a.post('/settings/password/', {
            'current_password': 'Password123!',
            'new_password': 'BrandNewPassword789!',
            'confirm_password': 'BrandNewPassword789!'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(pwd_resp.status_code, 200)
        self.assertTrue(pwd_resp.json()['success'])

        # Old password fails
        self.assertFalse(self.client.login(username='alice', password='Password123!'))
        # New password succeeds
        self.assertTrue(self.client.login(username='alice', password='BrandNewPassword789!'))
