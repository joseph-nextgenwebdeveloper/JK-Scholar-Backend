"""
Notes models for Study Vault backend.
Notes belong to a Unit in the student's academic hierarchy.
"""

from django.db import models


class Note(models.Model):
    """
    Note model associated with a Unit.
    """
    unit = models.ForeignKey(
        'academics.Unit',
        on_delete=models.CASCADE,
        related_name='notes',
        db_index=True
    )
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Note'
        verbose_name_plural = 'Notes'

    def __str__(self):
        return f"{self.title} ({self.unit.code})"


class NoteAttachment(models.Model):
    """
    A file attached to a note.

    The bytes are stored in the database so attachments survive redeploys on
    hosts with an ephemeral filesystem and are reachable from any device the
    student signs in on.
    """
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='attachments', db_index=True)
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100, blank=True, default='application/octet-stream')
    size = models.PositiveIntegerField(default=0)
    data = models.BinaryField(editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']
        verbose_name = 'Note attachment'
        verbose_name_plural = 'Note attachments'

    def __str__(self):
        return f"{self.filename} ({self.size} bytes)"
