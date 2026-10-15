import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0005_single_active_semester'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PlannerEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.CharField(choices=[('CLASS', 'Class'), ('EVENT', 'Event')], default='CLASS', max_length=10)),
                ('title', models.CharField(max_length=150)),
                ('location', models.CharField(blank=True, default='', max_length=150)),
                ('note', models.TextField(blank=True, default='')),
                ('date', models.DateField(blank=True, null=True)),
                ('weekday', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('repeat_until', models.DateField(blank=True, null=True)),
                ('remind_minutes_before', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('unit', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='planner_events', to='academics.unit')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='planner_events', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['weekday', 'date', 'start_time']},
        ),
    ]
