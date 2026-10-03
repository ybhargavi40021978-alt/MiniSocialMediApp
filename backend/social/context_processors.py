from .models import Message

def unread_counts(request):
    if request.user.is_authenticated:
        unread_notifs = request.user.notifications.filter(is_read=False).count()
        unread_msgs = Message.objects.filter(
            conversation__participants__user=request.user,
            is_read=False
        ).exclude(sender=request.user).distinct().count()
        return {
            'unread_notifications_count': unread_notifs,
            'unread_messages_count': unread_msgs,
        }
    return {'unread_notifications_count': 0, 'unread_messages_count': 0}

# Backwards compatibility alias
unread_notifications_count = unread_counts
