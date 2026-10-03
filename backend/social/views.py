import json
import re
import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.db.models import Prefetch, Q, Count, Case, When, IntegerField
from django.utils import timezone

from .models import (
    Profile, Post, Comment, Like, Follow, Notification,
    Conversation, ConversationParticipant, Message,
    Circle, CircleMember, PostVersion, Poll, PollOption,
    PollVote, UserMood, UserPreference, DailyMission,
    UserMission, Topic, PostTopic, UserInterest
)
from .forms import RegistrationForm, PostForm, CommentForm


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_visible_posts_for_user(user, queryset=None, include_expired=False):
    """
    Returns posts visible to the given user based on privacy rules:
    - Public: visible to everyone
    - Followers: visible only to followers of the author or author themselves
    - Circle: visible only to members of that circle
    - Private: visible only to the author
    Filters out expired posts unless include_expired is True.
    """
    if queryset is None:
        queryset = Post.objects.all()

    now = timezone.now()
    if not include_expired:
        queryset = queryset.filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))

    if not user or not user.is_authenticated:
        return queryset.filter(visibility='public')

    following_ids = list(Follow.objects.filter(follower=user).values_list('following_id', flat=True))
    circle_ids = list(CircleMember.objects.filter(user=user).values_list('circle_id', flat=True))

    condition = (
        Q(author=user) |
        Q(visibility='public') |
        (Q(visibility='followers') & Q(author_id__in=following_ids)) |
        (Q(visibility='circle') & Q(circle_id__in=circle_ids))
    )
    return queryset.filter(condition).distinct()


def user_can_view_post(user, post):
    """
    Verifies if a specific user is authorized to view a specific post.
    Strict backend check.
    """
    if not post:
        return False
    if user and user.is_authenticated and post.author == user:
        return True
    if post.is_expired:
        return False
    if post.visibility == 'public':
        return True
    if not user or not user.is_authenticated:
        return False
    if post.visibility == 'followers':
        return Follow.objects.filter(follower=user, following=post.author).exists()
    if post.visibility == 'circle':
        if not post.circle_id:
            return False
        return CircleMember.objects.filter(circle_id=post.circle_id, user=user).exists()
    if post.visibility == 'private':
        return False
    return False


def get_or_create_daily_missions():
    """
    Returns daily missions for today. Creates initial system configuration
    daily missions if none exist for today.
    """
    today = timezone.now().date()
    existing = DailyMission.objects.filter(active_date=today)
    if existing.exists():
        return existing

    defaults = [
        ("Leave a helpful comment", "Share feedback or encouragement on another user's post.", "comment"),
        ("Discover someone new", "Find an interesting profile and start following them.", "discover"),
        ("Share something you learned today", "Write a post sharing an insight, tool, or achievement.", "post"),
        ("Support a useful post", "React to a post with a reason like Helpful or Inspiring.", "like"),
        ("Participate in a poll", "Cast your vote in a community decision post.", "poll"),
    ]
    for title, desc, m_type in defaults:
        DailyMission.objects.get_or_create(
            title=title,
            active_date=today,
            defaults={'description': desc, 'mission_type': m_type}
        )
    return DailyMission.objects.filter(active_date=today)


def check_and_complete_mission(user, mission_type):
    """
    Marks the user's mission of type mission_type completed for today if active.
    """
    if not user or not user.is_authenticated:
        return
    today = timezone.now().date()
    mission = DailyMission.objects.filter(active_date=today, mission_type=mission_type).first()
    if mission:
        UserMission.objects.get_or_create(user=user, mission=mission, defaults={'completed': True})


def serialize_post(post, user=None):
    """
    Serializes a post instance into dictionary for JSON responses.
    """
    now = timezone.now()
    expires_in_seconds = None
    if post.expires_at:
        diff = (post.expires_at - now).total_seconds()
        expires_in_seconds = max(0, int(diff))

    is_liked = False
    reaction_reason = None
    if user and user.is_authenticated:
        like = post.likes.filter(user=user).first()
        if like:
            is_liked = True
            reaction_reason = like.reason

    breakdown = {}
    for r in ['Helpful', 'Funny', 'Inspiring', 'Interesting', 'Supportive']:
        cnt = post.likes.filter(reason=r).count()
        if cnt > 0:
            breakdown[r] = cnt

    poll_data = None
    if hasattr(post, 'poll') and post.poll:
        p = post.poll
        poll_data = {
            'id': p.id,
            'question': p.question,
            'total_votes': p.total_votes,
            'has_voted': p.has_user_voted(user) if user and user.is_authenticated else False,
            'user_voted_option_id': p.user_voted_option_id(user) if user and user.is_authenticated else None,
            'options': [
                {
                    'id': opt.id,
                    'text': opt.option_text,
                    'votes': opt.vote_count,
                    'percentage': opt.vote_percentage()
                } for opt in p.options.all()
            ]
        }

    topics_list = [pt.topic.name for pt in post.post_topics.select_related('topic')]

    return {
        'id': post.id,
        'author': post.author.username,
        'author_avatar': post.author.profile.picture_url,
        'author_color': post.author.profile.avatar_color,
        'author_url': f'/user/{post.author.username}/',
        'detail_url': f'/post/{post.id}/',
        'content': post.content,
        'image_url': post.image.url if post.image else None,
        'created_at': 'Just now' if (now - post.created_at).total_seconds() < 60 else post.created_at.strftime('%b %d, %H:%M'),
        'visibility': post.visibility,
        'circle_id': post.circle_id,
        'circle_name': post.circle.name if post.circle else None,
        'mood': post.mood,
        'expires_at': post.expires_at.isoformat() if post.expires_at else None,
        'is_expired': post.is_expired,
        'expires_in_seconds': expires_in_seconds,
        'version_count': post.version_count,
        'like_count': post.likes.count(),
        'likes_count': post.likes.count(),
        'comment_count': post.comments.count(),
        'is_liked': is_liked,
        'user_reaction_reason': reaction_reason,
        'reaction_breakdown': breakdown,
        'poll': poll_data,
        'topics': topics_list,
        'is_author': (user == post.author) if user and user.is_authenticated else False,
    }


# ==============================================================================
# 1. AUTHENTICATION VIEWS
# ==============================================================================

def landing_view(request):
    return render(request, 'landing.html')



def register_view(request):
    error_message = None
    if request.method == 'POST':
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'message': 'Invalid JSON format'}, status=400)
            username = data.get('username', '').strip()
            email = data.get('email', '').strip()
            password = data.get('password', '')
            confirm_password = data.get('confirm_password', '')
        else:
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '')
            confirm_password = request.POST.get('confirm_password', '')

        # Validations
        if not username or not email or not password or not confirm_password:
            msg = 'All fields are required.'
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'success': False, 'message': msg})
            error_message = msg
        elif password != confirm_password:
            msg = 'Passwords do not match.'
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'success': False, 'message': msg})
            error_message = msg
        elif User.objects.filter(username__iexact=username).exists():
            msg = 'Username is already taken.'
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'success': False, 'message': msg})
            error_message = msg
        elif User.objects.filter(email__iexact=email).exists():
            msg = 'Email is already registered.'
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'success': False, 'message': msg})
            error_message = msg
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            Profile.objects.get_or_create(user=user)
            login(request, user)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'success': True, 'redirect_url': '/home/'})
            return redirect('home')

    return render(request, 'register.html', {'error_message': error_message})


