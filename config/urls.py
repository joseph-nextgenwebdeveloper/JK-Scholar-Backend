"""
URL configuration for Study Vault / JK Scholar backend.

Routes:
- /health/                  Health check (HTTP 200) — used by cron job monitor
- /admin/                   Django Administration
- /api/auth/                User Registration, Login (JWT), Logout, Profile (+ /api/auth/me/photo/)
- /api/academic-years/      Academic Years CRUD
- /api/semesters/           Semesters CRUD
- /api/units/               Units CRUD
- /api/notes/               Notes CRUD (+ /api/notes/<id>/attachments/, /api/note-attachments/<id>/)
- /api/cats/                CATs CRUD
- /api/assignments/         Assignments CRUD
- /api/reminders/           Reminders CRUD & /api/reminders/sync/
- /api/files/               Unit file library (PDF / Word / ... upload, download)
- /api/snapshot/            All main-screen data in one request
"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

from .snapshot import SnapshotView


def health_check(request):
    """Simple health-check endpoint used by cron-job monitors to keep the server awake."""
    return JsonResponse({"status": "ok"}, status=200)


urlpatterns = [
    # ── Health check (unauthenticated) ─────────────────────────────────────────
    path('health/', health_check),
    path('health', health_check),

    path('admin/', admin.site.urls),

    # Everything the main screens need, in one request
    path('api/snapshot/', SnapshotView.as_view(), name='snapshot'),

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

