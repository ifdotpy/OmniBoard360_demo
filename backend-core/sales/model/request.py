from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Request(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField()
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    @classmethod
    def create(cls, name: str, email: str, message: str):
        return Request.objects.create(name=name, email=email, message=message)

    def __str__(self):
        return f'Request by {self.name} {self.email} at {self.created}'


@receiver(post_save, sender=Request)
def on_request_created(sender, instance, created, **kwargs):
    if created:
        from celery_tasks.tasks import send_request_notification_mail, send_request_confirmation_mail
        send_request_notification_mail.apply_async((instance.id, ))
        send_request_confirmation_mail.apply_async((instance.id, ))
