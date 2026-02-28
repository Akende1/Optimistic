from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Notification API - user's message inbox.
    
    Endpoints:
        GET /api/notifications/              - List notifications
        GET /api/notifications/{id}/         - Get detail
        POST /api/notifications/{id}/read/   - Mark as read
        POST /api/notifications/read-all/    - Mark all as read
    
    Why ReadOnlyModelViewSet?
    - Users cannot create/update/delete notifications
    - System creates notifications automatically
    - Users can only mark as read (custom actions)
    
    Permission Logic:
    - IsAuthenticated: Must be logged in
    - get_queryset filters to user's own notifications
    - Cannot access other users' notifications
    
    Custom Actions:
    - read: Mark single notification as read
    - read_all: Mark all user's notifications as read
    
    Frontend Usage:
    - Notification bell shows unread count
    - Dropdown shows recent notifications
    - Click → mark as read → navigate to related object
    
    Performance:
    - Ordered by newest first (-created_at)
    - Paginated (don't load all at once)
    - Efficient count queries for unread badge
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Users see only their own notifications."""
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def read(self, request, pk=None):
        """Mark notification as read."""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})

    @action(detail=False, methods=['post'])
    def read_all(self, request):
        """Mark all notifications as read."""
        count = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'status': f'{count} notifications marked as read'})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications."""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})
