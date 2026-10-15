import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0005_single_active_semester'),
        ('notes', '0002_noteattachment'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnitFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.CharField(max_length=255)),
                ('content_type', models.CharField(blank=True, default='application/octet-stream', max_length=100)),
                ('size', models.PositiveIntegerField(default=0)),
                ('data', models.BinaryField(editable=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='files', to='academics.unit')),
            ],
            options={
                'verbose_name': 'Unit file',
                'verbose_name_plural': 'Unit files',
                'ordering': ['-created_at', '-id'],
            },
        ),
    ]
