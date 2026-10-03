"""
Tests for reminders app.
Validates:
- Automatic reminder generation on CAT and Assignment creation
- Default reminder naming format: Unit Name + Deadline
- Updating deadline updates automatic reminder without duplicate creation
- Maximum 3 reminders per CAT or Assignment (1 automatic + 2 manual)
- Rejection of 4th reminder attempt
- Ownership isolation between users
- Local notification sync endpoint (/api/reminders/sync/)
"""

from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from academics.models import AcademicYear, Semester, Unit
from assessments.models import CAT, Assignment
from .models import Reminder

User = get_user_model()


class ReminderTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1', email='user1@example.com', password='Password123!'
        )
        self.user2 = User.objects.create_user(
            username='user2', email='user2@example.com', password='Password123!'
        )

        year1 = AcademicYear.objects.create(user=self.user1, name="Year 1")
        sem1 = Semester.objects.create(academic_year=year1, name="Semester 1")
        self.unit1 = Unit.objects.create(
            semester=sem1,
            name="Programming for Internet",
            code="CS101"
        )

        year2 = AcademicYear.objects.create(user=self.user2, name="Year 2")
        sem2 = Semester.objects.create(academic_year=year2, name="Semester 2")
        self.unit2 = Unit.objects.create(
            semester=sem2,
            name="Data Structures",
            code="CS102"
        )

        self.reminders_url = reverse('reminders:reminder-list')
        self.sync_url = reverse('reminders:reminder-sync')
        self.client.force_authenticate(user=self.user1)

    def test_cat_creation_triggers_default_automatic_reminder(self):
        cat = CAT.objects.create(
            unit=self.unit1,
            title='CAT 1',
            cat_date='2026-10-20'
        )

        reminders = Reminder.objects.filter(cat=cat)
        self.assertEqual(reminders.count(), 1)

        auto_reminder = reminders.first()
        self.assertEqual(auto_reminder.reminder_type, Reminder.ReminderType.AUTOMATIC)
        self.assertEqual(auto_reminder.title, "Programming for Internet - 2026-10-20")
        self.assertEqual(auto_reminder.user, self.user1)

    def test_assignment_creation_triggers_default_automatic_reminder(self):
        assignment = Assignment.objects.create(
            unit=self.unit1,
            title='Coursework 1',
            deadline='2026-11-10T18:00:00Z'
        )

        reminders = Reminder.objects.filter(assignment=assignment)
        self.assertEqual(reminders.count(), 1)

        auto_reminder = reminders.first()
        self.assertEqual(auto_reminder.reminder_type, Reminder.ReminderType.AUTOMATIC)
        self.assertEqual(auto_reminder.title, "Programming for Internet - 2026-11-10")
        self.assertEqual(auto_reminder.user, self.user1)

    def test_updating_assessment_deadline_updates_reminder_without_duplicates(self):
        assignment = Assignment.objects.create(
            unit=self.unit1,
            title='Coursework 1',
            deadline='2026-11-10T18:00:00Z'
        )
        self.assertEqual(Reminder.objects.filter(assignment=assignment).count(), 1)

        # Update assignment deadline
        assignment.deadline = '2026-11-20T18:00:00Z'
        assignment.save()

        # Check that there is still exactly 1 automatic reminder with updated title
        reminders = Reminder.objects.filter(assignment=assignment)
        self.assertEqual(reminders.count(), 1)
        self.assertEqual(reminders.first().title, "Programming for Internet - 2026-11-20")

    def test_maximum_3_reminders_limit_enforced(self):
        # Creating assignment automatically generates 1 reminder
        assignment = Assignment.objects.create(
            unit=self.unit1,
            title='Final Project',
            deadline='2026-12-01T23:59:59Z'
        )
        self.assertEqual(Reminder.objects.filter(assignment=assignment).count(), 1)

        # User adds 1st manual reminder (total 2)
        res1 = self.client.post(self.reminders_url, {
            'assignment': assignment.id,
            'title': 'Prep project draft',
            'reminder_datetime': '2026-11-25T10:00:00Z'
        }, format='json')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reminder.objects.filter(assignment=assignment).count(), 2)

        # User adds 2nd manual reminder (total 3)
        res2 = self.client.post(self.reminders_url, {
            'assignment': assignment.id,
            'title': 'Review code and documentation',
            'reminder_datetime': '2026-11-30T10:00:00Z'
        }, format='json')
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reminder.objects.filter(assignment=assignment).count(), 3)

        # User attempts to add a 3rd manual reminder (total 4 - exceeds limit!)
        res3 = self.client.post(self.reminders_url, {
            'assignment': assignment.id,
            'title': 'Last minute panic check',
            'reminder_datetime': '2026-12-01T20:00:00Z'
        }, format='json')
        self.assertEqual(res3.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            res3.data.get('detail'),
            'A CAT or Assignment can have a maximum of 3 reminders.'
        )
        self.assertEqual(Reminder.objects.filter(assignment=assignment).count(), 3)

    def test_user_cannot_add_reminder_to_other_users_assessment(self):
        cat_u2 = CAT.objects.create(
            unit=self.unit2,
            title='User2 CAT',
            cat_date='2026-10-30'
        )

        # user1 attempts to add reminder for user2's CAT
        response = self.client.post(self.reminders_url, {
            'cat': cat_u2.id,
            'title': 'Intruder Reminder',
            'reminder_datetime': '2026-10-29T10:00:00Z'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sync_endpoint_for_offline_local_notifications(self):
        # Create an assignment with its default reminder
        assignment = Assignment.objects.create(
            unit=self.unit1,
            title='Sync Test Assignment',
            deadline='2026-11-10T12:00:00Z'
        )

        response = self.client.get(self.sync_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('server_time', response.data)
        self.assertIn('count', response.data)
        self.assertIn('reminders', response.data)
        self.assertGreaterEqual(response.data['count'], 1)

        first_reminder = response.data['reminders'][0]
        self.assertIn('id', first_reminder)
        self.assertIn('title', first_reminder)
        self.assertIn('reminder_datetime', first_reminder)
        self.assertIn('unit_name', first_reminder)
        self.assertIn('assessment_type', first_reminder)
