"""
Serializers for reminders app.
Enforces ownership, validation, and assessment limits (max 3 reminders per CAT/Assignment).
"""

from rest_framework import serializers
from .models import Reminder


class ReminderSerializer(serializers.ModelSerializer):
    unit_name = serializers.SerializerMethodField()
    unit_code = serializers.SerializerMethodField()
    assessment_type = serializers.SerializerMethodField()
    assessment_id = serializers.SerializerMethodField()
    assessment_title = serializers.SerializerMethodField()

    class Meta:
        model = Reminder
        fields = (
            'id', 'user', 'cat', 'assignment',
            'assessment_type', 'assessment_id', 'assessment_title',
            'unit_name', 'unit_code',
            'title', 'reminder_datetime', 'reminder_type',
            'is_completed', 'is_read',
            'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'user', 'reminder_type',
            'assessment_type', 'assessment_id', 'assessment_title',
            'unit_name', 'unit_code',
            'created_at', 'updated_at'
        )

    def get_unit_name(self, obj):
        if obj.cat:
            return obj.cat.unit.name
        elif obj.assignment:
            return obj.assignment.unit.name
        return None

    def get_unit_code(self, obj):
        if obj.cat:
            return obj.cat.unit.code
        elif obj.assignment:
            return obj.assignment.unit.code
        return None

    def get_assessment_type(self, obj):
        if obj.cat_id:
            return 'CAT'
        elif obj.assignment_id:
            return 'ASSIGNMENT'
        return None

    def get_assessment_id(self, obj):
        return obj.cat_id if obj.cat_id else obj.assignment_id

    def get_assessment_title(self, obj):
        if obj.cat:
            return obj.cat.title
        elif obj.assignment:
            return obj.assignment.title
        return None

    def validate(self, attrs):
        user = self.context['request'].user
        cat = attrs.get('cat', getattr(self.instance, 'cat', None))
        assignment = attrs.get('assignment', getattr(self.instance, 'assignment', None))

        if cat and assignment:
            raise serializers.ValidationError({"detail": "A reminder cannot be associated with both a CAT and an Assignment."})

        # Verify user ownership of the parent assessment
        if cat and cat.unit.semester.academic_year.user != user:
            raise serializers.ValidationError({"detail": "Invalid CAT or permission denied."})
        if assignment and assignment.unit.semester.academic_year.user != user:
            raise serializers.ValidationError({"detail": "Invalid Assignment or permission denied."})

        # Check max 3 reminders limit on creation
        if not self.instance:
            if cat and Reminder.objects.filter(cat=cat).count() >= 3:
                raise serializers.ValidationError({"detail": "A CAT or Assignment can have a maximum of 3 reminders."})
            if assignment and Reminder.objects.filter(assignment=assignment).count() >= 3:
                raise serializers.ValidationError({"detail": "A CAT or Assignment can have a maximum of 3 reminders."})

        return attrs

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['reminder_type'] = Reminder.ReminderType.MANUAL
        return super().create(validated_data)


class ReminderSyncSerializer(serializers.ModelSerializer):
    """
    Optimized serializer for mobile client offline scheduling synchronization.
    """
    unit_name = serializers.SerializerMethodField()
    unit_code = serializers.SerializerMethodField()
    assessment_type = serializers.SerializerMethodField()
    assessment_id = serializers.SerializerMethodField()

    class Meta:
        model = Reminder
        fields = (
            'id', 'cat_id', 'assignment_id', 'assessment_type', 'assessment_id',
            'unit_name', 'unit_code',
            'title', 'reminder_datetime', 'reminder_type',
            'is_completed', 'is_read', 'updated_at'
        )

    def get_unit_name(self, obj):
        if obj.cat:
            return obj.cat.unit.name
        if obj.assignment:
            return obj.assignment.unit.name
        return None

    def get_unit_code(self, obj):
        if obj.cat:
            return obj.cat.unit.code
        if obj.assignment:
            return obj.assignment.unit.code
        return None

    def get_assessment_type(self, obj):
        if obj.cat_id:
            return 'CAT'
        if obj.assignment_id:
            return 'ASSIGNMENT'
        return None

    def get_assessment_id(self, obj):
        return obj.cat_id or obj.assignment_id
