"""
One-call snapshot of everything the app shows on its main screens.

GET /api/snapshot/ replaces six or seven separate list requests at start-up, which matters a lot
on a free host where every request has a cold-start and round-trip cost. The app stores the
result in its offline cache, so the same data is then available instantly and without internet.
"""

from django.db.models import Count, Prefetch
from django.utils import timezone
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from academics.models import AcademicYear, Semester, Unit
from academics.models import PlannerEvent
from academics.serializers import (AcademicYearSerializer, SemesterSerializer, UnitSerializer,
                                   PlannerEventSerializer)
from assessments.models import CAT, Assignment
from assessments.serializers import CATSerializer, AssignmentSerializer
from notes.models import Note, NoteAttachment, UnitFile
from notes.serializers import NoteSerializer, UnitFileSerializer
from reminders.models import Reminder
from reminders.serializers import ReminderSerializer


class SnapshotView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = request.user
        ctx = {'request': request}

        years = AcademicYear.objects.filter(user=user).annotate(
            semesters_count=Count('semesters', distinct=True))
        semesters = (Semester.objects.filter(academic_year__user=user)
                     .select_related('academic_year')
                     .annotate(units_count=Count('units', distinct=True)))
        units = (Unit.objects.filter(semester__academic_year__user=user)
                 .select_related('semester__academic_year')
                 .annotate(notes_count=Count('notes', distinct=True),
                           cats_count=Count('cats', distinct=True),
                           assignments_count=Count('assignments', distinct=True)))
        notes = (Note.objects.filter(unit__semester__academic_year__user=user)
                 .select_related('unit')
                 .prefetch_related(Prefetch('attachments', queryset=NoteAttachment.objects.defer('data'))))
        cats = (CAT.objects.filter(unit__semester__academic_year__user=user)
                .select_related('unit').annotate(reminders_count=Count('reminders', distinct=True)))
        assignments = (Assignment.objects.filter(unit__semester__academic_year__user=user)
                       .select_related('unit').annotate(reminders_count=Count('reminders', distinct=True)))
        reminders = (Reminder.objects.filter(user=user)
                     .select_related('cat__unit', 'assignment__unit'))
        files = (UnitFile.objects.filter(unit__semester__academic_year__user=user)
                 .select_related('unit').defer('data'))

        return Response({
            'server_time': timezone.now().isoformat(),
            'academic_years': AcademicYearSerializer(years, many=True, context=ctx).data,
            'semesters': SemesterSerializer(semesters, many=True, context=ctx).data,
            'units': UnitSerializer(units, many=True, context=ctx).data,
            'notes': NoteSerializer(notes, many=True, context=ctx).data,
            'cats': CATSerializer(cats, many=True, context=ctx).data,
            'assignments': AssignmentSerializer(assignments, many=True, context=ctx).data,
            'reminders': ReminderSerializer(reminders, many=True, context=ctx).data,
            'files': UnitFileSerializer(files, many=True, context=ctx).data,
            'planner_events': PlannerEventSerializer(
                PlannerEvent.objects.filter(user=user).select_related('unit'),
                many=True, context=ctx).data,
        })
