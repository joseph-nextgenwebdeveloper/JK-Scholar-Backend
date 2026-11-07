"""
Views for reminders app.
Includes CRUD endpoints and mobile offline synchronization endpoint.
"""

from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Reminder
from .serializers import ReminderSerializer, ReminderSyncSerializer


def visible_reminders(queryset):
    """Hide class reminders that belong to a semester that is not the active one."""
    return queryset.filter(
        Q(planner_event__isnull=True)
        | Q(planner_event__unit__isnull=True)
        | Q(planner_event__unit__semester__is_active=True)
    )


class ReminderViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for Reminders.
    Scoped strictly to the authenticated user.
    """
    serializer_class = ReminderSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        queryset = Reminder.objects.filter(user=self.request.user).select_related(
            'cat__unit', 'assignment__unit'
        )
        # Class reminders only exist for the ACTIVE semester (classes of other semesters must not
        # ring or clutter the alerts). Standalone event reminders (no unit) always show.
        # ?include_inactive=true lifts the filter.
        if self.request.query_params.get('include_inactive', '').lower() not in ('true', '1'):
            queryset = visible_reminders(queryset)
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
        # Every id that currently exists: lets a client drop reminders deleted on another
        # device (the incremental list below can only report changes, not deletions).
        all_ids = list(queryset.values_list('id', flat=True))
        updated_since = request.query_params.get('updated_since')
        if updated_since:
            since = parse_datetime(updated_since.replace(' ', '+'))  # '+' arrives as ' ' in a query string
            if since is not None:  # malformed timestamp -> fall back to everything
                if timezone.is_naive(since):
                    since = timezone.make_aware(since, timezone.utc)
                queryset = queryset.filter(updated_at__gt=since)

        items = list(queryset)
        serializer = ReminderSyncSerializer(items, many=True)
        return Response({
            'server_time': timezone.now().isoformat(),
            'count': len(items),
            'all_ids': all_ids,
            'reminders': serializer.data
        }, status=status.HTTP_200_OK)
