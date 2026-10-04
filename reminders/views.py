"""
Views for reminders app.
Includes CRUD endpoints and mobile offline synchronization endpoint.
"""

from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Reminder
from .serializers import ReminderSerializer, ReminderSyncSerializer


class ReminderViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for Reminders.
    Scoped strictly to the authenticated user.
    """
    serializer_class = ReminderSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        queryset = Reminder.objects.filter(user=self.request.user)
        cat_id = self.request.query_params.get('cat')
        assignment_id = self.request.query_params.get('assignment')
        is_completed = self.request.query_params.get('is_completed')
        is_read = self.request.query_params.get('is_read')
        reminder_type = self.request.query_params.get('reminder_type')
        category = self.request.query_params.get('category')

        if cat_id:
            queryset = queryset.filter(cat_id=cat_id)
        if assignment_id:
            queryset = queryset.filter(assignment_id=assignment_id)
        if is_completed is not None:
            queryset = queryset.filter(is_completed=is_completed.lower() in ('true', '1'))
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() in ('true', '1'))
        if reminder_type:
            queryset = queryset.filter(reminder_type=reminder_type.upper())
        if category:
            queryset = queryset.filter(category=category.upper())

        return queryset

    @action(detail=False, methods=['get'], url_path='sync')
    def sync(self, request):
        """
        Endpoint: GET /api/reminders/sync/?updated_since=<ISO_TIMESTAMP>
        Provides synchronization payload for Flutter local notification scheduling.
        Returns server timestamp and all reminders updated since the provided timestamp.
        """
        queryset = self.get_queryset()
        updated_since = request.query_params.get('updated_since')
        if updated_since:
            try:
                queryset = queryset.filter(updated_at__gt=updated_since)
            except Exception:
                pass  # Fallback to all reminders if timestamp is malformed

        serializer = ReminderSyncSerializer(queryset, many=True)
        return Response({
            'server_time': timezone.now().isoformat(),
            'count': queryset.count(),
            'reminders': serializer.data
        }, status=status.HTTP_200_OK)
