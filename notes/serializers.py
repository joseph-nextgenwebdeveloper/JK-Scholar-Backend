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
    """File metadata only - the bytes are served by the download endpoint.

    Carries the unit / semester / year names so a client can group and search without extra calls."""
    unit_name = serializers.ReadOnlyField(source='unit.name')
    unit_code = serializers.ReadOnlyField(source='unit.code')
    semester = serializers.ReadOnlyField(source='unit.semester_id')
    semester_name = serializers.ReadOnlyField(source='unit.semester.name')
    academic_year = serializers.ReadOnlyField(source='unit.semester.academic_year_id')
    academic_year_name = serializers.ReadOnlyField(source='unit.semester.academic_year.name')
    extension = serializers.SerializerMethodField()

    class Meta:
        model = UnitFile
        fields = ('id', 'unit', 'unit_name', 'unit_code', 'semester', 'semester_name',
                  'academic_year', 'academic_year_name', 'filename', 'extension',
                  'content_type', 'size', 'created_at', 'updated_at')
        read_only_fields = fields

    def get_extension(self, obj):
        name = obj.filename or ''
        return name.rsplit('.', 1)[-1].lower() if '.' in name else ''
