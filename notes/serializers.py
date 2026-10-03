"""
Serializers for notes app.
"""

from rest_framework import serializers
from .models import Note


class NoteSerializer(serializers.ModelSerializer):
    unit_name = serializers.ReadOnlyField(source='unit.name')
    unit_code = serializers.ReadOnlyField(source='unit.code')

    class Meta:
        model = Note
        fields = ('id', 'unit', 'unit_name', 'unit_code', 'title', 'content', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at', 'unit_name', 'unit_code')

    def validate_unit(self, value):
        user = self.context['request'].user
        if value.semester.academic_year.user != user:
            raise serializers.ValidationError({"detail": "Invalid unit or permission denied."})
        return value
