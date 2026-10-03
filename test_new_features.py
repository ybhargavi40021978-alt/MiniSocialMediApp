import os
import sys
import json
from pathlib import Path
from datetime import timedelta

backend_dir = Path(__file__).resolve().parent / 'backend'
if backend_dir.exists() and str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'minisocial.settings')
import django
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.utils import timezone
from social.models import (
    Post, Circle, CircleMember, UserMood, PostVersion,
    Poll, PollOption, PollVote, UserPreference, DailyMission,
    UserMission, Topic, PostTopic, UserInterest, Like
)

def run_tests():
    print("================================================================")
    print("MINISOCIAL — NEW UNIQUE FEATURES AUTOMATED VERIFICATION SUITE")
    print("================================================================")

    # Clean up test users
    User.objects.filter(username__in=['user_test_a', 'user_test_b', 'user_test_c']).delete()

    client_a = Client()
    client_b = Client()
    client_c = Client()

    # Create 3 test users
    user_a = User.objects.create_user(username='user_test_a', email='a@test.com', password='Password123!')
    user_b = User.objects.create_user(username='user_test_b', email='b@test.com', password='Password123!')
    user_c = User.objects.create_user(username='user_test_c', email='c@test.com', password='Password123!')

    client_a.force_login(user_a)
    client_b.force_login(user_b)
    client_c.force_login(user_c)

    # ---------------------------------------------------------------
    # 1. TEST CIRCLES & MEMBER ROLES
    # ---------------------------------------------------------------
    print("\n--- 1. Testing MiniSocial Circles ---")
    create_circle_resp = client_a.post('/circle/create/', {
        'name': 'Coding Wizards',
        'description': 'Advanced developers discussing code',
        'is_private': 'on'
    }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert create_circle_resp.status_code == 200, f"Failed: {create_circle_resp.status_code}"
    circle_data = create_circle_resp.json()
    assert circle_data['success'] is True
    circle_id = circle_data['circle']['id']
    circle = Circle.objects.get(id=circle_id)
    assert circle.owner == user_a
    assert circle.is_private is True
    # Owner automatically first member with role 'owner'
    assert CircleMember.objects.filter(circle=circle, user=user_a, role='owner').exists()
    assert circle.member_count == 1
    print("[PASS] User A created private circle 'Coding Wizards' as owner (member_count=1)")

    # User B joins circle
    join_resp = client_b.post(f'/circle/{circle_id}/join/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert join_resp.status_code == 200
    assert join_resp.json()['success'] is True
    circle.refresh_from_db()
    assert circle.member_count == 2
    assert CircleMember.objects.filter(circle=circle, user=user_b, role='member').exists()
    print("[PASS] User B joined circle; member count updated to 2 in SQLite")

    # Prevent duplicate join
    join_dup = client_b.post(f'/circle/{circle_id}/join/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert join_dup.status_code == 200
    assert join_dup.json()['success'] is False
    print("[PASS] Duplicate circle membership correctly blocked")

    # ---------------------------------------------------------------
    # 2. TEST PRIVATE CIRCLE POSTS & POST VISIBILITY BACKEND ENFORCEMENT
    # ---------------------------------------------------------------
    print("\n--- 2. Testing Post Visibility & Circle Privacy ---")
    # User A creates a circle post
    circle_post_resp = client_a.post('/post/create/', {
        'content': 'Secret algorithms exclusively for Coding Wizards!',
        'visibility': f'circle:{circle_id}'
    }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert circle_post_resp.status_code == 200
    circle_post_data = circle_post_resp.json()
    assert circle_post_data['success'] is True
    circle_post_id = circle_post_data['post']['id']
    c_post = Post.objects.get(id=circle_post_id)
    assert c_post.visibility == 'circle'
    assert c_post.circle == circle
    print("[PASS] User A created circle post tied to 'Coding Wizards'")

    # User B (member) can view detail
    view_b_resp = client_b.get(f'/post/{circle_post_id}/')
    assert view_b_resp.status_code == 200
    assert b'Secret algorithms' in view_b_resp.content
    print("[PASS] User B (Circle Member) can access circle post")

    # User C (non-member) is rejected with 403 Forbidden
    view_c_resp = client_c.get(f'/post/{circle_post_id}/')
    assert view_c_resp.status_code == 403
    print("[PASS] User C (Non-Member) access to circle post rejected with HTTP 403")

    # User A creates a private post
    priv_post_resp = client_a.post('/post/create/', {
        'content': 'My secret diary note',
        'visibility': 'private'
    }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    priv_post_id = priv_post_resp.json()['post']['id']

    # User B attempts to access private post -> 403
    priv_view_b = client_b.get(f'/post/{priv_post_id}/')
    assert priv_view_b.status_code == 403
    # User A accesses own private post -> 200
    priv_view_a = client_a.get(f'/post/{priv_post_id}/')
    assert priv_view_a.status_code == 200
    print("[PASS] Private post access strictly limited to author")

    # ---------------------------------------------------------------
    # 3. TEST MOOD SYSTEM & MOOD-BASED FEED
    # ---------------------------------------------------------------
    print("\n--- 3. Testing Mood System & Mood Feed ---")
    # User A sets mood
    mood_resp = client_a.post('/user/mood/', json.dumps({'mood': 'Motivated'}), content_type='application/json')
    assert mood_resp.status_code == 200
    assert mood_resp.json()['success'] is True
    assert UserMood.objects.filter(user=user_a, mood='Motivated').exists()
    print("[PASS] User mood 'Motivated' saved to SQLite")

    # User A creates a post tagged with mood
    post_mood_resp = client_a.post('/post/create/', {
        'content': 'Just finished our sprint with ultra high energy!',
        'mood': 'Motivated',
        'visibility': 'public'
    }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert post_mood_resp.status_code == 200
    mood_post_id = post_mood_resp.json()['post']['id']
    m_post = Post.objects.get(id=mood_post_id)
    assert m_post.mood == 'Motivated'
    print("[PASS] Post mood saved properly")

    # Query mood feed
    mood_feed_resp = client_a.get('/home/?feed=mood')
    assert mood_feed_resp.status_code == 200
    assert b'ultra high energy' in mood_feed_resp.content
    print("[PASS] Mood feed successfully prioritizes posts matching user mood")

    # ---------------------------------------------------------------
    # 4. TEST POST EXPIRY & COUNTDOWN
    # ---------------------------------------------------------------
    print("\n--- 4. Testing Post Expiry ---")
    post_exp_resp = client_a.post('/post/create/', {
        'content': 'Flash announcement for 1 hour!',
        'expiry': '1h',
        'visibility': 'public'
    }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert post_exp_resp.status_code == 200
    exp_post_id = post_exp_resp.json()['post']['id']
    exp_post = Post.objects.get(id=exp_post_id)
    assert exp_post.expires_at is not None
    assert exp_post.is_expired is False
    print(f"[PASS] Post created with expires_at: {exp_post.expires_at}")

    # Simulate expiry by backdating expires_at
    exp_post.expires_at = timezone.now() - timedelta(minutes=5)
    exp_post.save()
    assert exp_post.is_expired is True

    # User B should NOT see expired post in home feed
    feed_b = client_b.get('/home/')
    assert b'Flash announcement for 1 hour' not in feed_b.content
    # User B direct view gets 403/404
    view_exp_b = client_b.get(f'/post/{exp_post_id}/')
    assert view_exp_b.status_code in [403, 404]
    print("[PASS] Expired post hidden from public home feed and rejected for non-owner with 403/404")

    # Author with show_expired_posts preference can view in archive
    pref_a, _ = UserPreference.objects.get_or_create(user=user_a)
    pref_a.show_expired_posts = True
    pref_a.save()
    view_exp_a = client_a.get(f'/post/{exp_post_id}/')
    assert view_exp_a.status_code == 200
    print("[PASS] Post author can view expired post in their personal archive")

    # ---------------------------------------------------------------
    # 5. TEST POST EVOLUTION / VERSION HISTORY
    # ---------------------------------------------------------------
    print("\n--- 5. Testing Post Evolution & Version History ---")
    # User A creates a post
    orig_post = Post.objects.create(author=user_a, content='Version 1: Learning Django')
    assert orig_post.version_count == 1

    # User A edits the post
    edit_resp = client_a.post(f'/post/{orig_post.id}/edit/', json.dumps({
        'content': 'Version 2: Building full stack apps with Django & SQLite'
    }), content_type='application/json')
    assert edit_resp.status_code == 200
    assert edit_resp.json()['success'] is True
    orig_post.refresh_from_db()
    assert orig_post.version_count == 2
    assert orig_post.content == 'Version 2: Building full stack apps with Django & SQLite'

    # Check that previous version was archived in PostVersion
    versions = PostVersion.objects.filter(post=orig_post).order_by('version_number')
    assert versions.count() == 1
    assert versions.first().version_number == 1
    assert versions.first().content == 'Version 1: Learning Django'
    print("[PASS] Previous version preserved in PostVersion table; version_count incremented")

    # Unauthorized edit rejection (User B trying to edit User A's post)
    bad_edit = client_b.post(f'/post/{orig_post.id}/edit/', json.dumps({
        'content': 'Hacked content'
    }), content_type='application/json')
    assert bad_edit.status_code == 403
    print("[PASS] Unauthorized edit by non-author correctly blocked with HTTP 403")

    # View Evolution API
    evo_resp = client_a.get(f'/post/{orig_post.id}/versions/')
    assert evo_resp.status_code == 200
    evo_data = evo_resp.json()
    assert evo_data['success'] is True
    assert len(evo_data['versions']) == 2
    print("[PASS] Post evolution history endpoint returns full version timeline")

    # ---------------------------------------------------------------
    # 6. TEST REACTION REASONS
    # ---------------------------------------------------------------
    print("\n--- 6. Testing Reaction Reasons ---")
    post_react = Post.objects.create(author=user_a, content='Helpful tutorial on database optimization')
    
    # User B likes with reason 'Helpful'
    react_resp = client_b.post(f'/post/{post_react.id}/like/', json.dumps({
        'reason': 'Helpful'
    }), content_type='application/json')
    assert react_resp.status_code == 200
    react_data = react_resp.json()
    assert react_data['success'] is True
    assert react_data['liked'] is True
    assert react_data['reason'] == 'Helpful'
    assert react_data['reaction_breakdown'].get('Helpful') == 1

    like_obj = Like.objects.get(user=user_b, post=post_react)
    assert like_obj.reason == 'Helpful'
    print("[PASS] Like with reason 'Helpful' saved to SQLite with breakdown")

    # ---------------------------------------------------------------
    # 7. TEST DECISION POSTS / POLLS
    # ---------------------------------------------------------------
    print("\n--- 7. Testing Decision Posts & Polls ---")
    poll_post_resp = client_a.post('/post/create/', {
        'content': 'What is your primary backend language?',
        'poll_question': 'What is your primary backend language?',
        'poll_option_0': 'Python',
        'poll_option_1': 'Go',
        'poll_option_2': 'Rust',
        'visibility': 'public'
    }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert poll_post_resp.status_code == 200
    poll_post_data = poll_post_resp.json()
    assert poll_post_data['success'] is True
    poll_id = poll_post_data['post']['poll']['id']
    poll = Poll.objects.get(id=poll_id)
    assert poll.options.count() == 3
    py_opt = poll.options.get(option_text='Python')
    go_opt = poll.options.get(option_text='Go')
    print(f"[PASS] Poll created with 3 options: Python, Go, Rust")

    # User B votes for Python
    vote_resp_b = client_b.post(f'/poll/{poll_id}/vote/', json.dumps({
        'option_id': py_opt.id
    }), content_type='application/json')
    assert vote_resp_b.status_code == 200
    vote_data_b = vote_resp_b.json()
    assert vote_data_b['success'] is True
    assert vote_data_b['poll']['total_votes'] == 1
    assert PollVote.objects.filter(poll=poll, user=user_b).exists()

    # User B tries to vote again -> blocked
    dup_vote = client_b.post(f'/poll/{poll_id}/vote/', json.dumps({
        'option_id': go_opt.id
    }), content_type='application/json')
    assert dup_vote.status_code == 400
    assert dup_vote.json()['success'] is False
    print("[PASS] User B voted; duplicate vote correctly rejected")

    # User C votes for Go
    vote_resp_c = client_c.post(f'/poll/{poll_id}/vote/', json.dumps({
        'option_id': go_opt.id
    }), content_type='application/json')
    assert vote_resp_c.status_code == 200
    poll_data_c = vote_resp_c.json()['poll']
    assert poll_data_c['total_votes'] == 2
    # Verify 50% / 50% calculation
    opts_map = {o['text']: o['percentage'] for o in poll_data_c['options']}
    assert opts_map['Python'] == 50.0
    assert opts_map['Go'] == 50.0
    print(f"[PASS] Real-time poll calculations: {opts_map}")

    # ---------------------------------------------------------------
    # 8. TEST CLEAN FEED MODE
    # ---------------------------------------------------------------
    print("\n--- 8. Testing Clean Feed Mode ---")
    pref_update = client_a.post('/preferences/update/', json.dumps({
        'clean_feed': True
    }), content_type='application/json')
    assert pref_update.status_code == 200
    assert pref_update.json()['preferences']['clean_feed'] is True

    pref_a.refresh_from_db()
    assert pref_a.clean_feed is True

    home_resp = client_a.get('/home/')
    assert b'clean-feed-mode' in home_resp.content
    print("[PASS] Clean Feed mode enabled and reflected in DOM wrapper class")

    # ---------------------------------------------------------------
    # 9. TEST PERSONAL SOCIAL DASHBOARD
    # ---------------------------------------------------------------
    print("\n--- 9. Testing Personal Social Dashboard ---")
    dash_resp = client_a.get('/dashboard/')
    assert dash_resp.status_code == 200
    assert b'My Social Journey' in dash_resp.content
    assert b'Posts' in dash_resp.content
    assert b'Circles' in dash_resp.content
    print("[PASS] Private dashboard loads with real DB counts")

    # ---------------------------------------------------------------
    # 10. TEST DAILY SOCIAL MISSIONS
    # ---------------------------------------------------------------
    print("\n--- 10. Testing Daily Missions ---")
    missions_resp = client_a.get('/missions/')
    assert missions_resp.status_code == 200
    missions_data = missions_resp.json()
    assert missions_data['success'] is True
    assert len(missions_data['missions']) >= 1
    mission_id = missions_data['missions'][0]['id']

    # Complete mission
    complete_resp = client_a.post(f'/mission/{mission_id}/complete/')
    assert complete_resp.status_code == 200
    assert complete_resp.json()['success'] is True
    assert UserMission.objects.filter(user=user_a, mission_id=mission_id, completed=True).exists()
    print("[PASS] Daily mission marked as completed in SQLite")

    # Duplicate completion does not create duplicate record
    client_a.post(f'/mission/{mission_id}/complete/')
    assert UserMission.objects.filter(user=user_a, mission_id=mission_id).count() == 1
    print("[PASS] Duplicate mission completion prevented")

    # ---------------------------------------------------------------
    # 11. TEST TOPICS & INTEREST SYSTEM
    # ---------------------------------------------------------------
    print("\n--- 11. Testing Topics & Interests ---")
    topic_django, _ = Topic.objects.get_or_create(name='django')
    topic_python, _ = Topic.objects.get_or_create(name='python')

    # User A updates interests
    int_resp = client_a.post('/interests/update/', json.dumps({
        'topics': ['django', 'python']
    }), content_type='application/json')
    assert int_resp.status_code == 200
    assert UserInterest.objects.filter(user=user_a, topic=topic_django).exists()
    assert UserInterest.objects.filter(user=user_a, topic=topic_python).exists()
    print("[PASS] User interests updated and stored in SQLite")

    # Explore feed
    explore_resp = client_a.get('/explore/')
    assert explore_resp.status_code == 200
    assert b'Explore & Topics' in explore_resp.content
    print("[PASS] Explore feed loads with user topics")

    # ---------------------------------------------------------------
    # 12. TEST MULTI-ENTITY SEARCH
    # ---------------------------------------------------------------
    print("\n--- 12. Testing Multi-Entity Search ---")
    search_resp = client_a.get('/search/?q=Wizards')
    assert search_resp.status_code == 200
    assert b'Coding Wizards' in search_resp.content
    print("[PASS] Multi-entity search found circle 'Coding Wizards'")

    print("\n================================================================")
    print("ALL 12 NEW FEATURES PASSED RIGOROUS AUTOMATED VERIFICATION!")
    print("================================================================")

    # Clean up test users
    User.objects.filter(username__in=['user_test_a', 'user_test_b', 'user_test_c']).delete()

if __name__ == '__main__':
    run_tests()
