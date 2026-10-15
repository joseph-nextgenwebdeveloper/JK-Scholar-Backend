"""
Views for notes app.
"""

import mimetypes
import os
from urllib.parse import quote

from django.conf import settings
from django.db.models import Prefetch
from django.http import HttpResponse
from rest_framework import viewsets, permissions, status, mixins
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response

from academics.models import Unit
from .models import Note, NoteAttachment, UnitFile
from .serializers import NoteSerializer, NoteAttachmentSerializer, UnitFileSerializer

# Limits (override in settings.py if needed).
MAX_ATTACHMENTS_PER_NOTE = getattr(settings, 'NOTE_MAX_ATTACHMENTS', 20)
MAX_ATTACHMENT_BYTES = getattr(settings, 'NOTE_MAX_ATTACHMENT_BYTES', 5 * 1024 * 1024)  # 5 MB

MAX_FILES_PER_UNIT = getattr(settings, 'UNIT_FILE_MAX_PER_UNIT', 50)
MAX_UNIT_FILE_BYTES = getattr(settings, 'UNIT_FILE_MAX_BYTES', 15 * 1024 * 1024)  # 15 MB

BLOCKED_EXTENSIONS = {'.exe', '.bat', '.cmd', '.com', '.msi', '.apk', '.scr', '.sh', '.js', '.vbs', '.jar'}


class NoteViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for Notes.
    Scoped strictly to notes belonging to the authenticated user's units.
    Supports filtering by ?unit=<id>.

    Extra endpoints:
      GET/POST /api/notes/<id>/attachments/   list / upload a file (multipart field "file")
    """
    serializer_class = NoteSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        queryset = (
            Note.objects.filter(unit__semester__academic_year__user=self.request.user)
            .select_related('unit')
            .prefetch_related(
                Prefetch('attachments', queryset=NoteAttachment.objects.defer('data'))
            )
        )
        unit_id = self.request.query_params.get('unit')
        if unit_id:
            queryset = queryset.filter(unit_id=unit_id)
        return queryset

    @action(detail=True, methods=['get', 'post'], url_path='attachments',
            parser_classes=[MultiPartParser, FormParser, JSONParser])
    def attachments(self, request, pk=None):
        note = self.get_object()

        if request.method == 'GET':
            items = NoteAttachment.objects.filter(note=note).defer('data')
            return Response(NoteAttachmentSerializer(items, many=True).data)

        upload = request.FILES.get('file')
        if upload is None:
            return Response({"detail": "No file uploaded (expected field 'file')."},
                            status=status.HTTP_400_BAD_REQUEST)
        if upload.size > MAX_ATTACHMENT_BYTES:
            limit_mb = MAX_ATTACHMENT_BYTES // (1024 * 1024)
            return Response({"detail": f"File is too large. Maximum size is {limit_mb} MB."},
                            status=status.HTTP_400_BAD_REQUEST)
        if NoteAttachment.objects.filter(note=note).count() >= MAX_ATTACHMENTS_PER_NOTE:
            return Response({"detail": f"A note can have at most {MAX_ATTACHMENTS_PER_NOTE} files."},
                            status=status.HTTP_400_BAD_REQUEST)

        filename = os.path.basename(upload.name or 'file')[:255] or 'file'
        if os.path.splitext(filename)[1].lower() in BLOCKED_EXTENSIONS:
            return Response({"detail": "This file type is not allowed."},
                            status=status.HTTP_400_BAD_REQUEST)

        content_type = upload.content_type
        if not content_type or content_type == 'application/octet-stream':
            content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        attachment = NoteAttachment.objects.create(
            note=note,
            filename=filename,
            content_type=content_type[:100],
            size=upload.size,
            data=upload.read(),
        )
        note.save(update_fields=['updated_at'])  # bump "last updated"
        return Response(NoteAttachmentSerializer(attachment).data, status=status.HTTP_201_CREATED)


class NoteAttachmentViewSet(mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """
    DELETE /api/note-attachments/<id>/            remove an attachment
    GET    /api/note-attachments/<id>/download/   download the file bytes
    """
    serializer_class = NoteAttachmentSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return NoteAttachment.objects.filter(
            note__unit__semester__academic_year__user=self.request.user
        )

    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        attachment = self.get_object()
        response = HttpResponse(bytes(attachment.data), content_type=attachment.content_type)
        response['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(attachment.filename)}"
        return response


class UnitFileViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.DestroyModelMixin,
                      viewsets.GenericViewSet):
    """
    The file library of a unit (PDF, Word, PowerPoint, Excel, images ...).

    GET    /api/files/                  list (optional ?unit=<id>)
    POST   /api/files/                  upload: multipart fields "unit" and "file"
    DELETE /api/files/<id>/             remove
    GET    /api/files/<id>/download/    the file bytes
    """
    serializer_class = UnitFileSerializer
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_queryset(self):
        queryset = (
            UnitFile.objects.filter(unit__semester__academic_year__user=self.request.user)
            .select_related('unit')
            .defer('data')
        )
        unit_id = self.request.query_params.get('unit')
        if unit_id:
            queryset = queryset.filter(unit_id=unit_id)
        return queryset

    def create(self, request, *args, **kwargs):
        upload = request.FILES.get('file')
        if upload is None:
            return Response({"detail": "No file uploaded (expected field 'file')."},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            unit_id = int(request.data.get('unit'))
        except (TypeError, ValueError):
            return Response({"detail": "Choose a unit for this file."}, status=status.HTTP_400_BAD_REQUEST)
        unit = Unit.objects.filter(pk=unit_id, semester__academic_year__user=request.user).first()
        if unit is None:
            return Response({"detail": "Invalid unit or permission denied."}, status=status.HTTP_400_BAD_REQUEST)
        if upload.size > MAX_UNIT_FILE_BYTES:
            limit_mb = MAX_UNIT_FILE_BYTES // (1024 * 1024)
            return Response({"detail": f"File is too large. Maximum size is {limit_mb} MB."},
                            status=status.HTTP_400_BAD_REQUEST)
        if UnitFile.objects.filter(unit=unit).count() >= MAX_FILES_PER_UNIT:
            return Response({"detail": f"A unit can hold at most {MAX_FILES_PER_UNIT} files."},
                            status=status.HTTP_400_BAD_REQUEST)
        filename = os.path.basename(upload.name or 'file')[:255] or 'file'
        if os.path.splitext(filename)[1].lower() in BLOCKED_EXTENSIONS:
            return Response({"detail": "This file type is not allowed."}, status=status.HTTP_400_BAD_REQUEST)
        content_type = upload.content_type
        if not content_type or content_type == 'application/octet-stream':
            content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        item = UnitFile.objects.create(
            unit=unit, filename=filename, content_type=content_type[:100],
            size=upload.size, data=upload.read(),
        )
        return Response(UnitFileSerializer(item).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        item = UnitFile.objects.filter(
            pk=pk, unit__semester__academic_year__user=request.user).first()
        if item is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        response = HttpResponse(bytes(item.data), content_type=item.content_type)
        response['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(item.filename)}"
        return response
