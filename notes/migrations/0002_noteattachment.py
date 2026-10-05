import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='NoteAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.CharField(max_length=255)),
                ('content_type', models.CharField(blank=True, default='application/octet-stream', max_length=100)),
                ('size', models.PositiveIntegerField(default=0)),
                ('data', models.BinaryField(editable=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('note', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='notes.note')),
            ],
            options={
                'verbose_name': 'Note attachment',
                'verbose_name_plural': 'Note attachments',
                'ordering': ['created_at', 'id'],
            },
        ),
    ]
