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
