from django.db import models
from django.contrib.auth.models import User

GENRE_CHOICES = [
    ('action', 'Action'),
    ('drama', 'Drama'),
    ('comedy', 'Comedy'),
    ('romance', 'Romance'),
    ('thriller', 'Thriller'),
    ('documentary', 'Documentary'),
    ('animation', 'Animation'),
]

class Video(models.Model):
    title = models.CharField(max_length=100, db_index=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=GENRE_CHOICES, db_index=True)