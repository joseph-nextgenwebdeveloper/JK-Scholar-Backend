"""
Views for academics hierarchy: AcademicYear, Semester, and Unit.
All endpoints strictly scoped to authenticated user.
"""

from django.db.models import Count
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
        return (
            AcademicYear.objects.filter(user=self.request.user)
            .annotate(semesters_count=Count('semesters', distinct=True))
        )


class SemesterViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for Semesters.
    Filtered by user's academic years.
    Supports filtering by ?academic_year=<id>.
    """
    serializer_class = SemesterSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        queryset = (
            Semester.objects.filter(academic_year__user=self.request.user)
            .select_related('academic_year')
            .annotate(units_count=Count('units', distinct=True))
        )
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
        queryset = (
            Unit.objects.filter(semester__academic_year__user=self.request.user)
            .select_related('semester__academic_year')
            .annotate(
                notes_count=Count('notes', distinct=True),
                cats_count=Count('cats', distinct=True),
                assignments_count=Count('assignments', distinct=True),
            )
        )
        semester_id = self.request.query_params.get('semester')
        if semester_id:
            queryset = queryset.filter(semester_id=semester_id)
        return queryset


from .models import PlannerEvent  # noqa: E402
from .serializers import PlannerEventSerializer  # noqa: E402


class PlannerEventViewSet(viewsets.ModelViewSet):
    """Classes and non-academic events, scoped to the signed-in student."""
    serializer_class = PlannerEventSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return PlannerEvent.objects.filter(user=self.request.user).select_related('unit')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
