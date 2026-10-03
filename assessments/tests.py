"""
Tests for assessments app: CATs and Assignments.
Verifies creation, date handling, status, and user ownership isolation.
"""

from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from academics.models import AcademicYear, Semester, Unit
from .models import CAT, Assignment

User = get_user_model()


class AssessmentTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1', email='user1@example.com', password='Password123!'
        )
        self.user2 = User.objects.create_user(
            username='user2', email='user2@example.com', password='Password123!'
        )

        year1 = AcademicYear.objects.create(user=self.user1, name="Year 1")
        sem1 = Semester.objects.create(academic_year=year1, name="Semester 1")
        self.unit1 = Unit.objects.create(semester=sem1, name="Operating Systems", code="CS301")

        year2 = AcademicYear.objects.create(user=self.user2, name="Year 2")
        sem2 = Semester.objects.create(academic_year=year2, name="Semester 2")
        self.unit2 = Unit.objects.create(semester=sem2, name="Algorithms", code="CS302")

        self.cats_url = reverse('assessments:cat-list')
        self.assignments_url = reverse('assessments:assignment-list')
        self.client.force_authenticate(user=self.user1)

    def test_cat_creation(self):
        payload = {
            'unit': self.unit1.id,
            'title': 'Midterm CAT',
            'description': 'Covers Processes and Threads',
            'cat_date': '2026-10-25',
            'deadline': '2026-10-25T10:00:00Z'
        }
        response = self.client.post(self.cats_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Midterm CAT')
        self.assertTrue(CAT.objects.filter(unit=self.unit1, title='Midterm CAT').exists())

    def test_assignment_creation_and_status(self):
        payload = {
            'unit': self.unit1.id,
            'title': 'Kernel Module Assignment',
            'description': 'Build a simple character device module',
            'deadline': '2026-11-15T23:59:59Z',
            'status': 'PENDING'
        }
        response = self.client.post(self.assignments_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Kernel Module Assignment')
        self.assertEqual(response.data['status'], 'PENDING')
        self.assertTrue(Assignment.objects.filter(unit=self.unit1).exists())

    def test_ownership_isolation(self):
        # User 1 cannot create CAT for User 2's unit
        cat_payload = {
            'unit': self.unit2.id,
            'title': 'Intruder CAT',
            'cat_date': '2026-10-20'
        }
        res_cat = self.client.post(self.cats_url, cat_payload, format='json')
        self.assertEqual(res_cat.status_code, status.HTTP_400_BAD_REQUEST)

        # User 1 cannot create Assignment for User 2's unit
        assignment_payload = {
            'unit': self.unit2.id,
            'title': 'Intruder Assignment',
            'deadline': '2026-10-20T12:00:00Z'
        }
        res_assign = self.client.post(self.assignments_url, assignment_payload, format='json')
        self.assertEqual(res_assign.status_code, status.HTTP_400_BAD_REQUEST)

        # User 1 cannot view User 2's CAT
        cat2 = CAT.objects.create(unit=self.unit2, title='User2 CAT', cat_date='2026-10-20')
        detail_cat_url = reverse('assessments:cat-detail', kwargs={'pk': cat2.id})
        res_get_cat = self.client.get(detail_cat_url)
        self.assertEqual(res_get_cat.status_code, status.HTTP_404_NOT_FOUND)
