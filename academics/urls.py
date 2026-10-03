"""
URL patterns for academic hierarchy: AcademicYear, Semester, and Unit.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AcademicYearViewSet, SemesterViewSet, UnitViewSet

app_name = 'academics'

router = DefaultRouter()
router.register(r'academic-years', AcademicYearViewSet, basename='academic-year')
router.register(r'semesters', SemesterViewSet, basename='semester')
router.register(r'units', UnitViewSet, basename='unit')

urlpatterns = [
    path('', include(router.urls)),
]
