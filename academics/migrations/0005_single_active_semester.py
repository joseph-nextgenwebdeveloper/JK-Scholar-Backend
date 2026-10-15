from django.db import migrations


def one_active_per_user(apps, schema_editor):
    """Keep only the most recently updated active semester of each student."""
    Semester = apps.get_model('academics', 'Semester')
    seen = set()
    active = (Semester.objects.filter(is_active=True)
              .select_related('academic_year').order_by('-updated_at', '-id'))
    for sem in active:
        uid = sem.academic_year.user_id
        if uid in seen:
            Semester.objects.filter(pk=sem.pk).update(is_active=False)
        else:
            seen.add(uid)
    # Students with no active semester get their newest one activated.
    users = set(Semester.objects.values_list('academic_year__user_id', flat=True))
    for uid in users - seen:
        newest = (Semester.objects.filter(academic_year__user_id=uid)
                  .order_by('-academic_year__created_at', '-created_at', '-id').first())
        if newest:
            Semester.objects.filter(pk=newest.pk).update(is_active=True)


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0004_academicyear_cover_semester_is_active'),
    ]

    operations = [
        migrations.RunPython(one_active_per_user, migrations.RunPython.noop),
    ]
