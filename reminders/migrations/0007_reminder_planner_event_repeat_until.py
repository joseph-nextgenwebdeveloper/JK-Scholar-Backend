"""Adds class/event linkage and an end date to reminders. Purely additive: no existing row is
changed, deleted or re-written."""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0007_semester_end_date_semester_start_date'),
        ('reminders', '0006_alter_reminder_reminder_datetime'),
    ]

    operations = [
        migrations.AddField(
            model_name='reminder',
            name='planner_event',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                related_name='reminders', to='academics.plannerevent'),
        ),
        migrations.AddField(
            model_name='reminder',
            name='repeat_until',
            field=models.DateField(
                blank=True, null=True,
                help_text='Last date a repeating reminder may ring (e.g. the end of the semester). Empty = no end.'),
        ),
        migrations.AlterField(
            model_name='reminder',
            name='category',
            field=models.CharField(
                choices=[('CAT_REMINDER', 'CAT Reminder'),
                         ('ASSIGNMENT_REMINDER', 'Assignment Reminder'),
                         ('OTHER', 'Other Notification'),
                         ('CLASS_REMINDER', 'Class / Event Reminder')],
                db_index=True, default='OTHER', max_length=30),
        ),
    ]
