"""
Serializers for notes app.
"""

from rest_framework import serializers
from .models import Note, NoteAttachment, UnitFile


class NoteAttachmentSerializer(serializers.ModelSerializer):
    """Attachment metadata only - the bytes are served by the download endpoint."""

    class Meta:
        model = NoteAttachment
        fields = ('id', 'note', 'filename', 'content_type', 'size', 'created_at')
        read_only_fields = fields


class NoteSerializer(serializers.ModelSerializer):
    unit_name = serializers.ReadOnlyField(source='unit.name')
    unit_code = serializers.ReadOnlyField(source='unit.code')
    attachments = NoteAttachmentSerializer(many=True, read_only=True)
    attachments_count = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = ('id', 'unit', 'unit_name', 'unit_code', 'title', 'content',
                  'attachments', 'attachments_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at', 'unit_name', 'unit_code',
                            'attachments', 'attachments_count')

    def get_attachments_count(self, obj):
        return len(obj.attachments.all())

    def validate_unit(self, value):
        user = self.context['request'].user
        if value.semester.academic_year.user != user:
            raise serializers.ValidationError({"detail": "Invalid unit or permission denied."})
        return value


class UnitFileSerializer(serializers.ModelSerializer):
    """File metadata only - the bytes are served by the download endpoint."""
    unit_name = serializers.ReadOnlyField(source='unit.name')
    unit_code = serializers.ReadOnlyField(source='unit.code')

    class Meta:
        model = UnitFile
        fields = ('id', 'unit', 'unit_name', 'unit_code', 'filename', 'content_type', 'size',
                  'created_at', 'updated_at')
        read_only_fields = fields
