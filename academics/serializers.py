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
        fields = ('id', 'academic_year', 'academic_year_name', 'name', 'is_active', 'units_count', 'created_at', 'updated_at')
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

