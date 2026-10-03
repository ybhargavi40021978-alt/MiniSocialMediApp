from django.contrib import admin
from .models import (
    Profile, Post, Comment, Like, Follow, Notification, Conversation,
    ConversationParticipant, Message, Circle, CircleMember, PostVersion,
    Poll, PollOption, PollVote, UserMood, UserPreference, DailyMission,
    UserMission, Topic, PostTopic, UserInterest
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'created_at', 'updated_at')
    search_fields = ('user__username', 'bio')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'content', 'visibility', 'circle', 'mood', 'expires_at', 'created_at')
    list_filter = ('visibility', 'mood', 'created_at')
    search_fields = ('author__username', 'content')


@admin.register(Circle)
class CircleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'is_private', 'created_at')
    search_fields = ('name', 'description', 'owner__username')


@admin.register(CircleMember)
class CircleMemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'circle', 'user', 'role', 'joined_at')
    list_filter = ('role', 'circle')


@admin.register(PostVersion)
class PostVersionAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'version_number', 'edited_by', 'created_at')


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'question', 'created_at')


@admin.register(PollOption)
class PollOptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'poll', 'option_text')


@admin.register(PollVote)
class PollVoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'poll', 'option', 'user', 'created_at')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'author', 'content', 'created_at')
    search_fields = ('author__username', 'content')


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'post', 'reason', 'created_at')


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'follower', 'following', 'created_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipient', 'sender', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')


class ConversationParticipantInline(admin.TabularInline):
    model = ConversationParticipant
    extra = 1


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'updated_at')
    inlines = [ConversationParticipantInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender', 'content', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('sender__username', 'content')


@admin.register(UserMood)
class UserMoodAdmin(admin.ModelAdmin):
    list_display = ('user', 'mood', 'updated_at')


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'clean_feed', 'preferred_mood', 'show_expired_posts', 'updated_at')


@admin.register(DailyMission)
class DailyMissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'mission_type', 'active_date')


@admin.register(UserMission)
class UserMissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'mission', 'completed', 'completed_at')


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')
    search_fields = ('name',)


@admin.register(PostTopic)
class PostTopicAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'topic')


@admin.register(UserInterest)
class UserInterestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'topic', 'created_at')