def login_view(request):
    error_message = None
    if request.method == 'POST':
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'message': 'Invalid JSON format'}, status=400)
            username = data.get('username', '').strip()
            password = data.get('password', '')
        else:
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'success': True, 'redirect_url': '/home/'})
            return redirect('home')
        else:
            msg = 'Invalid username or password.'
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'success': False, 'message': msg})
            error_message = msg

    return render(request, 'login.html', {'error_message': error_message})


@login_required
def logout_view(request):
    logout(request)
    return redirect('landing')


# ==============================================================================
# 2. MAIN PAGES
# ==============================================================================

@login_required
def home_view(request):
    user = request.user
    pref, _ = UserPreference.objects.get_or_create(user=user)
    user_mood_obj = UserMood.objects.filter(user=user).first()
    current_mood = user_mood_obj.mood if user_mood_obj else None

    feed_mode = request.GET.get('feed', 'normal')

    base_posts = get_visible_posts_for_user(user, include_expired=pref.show_expired_posts).select_related(
        'author', 'author__profile', 'circle'
    ).prefetch_related(
        'likes', 'comments', 'post_topics__topic', 'poll__options__votes', 'poll__votes'
    )

    if feed_mode == 'mood' and current_mood:
        posts = base_posts.order_by(
            Case(
                When(mood=current_mood, then=0),
                default=1,
                output_field=IntegerField(),
            ),
            '-created_at'
        )
    else:
        posts = base_posts.order_by('-created_at')

    user_likes = {l.post_id: l.reason for l in user.likes.all()}

    post_list = []
    for p in posts:
        p.is_liked = p.id in user_likes
        p.user_reaction_reason = user_likes.get(p.id)
        if p.expires_at:
            p.expires_in_seconds = max(0, int((p.expires_at - timezone.now()).total_seconds()))
        else:
            p.expires_in_seconds = None

        p.reaction_breakdown = {}
        for r in ['Helpful', 'Funny', 'Inspiring', 'Interesting', 'Supportive']:
            cnt = p.likes.filter(reason=r).count()
            if cnt > 0:
                p.reaction_breakdown[r] = cnt

        post_list.append(p)

    user_circles = Circle.objects.filter(members__user=user).distinct()
    daily_missions = get_or_create_daily_missions()
    completed_mission_ids = set(user.completed_missions.filter(mission__in=daily_missions).values_list('mission_id', flat=True))
    missions_data = []
    for m in daily_missions:
        missions_data.append({
            'mission': m,
            'completed': m.id in completed_mission_ids
        })

    return render(request, 'home.html', {
        'posts': post_list,
        'current_user': user,
        'user_circles': user_circles,
        'current_mood': current_mood,
        'feed_mode': feed_mode,
        'daily_missions': missions_data,
        'user_preference': pref,
    })


@login_required
def profile_view(request):
    user = request.user
    pref, _ = UserPreference.objects.get_or_create(user=user)

    posts_qs = user.posts.select_related('author', 'author__profile', 'circle').prefetch_related(
        'likes', 'comments', 'post_topics__topic', 'poll__options__votes', 'poll__votes'
    )
    if not pref.show_expired_posts:
        posts_qs = posts_qs.filter(Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now()))

    posts = posts_qs.order_by('-created_at')
    user_likes = {l.post_id: l.reason for l in user.likes.all()}

    post_list = []
    for p in posts:
        p.is_liked = p.id in user_likes
        p.user_reaction_reason = user_likes.get(p.id)
        if p.expires_at:
            p.expires_in_seconds = max(0, int((p.expires_at - timezone.now()).total_seconds()))
        else:
            p.expires_in_seconds = None

        p.reaction_breakdown = {}
        for r in ['Helpful', 'Funny', 'Inspiring', 'Interesting', 'Supportive']:
            cnt = p.likes.filter(reason=r).count()
            if cnt > 0:
                p.reaction_breakdown[r] = cnt
        post_list.append(p)

    followers_count = Follow.objects.filter(following=user).count()
    following_count = Follow.objects.filter(follower=user).count()
    user_circles = Circle.objects.filter(members__user=user).distinct()

    return render(request, 'profile.html', {
        'profile_user': user,
        'posts': post_list,
        'followers_count': followers_count,
        'following_count': following_count,
        'posts_count': user.posts.count(),
        'user_circles': user_circles,
        'user_preference': pref,
    })


@login_required
def user_profile_view(request, username):
    if username == request.user.username:
        return redirect('profile')

    user = get_object_or_404(User.objects.select_related('profile'), username=username)

    # Use privacy rules: only show posts visible to request.user
    posts_qs = get_visible_posts_for_user(request.user, user.posts.all()).select_related(
        'author', 'author__profile', 'circle'
    ).prefetch_related(
        'likes', 'comments', 'post_topics__topic', 'poll__options__votes', 'poll__votes'
    ).order_by('-created_at')

    user_likes = {l.post_id: l.reason for l in request.user.likes.all()}
    post_list = []
    for p in posts_qs:
        p.is_liked = p.id in user_likes
        p.user_reaction_reason = user_likes.get(p.id)
        if p.expires_at:
            p.expires_in_seconds = max(0, int((p.expires_at - timezone.now()).total_seconds()))
        else:
            p.expires_in_seconds = None

        p.reaction_breakdown = {}
        for r in ['Helpful', 'Funny', 'Inspiring', 'Interesting', 'Supportive']:
            cnt = p.likes.filter(reason=r).count()
            if cnt > 0:
                p.reaction_breakdown[r] = cnt
        post_list.append(p)

    is_following = Follow.objects.filter(follower=request.user, following=user).exists()
    follows_you = Follow.objects.filter(follower=user, following=request.user).exists()

    followers_count = Follow.objects.filter(following=user).count()
    following_count = Follow.objects.filter(follower=user).count()

    return render(request, 'user_profile.html', {
        'profile_user': user,
        'posts': post_list,
        'followers_count': followers_count,
        'following_count': following_count,
        'posts_count': posts_qs.count(),
        'is_following': is_following,
        'follows_you': follows_you,
    })


@login_required
def post_detail_view(request, pk):
    post = get_object_or_404(
        Post.objects.select_related('author', 'author__profile', 'circle').prefetch_related(
            'likes', 'comments', 'post_topics__topic', 'poll__options__votes', 'poll__votes'
        ),
        pk=pk
    )
    if not user_can_view_post(request.user, post):
        return render(request, 'forbidden.html', {
            'message': 'You do not have permission to view this post. It may be private or restricted to circle members.'
        }, status=403)

    comments = post.comments.select_related('author', 'author__profile').all()
    user_like = post.likes.filter(user=request.user).first()
    is_liked = user_like is not None
    user_reaction = user_like.reason if user_like else None

    reaction_breakdown = {}
    for r in ['Helpful', 'Funny', 'Inspiring', 'Interesting', 'Supportive']:
        cnt = post.likes.filter(reason=r).count()
        if cnt > 0:
            reaction_breakdown[r] = cnt

    if post.expires_at:
        post.expires_in_seconds = max(0, int((post.expires_at - timezone.now()).total_seconds()))
    else:
        post.expires_in_seconds = None

    return render(request, 'post_details.html', {
        'post': post,
        'comments': comments,
        'is_liked': is_liked,
        'user_reaction': user_reaction,
        'reaction_breakdown': reaction_breakdown,
    })


@login_required
def notifications_view(request):
    notifications = request.user.notifications.select_related('sender', 'sender__profile', 'post').all()
    return render(request, 'notifications.html', {
        'notifications': notifications,
    })


