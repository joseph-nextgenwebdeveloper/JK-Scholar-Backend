"""
Serializers for assessments app: CAT and Assignment.
"""

from rest_framework import serializers
from .models import CAT, Assignment


class CATSerializer(serializers.ModelSerializer):
    unit_name = serializers.ReadOnlyField(source='unit.name')
    unit_code = serializers.ReadOnlyField(source='unit.code')
    reminders_count = serializers.SerializerMethodField()

    class Meta:
        model = CAT
        fields = (
            'id', 'unit', 'unit_name', 'unit_code',
            'title', 'description', 'cat_date', 'deadline', 'remind_minutes_before',
            'reminders_count', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'unit_name', 'unit_code', 'reminders_count')

    def get_reminders_count(self, obj):
        value = getattr(obj, 'reminders_count', None)
        if value is None:
            value = obj.reminders.count()
        return value

    def validate_remind_minutes_before(self, value):
        if value > 7 * 24 * 60:
            raise serializers.ValidationError('Choose an alarm of at most 7 days before.')
        return value

    def validate_unit(self, value):
        user = self.context['request'].user
        if value.semester.academic_year.user != user:
            raise serializers.ValidationError({"detail": "Invalid unit or permission denied."})
        return value


class AssignmentSerializer(serializers.ModelSerializer):
    unit_name = serializers.ReadOnlyField(source='unit.name')
    unit_code = serializers.ReadOnlyField(source='unit.code')
    reminders_count = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = (
            'id', 'unit', 'unit_name', 'unit_code',
            'title', 'description', 'deadline', 'submission_date', 'status', 'remind_minutes_before',
            'reminders_count', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'unit_name', 'unit_code', 'reminders_count')

    def get_reminders_count(self, obj):
        value = getattr(obj, 'reminders_count', None)
        if value is None:
            value = obj.reminders.count()
        return value

    def validate_remind_minutes_before(self, value):
        if value > 7 * 24 * 60:
            raise serializers.ValidationError('Choose an alarm of at most 7 days before.')
        return value

    def validate_unit(self, value):
        user = self.context['request'].user
        if value.semester.academic_year.user != user:
            raise serializers.ValidationError({"detail": "Invalid unit or permission denied."})
        return value
