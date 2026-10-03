"""
Serializers for academics app: AcademicYear, Semester, and Unit.
Enforces business rules and ownership limits.
"""

from rest_framework import serializers
from .models import AcademicYear, Semester, Unit


class AcademicYearSerializer(serializers.ModelSerializer):
    semesters_count = serializers.IntegerField(source='semesters.count', read_only=True)

    class Meta:
        model = AcademicYear
        fields = ('id', 'name', 'start_date', 'end_date', 'semesters_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at', 'semesters_count')

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
        return super().create(validated_data)


class SemesterSerializer(serializers.ModelSerializer):
    academic_year_name = serializers.ReadOnlyField(source='academic_year.name')
    units_count = serializers.IntegerField(source='units.count', read_only=True)

    class Meta:
        model = Semester
        fields = ('id', 'academic_year', 'academic_year_name', 'name', 'units_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at', 'academic_year_name', 'units_count')

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
    notes_count = serializers.IntegerField(source='notes.count', read_only=True)
    cats_count = serializers.IntegerField(source='cats.count', read_only=True)
    assignments_count = serializers.IntegerField(source='assignments.count', read_only=True)

    class Meta:
        model = Unit
        fields = (
            'id', 'semester', 'semester_name', 'academic_year_id',
            'name', 'code', 'description',
            'notes_count', 'cats_count', 'assignments_count',
            'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'created_at', 'updated_at', 'semester_name',
            'academic_year_id', 'notes_count', 'cats_count', 'assignments_count'
        )

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
