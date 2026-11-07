"""
Serializers for academics app: AcademicYear, Semester, and Unit.
Enforces business rules and ownership limits.
"""

from django.db import transaction
from rest_framework import serializers
from .models import AcademicYear, Semester, Unit


COVER_SLUGS = (
    'library', 'graduation', 'science', 'globe', 'maths',
    'code', 'biology', 'notes', 'ideas', 'campus',
)

DEFAULT_SEMESTER_NAMES = ('First Semester', 'Second Semester')


def _count(obj, annotated_name, related_name):
    """Use the queryset annotation when present, else fall back to a COUNT query."""
    value = getattr(obj, annotated_name, None)
    if value is None:
        value = getattr(obj, related_name).count()
    return value


class AcademicYearSerializer(serializers.ModelSerializer):
    semesters_count = serializers.SerializerMethodField()

    class Meta:
        model = AcademicYear
        fields = ('id', 'name', 'start_date', 'end_date', 'cover', 'semesters_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at', 'semesters_count')

    def get_semesters_count(self, obj):
        return _count(obj, 'semesters_count', 'semesters')

    def validate_cover(self, value):
        if value and value not in COVER_SLUGS:
            raise serializers.ValidationError(
                "Invalid cover. Allowed values: " + ", ".join(COVER_SLUGS) + "."
            )
        return value

    def validate(self, attrs):
        user = self.context['request'].user
        start_date = attrs.get('start_date', getattr(self.instance, 'start_date', None))
        end_date = attrs.get('end_date', getattr(self.instance, 'end_date', None))

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({"detail": "Start date cannot be after end date."})

        # Check maximum limit for creation
        if not self.instance:
            if AcademicYear.objects.filter(user=user).count() >= 6:
                raise serializers.ValidationError({"detail": "You can have a maximum of 6 academic years."})

        return attrs

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        with transaction.atomic():
            year = AcademicYear.objects.create(**validated_data)
            for name in DEFAULT_SEMESTER_NAMES:
                Semester.objects.create(academic_year=year, name=name, is_active=False)
        # No annotation on a freshly created instance: semesters_count falls back
        # to a COUNT query and therefore reports 2.
        return year


class SemesterSerializer(serializers.ModelSerializer):
    academic_year_name = serializers.ReadOnlyField(source='academic_year.name')
    units_count = serializers.SerializerMethodField()

    class Meta:
        model = Semester
        fields = ('id', 'academic_year', 'academic_year_name', 'name', 'start_date', 'end_date', 'is_active', 'units_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at', 'academic_year_name', 'units_count')

    def get_units_count(self, obj):
        return _count(obj, 'units_count', 'units')

    def validate_academic_year(self, value):
        user = self.context['request'].user
        if value.user != user:
            raise serializers.ValidationError({"detail": "Invalid academic year or permission denied."})
        return value

    def validate(self, attrs):
        academic_year = attrs.get('academic_year', getattr(self.instance, 'academic_year', None))
        start_date = attrs.get('start_date', getattr(self.instance, 'start_date', None))
        end_date = attrs.get('end_date', getattr(self.instance, 'end_date', None))

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({"detail": "Start date cannot be after end date."})

        # There is always exactly one active semester: switch by activating another one.
        if self.instance and self.instance.is_active and attrs.get('is_active') is False:
            raise serializers.ValidationError(
                {"detail": "One semester must stay active. Make another semester active instead."})

        # Check maximum limit for creation
        if not self.instance and academic_year:
            if Semester.objects.filter(academic_year=academic_year).count() >= 3:
                raise serializers.ValidationError({"detail": "An academic year can contain a maximum of 3 semesters."})

        return attrs


class UnitSerializer(serializers.ModelSerializer):
    semester_name = serializers.ReadOnlyField(source='semester.name')
    academic_year_id = serializers.ReadOnlyField(source='semester.academic_year_id')
    notes_count = serializers.SerializerMethodField()
    cats_count = serializers.SerializerMethodField()
    assignments_count = serializers.SerializerMethodField()

    class Meta:
        model = Unit
        fields = (
            'id', 'semester', 'semester_name', 'academic_year_id',
            'name', 'code', 'description',
            'lecturer_name', 'lecturer_phone',
            'notes_count', 'cats_count', 'assignments_count',
            'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'created_at', 'updated_at', 'semester_name',
            'academic_year_id', 'notes_count', 'cats_count', 'assignments_count'
        )

    def get_notes_count(self, obj):
        return _count(obj, 'notes_count', 'notes')

    def get_cats_count(self, obj):
        return _count(obj, 'cats_count', 'cats')

    def get_assignments_count(self, obj):
        return _count(obj, 'assignments_count', 'assignments')

    def validate_semester(self, value):
        user = self.context['request'].user
        if value.academic_year.user != user:
            raise serializers.ValidationError({"detail": "Invalid semester or permission denied."})
        return value

    def validate(self, attrs):
        semester = attrs.get('semester', getattr(self.instance, 'semester', None))

        # Check maximum limit for creation
        if not self.instance and semester:
            if Unit.objects.filter(semester=semester).count() >= 10:
                raise serializers.ValidationError({"detail": "A semester can contain a maximum of 10 units."})

        return attrs