@login_required
def followers_view(request):
    user = request.user
    followers_relations = Follow.objects.filter(following=user).select_related('follower', 'follower__profile')
    following_relations = Follow.objects.filter(follower=user).select_related('following', 'following__profile')

    following_user_ids = set(following_relations.values_list('following_id', flat=True))

    followers_list = []
    for rel in followers_relations:
        u = rel.follower
        followers_list.append({
            'user': u,
            'is_following': u.id in following_user_ids
        })

    following_list = []
    for rel in following_relations:
        u = rel.following
        following_list.append({
            'user': u,
            'is_following': True
        })

    return render(request, 'followers.html', {
        'followers_list': followers_list,
        'following_list': following_list,
        'followers_count': followers_relations.count(),
        'following_count': following_relations.count(),
        'active_tab': 'followers',
    })


@login_required
def following_view(request):
    user = request.user
    followers_relations = Follow.objects.filter(following=user).select_related('follower', 'follower__profile')
    following_relations = Follow.objects.filter(follower=user).select_related('following', 'following__profile')

    following_user_ids = set(following_relations.values_list('following_id', flat=True))

    followers_list = []
    for rel in followers_relations:
        u = rel.follower
        followers_list.append({
            'user': u,
            'is_following': u.id in following_user_ids
        })

    following_list = []
    for rel in following_relations:
        u = rel.following
        following_list.append({
            'user': u,
            'is_following': True
        })

    return render(request, 'following.html', {
        'followers_list': followers_list,
        'following_list': following_list,
        'followers_count': followers_relations.count(),
        'following_count': following_relations.count(),
        'active_tab': 'following',
    })


@login_required
def settings_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    pref, _ = UserPreference.objects.get_or_create(user=request.user)
    user_mood = UserMood.objects.filter(user=request.user).first()
    return render(request, 'settings.html', {
        'current_user': request.user,
        'profile': profile,
        'preference': pref,
        'user_mood': user_mood,
    })


# ==============================================================================
# 3. MESSAGES VIEWS
# ==============================================================================

@login_required
def messages_view(request):
    conversations = Conversation.objects.filter(
        participants__user=request.user
    ).prefetch_related(
        'participants__user__profile',
        'messages'
    ).order_by('-updated_at')

    conv_list = []
    for conv in conversations:
        other_user = conv.get_other_participant(request.user)
        last_msg = conv.latest_message
        unread_count = conv.unread_count_for(request.user)
        conv_list.append({
            'conversation': conv,
            'other_user': other_user,
            'last_message': last_msg,
            'unread_count': unread_count,
        })

    # Available users to start new chat with (users followed or followers)
    related_user_ids = set(Follow.objects.filter(
        Q(follower=request.user) | Q(following=request.user)
    ).values_list('follower_id', 'following_id'))
    flat_ids = {uid for pair in related_user_ids for uid in pair if uid != request.user.id}
    suggested_users = User.objects.filter(id__in=flat_ids).select_related('profile')[:10]

    return render(request, 'messages.html', {
        'conversations': conv_list,
        'active_conversation': None,
        'active_other_user': None,
        'chat_messages': [],
        'suggested_users': suggested_users,
    })


@login_required
def messages_conversation_view(request, conversation_id):
    conv = get_object_or_404(
        Conversation.objects.filter(participants__user=request.user),
        id=conversation_id
    )

    # Mark all incoming messages as read
    conv.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    other_user = conv.get_other_participant(request.user)
    chat_messages = conv.messages.select_related('sender', 'sender__profile').order_by('created_at')

    all_conversations = Conversation.objects.filter(
        participants__user=request.user
    ).prefetch_related(
        'participants__user__profile',
        'messages'
    ).order_by('-updated_at')

    conv_list = []
    for c in all_conversations:
        c_other = c.get_other_participant(request.user)
        c_last = c.latest_message
        c_unread = c.unread_count_for(request.user) if c.id != conv.id else 0
        conv_list.append({
            'conversation': c,
            'other_user': c_other,
            'last_message': c_last,
            'unread_count': c_unread,
        })

    return render(request, 'messages.html', {
        'conversations': conv_list,
        'active_conversation': conv,
        'active_other_user': other_user,
        'chat_messages': chat_messages,
    })


@login_required
def messages_user_view(request, username):
    target_user = get_object_or_404(User, username=username)
    if target_user == request.user:
        return redirect('messages')

    # Find existing conversation between request.user and target_user
    conv = Conversation.objects.filter(
        participants__user=request.user
    ).filter(
        participants__user=target_user
    ).first()

    if not conv:
        conv = Conversation.objects.create()
        ConversationParticipant.objects.create(conversation=conv, user=request.user)
        ConversationParticipant.objects.create(conversation=conv, user=target_user)

    return redirect('messages_conversation', conversation_id=conv.id)


@login_required
@require_POST
def send_message_view(request):
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON format'}, status=400)
        conversation_id = data.get('conversation_id')
        target_username = data.get('recipient_username') or data.get('recipient') or data.get('username')
        content = data.get('content', '').strip()
    else:
        conversation_id = request.POST.get('conversation_id')
        target_username = request.POST.get('recipient_username') or request.POST.get('recipient') or request.POST.get('username')
        content = request.POST.get('content', '').strip()

    if not content:
        return JsonResponse({'success': False, 'message': 'Message content cannot be empty.'}, status=400)

    conv = None
    if conversation_id:
        conv = get_object_or_404(Conversation, id=conversation_id, participants__user=request.user)
    elif target_username:
        target_user = get_object_or_404(User, username=target_username)
        if target_user == request.user:
            return JsonResponse({'success': False, 'message': 'You cannot message yourself.'}, status=400)
        conv = Conversation.objects.filter(
            participants__user=request.user
        ).filter(
            participants__user=target_user
        ).first()
        if not conv:
            conv = Conversation.objects.create()
            ConversationParticipant.objects.create(conversation=conv, user=request.user)
            ConversationParticipant.objects.create(conversation=conv, user=target_user)
    else:
        return JsonResponse({'success': False, 'message': 'Conversation or recipient required.'}, status=400)

    msg = Message.objects.create(
        conversation=conv,
        sender=request.user,
        content=content
    )
    conv.updated_at = timezone.now()
    conv.save()

    # Create notification for recipient
    other_user = conv.get_other_participant(request.user)
    if other_user:
        Notification.objects.create(
            recipient=other_user,
            sender=request.user,
            notification_type='message',
            message=msg
        )

    return JsonResponse({
        'success': True,
        'conversation_id': conv.id,
        'message': {
            'id': msg.id,
            'conversation_id': conv.id,
            'sender': request.user.username,
            'sender_avatar': request.user.profile.picture_url,
            'sender_color': request.user.profile.avatar_color,
            'content': msg.content,
            'created_at': msg.created_at.strftime('%I:%M %p').lstrip('0'),
            'is_me': True,
        }
    })


@login_required
def messages_updates_view(request, conversation_id):
    conv = get_object_or_404(Conversation, id=conversation_id, participants__user=request.user)
    after_id = request.GET.get('after', 0)
    try:
        after_id = int(after_id)
    except ValueError:
        after_id = 0

    new_messages = conv.messages.filter(
        id__gt=after_id
    ).select_related('sender', 'sender__profile').order_by('created_at')

    # Mark incoming newly fetched messages as read
    new_messages.exclude(sender=request.user).update(is_read=True)

    msgs_data = []
    for m in new_messages:
        msgs_data.append({
            'id': m.id,
            'conversation_id': conv.id,
            'sender': m.sender.username,
            'sender_avatar': m.sender.profile.picture_url,
            'sender_color': m.sender.profile.avatar_color,
            'content': m.content,
            'created_at': m.created_at.strftime('%I:%M %p').lstrip('0'),
            'is_me': m.sender == request.user,
        })

    unread_total = Message.objects.filter(
        conversation__participants__user=request.user,
        is_read=False
    ).exclude(sender=request.user).distinct().count()

    return JsonResponse({
        'success': True,
        'messages': msgs_data,
        'unread_count': unread_total
    })


