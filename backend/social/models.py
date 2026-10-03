from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    avatar_color = models.CharField(max_length=20, default='#1976F3')
    bio = models.TextField(blank=True, default='')
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def picture_url(self):
        if self.profile_picture:
            return self.profile_picture.url
        if self.profile_image:
            return self.profile_image.url
        return None

    @property
    def followers_count(self):
        return self.user.followers_set.count()

    @property
    def following_count(self):
        return self.user.following_set.count()

    @property
    def posts_count(self):
        return self.user.posts.count()


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)
        UserPreference.objects.get_or_create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()


class Circle(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_circles')
    is_private = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        return self.members.count()

    def is_member(self, user):
        if not user or not user.is_authenticated:
            return False
        return self.members.filter(user=user).exists()

    def get_user_role(self, user):
        if not user or not user.is_authenticated:
            return None
        membership = self.members.filter(user=user).first()
        return membership.role if membership else None


class CircleMember(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
    ]

    circle = models.ForeignKey(Circle, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='circle_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['circle', 'user'], name='unique_circle_user')
        ]
        ordering = ['joined_at']

    def __str__(self):
        return f"{self.user.username} in {self.circle.name} ({self.role})"


class Post(models.Model):
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('followers', 'Followers'),
        ('circle', 'Circle'),
        ('private', 'Private'),
    ]

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(blank=True, default='')
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public')
    circle = models.ForeignKey(Circle, on_delete=models.CASCADE, null=True, blank=True, related_name='posts')
    mood = models.CharField(max_length=50, blank=True, null=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    version_count = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Post by {self.author.username} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    @property
    def like_count(self):
        return self.likes.count()

    @property
    def comment_count(self):
        return self.comments.count()

    @property
    def is_expired(self):
        if self.expires_at and timezone.now() >= self.expires_at:
            return True
        return False

    def is_liked_by(self, user):
        if not user or not user.is_authenticated:
            return False
        return self.likes.filter(user=user).exists()

    def get_user_reaction_reason(self, user):
        if not user or not user.is_authenticated:
            return None
        like = self.likes.filter(user=user).first()
        return like.reason if like else None


class PostVersion(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField()
    content = models.TextField(blank=True, default='')
    image = models.ImageField(upload_to='posts/versions/', blank=True, null=True)
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-version_number']
        constraints = [
            models.UniqueConstraint(fields=['post', 'version_number'], name='unique_post_version')
        ]

    def __str__(self):
        return f"Post #{self.post.id} v{self.version_number}"


class Poll(models.Model):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='poll')
    question = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question

    @property
    def total_votes(self):
        return self.votes.count()

    def has_user_voted(self, user):
        if not user or not user.is_authenticated:
            return False
        return self.votes.filter(user=user).exists()

    def user_voted_option_id(self, user):
        if not user or not user.is_authenticated:
            return None
        vote = self.votes.filter(user=user).first()
        return vote.option_id if vote else None


class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.option_text} for Poll #{self.poll.id}"

    @property
    def vote_count(self):
        return self.votes.count()

    def vote_percentage(self):
        total = self.poll.total_votes
        if total == 0:
            return 0
        return round((self.vote_count / total) * 100)


class PollVote(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='votes')
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='poll_votes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['poll', 'user'], name='unique_poll_user_vote')
        ]

    def __str__(self):
        return f"{self.user.username} voted on Poll #{self.poll.id}"


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on Post #{self.post.id}"


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    reason = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'post'], name='unique_user_post_like')
        ]

    def __str__(self):
        return f"{self.user.username} liked Post #{self.post.id}"


class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following_set')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers_set')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['follower', 'following'], name='unique_follower_following'),
            models.CheckConstraint(
                condition=~models.Q(follower=models.F('following')),
                name='prevent_self_follow'
            )
        ]

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class Conversation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversation #{self.id}"

    def get_other_participant(self, user):
        participant = self.participants.exclude(user=user).select_related('user', 'user__profile').first()
        return participant.user if participant else None

    @property
    def latest_message(self):
        return self.messages.order_by('-created_at').first()

    def unread_count_for(self, user):
        return self.messages.filter(is_read=False).exclude(sender=user).count()


class ConversationParticipant(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversation_participations')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['conversation', 'user'], name='unique_conversation_user')
        ]

    def __str__(self):
        return f"{self.user.username} in Conversation #{self.conversation.id}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender.username} in Conv #{self.conversation.id}"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('follow', 'Follow'),
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('message', 'Message'),
        ('circle', 'Circle'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, blank=True, null=True, related_name='notifications')
    message = models.ForeignKey(Message, on_delete=models.CASCADE, blank=True, null=True, related_name='notifications')
    circle = models.ForeignKey(Circle, on_delete=models.CASCADE, blank=True, null=True, related_name='notifications')
    custom_text = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification to {self.recipient.username}: {self.sender.username} {self.notification_type}"

    @property
    def target_url(self):
        if self.circle:
            return f'/circle/{self.circle.id}/'
        if self.notification_type == 'follow':
            return f'/user/{self.sender.username}/'
        elif self.notification_type in ['like', 'comment'] and self.post:
            return f'/post/{self.post.id}/'
        elif self.notification_type == 'message':
            return '/messages/'
        return '#'

    @property
    def display_text(self):
        if self.custom_text:
            return self.custom_text
        if self.notification_type == 'follow':
            return 'started following you'
        elif self.notification_type == 'like':
            return 'liked your post'
        elif self.notification_type == 'comment':
            return 'commented on your post'
        elif self.notification_type == 'message':
            return 'sent you a message'
        elif self.notification_type == 'circle':
            return 'updated a circle with you'
        return 'interacted with you'


class UserMood(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_mood')
    mood = models.CharField(max_length=50)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} is feeling {self.mood}"


class UserPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preference')
    clean_feed = models.BooleanField(default=False)
    preferred_mood = models.CharField(max_length=50, blank=True, null=True)
    show_expired_posts = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s preferences"


class DailyMission(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    mission_type = models.CharField(max_length=50)  # comment, discover, share, like, poll
    active_date = models.DateField(default=timezone.now)

    class Meta:
        ordering = ['-active_date']

    def __str__(self):
        return f"{self.title} ({self.active_date})"


class UserMission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='completed_missions')
    mission = models.ForeignKey(DailyMission, on_delete=models.CASCADE, related_name='user_completions')
    completed = models.BooleanField(default=True)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'mission'], name='unique_user_mission')
        ]

    def __str__(self):
        return f"{self.user.username} completed {self.mission.title}"


class Topic(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"#{self.name}"


class PostTopic(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_topics')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='topic_posts')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['post', 'topic'], name='unique_post_topic')
        ]

    def __str__(self):
        return f"#{self.topic.name} on Post #{self.post.id}"


class UserInterest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interests')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='interested_users')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'topic'], name='unique_user_topic_interest')
        ]

    def __str__(self):
        return f"{self.user.username} interested in #{self.topic.name}"

