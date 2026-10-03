"""
Views for assessments app: CAT and Assignment.
"""

from rest_framework import viewsets, permissions
from .models import CAT, Assignment
from .serializers import CATSerializer, AssignmentSerializer


class CATViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for Continuous Assessment Tests (CATs).
    Scoped to authenticated student's unit hierarchy.
    Supports filtering by ?unit=<id>.
    """
    serializer_class = CATSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        queryset = CAT.objects.filter(unit__semester__academic_year__user=self.request.user)
        unit_id = self.request.query_params.get('unit')
        if unit_id:
            queryset = queryset.filter(unit_id=unit_id)
        return queryset


class AssignmentViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for Assignments.
    Scoped to authenticated student's unit hierarchy.
    Supports filtering by ?unit=<id> and ?status=<status>.
    """
    serializer_class = AssignmentSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        queryset = Assignment.objects.filter(unit__semester__academic_year__user=self.request.user)
        unit_id = self.request.query_params.get('unit')
        status_param = self.request.query_params.get('status')
        if unit_id:
            queryset = queryset.filter(unit_id=unit_id)
        if status_param:
            queryset = queryset.filter(status=status_param.upper())
        return queryset
