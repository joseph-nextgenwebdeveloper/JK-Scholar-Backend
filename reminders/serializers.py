"""
Serializers for reminders app.
Enforces ownership, validation, and assessment limits (max 3 reminders per CAT/Assignment).
Supports standalone 'OTHER' category reminders not linked to any assessment.
"""

from rest_framework import serializers
from .models import Reminder


def normalise_repeat_days(value):
    """'5, 1,1,3' -> '1,3,5'. Raises ValidationError on anything but weekday numbers 1-7."""
    value = (value or '').strip()
    if not value:
        return ''
    days = set()
    for part in value.split(','):
        part = part.strip()
        if not (part.isascii() and part.isdigit()) or not 1 <= int(part) <= 7:
            raise serializers.ValidationError(
                "repeat_days must be comma-separated weekday numbers from 1 (Monday) to 7 (Sunday)."
            )
        days.add(int(part))
    return ','.join(str(d) for d in sorted(days))


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
            'category',
            'assessment_type', 'assessment_id', 'assessment_title',
            'unit_name', 'unit_code',
            'title', 'note', 'reminder_datetime', 'reminder_type',
            'repeat_days',
            'is_completed', 'is_read', 'user_modified',
            'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'user', 'reminder_type', 'user_modified',
            'assessment_type', 'assessment_id', 'assessment_title',
            'unit_name', 'unit_code',
            'created_at', 'updated_at'
        )

    def validate_repeat_days(self, value):
        return normalise_repeat_days(value)

    def get_unit_name(self, obj):
        if obj.cat:
            return obj.cat.unit.name
        elif obj.assignment:
            return obj.assignment.unit.name
        return ''

    def get_unit_code(self, obj):
        if obj.cat:
            return obj.cat.unit.code
        elif obj.assignment:
            return obj.assignment.unit.code
        return ''

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
        category = attrs.get('category', getattr(self.instance, 'category', Reminder.Category.OTHER))

        if cat and assignment:
            raise serializers.ValidationError({"detail": "A reminder cannot be associated with both a CAT and an Assignment."})

        # Verify user ownership of the parent assessment
        if cat and cat.unit.semester.academic_year.user != user:
            raise serializers.ValidationError({"detail": "Invalid CAT or permission denied."})
        if assignment and assignment.unit.semester.academic_year.user != user:
            raise serializers.ValidationError({"detail": "Invalid Assignment or permission denied."})

        # Auto-derive category from FK links
        if cat:
            attrs['category'] = Reminder.Category.CAT_REMINDER
        elif assignment:
            attrs['category'] = Reminder.Category.ASSIGNMENT_REMINDER
        elif not cat and not assignment:
            attrs['category'] = Reminder.Category.OTHER

        # Check max 3 reminders limit on creation (only for assessment-linked reminders)
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

    def update(self, instance, validated_data):
        # Editing the time or title of any alarm (including the automatic CAT / assignment ones)
        # is allowed; remember it so the automatic sync does not undo the edit.
        if any(k in validated_data for k in ('reminder_datetime', 'title', 'note', 'repeat_days')):
            validated_data['user_modified'] = True
        return super().update(instance, validated_data)


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
            'id', 'cat_id', 'assignment_id', 'category',
            'assessment_type', 'assessment_id',
            'unit_name', 'unit_code',
            'title', 'note', 'reminder_datetime', 'reminder_type',
            'repeat_days',
            'is_completed', 'is_read', 'updated_at'
        )

    def get_unit_name(self, obj):
        if obj.cat:
            return obj.cat.unit.name
        if obj.assignment:
            return obj.assignment.unit.name
        return ''

    def get_unit_code(self, obj):
        if obj.cat:
            return obj.cat.unit.code
        if obj.assignment:
            return obj.assignment.unit.code
        return ''

    def get_assessment_type(self, obj):
        if obj.cat_id:
            return 'CAT'
        if obj.assignment_id:
            return 'ASSIGNMENT'
        return None

    def get_assessment_id(self, obj):
        return obj.cat_id or obj.assignment_id
