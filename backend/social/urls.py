from django.urls import path
from . import views

urlpatterns = [
    # Public Landing Page (Root)
    path('', views.landing_view, name='landing'),
    path('landing/', views.landing_view, name='landing_page'),
    path('index/', views.landing_view, name='index'),
    path('index.html', views.landing_view, name='index_html'),

    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Main views
    path('home/', views.home_view, name='home'),
    path('profile/', views.profile_view, name='profile'),
    path('user/mood/', views.update_mood_view, name='user_mood'),
    path('user/mood/update/', views.update_mood_view, name='update_mood'),
    path('user/<str:username>/', views.user_profile_view, name='user_profile'),
    path('post/<int:pk>/', views.post_detail_view, name='post_detail'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('followers/', views.followers_view, name='followers'),
    path('following/', views.following_view, name='following'),
    path('settings/', views.settings_view, name='settings'),
    path('messages/', views.messages_view, name='messages'),
    path('messages/<int:conversation_id>/', views.messages_conversation_view, name='messages_conversation'),
    path('messages/user/<str:username>/', views.messages_user_view, name='messages_user'),

    # Actions (AJAX / POST)
    path('post/create/', views.create_post_view, name='create_post'),
    path('post/<int:pk>/like/', views.like_post_view, name='like_post'),
    path('post/<int:pk>/react/', views.like_post_view, name='post_react'),
    path('post/<int:pk>/comment/', views.comment_post_view, name='comment_post'),
    path('post/<int:pk>/edit/', views.post_edit_view, name='post_edit'),
    path('post/<int:pk>/versions/', views.post_versions_view, name='post_versions'),
    path('user/<str:username>/follow/', views.follow_user_view, name='follow_user'),
    path('profile/update/', views.profile_update_view, name='profile_update'),
    path('profile/photo/', views.profile_photo_upload_view, name='profile_photo_upload'),
    path('settings/password/', views.change_password_view, name='change_password'),
    path('messages/send/', views.send_message_view, name='send_message'),
    path('notification/<int:pk>/read/', views.mark_notification_read_view, name='mark_notification_read'),
    path('notification/<int:pk>/delete/', views.delete_notification_view, name='delete_notification'),
    path('notification/read-all/', views.mark_all_notifications_read_view, name='mark_all_notifications_read'),
    path('notifications/read-all/', views.mark_all_notifications_read_view, name='notifications_read_all'),
    path('notifications/mark-read/', views.mark_all_notifications_read_view, name='notifications_mark_read'),

    # MiniSocial Circles
    path('circles/', views.circles_view, name='circles'),
    path('circle/create/', views.create_circle_view, name='create_circle'),
    path('circle/<int:pk>/', views.circle_detail_view, name='circle_detail'),
    path('circle/<int:pk>/join/', views.join_circle_view, name='join_circle'),
    path('circle/<int:pk>/leave/', views.leave_circle_view, name='leave_circle'),
    path('circle/<int:pk>/members/', views.manage_circle_members_view, name='manage_circle_members'),
    path('circle/<int:pk>/post/create/', views.circle_create_post_view, name='circle_create_post'),

    # Polls / Decision Posts
    path('poll/<int:pk>/vote/', views.poll_vote_view, name='poll_vote'),
    path('poll/<int:pk>/updates/', views.poll_updates_view, name='poll_updates'),

    # Personal Social Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Daily Missions
    path('missions/', views.daily_missions_view, name='daily_missions'),
    path('mission/<int:pk>/complete/', views.complete_mission_view, name='complete_mission'),

    # Explore & Topics & Interests
    path('explore/', views.explore_view, name='explore'),
    path('interests/', views.explore_view, name='interests'),
    path('interests/update/', views.update_interests_view, name='update_interests'),

    # User Mood & Preferences
    path('user/mood/', views.update_mood_view, name='user_mood'),
    path('user/mood/update/', views.update_mood_view, name='update_mood'),
    path('feed/mood/', views.home_view, name='feed_mood'),
    path('preferences/update/', views.update_preferences_view, name='update_preferences'),

    # Search
    path('search/', views.search_view, name='search'),

    # Polling & Real-time Live Updates
    path('notifications/updates/', views.notifications_updates_view, name='notifications_updates'),
    path('messages/<int:conversation_id>/updates/', views.messages_updates_view, name='messages_updates'),
    path('messages/updates/', views.messages_global_updates_view, name='messages_global_updates'),
    path('feed/updates/', views.feed_updates_view, name='feed_updates'),
    path('profile/followers/updates/', views.followers_updates_view, name='followers_updates'),

    # UI State Demos (Preserved)
    path('demo/create-post/', views.create_post_modal_demo_view, name='demo_create_post'),
    path('demo/like-unlike/', views.like_unlike_state_demo_view, name='demo_like_unlike'),
    path('demo/follow-unfollow/', views.follow_unfollow_state_demo_view, name='demo_follow_unfollow'),
]
