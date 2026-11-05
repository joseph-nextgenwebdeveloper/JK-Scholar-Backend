"""
Views for academics hierarchy: AcademicYear, Semester, and Unit.
All endpoints strictly scoped to authenticated user.
"""

from django.db.models import Count
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
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

    def destroy(self, request, *args, **kwargs):
        """A year that already holds units can't be deleted (that would wipe its notes,
        files and assessments). It can be made the active year instead."""
        year = self.get_object()
        units = Unit.objects.filter(semester__academic_year=year).count()
        if units:
            return Response(
                {'detail': f'"{year.name}" has {units} unit{"s" if units != 1 else ""}, so it cannot be '
                           f'deleted. You can make it your active year instead.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Make this year the current one: activates its first semester (the student
        only ever has one active semester)."""
        year = self.get_object()
        sems = list(year.semesters.order_by('id'))
        if not sems:
            return Response({'detail': 'This year has no semesters yet.'}, status=status.HTTP_400_BAD_REQUEST)
        if not any(s.is_active for s in sems):
            sem = sems[0]
            sem.is_active = True
            sem.save()
        return Response({'detail': 'Year activated.', 'semester': next(s.id for s in year.semesters.order_by('id') if s.is_active)})


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
