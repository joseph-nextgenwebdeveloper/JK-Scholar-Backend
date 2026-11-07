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
from .models import AcademicYear, Semester, Unit, PlannerEvent

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

    def test_semester_inherits_dates_from_academic_year(self):
        year = AcademicYear.objects.create(
            user=self.user1,
            name="Year With Dates",
            start_date="2026-09-01",
            end_date="2027-06-30"
        )
        payload = {'academic_year': year.id, 'name': 'Semester Inherit'}
        response = self.client.post(self.semesters_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['start_date'], '2026-09-01')
        self.assertEqual(response.data['end_date'], '2027-06-30')

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


class AcademicYearFeatureTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='feat', email='feat@example.com', password='Password123!'
        )
        self.years_url = reverse('academics:academic-year-list')
        self.client.force_authenticate(user=self.user)

    def test_year_creation_auto_creates_two_semesters_first_is_active(self):
        response = self.client.post(self.years_url, {'name': 'Year 1', 'cover': 'library'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['semesters_count'], 2)
        self.assertEqual(response.data['cover'], 'library')
        year = AcademicYear.objects.get(pk=response.data['id'])
        semesters = list(year.semesters.order_by('id'))
        self.assertEqual([s.name for s in semesters], ['First Semester', 'Second Semester'])
        # The student's very first semester becomes the (single) active one.
        self.assertEqual([s.is_active for s in semesters], [True, False])

    def test_activating_a_semester_deactivates_its_sibling(self):
        year = AcademicYear.objects.create(user=self.user, name='Year 1')
        first = Semester.objects.create(academic_year=year, name='First Semester', is_active=True)
        second = Semester.objects.create(academic_year=year, name='Second Semester')
        url = reverse('academics:semester-detail', kwargs={'pk': second.id})
        response = self.client.patch(url, {'is_active': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertFalse(first.is_active)
        self.assertTrue(second.is_active)

    def test_unknown_cover_slug_rejected(self):
        response = self.client.post(self.years_url, {'name': 'Year 1', 'cover': 'nope'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_semester_dates_and_validation(self):
        year = AcademicYear.objects.create(user=self.user, name='Year Dates Test')
        # Invalid: start_date > end_date
        url = reverse('academics:semester-list')
        res = self.client.post(url, {
            'academic_year': year.id,
            'name': 'Semester With Bad Dates',
            'start_date': '2026-06-01',
            'end_date': '2026-01-01',
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Valid dates
        res_ok = self.client.post(url, {
            'academic_year': year.id,
            'name': 'Semester With Good Dates',
            'start_date': '2026-01-01',
            'end_date': '2026-06-01',
        }, format='json')
        self.assertEqual(res_ok.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_ok.data['start_date'], '2026-01-01')
        self.assertEqual(res_ok.data['end_date'], '2026-06-01')


class SingleActiveSemesterTests(APITestCase):
    def test_only_one_active_semester_across_years(self):
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.create_user(username='u1', email='u1@example.com', password='x12345678!')
        self.client.force_authenticate(user)
        y1 = self.client.post('/api/academic-years/', {'name': 'First Year'}, format='json').data['id']
        y2 = self.client.post('/api/academic-years/', {'name': 'Second Year'}, format='json').data['id']
        sems = self.client.get('/api/semesters/').data['results']
        self.assertEqual(sum(1 for s in sems if s['is_active']), 1)       # first one auto-activated
        other = [s for s in sems if s['academic_year'] == y2][0]
        r = self.client.patch(f"/api/semesters/{other['id']}/", {'is_active': True}, format='json')
        self.assertEqual(r.status_code, 200)
        sems = self.client.get('/api/semesters/').data['results']
        self.assertEqual([s['id'] for s in sems if s['is_active']], [other['id']])
        r = self.client.patch(f"/api/semesters/{other['id']}/", {'is_active': False}, format='json')
        self.assertEqual(r.status_code, 400)


class PlannerEventTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='pl', email='pl@example.com', password='Password123!')
        self.client.force_authenticate(self.user)

    def _active_unit(self, code='ECO1', **sem_kw):
        year = AcademicYear.objects.create(user=self.user, name='Year 1')
        sem = Semester.objects.create(academic_year=year, name='Sem 1', is_active=True, **sem_kw)
        return Unit.objects.create(semester=sem, name='Economics', code=code)

    def test_weekly_class_roundtrip_name_comes_from_unit(self):
        unit = self._active_unit()
        r = self.client.post('/api/planner-events/', {
            'kind': 'CLASS', 'unit': unit.id, 'weekday': 1,
            'start_time': '10:00', 'end_time': '13:00', 'location': 'Hall B'}, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data['title'], 'Economics')          # derived, not typed
        self.assertEqual(r.data['semester_active'], True)
        self.assertEqual(self.client.get('/api/planner-events/').data['results'][0]['title'], 'Economics')

    def test_class_rejects_unit_from_inactive_semester_and_missing_unit(self):
        unit = self._active_unit()
        other = Semester.objects.create(academic_year=unit.semester.academic_year, name='Sem 2')
        inactive_unit = Unit.objects.create(semester=other, name='Physics', code='PHY1')
        body = {'kind': 'CLASS', 'weekday': 2, 'start_time': '09:00', 'end_time': '10:00'}
        self.assertEqual(self.client.post('/api/planner-events/', {**body, 'unit': inactive_unit.id},
                                          format='json').status_code, 400)
        self.assertEqual(self.client.post('/api/planner-events/', {**body, 'title': 'Typed'},
                                          format='json').status_code, 400)

    def test_class_can_be_deleted_and_takes_its_reminder_with_it(self):
        unit = self._active_unit()
        ev = self.client.post('/api/planner-events/', {
            'kind': 'CLASS', 'unit': unit.id, 'weekday': 3,
            'start_time': '08:00', 'end_time': '10:00', 'remind_minutes_before': 15}, format='json').data
        from reminders.models import Reminder
        self.assertEqual(Reminder.objects.filter(planner_event_id=ev['id']).count(), 1)
        self.assertEqual(self.client.delete(f"/api/planner-events/{ev['id']}/").status_code, 204)
        self.assertEqual(Reminder.objects.filter(planner_event_id=ev['id']).count(), 0)

    def test_class_needs_weekday_and_valid_times(self):
        unit = self._active_unit('ECO2')
        r = self.client.post('/api/planner-events/', {
            'kind': 'CLASS', 'unit': unit.id, 'start_time': '10:00', 'end_time': '11:00'}, format='json')
        self.assertEqual(r.status_code, 400)
        r = self.client.post('/api/planner-events/', {
            'kind': 'CLASS', 'unit': unit.id, 'weekday': 2,
            'start_time': '12:00', 'end_time': '11:00'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_active_semester_filter(self):
        year = AcademicYear.objects.create(user=self.user, name='Year 1')
        sem1 = Semester.objects.create(academic_year=year, name='Sem 1', is_active=True, start_date='2026-01-01', end_date='2026-05-31')
        sem2 = Semester.objects.create(academic_year=year, name='Sem 2', is_active=False, start_date='2026-06-01', end_date='2026-12-31')
        unit1 = Unit.objects.create(semester=sem1, name='Maths', code='MTH101')
        unit2 = Unit.objects.create(semester=sem2, name='Physics', code='PHY101')

        # Class in active semester
        PlannerEvent.objects.create(user=self.user, kind='CLASS', title='Maths Lecture', unit=unit1, weekday=1, start_time='09:00', end_time='11:00')
        # Class in inactive semester
        PlannerEvent.objects.create(user=self.user, kind='CLASS', title='Physics Lecture', unit=unit2, weekday=2, start_time='09:00', end_time='11:00')
        # Non-academic event within date range
        PlannerEvent.objects.create(user=self.user, kind='EVENT', title='Doctor Appointment', date='2026-03-15', start_time='14:00', end_time='15:00')
        # Non-academic event outside date range
        PlannerEvent.objects.create(user=self.user, kind='EVENT', title='Summer Trip', date='2026-07-20', start_time='10:00', end_time='12:00')

        # Filter by active semester
        res = self.client.get('/api/planner-events/?active_semester=true')
        self.assertEqual(res.status_code, 200)
        titles = [e['title'] for e in res.data['results']]
        self.assertIn('Maths Lecture', titles)
        self.assertIn('Doctor Appointment', titles)
        self.assertNotIn('Physics Lecture', titles)
        self.assertNotIn('Summer Trip', titles)


class YearDeleteRuleTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='yd', email='yd@example.com', password='Password123!')
        self.client.force_authenticate(self.user)

    def test_year_with_units_cannot_be_deleted_but_empty_year_can(self):
        y = self.client.post('/api/academic-years/', {'name': 'Year 1'}, format='json').data['id']
        sem = Semester.objects.filter(academic_year_id=y).first()
        Unit.objects.create(semester=sem, name='Econ', code='EC1')
        r = self.client.delete(f'/api/academic-years/{y}/')
        self.assertEqual(r.status_code, 400)
        self.assertTrue(AcademicYear.objects.filter(pk=y).exists())
        y2 = self.client.post('/api/academic-years/', {'name': 'Year 2'}, format='json').data['id']
        self.assertEqual(self.client.delete(f'/api/academic-years/{y2}/').status_code, 204)

    def test_activate_year(self):
        y1 = self.client.post('/api/academic-years/', {'name': 'Year 1'}, format='json').data['id']
        y2 = self.client.post('/api/academic-years/', {'name': 'Year 2'}, format='json').data['id']
        r = self.client.post(f'/api/academic-years/{y2}/activate/')
        self.assertEqual(r.status_code, 200)
        active = list(Semester.objects.filter(is_active=True, academic_year__user=self.user))
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].academic_year_id, y2)


class ClassReminderTests(APITestCase):
    """A class creates ONE repeating reminder bounded by its semester."""

    def setUp(self):
        self.user = User.objects.create_user(username='cr', email='cr@example.com', password='Password123!')
        self.client.force_authenticate(self.user)
        year = AcademicYear.objects.create(user=self.user, name='Y1')
        self.sem1 = Semester.objects.create(academic_year=year, name='S1', is_active=True,
                                            start_date='2026-01-05', end_date='2026-04-30')
        self.sem2 = Semester.objects.create(academic_year=year, name='S2',
                                            start_date='2026-05-04', end_date='2026-08-28')
        self.u1 = Unit.objects.create(semester=self.sem1, name='Maths', code='M1')
        self.u2 = Unit.objects.create(semester=self.sem2, name='Physics', code='P1')

    def _reminders(self):
        from reminders.models import Reminder
        return Reminder.objects.filter(planner_event__isnull=False)

    def test_class_reminder_repeats_weekly_until_semester_end(self):
        PlannerEvent.objects.create(user=self.user, kind='CLASS', unit=self.u1, title='Maths',
                                    weekday=2, start_time='09:00', end_time='11:00',
                                    remind_minutes_before=10)
        rem = self._reminders().get()
        self.assertEqual(rem.category, 'CLASS_REMINDER')
        self.assertEqual(rem.repeat_days, '2')
        self.assertEqual(str(rem.repeat_until), '2026-04-30')

    def test_switching_active_semester_swaps_which_class_reminders_are_visible(self):
        PlannerEvent.objects.create(user=self.user, kind='CLASS', unit=self.u1, title='Maths',
                                    weekday=1, start_time='09:00', end_time='10:00')
        PlannerEvent.objects.create(user=self.user, kind='CLASS', unit=self.u2, title='Physics',
                                    weekday=1, start_time='11:00', end_time='12:00')
        titles = lambda: sorted(r['title'] for r in self.client.get('/api/reminders/').data['results'])  # noqa: E731
        self.assertEqual(titles(), ['Class: Maths'])
        self.sem2.is_active = True
        self.sem2.save()
        self.assertEqual(titles(), ['Class: Physics'])
        # the sync feed reports exactly the visible ids so other devices can drop the rest
        sync = self.client.get('/api/reminders/sync/').data
        self.assertEqual(len(sync['all_ids']), 1)

    def test_editing_class_updates_reminder_and_event_in_past_is_finished(self):
        ev = PlannerEvent.objects.create(user=self.user, kind='EVENT', title='Old', date='2020-01-01',
                                         start_time='09:00', end_time='10:00')
        self.assertTrue(self._reminders().get(planner_event=ev).is_completed)
