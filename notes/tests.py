"""
Tests for notes app.
Verifies CRUD operations and strict user ownership boundaries.
"""

from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from academics.models import AcademicYear, Semester, Unit
from .models import Note

User = get_user_model()


class NoteTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1', email='user1@example.com', password='Password123!'
        )
        self.user2 = User.objects.create_user(
            username='user2', email='user2@example.com', password='Password123!'
        )

        year1 = AcademicYear.objects.create(user=self.user1, name="Year 1")
        sem1 = Semester.objects.create(academic_year=year1, name="Semester 1")
        self.unit1 = Unit.objects.create(semester=sem1, name="Computer Networks", code="CS201")

        year2 = AcademicYear.objects.create(user=self.user2, name="Year 2")
        sem2 = Semester.objects.create(academic_year=year2, name="Semester 2")
        self.unit2 = Unit.objects.create(semester=sem2, name="Database Systems", code="CS202")

        self.notes_url = reverse('notes:note-list')
        self.client.force_authenticate(user=self.user1)

    def test_note_creation(self):
        payload = {
            'unit': self.unit1.id,
            'title': 'OSI Model Summary',
            'content': 'Layer 1: Physical, Layer 2: Data Link...'
        }
        response = self.client.post(self.notes_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'OSI Model Summary')
        self.assertEqual(Note.objects.filter(unit=self.unit1).count(), 1)

    def test_note_list_scoped_to_user(self):
        Note.objects.create(unit=self.unit1, title='User 1 Note', content='Content')
        Note.objects.create(unit=self.unit2, title='User 2 Note', content='Content')

        response = self.client.get(self.notes_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'User 1 Note')

    def test_user_cannot_access_or_create_for_other_user_unit(self):
        # Attempt to create note for user2's unit
        payload = {
            'unit': self.unit2.id,
            'title': 'Intruder Note',
            'content': 'Attempting unauthorized write'
        }
        response = self.client.post(self.notes_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Attempt to retrieve user2's note
        note2 = Note.objects.create(unit=self.unit2, title='Private Note', content='Secret')
        detail_url = reverse('notes:note-detail', kwargs={'pk': note2.id})
        get_res = self.client.get(detail_url)
        self.assertEqual(get_res.status_code, status.HTTP_404_NOT_FOUND)


class UnitFileSearchTests(APITestCase):
    """Several documents per unit, and a server-side search over them."""

    def setUp(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.Upload = SimpleUploadedFile
        self.user = User.objects.create_user(username='fs', email='fs@example.com', password='Password123!')
        self.client.force_authenticate(self.user)
        year = AcademicYear.objects.create(user=self.user, name='Year 2')
        sem = Semester.objects.create(academic_year=year, name='Semester 1')
        self.unit = Unit.objects.create(semester=sem, name='Microeconomics', code='ECO201')

    def _upload(self, name, content_type='application/pdf'):
        return self.client.post('/api/files/', {
            'unit': self.unit.id, 'file': self.Upload(name, b'x' * 10, content_type=content_type)},
            format='multipart')

    def test_multiple_documents_in_one_unit_and_search(self):
        for n in ('lecture1.pdf', 'lecture2.docx', 'slides.pptx'):
            self.assertEqual(self._upload(n).status_code, 201)
        self.assertEqual(len(self.client.get(f'/api/files/?unit={self.unit.id}').data['results']), 3)
        by = lambda q: sorted(f['filename'] for f in self.client.get(f'/api/files/?search={q}').data['results'])  # noqa: E731
        self.assertEqual(by('pptx'), ['slides.pptx'])        # extension
        self.assertEqual(by('eco201'), ['lecture1.pdf', 'lecture2.docx', 'slides.pptx'])  # unit code
        self.assertEqual(by('micro+lecture1'.replace('+', ' ')), ['lecture1.pdf'])  # all words must match
        self.assertEqual(by('year'), ['lecture1.pdf', 'lecture2.docx', 'slides.pptx'])  # academic year
        self.assertEqual(by('nomatch'), [])
        f = self.client.get('/api/files/?search=slides').data['results'][0]
        self.assertEqual((f['extension'], f['semester_name'], f['academic_year_name']),
                         ('pptx', 'Semester 1', 'Year 2'))