from .models import PlannerEvent  # noqa: E402


class PlannerEventSerializer(serializers.ModelSerializer):
    """A timetable class (weekly) or one-off event.

    Classes are tied to a unit, and the unit's semester decides WHEN the class exists: it recurs
    weekly only between the semester's start and end dates, and only while that semester is the
    active one. The semester facts are returned (read-only) so every client applies the same rule
    without a second request.
    """
    unit_name = serializers.CharField(source='unit.name', read_only=True, default='')
    unit_code = serializers.CharField(source='unit.code', read_only=True, default='')
    semester = serializers.IntegerField(source='unit.semester_id', read_only=True, default=None)
    semester_name = serializers.CharField(source='unit.semester.name', read_only=True, default='')
    semester_start = serializers.DateField(source='unit.semester.start_date', read_only=True, default=None)
    semester_end = serializers.DateField(source='unit.semester.end_date', read_only=True, default=None)
    semester_active = serializers.BooleanField(source='unit.semester.is_active', read_only=True, default=None)
    academic_year_name = serializers.CharField(source='unit.semester.academic_year.name', read_only=True, default='')

    class Meta:
        model = PlannerEvent
        fields = [
            'id', 'kind', 'title', 'unit', 'unit_name', 'unit_code',
            'semester', 'semester_name', 'semester_start', 'semester_end', 'semester_active',
            'academic_year_name', 'location', 'note',
            'date', 'weekday', 'start_time', 'end_time', 'repeat_until',
            'remind_minutes_before', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {'title': {'required': False, 'allow_blank': True}}

    def validate_remind_minutes_before(self, v):
        if v > 7 * 24 * 60:
            raise serializers.ValidationError('Choose a reminder of at most 7 days before.')
        return v

    def validate_unit(self, unit):
        if unit and unit.semester.academic_year.user_id != self.context['request'].user.id:
            raise serializers.ValidationError('Unknown unit.')
        return unit

    def validate(self, attrs):
        inst = self.instance
        get = lambda k: attrs.get(k, getattr(inst, k, None))  # noqa: E731
        kind, unit = get('kind'), get('unit')

        if kind == PlannerEvent.KIND_CLASS:
            if not get('weekday'):
                raise serializers.ValidationError({'weekday': 'Choose the day of the week for a class.'})
            if unit is None:
                # Legacy classes saved before units were required may still be edited as they are.
                if inst is None or inst.unit_id is not None or 'unit' in attrs:
                    raise serializers.ValidationError({'unit': 'Choose the unit this class is for.'})
            elif inst is None or 'unit' in attrs and (inst.unit_id != unit.id):
                if not unit.semester.is_active:
                    raise serializers.ValidationError(
                        {'unit': 'Pick a unit from your active semester. Make that semester active first.'})
        if kind == PlannerEvent.KIND_EVENT and not (get('date') or get('weekday')):
            raise serializers.ValidationError({'date': 'Choose a date for the event.'})
        wd = get('weekday')
        if wd is not None and not 1 <= wd <= 7:
            raise serializers.ValidationError({'weekday': 'Weekday must be 1 (Mon) to 7 (Sun).'})
        if get('start_time') and get('end_time') and get('end_time') <= get('start_time'):
            raise serializers.ValidationError({'end_time': 'End time must be after the start time.'})

        # The class name comes from the unit: no free-typed, unrelated class names.
        title = (attrs.get('title') if 'title' in attrs else getattr(inst, 'title', '')) or ''
        if not title.strip():
            if unit is not None and kind == PlannerEvent.KIND_CLASS:
                attrs['title'] = unit.name
            else:
                raise serializers.ValidationError({'title': 'Enter a title.'})
        elif unit is not None and kind == PlannerEvent.KIND_CLASS and 'title' not in attrs and inst is None:
            attrs['title'] = unit.name
        return attrs
