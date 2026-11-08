from django.db import migrations, models


class Migration(migrations.Migration):
    """Adds the alarm lead time to CATs and assignments (default 1 day = the old behaviour)."""

    dependencies = [
        ('assessments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cat',
            name='remind_minutes_before',
            field=models.PositiveIntegerField(
                default=1440,
                help_text='How many minutes before the CAT the alarm rings (0 = at the time itself)'),
        ),
        migrations.AddField(
            model_name='assignment',
            name='remind_minutes_before',
            field=models.PositiveIntegerField(
                default=1440,
                help_text='How many minutes before the deadline the alarm rings (0 = at the time itself)'),
        ),
    ]
