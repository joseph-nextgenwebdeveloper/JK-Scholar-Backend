from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_user_degree_user_profile_photo_user_school'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='photo_data',
            field=models.BinaryField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='photo_content_type',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='user',
            name='photo_updated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
