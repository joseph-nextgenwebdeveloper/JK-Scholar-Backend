"""
Assessment models: CAT (Continuous Assessment Test) and Assignment.
Belong to a Unit in the student's academic hierarchy.
"""

from django.db import models


class CAT(models.Model):
    """
    Continuous Assessment Test (CAT) model.
    """
    unit = models.ForeignKey(
        'academics.Unit',
        on_delete=models.CASCADE,
        related_name='cats',
        db_index=True
    )
    title = models.CharField(max_length=255, help_text="e.g. 'CAT 1'")
    description = models.TextField(blank=True, default='')
    cat_date = models.DateField(help_text="Date when the CAT takes place")
    deadline = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Specific deadline or start datetime if applicable"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['cat_date', 'created_at']
        verbose_name = 'CAT'
        verbose_name_plural = 'CATs'

    def __str__(self):
        return f"{self.title} - {self.unit.name}"


class Assignment(models.Model):
    """
    Assignment model associated with a Unit.
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SUBMITTED = 'SUBMITTED', 'Submitted'
        GRADED = 'GRADED', 'Graded'

    unit = models.ForeignKey(
        'academics.Unit',
        on_delete=models.CASCADE,
        related_name='assignments',
        db_index=True
    )
    title = models.CharField(max_length=255, help_text="e.g. 'Research Essay'")
    description = models.TextField(blank=True, default='')
    deadline = models.DateTimeField(help_text="Submission deadline datetime")
    submission_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['deadline', 'created_at']
        verbose_name = 'Assignment'
        verbose_name_plural = 'Assignments'

    def __str__(self):
        return f"{self.title} - {self.unit.name}"
