"""
Views for notes app.
"""

from rest_framework import viewsets, permissions
from .models import Note
from .serializers import NoteSerializer


class NoteViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for Notes.
    Scoped strictly to notes belonging to the authenticated user's units.
    Supports filtering by ?unit=<id>.
    """
    serializer_class = NoteSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        queryset = Note.objects.filter(unit__semester__academic_year__user=self.request.user)
        unit_id = self.request.query_params.get('unit')
        if unit_id:
            queryset = queryset.filter(unit_id=unit_id)
        return queryset
