"""
Signal handlers to manage default automatic reminders for CATs and Assignments.
Ensures exactly one default reminder per assessment, automatically updated
when deadlines change, without creating duplicates.
"""

import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from assessments.models import CAT, Assignment
from .models import Reminder


def _to_datetime(val):
    if not val:
        return None
    if isinstance(val, datetime.datetime):
        if timezone.is_naive(val):
            return timezone.make_aware(val, timezone.get_current_timezone())
        return val
    if isinstance(val, datetime.date):
        naive_dt = datetime.datetime.combine(val, datetime.time(9, 0, 0))
        return timezone.make_aware(naive_dt, timezone.get_current_timezone())
    if isinstance(val, str):
        parsed = parse_datetime(val)
        if parsed:
            if timezone.is_naive(parsed):
                return timezone.make_aware(parsed, timezone.get_current_timezone())
            return parsed
        parsed_d = parse_date(val)
        if parsed_d:
            naive_dt = datetime.datetime.combine(parsed_d, datetime.time(9, 0, 0))
            return timezone.make_aware(naive_dt, timezone.get_current_timezone())
    return None


def _format_date(val):
    if not val:
        return ""
    if isinstance(val, (datetime.datetime, datetime.date)):
        return val.strftime('%Y-%m-%d')
    if isinstance(val, str):
        # Extract YYYY-MM-DD from prefix if string
        return val[:10]
    return str(val)


@receiver(post_save, sender=CAT)
def sync_cat_automatic_reminder(sender, instance, created, **kwargs):
    """
    Creates or updates the single default automatic reminder for a CAT.
    """
    user = instance.unit.semester.academic_year.user

    if instance.deadline:
        deadline_str = _format_date(instance.deadline)
        reminder_dt = _to_datetime(instance.deadline)
    else:
        deadline_str = _format_date(instance.cat_date)
        reminder_dt = _to_datetime(instance.cat_date)

    title = f"{instance.unit.name} - {deadline_str}"

    existing_reminder = Reminder.objects.filter(
        cat=instance,
        reminder_type=Reminder.ReminderType.AUTOMATIC
    ).first()

    if existing_reminder:
        updated = False
        if existing_reminder.title != title:
            existing_reminder.title = title
            updated = True
        if existing_reminder.reminder_datetime != reminder_dt:
            existing_reminder.reminder_datetime = reminder_dt
            updated = True
        if existing_reminder.user != user:
            existing_reminder.user = user
            updated = True
        if updated:
            existing_reminder.save(update_fields=['title', 'reminder_datetime', 'user', 'updated_at'])
    else:
        Reminder.objects.create(
            user=user,
            cat=instance,
            title=title,
            reminder_datetime=reminder_dt,
            reminder_type=Reminder.ReminderType.AUTOMATIC
        )


@receiver(post_save, sender=Assignment)
def sync_assignment_automatic_reminder(sender, instance, created, **kwargs):
    """
    Creates or updates the single default automatic reminder for an Assignment.
    """
    user = instance.unit.semester.academic_year.user
    deadline_str = _format_date(instance.deadline)
    reminder_dt = _to_datetime(instance.deadline)
    title = f"{instance.unit.name} - {deadline_str}"

    existing_reminder = Reminder.objects.filter(
        assignment=instance,
        reminder_type=Reminder.ReminderType.AUTOMATIC
    ).first()

    if existing_reminder:
        updated = False
        if existing_reminder.title != title:
            existing_reminder.title = title
            updated = True
        if existing_reminder.reminder_datetime != reminder_dt:
            existing_reminder.reminder_datetime = reminder_dt
            updated = True
        if existing_reminder.user != user:
            existing_reminder.user = user
            updated = True
        if updated:
            existing_reminder.save(update_fields=['title', 'reminder_datetime', 'user', 'updated_at'])
    else:
        Reminder.objects.create(
            user=user,
            assignment=instance,
            title=title,
            reminder_datetime=reminder_dt,
            reminder_type=Reminder.ReminderType.AUTOMATIC
        )
