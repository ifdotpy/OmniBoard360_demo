from django.db import models

from hr.model.position import Position


class Response(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=17, null=True, blank=True)
    email = models.EmailField()
    cv_link = models.URLField(max_length=128, null=True, blank=True)
    position_id = models.ForeignKey(Position, on_delete=models.CASCADE)
    comment = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name
