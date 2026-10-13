from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0003_unit_lecturer_name_unit_lecturer_phone'),
    ]

    operations = [
        migrations.AddField(
            model_name='academicyear',
            name='cover',
            field=models.CharField(blank=True, default='', help_text='Slug of the cover picture shown in the app', max_length=30),
        ),
        migrations.AddField(
            model_name='semester',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
    ]
