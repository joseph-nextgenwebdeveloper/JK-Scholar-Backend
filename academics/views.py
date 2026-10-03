"""
Views for academics hierarchy: AcademicYear, Semester, and Unit.
All endpoints strictly scoped to authenticated user.
"""

from rest_framework import viewsets, permissions
from .models import AcademicYear, Semester, Unit
from .serializers import AcademicYearSerializer, SemesterSerializer, UnitSerializer


class AcademicYearViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for Academic Years.
    Scoped to the authenticated user.
    """
    serializer_class = AcademicYearSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return AcademicYear.objects.filter(user=self.request.user)


class SemesterViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for Semesters.
    Filtered by user's academic years.
    Supports filtering by ?academic_year=<id>.
    """
    serializer_class = SemesterSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        queryset = Semester.objects.filter(academic_year__user=self.request.user)
        academic_year_id = self.request.query_params.get('academic_year')
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        return queryset


class UnitViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for Units.
    Filtered by user's semester hierarchy.
    Supports filtering by ?semester=<id>.
    """
    serializer_class = UnitSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        queryset = Unit.objects.filter(semester__academic_year__user=self.request.user)
        semester_id = self.request.query_params.get('semester')
        if semester_id:
            queryset = queryset.filter(semester_id=semester_id)
        return queryset