@login_required
def messages_global_updates_view(request):
    unread_total = Message.objects.filter(
        conversation__participants__user=request.user,
        is_read=False
    ).exclude(sender=request.user).distinct().count()

    return JsonResponse({
        'success': True,
        'unread_count': unread_total
    })


# ==============================================================================
# 4. PROFILE EDITING & PHOTO UPLOAD
# ==============================================================================

@login_required
@require_POST
def profile_update_view(request):
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON format'}, status=400)
        bio = data.get('bio', '')
        avatar_color = data.get('avatar_color', '')
        username = data.get('username', '').strip()
    else:
        bio = request.POST.get('bio', '')
        avatar_color = request.POST.get('avatar_color', '')
        username = request.POST.get('username', '').strip()

    profile, _ = Profile.objects.get_or_create(user=request.user)

    if bio is not None:
        profile.bio = bio.strip()
    if avatar_color:
        profile.avatar_color = avatar_color

    profile.save()

    # Optional username update
    if username and username != request.user.username:
        if User.objects.filter(username__iexact=username).exclude(id=request.user.id).exists():
            return JsonResponse({'success': False, 'message': 'Username is already taken.'}, status=400)
        request.user.username = username
        request.user.save()

    return JsonResponse({
        'success': True,
        'message': 'Profile updated successfully.',
        'user': {
            'username': request.user.username,
            'bio': profile.bio,
            'avatar_color': profile.avatar_color,
            'image_url': profile.picture_url
        }
    })


@login_required
@require_POST
def profile_photo_upload_view(request):
    photo = request.FILES.get('profile_picture') or request.FILES.get('photo') or request.FILES.get('image')

    if not photo:
        return JsonResponse({'success': False, 'message': 'No image file provided.'}, status=400)

    # Validate image size (max 5MB)
    if photo.size > 5 * 1024 * 1024:
        return JsonResponse({'success': False, 'message': 'Image file is too large. Maximum size is 5MB.'}, status=400)

    # Validate content type
    allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
    if hasattr(photo, 'content_type') and photo.content_type not in allowed_types:
        return JsonResponse({'success': False, 'message': 'Invalid image format. Supported formats: JPG, PNG, WEBP, GIF.'}, status=400)

    profile, _ = Profile.objects.get_or_create(user=request.user)
    profile.profile_picture = photo
    profile.profile_image = photo
    profile.save()

    return JsonResponse({
        'success': True,
        'message': 'Profile picture updated successfully.',
        'image_url': profile.picture_url
    })


@login_required
@require_POST
def change_password_view(request):
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON format'}, status=400)
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
    else:
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

    if not current_password or not new_password or not confirm_password:
        return JsonResponse({'success': False, 'message': 'All password fields are required.'}, status=400)

    if not request.user.check_password(current_password):
        return JsonResponse({'success': False, 'message': 'Current password is incorrect.'}, status=400)

    if new_password != confirm_password:
        return JsonResponse({'success': False, 'message': 'New passwords do not match.'}, status=400)

    if len(new_password) < 4:
        return JsonResponse({'success': False, 'message': 'Password must be at least 4 characters long.'}, status=400)

    request.user.set_password(new_password)
    request.user.save()
    update_session_auth_hash(request, request.user)

    return JsonResponse({
        'success': True,
        'message': 'Password changed successfully.'
    })


# ==============================================================================
# 5. AJAX ACTION ENDPOINTS (POST, LIKE, COMMENT, FOLLOW)
# ==============================================================================

@login_required
@require_POST
def create_post_view(request):
    content = request.POST.get('content', '').strip()
    image = request.FILES.get('image')
    visibility = request.POST.get('visibility', 'public')
    circle_id = request.POST.get('circle_id') or request.POST.get('circle')
    if visibility and visibility.startswith('circle:'):
        circle_id = visibility.split(':')[1]
        visibility = 'circle'
    mood = request.POST.get('mood', '').strip() or None
    expiry = request.POST.get('expiry', 'permanent')
    post_type = request.POST.get('post_type', 'normal')
    poll_question = request.POST.get('poll_question', '').strip()
    poll_options_raw = request.POST.getlist('poll_options') or request.POST.get('poll_options', '')

    if not content and not image and not poll_question:
        return JsonResponse({'success': False, 'message': 'Please provide text content, an image, or a poll.'}, status=400)

    circle = None
    if visibility == 'circle' and circle_id:
        try:
            circle = Circle.objects.get(id=circle_id)
            if not circle.is_member(request.user):
                return JsonResponse({'success': False, 'message': 'You must be a member of this Circle to post in it.'}, status=403)
        except (Circle.DoesNotExist, ValueError):
            return JsonResponse({'success': False, 'message': 'Selected circle does not exist.'}, status=404)
    elif visibility not in ['public', 'followers', 'circle', 'private']:
        visibility = 'public'

    expires_at = None
    now = timezone.now()
    if expiry == '1h':
        expires_at = now + datetime.timedelta(hours=1)
    elif expiry == '6h':
        expires_at = now + datetime.timedelta(hours=6)
    elif expiry == '24h':
        expires_at = now + datetime.timedelta(hours=24)
    elif expiry == '3d':
        expires_at = now + datetime.timedelta(days=3)
    elif expiry == '7d':
        expires_at = now + datetime.timedelta(days=7)

    # Double-click / rapid submission duplicate prevention
    if content:
        recent_post = Post.objects.filter(author=request.user, content=content).order_by('-created_at').first()
        if recent_post and (now - recent_post.created_at < datetime.timedelta(seconds=2)):
            return JsonResponse({
                'success': True,
                'message': 'Post created successfully.',
                'post': serialize_post(recent_post, request.user)
            })

    post = Post.objects.create(
        author=request.user,
        content=content,
        image=image,
        visibility=visibility,
        circle=circle,
        mood=mood,
        expires_at=expires_at
    )

    # Topics handling: extract hashtags from content and from topics field
    topics_raw = request.POST.get('topics', '')
    found_topics = set(re.findall(r'#(\w+)', content))
    if topics_raw:
        for t in topics_raw.split(','):
            cleaned = t.strip().lstrip('#')
            if cleaned:
                found_topics.add(cleaned)

    for t_name in found_topics:
        topic_obj, _ = Topic.objects.get_or_create(name=t_name.lower())
        PostTopic.objects.get_or_create(post=post, topic=topic_obj)

    # Poll handling
    if poll_question or post_type == 'poll':
        options = []
        if isinstance(poll_options_raw, list) and poll_options_raw:
            options = [o.strip() for o in poll_options_raw if o.strip()]
        elif isinstance(poll_options_raw, str) and poll_options_raw:
            try:
                parsed = json.loads(poll_options_raw)
                if isinstance(parsed, list):
                    options = [str(o).strip() for o in parsed if str(o).strip()]
            except Exception:
                options = [o.strip() for o in poll_options_raw.split('\n') if o.strip()]

        if not options:
            for key in sorted(request.POST.keys()):
                if key.startswith('poll_option') and key != 'poll_options':
                    val = request.POST.get(key, '').strip()
                    if val:
                        options.append(val)

        if poll_question and len(options) >= 2:
            poll = Poll.objects.create(post=post, question=poll_question)
            for opt_text in options:
                PollOption.objects.create(poll=poll, option_text=opt_text)

    # Daily mission completion check
    check_and_complete_mission(request.user, 'post')

    return JsonResponse({
        'success': True,
        'message': 'Post created successfully.',
        'post': serialize_post(post, request.user)
    })


