"""
Tests for academic hierarchy: AcademicYear, Semester, and Unit.
Validates limits:
- Max 6 Academic Years
- Max 3 Semesters per Academic Year
- Max 10 Units per Semester
- Ownership boundaries between users
"""

from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from .models import AcademicYear, Semester, Unit

User = get_user_model()


class AcademicHierarchyTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1', email='user1@example.com', password='Password123!'
        )
        self.user2 = User.objects.create_user(
            username='user2', email='user2@example.com', password='Password123!'
        )
        self.years_url = reverse('academics:academic-year-list')
        self.semesters_url = reverse('academics:semester-list')
        self.units_url = reverse('academics:unit-list')

        self.client.force_authenticate(user=self.user1)

    def test_academic_year_creation(self):
        payload = {'name': 'Year 1', 'start_date': '2026-09-01', 'end_date': '2027-06-30'}
        response = self.client.post(self.years_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Year 1')
        self.assertEqual(AcademicYear.objects.filter(user=self.user1).count(), 1)

    def test_academic_year_maximum_limit_enforced(self):
        # Create 6 academic years (allowed limit)
        for i in range(1, 7):
            AcademicYear.objects.create(user=self.user1, name=f"Year {i}")

        # Attempt to create a 7th academic year
        response = self.client.post(self.years_url, {'name': 'Year 7'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data.get('detail'),
            'You can have a maximum of 6 academic years.'
        )
        self.assertEqual(AcademicYear.objects.filter(user=self.user1).count(), 6)

    def test_semester_creation(self):
        year = AcademicYear.objects.create(user=self.user1, name="Year 1")
        payload = {'academic_year': year.id, 'name': 'Semester 1'}
        response = self.client.post(self.semesters_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Semester 1')
        self.assertEqual(Semester.objects.filter(academic_year=year).count(), 1)

    def test_semester_maximum_limit_enforced(self):
        year = AcademicYear.objects.create(user=self.user1, name="Year 1")
        for i in range(1, 4):
            Semester.objects.create(academic_year=year, name=f"Semester {i}")

        # Attempt to create a 4th semester
        payload = {'academic_year': year.id, 'name': 'Semester 4'}
        response = self.client.post(self.semesters_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data.get('detail'),
            'An academic year can contain a maximum of 3 semesters.'
        )
        self.assertEqual(Semester.objects.filter(academic_year=year).count(), 3)

    def test_unit_creation(self):
        year = AcademicYear.objects.create(user=self.user1, name="Year 1")
        semester = Semester.objects.create(academic_year=year, name="Semester 1")
        payload = {
            'semester': semester.id,
            'name': 'Programming for Internet',
            'code': 'CS101',
            'description': 'Web development concepts'
        }
        response = self.client.post(self.units_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['code'], 'CS101')
        self.assertEqual(Unit.objects.filter(semester=semester).count(), 1)

    def test_unit_maximum_limit_enforced(self):
        year = AcademicYear.objects.create(user=self.user1, name="Year 1")
        semester = Semester.objects.create(academic_year=year, name="Semester 1")
        for i in range(1, 11):
            Unit.objects.create(semester=semester, name=f"Unit {i}", code=f"CODE{i}")

        # Attempt to create an 11th unit
        payload = {
            'semester': semester.id,
            'name': 'Unit 11',
            'code': 'CODE11'
        }
        response = self.client.post(self.units_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data.get('detail'),
            'A semester can contain a maximum of 10 units.'
        )
        self.assertEqual(Unit.objects.filter(semester=semester).count(), 10)

    def test_ownership_data_isolation(self):
        # Create hierarchy for user2
        year_u2 = AcademicYear.objects.create(user=self.user2, name="User2 Year")
        sem_u2 = Semester.objects.create(academic_year=year_u2, name="User2 Semester")
        unit_u2 = Unit.objects.create(semester=sem_u2, name="User2 Unit", code="U201")

        # user1 is authenticated
        # user1 should not see user2's academic year
        res_years = self.client.get(self.years_url)
        self.assertEqual(len(res_years.data['results'] if 'results' in res_years.data else res_years.data), 0)

        # user1 cannot retrieve user2's academic year
        detail_year_url = reverse('academics:academic-year-detail', kwargs={'pk': year_u2.id})
        res_get_year = self.client.get(detail_year_url)
        self.assertEqual(res_get_year.status_code, status.HTTP_404_NOT_FOUND)

        # user1 cannot create a semester under user2's academic year
        res_create_sem = self.client.post(self.semesters_url, {
            'academic_year': year_u2.id,
            'name': 'Intruder Semester'
        }, format='json')
        self.assertEqual(res_create_sem.status_code, status.HTTP_400_BAD_REQUEST)

        # user1 cannot create a unit under user2's semester
        res_create_unit = self.client.post(self.units_url, {
            'semester': sem_u2.id,
            'name': 'Intruder Unit',
            'code': 'INT101'
        }, format='json')
        self.assertEqual(res_create_unit.status_code, status.HTTP_400_BAD_REQUEST)
