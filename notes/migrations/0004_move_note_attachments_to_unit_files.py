from django.db import migrations


def copy_attachments(apps, schema_editor):
    """Notes are text only now: files that were attached to notes move to the unit's
    Files library (copies; the originals are left untouched)."""
    NoteAttachment = apps.get_model('notes', 'NoteAttachment')
    UnitFile = apps.get_model('notes', 'UnitFile')
    for att in NoteAttachment.objects.select_related('note').iterator():
        unit_id = att.note.unit_id
        if UnitFile.objects.filter(unit_id=unit_id, filename=att.filename, size=att.size).exists():
            continue
        UnitFile.objects.create(
            unit_id=unit_id, filename=att.filename, content_type=att.content_type,
            size=att.size, data=att.data,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('notes', '0003_unitfile'),
    ]

    operations = [
        migrations.RunPython(copy_attachments, migrations.RunPython.noop),
    ]
