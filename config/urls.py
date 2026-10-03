"""
URL configuration for Study Vault backend project.

Routes:
- /admin/                   Django Administration
- /api/auth/                User Registration, Login (JWT), Logout, Profile
- /api/academic-years/      Academic Years CRUD
- /api/semesters/           Semesters CRUD
- /api/units/               Units CRUD
- /api/notes/               Notes CRUD
- /api/cats/                CATs CRUD
- /api/assignments/         Assignments CRUD
- /api/reminders/           Reminders CRUD & /api/reminders/sync/
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication endpoints
    path('api/auth/', include('accounts.urls')),

    # Academic hierarchy endpoints
    path('api/', include('academics.urls')),

    # Notes endpoints
    path('api/', include('notes.urls')),

    # Assessments endpoints (CATs and Assignments)
    path('api/', include('assessments.urls')),

    # Reminders and local notification synchronization endpoints
    path('api/', include('reminders.urls')),
]