@login_required
@require_POST
def like_post_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if not user_can_view_post(request.user, post):
        return JsonResponse({'success': False, 'message': 'Permission denied.'}, status=403)

    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = {}
        reason = data.get('reason')
    else:
        reason = request.POST.get('reason')

    if reason:
        reason = reason.strip()

    like_obj = Like.objects.filter(user=request.user, post=post).first()

    if like_obj:
        if reason and like_obj.reason != reason:
            # Change reaction reason
            like_obj.reason = reason
            like_obj.save()
            liked = True
        else:
            # Toggle off
            like_obj.delete()
            liked = False
    else:
        like_obj = Like.objects.create(user=request.user, post=post, reason=reason)
        liked = True

        # Create notification if liking someone else's post
        if post.author != request.user:
            Notification.objects.get_or_create(
                recipient=post.author,
                sender=request.user,
                notification_type='like',
                post=post,
                is_read=False
            )
        # Daily mission check
        check_and_complete_mission(request.user, 'like')

    # Reaction breakdown
    breakdown = {}
    for r in ['Helpful', 'Funny', 'Inspiring', 'Interesting', 'Supportive']:
        cnt = post.likes.filter(reason=r).count()
        if cnt > 0:
            breakdown[r] = cnt

    count = post.likes.count()
    return JsonResponse({
        'success': True,
        'liked': liked,
        'like_count': count,
        'likes_count': count,
        'reason': like_obj.reason if liked and like_obj else None,
        'user_reaction_reason': like_obj.reason if liked and like_obj else None,
        'reaction_breakdown': breakdown,
    })


@login_required
@require_POST
def comment_post_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if not user_can_view_post(request.user, post):
        return JsonResponse({'success': False, 'message': 'Permission denied.'}, status=403)

    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON format'}, status=400)
        content = data.get('content', '').strip()
    else:
        content = request.POST.get('content', '').strip()

    if not content:
        return JsonResponse({'success': False, 'message': 'Comment cannot be empty.'}, status=400)

    # Duplicate prevention within 2 seconds
    recent_dup = Comment.objects.filter(
        post=post,
        author=request.user,
        content=content
    ).order_by('-created_at').first()

    if recent_dup and (timezone.now() - recent_dup.created_at < datetime.timedelta(seconds=2)):
        return JsonResponse({
            'success': True,
            'comment_count': post.comments.count(),
            'comment': {
                'id': recent_dup.id,
                'author': request.user.username,
                'author_url': f'/user/{request.user.username}/',
                'avatar_url': request.user.profile.picture_url,
                'avatar_color': request.user.profile.avatar_color,
                'content': recent_dup.content,
                'created_at': 'Just now',
            }
        })

    comment = Comment.objects.create(post=post, author=request.user, content=content)

    if post.author != request.user:
        Notification.objects.create(
            recipient=post.author,
            sender=request.user,
            notification_type='comment',
            post=post
        )

    # Daily mission check
    check_and_complete_mission(request.user, 'comment')

    return JsonResponse({
        'success': True,
        'comment_count': post.comments.count(),
        'comment': {
            'id': comment.id,
            'author': request.user.username,
            'author_url': f'/user/{request.user.username}/',
            'avatar_url': request.user.profile.picture_url,
            'avatar_color': request.user.profile.avatar_color,
            'content': comment.content,
            'created_at': 'Just now',
        }
    })


@login_required
@require_POST
def follow_user_view(request, username):
    target_user = get_object_or_404(User, username=username)

    if target_user == request.user:
        return JsonResponse({'success': False, 'message': 'You cannot follow yourself.'}, status=400)

    follow_obj = Follow.objects.filter(follower=request.user, following=target_user).first()

    if follow_obj:
        follow_obj.delete()
        following = False
    else:
        follow_obj, created = Follow.objects.get_or_create(follower=request.user, following=target_user)
        following = True

        # Notification for followed user
        Notification.objects.get_or_create(
            recipient=target_user,
            sender=request.user,
            notification_type='follow',
            is_read=False
        )
        # Daily mission check
        check_and_complete_mission(request.user, 'discover')

    count = target_user.followers_set.count()
    return JsonResponse({
        'success': True,
        'following': following,
        'follower_count': count,
        'followers_count': count,
    })


