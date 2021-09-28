from django.db import models

from siebox.model.abstract import AbstractArchived


class Position(AbstractArchived):
    title = models.CharField(max_length=200)
    description = models.TextField()
    hourly_min = models.IntegerField()
    hourly_max = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.title
