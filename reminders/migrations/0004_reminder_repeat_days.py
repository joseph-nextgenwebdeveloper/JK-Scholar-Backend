from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reminders', '0003_remove_reminder_reminder_not_both_cat_and_assignment_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='reminder',
            name='repeat_days',
            field=models.CharField(blank=True, default='', help_text='Weekdays the alarm repeats on, comma-separated ISO numbers (1=Mon..7=Sun). Empty = one-time.', max_length=20),
        ),
    ]