@login_required
@require_POST
def mark_notification_read_view(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.save()
    unread_count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({'success': True, 'unread_count': unread_count})


@login_required
@require_POST
def mark_all_notifications_read_view(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return JsonResponse({'success': True, 'unread_count': 0})


@login_required
@require_POST
def delete_notification_view(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.delete()
    unread_count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({'success': True, 'unread_count': unread_count})


# ==============================================================================
# 6. POLLING / REAL-TIME SYNCHRONIZATION ENDPOINTS
# ==============================================================================

@login_required
def notifications_updates_view(request):
    after_id = request.GET.get('after', 0)
    try:
        after_id = int(after_id)
    except ValueError:
        after_id = 0

    new_notifs = request.user.notifications.filter(
        id__gt=after_id
    ).select_related('sender', 'sender__profile', 'post', 'circle').order_by('-created_at')[:20]

    notif_data = []
    for n in new_notifs:
        notif_data.append({
            'id': n.id,
            'sender': n.sender.username,
            'sender_avatar': n.sender.profile.picture_url,
            'sender_color': n.sender.profile.avatar_color,
            'notification_type': n.notification_type,
            'text': n.display_text,
            'target_url': n.target_url,
            'post_id': n.post_id,
            'circle_id': n.circle_id,
            'is_read': n.is_read,
            'created_at': n.created_at.strftime('%Y-%m-%d %H:%M'),
        })

    unread_count = request.user.notifications.filter(is_read=False).count()

    return JsonResponse({
        'success': True,
        'notifications': notif_data,
        'unread_count': unread_count,
    })


@login_required
def feed_updates_view(request):
    after_id = request.GET.get('after', 0)
    try:
        after_id = int(after_id)
    except ValueError:
        after_id = 0

    mood_filter = request.GET.get('mood')

    visible = get_visible_posts_for_user(request.user)
    if mood_filter:
        visible = visible.filter(mood__iexact=mood_filter)

    new_posts = visible.filter(
        id__gt=after_id
    ).select_related(
        'author', 'author__profile', 'circle'
    ).prefetch_related(
        'likes', 'comments', 'poll__options__votes', 'post_topics__topic'
    ).order_by('-created_at')[:20]

    posts_data = [serialize_post(p, request.user) for p in new_posts]

    return JsonResponse({
        'success': True,
        'posts': posts_data,
    })


@login_required
def followers_updates_view(request):
    username = request.GET.get('user', request.user.username)
    target_user = get_object_or_404(User, username=username)

    followers_relations = Follow.objects.filter(following=target_user).select_related('follower', 'follower__profile')
    following_relations = Follow.objects.filter(follower=target_user).select_related('following', 'following__profile')

    my_following_ids = set(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))

    followers_list = []
    for rel in followers_relations:
        u = rel.follower
        followers_list.append({
            'id': u.id,
            'username': u.username,
            'avatar': u.profile.picture_url,
            'color': u.profile.avatar_color,
            'profile_url': f'/user/{u.username}/',
            'is_following': u.id in my_following_ids
        })

    return JsonResponse({
        'success': True,
        'followers_count': followers_relations.count(),
        'following_count': following_relations.count(),
        'is_following': Follow.objects.filter(follower=request.user, following=target_user).exists(),
        'followers': followers_list
    })


# ==============================================================================
# 7. CIRCLES VIEWS & API
# ==============================================================================

@login_required
def circles_view(request):
    user = request.user
    my_circles = Circle.objects.filter(members__user=user).select_related('owner').distinct()
    explore_circles = Circle.objects.filter(is_private=False).exclude(members__user=user).select_related('owner')[:20]

    return render(request, 'circles.html', {
        'my_circles': my_circles,
        'explore_circles': explore_circles,
    })


@login_required
@require_POST
def create_circle_view(request):
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON format'}, status=400)
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        is_private = data.get('is_private', True)
    else:
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        privacy_val = str(request.POST.get('privacy', 'private')).lower()
        is_private = privacy_val in ['private', 'true', '1']

    if not name:
        return JsonResponse({'success': False, 'message': 'Circle name is required.'}, status=400)

    circle = Circle.objects.create(
        name=name,
        description=description,
        owner=request.user,
        is_private=is_private
    )
    # The owner automatically becomes the first CircleMember
    CircleMember.objects.create(circle=circle, user=request.user, role='owner')

    return JsonResponse({
        'success': True,
        'message': 'Circle created successfully.',
        'circle': {
            'id': circle.id,
            'name': circle.name,
            'description': circle.description,
            'is_private': circle.is_private,
            'member_count': 1,
            'url': f'/circle/{circle.id}/',
        },
        'redirect_url': f'/circle/{circle.id}/'
    })


@login_required
def circle_detail_view(request, pk):
    circle = get_object_or_404(Circle.objects.select_related('owner'), pk=pk)
    is_member = circle.is_member(request.user)
    user_role = circle.get_user_role(request.user)
    is_owner = (circle.owner == request.user) or (user_role == 'owner')
    is_admin = is_owner or (user_role == 'admin')

    members = []
    posts = []

    if not circle.is_private or is_member:
        members = circle.members.select_related('user', 'user__profile').all()
        user_likes = {l.post_id: l.reason for l in request.user.likes.all()}
        circle_posts = circle.posts.filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        ).select_related('author', 'author__profile').prefetch_related('likes', 'comments', 'poll__options__votes')

        for p in circle_posts:
            p.is_liked = p.id in user_likes
            p.user_reaction_reason = user_likes.get(p.id)
            if p.expires_at:
                p.expires_in_seconds = max(0, int((p.expires_at - timezone.now()).total_seconds()))
            else:
                p.expires_in_seconds = None
            p.reaction_breakdown = {}
            for r in ['Helpful', 'Funny', 'Inspiring', 'Interesting', 'Supportive']:
                cnt = p.likes.filter(reason=r).count()
                if cnt > 0:
                    p.reaction_breakdown[r] = cnt
            posts.append(p)

    return render(request, 'circle_detail.html', {
        'circle': circle,
        'is_member': is_member,
        'user_role': user_role,
        'is_owner': is_owner,
        'is_admin': is_admin,
        'members': members,
        'posts': posts,
    })


@login_required
@require_POST
def join_circle_view(request, pk):
    circle = get_object_or_404(Circle, pk=pk)
    if CircleMember.objects.filter(circle=circle, user=request.user).exists():
        return JsonResponse({'success': False, 'message': 'Already a member.', 'member_count': circle.member_count})

    CircleMember.objects.create(circle=circle, user=request.user, role='member')

    # Notify owner
    if circle.owner != request.user:
        Notification.objects.create(
            recipient=circle.owner,
            sender=request.user,
            notification_type='circle',
            circle=circle,
            custom_text=f'joined your circle "{circle.name}"'
        )

    return JsonResponse({
        'success': True,
        'message': f'You joined {circle.name}.',
        'member_count': circle.member_count
    })


@login_required
@require_POST
def leave_circle_view(request, pk):
    circle = get_object_or_404(Circle, pk=pk)
    if circle.owner == request.user:
        return JsonResponse({'success': False, 'message': 'Circle owners cannot leave their own circle. You may manage or delete it.'}, status=400)

    membership = CircleMember.objects.filter(circle=circle, user=request.user).first()
    if membership:
        membership.delete()

    return JsonResponse({'success': True, 'message': f'You left {circle.name}.'})


@login_required
@require_POST
def manage_circle_members_view(request, pk):
    circle = get_object_or_404(Circle, pk=pk)
    user_role = circle.get_user_role(request.user)
    if user_role not in ['owner', 'admin']:
        return JsonResponse({'success': False, 'message': 'You must be an owner or admin to manage members.'}, status=403)

    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON format'}, status=400)
        action = data.get('action')
        target_username = data.get('username')
        new_role = data.get('role')
    else:
        action = request.POST.get('action')
        target_username = request.POST.get('username')
        new_role = request.POST.get('role')

    target_user = get_object_or_404(User, username=target_username)

    if action == 'add':
        if CircleMember.objects.filter(circle=circle, user=target_user).exists():
            return JsonResponse({'success': False, 'message': 'User is already a member.'}, status=400)
        CircleMember.objects.create(circle=circle, user=target_user, role='member')
        Notification.objects.create(
            recipient=target_user,
            sender=request.user,
            notification_type='circle',
            circle=circle,
            custom_text=f'added you to the circle "{circle.name}"'
        )
        return JsonResponse({'success': True, 'message': f'Added {target_user.username} to circle.'})

    elif action == 'remove':
        if target_user == circle.owner:
            return JsonResponse({'success': False, 'message': 'Cannot remove circle owner.'}, status=400)
        membership = CircleMember.objects.filter(circle=circle, user=target_user).first()
        if not membership:
            return JsonResponse({'success': False, 'message': 'User is not a member.'}, status=400)
        if membership.role == 'admin' and user_role != 'owner':
            return JsonResponse({'success': False, 'message': 'Only owner can remove admins.'}, status=403)
        membership.delete()
        Notification.objects.create(
            recipient=target_user,
            sender=request.user,
            notification_type='circle',
            circle=circle,
            custom_text=f'removed you from the circle "{circle.name}"'
        )
        return JsonResponse({'success': True, 'message': f'Removed {target_user.username} from circle.'})

    elif action == 'role':
        if user_role != 'owner':
            return JsonResponse({'success': False, 'message': 'Only circle owner can change member roles.'}, status=403)
        if target_user == circle.owner:
            return JsonResponse({'success': False, 'message': 'Cannot change owner role.'}, status=400)
        if new_role not in ['admin', 'member']:
            return JsonResponse({'success': False, 'message': 'Invalid role.'}, status=400)
        membership = CircleMember.objects.filter(circle=circle, user=target_user).first()
        if not membership:
            return JsonResponse({'success': False, 'message': 'User is not a member.'}, status=400)
        membership.role = new_role
        membership.save()
        Notification.objects.create(
            recipient=target_user,
            sender=request.user,
            notification_type='circle',
            circle=circle,
            custom_text=f'updated your role in "{circle.name}" to {new_role.capitalize()}'
        )
        return JsonResponse({'success': True, 'message': f'Updated {target_user.username} role to {new_role}.'})

    return JsonResponse({'success': False, 'message': 'Invalid action.'}, status=400)


@login_required
@require_POST
def circle_create_post_view(request, pk):
    circle = get_object_or_404(Circle, pk=pk)
    if not circle.is_member(request.user):
        return JsonResponse({'success': False, 'message': 'You must be a member of this Circle to post.'}, status=403)

    content = request.POST.get('content', '').strip()
    image = request.FILES.get('image')
    mood = request.POST.get('mood', '').strip() or None

    if not content and not image:
        return JsonResponse({'success': False, 'message': 'Content or image required.'}, status=400)

    post = Post.objects.create(
        author=request.user,
        content=content,
        image=image,
        visibility='circle',
        circle=circle,
        mood=mood
    )
    return JsonResponse({
        'success': True,
        'message': 'Circle post published.',
        'post': serialize_post(post, request.user)
    })


# ==============================================================================
# 8. DECISION POSTS / POLLS
# ==============================================================================

@login_required
@require_POST
def poll_vote_view(request, pk):
    poll = get_object_or_404(Poll, pk=pk)
    if not user_can_view_post(request.user, poll.post):
        return JsonResponse({'success': False, 'message': 'Permission denied.'}, status=403)

    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON format'}, status=400)
        option_id = data.get('option_id')
    else:
        option_id = request.POST.get('option_id')

    if not option_id:
        return JsonResponse({'success': False, 'message': 'Please select an option to vote.'}, status=400)

    option = get_object_or_404(PollOption, id=option_id, poll=poll)

    # Prevent duplicate vote
    if PollVote.objects.filter(poll=poll, user=request.user).exists():
        return JsonResponse({'success': False, 'message': 'You have already voted on this poll.'}, status=400)

    PollVote.objects.create(poll=poll, option=option, user=request.user)

    # Daily mission check
    check_and_complete_mission(request.user, 'poll')

    options_data = [
        {
            'id': opt.id,
            'text': opt.option_text,
            'votes': opt.vote_count,
            'percentage': opt.vote_percentage()
        } for opt in poll.options.all()
    ]

    return JsonResponse({
        'success': True,
        'message': 'Vote recorded successfully.',
        'poll_id': poll.id,
        'total_votes': poll.total_votes,
        'user_voted_option_id': option.id,
        'options': options_data,
        'poll': {
            'id': poll.id,
            'question': poll.question,
            'total_votes': poll.total_votes,
            'has_voted': True,
            'user_voted_option_id': option.id,
            'options': options_data
        }
    })


@login_required
def poll_updates_view(request, pk):
    poll = get_object_or_404(Poll, pk=pk)
    if not user_can_view_post(request.user, poll.post):
        return JsonResponse({'success': False, 'message': 'Permission denied.'}, status=403)

    options_data = [
        {
            'id': opt.id,
            'text': opt.option_text,
            'votes': opt.vote_count,
            'percentage': opt.vote_percentage()
        } for opt in poll.options.all()
    ]
    return JsonResponse({
        'success': True,
        'poll_id': poll.id,
        'total_votes': poll.total_votes,
        'has_voted': poll.has_user_voted(request.user),
        'user_voted_option_id': poll.user_voted_option_id(request.user),
        'options': options_data,
    })


# ==============================================================================
# 9. POST EVOLUTION / VERSION HISTORY
# ==============================================================================

@login_required
@require_POST
def post_edit_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user:
        return JsonResponse({'success': False, 'message': 'You can only edit your own posts.'}, status=403)

    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON format'}, status=400)
        new_content = data.get('content', '').strip()
    else:
        new_content = request.POST.get('content', '').strip()

    if not new_content:
        return JsonResponse({'success': False, 'message': 'Post content cannot be empty.'}, status=400)

    # Save previous version in PostVersion
    PostVersion.objects.create(
        post=post,
        version_number=post.version_count,
        content=post.content,
        image=post.image,
        edited_by=request.user
    )

    post.content = new_content
    post.version_count += 1
    post.save()

    return JsonResponse({
        'success': True,
        'message': 'Post updated successfully.',
        'post_id': post.id,
        'content': post.content,
        'version_count': post.version_count,
    })


@login_required
def post_versions_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if not user_can_view_post(request.user, post):
        return JsonResponse({'success': False, 'message': 'Permission denied.'}, status=403)

    versions = post.versions.select_related('edited_by').order_by('-version_number')
    data = []
    # Current version is latest
    data.append({
        'version_number': post.version_count,
        'content': post.content,
        'image_url': post.image.url if post.image else None,
        'edited_by': post.author.username,
        'created_at': post.updated_at.strftime('%Y-%m-%d %H:%M'),
        'is_current': True,
    })
    for v in versions:
        data.append({
            'version_number': v.version_number,
            'content': v.content,
            'image_url': v.image.url if v.image else None,
            'edited_by': v.edited_by.username if v.edited_by else post.author.username,
            'created_at': v.created_at.strftime('%Y-%m-%d %H:%M'),
            'is_current': False,
        })

    return JsonResponse({
        'success': True,
        'post_id': post.id,
        'versions': data,
    })


# ==============================================================================
# 10. PERSONAL SOCIAL DASHBOARD
# ==============================================================================

@login_required
def dashboard_view(request):
    user = request.user
    now = timezone.now()
    week_ago = now - datetime.timedelta(days=7)
    month_ago = now - datetime.timedelta(days=30)

    posts_count = user.posts.count()
    comments_count = Comment.objects.filter(author=user).count()
    likes_received = Like.objects.filter(post__author=user).count()
    likes_given = Like.objects.filter(user=user).count()
    followers_count = Follow.objects.filter(following=user).count()
    following_count = Follow.objects.filter(follower=user).count()
    circle_memberships = CircleMember.objects.filter(user=user).count()
    polls_created = Poll.objects.filter(post__author=user).count()
    polls_voted = PollVote.objects.filter(user=user).count()

    posts_this_week = user.posts.filter(created_at__gte=week_ago).count()
    posts_this_month = user.posts.filter(created_at__gte=month_ago).count()
    comments_this_week = Comment.objects.filter(author=user, created_at__gte=week_ago).count()
    new_followers_week = Follow.objects.filter(following=user, created_at__gte=week_ago).count()
    reactions_received_week = Like.objects.filter(post__author=user, created_at__gte=week_ago).count()

    daily_missions = get_or_create_daily_missions()
    completed_missions = UserMission.objects.filter(user=user, mission__in=daily_missions).count()

    return render(request, 'dashboard.html', {
        'current_user': user,
        'posts_count': posts_count,
        'comments_count': comments_count,
        'likes_received': likes_received,
        'likes_given': likes_given,
        'followers_count': followers_count,
        'following_count': following_count,
        'circle_memberships': circle_memberships,
        'polls_created': polls_created,
        'polls_voted': polls_voted,
        'posts_this_week': posts_this_week,
        'posts_this_month': posts_this_month,
        'comments_this_week': comments_this_week,
        'new_followers_week': new_followers_week,
        'reactions_received_week': reactions_received_week,
        'total_missions': daily_missions.count(),
        'completed_missions': completed_missions,
    })


# ==============================================================================
# 11. DAILY SOCIAL MISSIONS
# ==============================================================================

@login_required
def daily_missions_view(request):
    missions = get_or_create_daily_missions()
    completed_ids = set(request.user.completed_missions.filter(mission__in=missions).values_list('mission_id', flat=True))

    data = []
    for m in missions:
        data.append({
            'id': m.id,
            'title': m.title,
            'description': m.description,
            'mission_type': m.mission_type,
            'completed': m.id in completed_ids,
        })
    return JsonResponse({'success': True, 'missions': data})


@login_required
@require_POST
def complete_mission_view(request, pk):
    mission = get_object_or_404(DailyMission, pk=pk)
    UserMission.objects.get_or_create(user=request.user, mission=mission, defaults={'completed': True})
    return JsonResponse({'success': True, 'message': 'Mission completed!', 'mission_id': mission.id})


# ==============================================================================
# 12. INTEREST / TOPIC SYSTEM & EXPLORE
# ==============================================================================

@login_required
def explore_view(request):
    user = request.user
    selected_topic = request.GET.get('topic', '').strip().lstrip('#')

    all_topics = Topic.objects.annotate(posts_count=Count('topic_posts')).order_by('-posts_count')[:30]
    user_interest_ids = set(user.interests.values_list('topic_id', flat=True))

    visible_posts = get_visible_posts_for_user(user).select_related(
        'author', 'author__profile', 'circle'
    ).prefetch_related(
        'likes', 'comments', 'post_topics__topic', 'poll__options__votes'
    )

    if selected_topic:
        posts = visible_posts.filter(post_topics__topic__name__iexact=selected_topic).order_by('-created_at')
    elif user_interest_ids:
        posts = visible_posts.order_by(
            Case(
                When(post_topics__topic_id__in=user_interest_ids, then=0),
                default=1,
                output_field=IntegerField(),
            ),
            '-created_at'
        ).distinct()
    else:
        posts = visible_posts.order_by('-created_at')

    user_likes = {l.post_id: l.reason for l in user.likes.all()}
    post_list = []
    for p in posts[:30]:
        p.is_liked = p.id in user_likes
        p.user_reaction_reason = user_likes.get(p.id)
        if p.expires_at:
            p.expires_in_seconds = max(0, int((p.expires_at - timezone.now()).total_seconds()))
        else:
            p.expires_in_seconds = None
        p.reaction_breakdown = {}
        for r in ['Helpful', 'Funny', 'Inspiring', 'Interesting', 'Supportive']:
            cnt = p.likes.filter(reason=r).count()
            if cnt > 0:
                p.reaction_breakdown[r] = cnt
        post_list.append(p)

    return render(request, 'explore.html', {
        'topics': all_topics,
        'user_interest_ids': user_interest_ids,
        'selected_topic': selected_topic,
        'posts': post_list,
    })


@login_required
@require_POST
def update_interests_view(request):
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON format'}, status=400)
        topic_name = data.get('topic')
        topics_list = data.get('topics')
        action = data.get('action', 'toggle')
    else:
        topic_name = request.POST.get('topic')
        topics_list = request.POST.getlist('topics')
        action = request.POST.get('action', 'toggle')

    if topics_list and isinstance(topics_list, list):
        for t in topics_list:
            clean_name = str(t).strip().lstrip('#').lower()
            if clean_name:
                t_obj, _ = Topic.objects.get_or_create(name=clean_name)
                UserInterest.objects.get_or_create(user=request.user, topic=t_obj)
        return JsonResponse({'success': True, 'message': 'Interests updated successfully.'})

    if not topic_name:
        return JsonResponse({'success': False, 'message': 'Topic required.'}, status=400)

    clean_name = topic_name.strip().lstrip('#').lower()
    topic, _ = Topic.objects.get_or_create(name=clean_name)

    interest = UserInterest.objects.filter(user=request.user, topic=topic).first()
    if interest:
        if action in ['toggle', 'remove']:
            interest.delete()
            is_interested = False
        else:
            is_interested = True
    else:
        if action in ['toggle', 'add']:
            UserInterest.objects.create(user=request.user, topic=topic)
            is_interested = True
        else:
            is_interested = False

    user_interests = list(request.user.interests.values_list('topic__name', flat=True))
    return JsonResponse({
        'success': True,
        'is_interested': is_interested,
        'topic': clean_name,
        'user_interests': user_interests
    })


# ==============================================================================
# 13. USER MOOD & PREFERENCES (CLEAN FEED)
# ==============================================================================

@login_required
@require_POST
def update_mood_view(request):
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON format'}, status=400)
        mood = data.get('mood', '').strip()
    else:
        mood = request.POST.get('mood', '').strip()

    valid_moods = ['Happy', 'Motivated', 'Relaxed', 'Focused', 'Learning', 'Creative', 'Quiet']
    if mood not in valid_moods:
        return JsonResponse({'success': False, 'message': 'Invalid mood.'}, status=400)

    user_mood, _ = UserMood.objects.update_or_create(user=request.user, defaults={'mood': mood})

    return JsonResponse({'success': True, 'mood': user_mood.mood})


@login_required
@require_POST
def update_preferences_view(request):
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON format'}, status=400)
        clean_feed = data.get('clean_feed')
        show_expired_posts = data.get('show_expired_posts')
        preferred_mood = data.get('preferred_mood')
    else:
        clean_feed = request.POST.get('clean_feed')
        show_expired_posts = request.POST.get('show_expired_posts')
        preferred_mood = request.POST.get('preferred_mood')

    pref, _ = UserPreference.objects.get_or_create(user=request.user)

    if clean_feed is not None:
        if isinstance(clean_feed, str):
            pref.clean_feed = clean_feed.lower() in ['true', '1', 'on']
        else:
            pref.clean_feed = bool(clean_feed)

    if show_expired_posts is not None:
        if isinstance(show_expired_posts, str):
            pref.show_expired_posts = show_expired_posts.lower() in ['true', '1', 'on']
        else:
            pref.show_expired_posts = bool(show_expired_posts)

    if preferred_mood is not None:
        pref.preferred_mood = preferred_mood.strip() or None

    pref.save()
    return JsonResponse({
        'success': True,
        'message': 'Preferences updated.',
        'preferences': {
            'clean_feed': pref.clean_feed,
            'show_expired_posts': pref.show_expired_posts,
            'preferred_mood': pref.preferred_mood,
        }
    })


# ==============================================================================
# 14. SEARCH (USERS, POSTS, CIRCLES, TOPICS)
# ==============================================================================

@login_required
def search_view(request):
    q = request.GET.get('q', '').strip()
    if not q:
        users = []
        posts = []
        circles = []
        topics = []
    else:
        users = User.objects.filter(
            Q(username__icontains=q) | Q(first_name__icontains=q) | Q(profile__bio__icontains=q)
        ).select_related('profile')[:10]

        posts_qs = get_visible_posts_for_user(request.user).filter(content__icontains=q).select_related(
            'author', 'author__profile'
        )[:15]
        user_likes = {l.post_id: l.reason for l in request.user.likes.all()}
        posts = []
        for p in posts_qs:
            p.is_liked = p.id in user_likes
            posts.append(p)

        circles = Circle.objects.filter(
            Q(name__icontains=q) | Q(description__icontains=q)
        ).filter(
            Q(is_private=False) | Q(members__user=request.user)
        ).distinct()[:10]

        topics = Topic.objects.filter(name__icontains=q.lstrip('#'))[:10]

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({
            'success': True,
            'query': q,
            'users': [{'username': u.username, 'avatar': u.profile.picture_url, 'color': u.profile.avatar_color} for u in users],
            'circles': [{'id': c.id, 'name': c.name, 'member_count': c.member_count} for c in circles],
            'topics': [{'name': t.name} for t in topics],
            'posts_count': len(posts),
        })

    return render(request, 'search.html', {
        'query': q,
        'users': users,
        'posts': posts,
        'circles': circles,
        'topics': topics,
    })


# ==============================================================================
# 15. STANDALONE UI STATE DEMO SCREENS (PRESERVED)
# ==============================================================================

@login_required
def create_post_modal_demo_view(request):
    posts = Post.objects.select_related('author', 'author__profile').all()[:2]
    return render(request, 'create_post.html', {'posts': posts})


@login_required
def like_unlike_state_demo_view(request):
    return render(request, 'like_unlike.html')


@login_required
def follow_unfollow_state_demo_view(request):
    return render(request, 'follow_unfollow.html')

