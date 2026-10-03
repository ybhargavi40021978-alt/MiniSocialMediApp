import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent / 'backend'
if backend_dir.exists() and str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'minisocial.settings')
import django
django.setup()

from django.contrib.auth.models import User
from social.models import Profile, Post, Comment, Like, Follow, Notification
from django.utils import timezone
from datetime import timedelta


def run():
    print("Populating MiniSocial test database...")

    # Define test users
    users_data = [
        {'username': 'bhargavi', 'email': 'bhargavi@example.com', 'bio': 'Digital creator & developer. Sharing my journey! 💻✨', 'color': '#6366F1'},
        {'username': 'sai_kumar', 'email': 'sai_kumar@example.com', 'bio': 'Product Designer & Frontend enthusiast 🚀', 'color': '#1976F3'},
        {'username': 'priya', 'email': 'priya@example.com', 'bio': 'Design student, caffeine addict, and creative spirit 🌸', 'color': '#EC4899'},
        {'username': 'rahul', 'email': 'rahul@example.com', 'bio': 'Full stack explorer. Building things for the web ⚡', 'color': '#10B981'},
        {'username': 'ananya', 'email': 'ananya@example.com', 'bio': 'Bookworm, photographer, and sunset chaser 📚🌅', 'color': '#8B5CF6'},
        {'username': 'teja', 'email': 'teja@example.com', 'bio': 'Tech lover & sports fan 🏀💻', 'color': '#F59E0B'},
        {'username': 'vikas', 'email': 'vikas@example.com', 'bio': 'Software engineer & traveler ✈️', 'color': '#3B82F6'},
        {'username': 'neha', 'email': 'neha@example.com', 'bio': 'UI/UX dreamer and nature lover 🌿', 'color': '#06B6D4'},
    ]

    user_objs = {}
    for u_data in users_data:
        u, created = User.objects.get_or_create(
            username=u_data['username'],
            defaults={'email': u_data['email']}
        )
        if created:
            u.set_password('password123')
            u.save()
        profile, _ = Profile.objects.get_or_create(user=u)
        profile.bio = u_data['bio']
        profile.avatar_color = u_data['color']
        profile.save()
        user_objs[u.username] = u

    # Follow relationships for bhargavi:
    # People who follow bhargavi (25 represented in stats, sample 5 for active list):
    for follower_name in ['sai_kumar', 'priya', 'rahul', 'ananya', 'teja']:
        Follow.objects.get_or_create(
            follower=user_objs[follower_name],
            following=user_objs['bhargavi']
        )

    # People bhargavi follows:
    for following_name in ['sai_kumar', 'priya']:
        Follow.objects.get_or_create(
            follower=user_objs['bhargavi'],
            following=user_objs[following_name]
        )

    # Cross follows
    Follow.objects.get_or_create(follower=user_objs['sai_kumar'], following=user_objs['priya'])
    Follow.objects.get_or_create(follower=user_objs['priya'], following=user_objs['sai_kumar'])

    # Sample Posts
    now = timezone.now()
    posts_data = [
        {
            'author': 'bhargavi',
            'content': 'Just completed the full stack integration of MiniSocial! Powered by Django and clean Vanilla JS. 🚀',
            'minutes_ago': 20,
        },
        {
            'author': 'sai_kumar',
            'content': 'Design is not just what it looks like and feels like. Design is how it works. Starting the new sprint today!',
            'minutes_ago': 120,
        },
        {
            'author': 'priya',
            'content': 'Good vibes only! Working on some fresh mobile UI concepts. ✨📱',
            'minutes_ago': 240,
        },
        {
            'author': 'rahul',
            'content': 'Loving the speed of SQLite and Django ORM for rapid feature development.',
            'minutes_ago': 400,
        },
        {
            'author': 'ananya',
            'content': 'Golden hour in the mountains is unbeatable. Always take time to appreciate nature! 🌄',
            'minutes_ago': 600,
        },
    ]

    created_posts = []
    for p_data in posts_data:
        p, created = Post.objects.get_or_create(
            author=user_objs[p_data['author']],
            content=p_data['content'],
            defaults={'created_at': now - timedelta(minutes=p_data['minutes_ago'])}
        )
        if not created:
            p.created_at = now - timedelta(minutes=p_data['minutes_ago'])
            p.save()
        created_posts.append(p)

    # Comments
    comments_data = [
        {'post': created_posts[1], 'author': 'priya', 'content': 'Totally agree! Clean architecture makes all the difference.'},
        {'post': created_posts[1], 'author': 'bhargavi', 'content': 'Awesome work sai_kumar! Looking forward to testing it.'},
        {'post': created_posts[2], 'author': 'rahul', 'content': 'Love the aesthetic vibes here! 🔥'},
        {'post': created_posts[0], 'author': 'sai_kumar', 'content': 'Great job Bhargavi, everything looks super clean.'},
    ]

    for c in comments_data:
        Comment.objects.get_or_create(
            post=c['post'],
            author=user_objs[c['author']],
            content=c['content']
        )

    # Likes
    Like.objects.get_or_create(user=user_objs['bhargavi'], post=created_posts[1])
    Like.objects.get_or_create(user=user_objs['priya'], post=created_posts[1])
    Like.objects.get_or_create(user=user_objs['rahul'], post=created_posts[1])
    Like.objects.get_or_create(user=user_objs['sai_kumar'], post=created_posts[0])
    Like.objects.get_or_create(user=user_objs['bhargavi'], post=created_posts[2])

    # Sample Notifications for bhargavi
    Notification.objects.get_or_create(
        recipient=user_objs['bhargavi'],
        sender=user_objs['sai_kumar'],
        notification_type='follow',
        defaults={'is_read': False, 'created_at': now - timedelta(minutes=15)}
    )
    Notification.objects.get_or_create(
        recipient=user_objs['bhargavi'],
        sender=user_objs['priya'],
        notification_type='like',
        post=created_posts[0],
        defaults={'is_read': False, 'created_at': now - timedelta(minutes=30)}
    )
    Notification.objects.get_or_create(
        recipient=user_objs['bhargavi'],
        sender=user_objs['rahul'],
        notification_type='comment',
        post=created_posts[0],
        defaults={'is_read': False, 'created_at': now - timedelta(hours=2)}
    )

    print("Test data successfully populated!")
    print("Default test credentials for all users: username = <name>, password = password123")


if __name__ == '__main__':
    run()
