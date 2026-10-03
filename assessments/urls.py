"""
URL configuration for assessments app: CATs and Assignments.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CATViewSet, AssignmentViewSet

app_name = 'assessments'

router = DefaultRouter()
router.register(r'cats', CATViewSet, basename='cat')
router.register(r'assignments', AssignmentViewSet, basename='assignment')

urlpatterns = [
    path('', include(router.urls)),
]
