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

from django.conf import settings
from assessments.models import CAT, Assignment
from academics.models import PlannerEvent, Semester
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


def _to_reminder_dt(val):
    dt = _to_datetime(val)
    if not dt:
        return None
    # 1 day before at 9:00 AM (or 24 hours prior)
    one_day_before = dt - datetime.timedelta(days=1)
    # If 1 day before is in the past, use the event datetime itself
    if one_day_before < timezone.now():
        return dt
    return one_day_before


@receiver(post_save, sender=CAT)
def sync_cat_automatic_reminder(sender, instance, created, **kwargs):
    """
    Creates or updates the single default automatic reminder for a CAT (1 day before).
    """
    user = instance.unit.semester.academic_year.user

    target_dt = instance.deadline or instance.cat_date
    reminder_dt = _to_reminder_dt(target_dt)

    existing_reminder = Reminder.objects.filter(
        cat=instance,
        reminder_type=Reminder.ReminderType.AUTOMATIC
    ).first()

    if not reminder_dt:
        if existing_reminder and not existing_reminder.user_modified:
            existing_reminder.delete()
        return

    deadline_str = _format_date(target_dt)
    title = f"{instance.unit.name} - {deadline_str}"

    if existing_reminder:
        updated = False
        # A reminder the student edited keeps their time / title.
        if not existing_reminder.user_modified:
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
    Creates or updates the single default automatic reminder for an Assignment (1 day before).
    """
    user = instance.unit.semester.academic_year.user
    target_dt = instance.deadline
    reminder_dt = _to_reminder_dt(target_dt)

    existing_reminder = Reminder.objects.filter(
        assignment=instance,
        reminder_type=Reminder.ReminderType.AUTOMATIC
    ).first()

    if not reminder_dt:
        if existing_reminder and not existing_reminder.user_modified:
            existing_reminder.delete()
        return

    deadline_str = _format_date(target_dt)
    title = f"{instance.unit.name} - {deadline_str}"

    if existing_reminder:
        updated = False
        # A reminder the student edited keeps their time / title.
        if not existing_reminder.user_modified:
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


# ───────────────────────── Timetable classes / events → reminders ─────────────────────────
#
# A class repeats weekly, so it gets ONE repeating reminder (repeat_days = the weekday it rings
# on, repeat_until = the end of its semester) instead of one row per week. Clients expand the
# repetition locally, exactly as they already do for repeating alarms.

def _class_tz():
    """Class times are wall-clock times in the student's timezone, not UTC."""
    import zoneinfo
    try:
        return zoneinfo.ZoneInfo(getattr(settings, 'CLASS_TIME_ZONE', 'Africa/Nairobi'))
    except Exception:  # unknown tz name -> fall back to the server zone
        return timezone.get_current_timezone()


def class_window(event):
    """(first_date, last_date) the event may occur on; either may be None (= unbounded).

    The semester's real dates are used and never invented. An explicit
    ``event.repeat_until`` can only shorten the window."""
    first = last = None
    sem = event.unit.semester if event.unit_id else None
    if sem is not None:
        first, last = sem.start_date, sem.end_date
    if event.repeat_until and (last is None or event.repeat_until < last):
        last = event.repeat_until
    return first, last


def next_occurrence(event, now=None):
    """Next local (date, start datetime) the event happens on at/after ``now``; None if over."""
    tz = _class_tz()
    now = (now or timezone.now()).astimezone(tz)
    first, last = class_window(event)
    if event.kind == PlannerEvent.KIND_EVENT and event.date:
        day = event.date
        start = datetime.datetime.combine(day, event.start_time, tzinfo=tz)
        return (day, start) if start >= now else None
    if not event.weekday:
        return None
    day = now.date()
    if first and day < first:
        day = first
    # advance to the right weekday
    day += datetime.timedelta(days=(event.weekday - day.isoweekday()) % 7)
    start = datetime.datetime.combine(day, event.start_time, tzinfo=tz)
    if start < now:
        day += datetime.timedelta(days=7)
        start = datetime.datetime.combine(day, event.start_time, tzinfo=tz)
    if last and day > last:
        return None
    return day, start


def sync_planner_event_reminder(event):
    """Create / update / retire the reminder that belongs to a class or event."""
    from django.utils.dateparse import parse_time
    # Objects built in code may still hold the raw strings they were given.
    for f in ('start_time', 'end_time'):
        if isinstance(getattr(event, f), str):
            setattr(event, f, parse_time(getattr(event, f)))
    for f in ('date', 'repeat_until'):
        if isinstance(getattr(event, f), str):
            setattr(event, f, parse_date(getattr(event, f)))
    reminder = Reminder.objects.filter(planner_event=event).first()
    tz = _class_tz()
    minutes = event.remind_minutes_before or 0
    occ = next_occurrence(event)
    _, last = class_window(event)

    if occ:
        fire = occ[1] - datetime.timedelta(minutes=minutes)
        finished = False
    else:  # semester over / one-off event in the past: keep the row, but it is done
        fire = datetime.datetime.combine(
            last or event.date or timezone.now().astimezone(tz).date(), event.start_time, tzinfo=tz
        ) - datetime.timedelta(minutes=minutes)
        finished = True

    repeats = event.kind == PlannerEvent.KIND_CLASS and bool(event.weekday)
    repeat_days = str(fire.astimezone(tz).isoweekday()) if repeats else ''
    label = 'Class' if event.kind == PlannerEvent.KIND_CLASS else 'Event'
    title = f"{label}: {event.title}"
    when = f"{event.start_time.strftime('%H:%M')}–{event.end_time.strftime('%H:%M')}"
    note = when + (f" · {event.location}" if event.location else '')
    if event.unit_id:
        note = f"{event.unit.code} · {note}"

    values = {
        'user_id': event.user_id,
        'category': Reminder.Category.CLASS_REMINDER,
        'repeat_until': last if repeats else None,
    }
    if reminder is None:
        Reminder.objects.create(
            planner_event=event, title=title, note=note,
            reminder_datetime=fire, repeat_days=repeat_days,
            reminder_type=Reminder.ReminderType.AUTOMATIC, is_completed=finished, **values)
        return
    # An alarm the student edited keeps their own time / title / note.
    if not reminder.user_modified:
        reminder.title, reminder.note = title, note
        reminder.reminder_datetime, reminder.repeat_days = fire, repeat_days
        reminder.is_completed = finished
    for k, v in values.items():
        setattr(reminder, k, v)
    reminder.save()


@receiver(post_save, sender=PlannerEvent)
def sync_planner_event_reminder_on_save(sender, instance, **kwargs):
    sync_planner_event_reminder(instance)


@receiver(post_save, sender=Semester)
def resync_class_reminders_on_semester_change(sender, instance, **kwargs):
    """Semester dates / active state changed: the reminders of its classes follow."""
    for event in PlannerEvent.objects.filter(unit__semester=instance).select_related('unit__semester'):
        sync_planner_event_reminder(event)
    # Touch updated_at so incremental sync delivers the (re)appearing / vanishing reminders.
    Reminder.objects.filter(planner_event__unit__semester=instance).update(updated_at=timezone.now())
