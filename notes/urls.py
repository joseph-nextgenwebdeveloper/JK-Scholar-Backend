"""
URL configuration for notes app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NoteViewSet, NoteAttachmentViewSet, UnitFileViewSet

app_name = 'notes'

router = DefaultRouter()
router.register(r'notes', NoteViewSet, basename='note')
router.register(r'note-attachments', NoteAttachmentViewSet, basename='note-attachment')
router.register(r'files', UnitFileViewSet, basename='unit-file')

urlpatterns = [
    path('', include(router.urls)),
]
