"""
Custom User model for Study Vault backend.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model where email is unique and required.
    """
    email = models.EmailField(unique=True, verbose_name="Email Address")
    school = models.CharField(max_length=255, blank=True, default='', verbose_name="School / University")
    degree = models.CharField(max_length=255, blank=True, default='', verbose_name="Degree / Course")
    profile_photo = models.CharField(max_length=500, blank=True, default='avatar1', verbose_name="Profile Photo / Avatar")
    # Uploaded profile picture. Stored in the database (not on disk) so it survives
    # redeploys on hosts with an ephemeral filesystem such as Render.
    photo_data = models.BinaryField(null=True, blank=True, editable=False)
    photo_content_type = models.CharField(max_length=100, blank=True, default='')
    photo_updated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_joined']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username or self.email
