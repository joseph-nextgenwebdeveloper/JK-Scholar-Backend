"""
URL configuration for reminders app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReminderViewSet

app_name = 'reminders'

router = DefaultRouter()
router.register(r'reminders', ReminderViewSet, basename='reminder')

urlpatterns = [
    path('', include(router.urls)),
]
