from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reminders', '0004_reminder_repeat_days'),
    ]

    operations = [
        migrations.AddField(
            model_name='reminder',
            name='user_modified',
            field=models.BooleanField(default=False),
        ),
    ]
