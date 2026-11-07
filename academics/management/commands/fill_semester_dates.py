"""
Safely fill in missing semester start/end dates.

    python manage.py fill_semester_dates            # dry run: only reports what would change
    python manage.py fill_semester_dates --apply    # writes the changes

Rules (nothing is ever invented):
  * a missing date is copied from the semester's academic year ONLY if the year has that date;
  * semesters that already have dates are never touched;
  * semesters whose year has no dates are listed so the student can enter real dates in the app.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from academics.models import Semester


class Command(BaseCommand):
    help = "Copy missing semester dates from their academic year (dry run unless --apply)."

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Write the changes (default: dry run).')

    def handle(self, *args, **opts):
        changed, unresolved = [], []
        qs = Semester.objects.select_related('academic_year').filter(
            start_date__isnull=True) | Semester.objects.select_related('academic_year').filter(end_date__isnull=True)
        for sem in qs.distinct():
            year = sem.academic_year
            new_start = sem.start_date or year.start_date
            new_end = sem.end_date or year.end_date
            if (new_start, new_end) == (sem.start_date, sem.end_date):
                unresolved.append(sem)
                continue
            changed.append((sem, new_start, new_end))

        for sem, s, e in changed:
            self.stdout.write(f"{'SET ' if opts['apply'] else 'WOULD SET '}{sem} -> {s} .. {e}")
        for sem in unresolved:
            self.stdout.write(self.style.WARNING(
                f"NEEDS DATES (year has none): {sem} - {sem.academic_year.user}"))

        if opts['apply'] and changed:
            with transaction.atomic():
                for sem, s, e in changed:
                    # save() re-validates and re-syncs the class reminders of that semester.
                    sem.start_date, sem.end_date = s, e
                    sem.save()
        self.stdout.write(self.style.SUCCESS(
            f"{len(changed)} updatable, {len(unresolved)} need real dates. "
            + ("Applied." if opts['apply'] else "Dry run only - re-run with --apply.")))
