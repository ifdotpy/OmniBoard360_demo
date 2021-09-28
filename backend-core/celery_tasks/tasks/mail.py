from django.contrib.auth.models import User
from sentry_sdk import capture_message

from celery_tasks.celery import app
from sales.model.request import Request
from siebox.util import mail_utils


@app.task()
def send_recovery_mail(user_id: int, recovery_link: str) -> None:
    user = User.objects.get(pk=user_id)
    try:
        mail_utils.send_recovery_mail(user, recovery_link)
    except Exception:
        capture_message("Recovery mail not sent!", level="error")


@app.task()
def send_welcome_mail(user_id: int) -> None:
    user = User.objects.get(pk=user_id)
    try:
        mail_utils.send_welcome_mail(user)
    except Exception:
        capture_message("Welcome mail not sent!", level="error")


@app.task()
def send_request_notification_mail(request_id: int) -> None:
    request = Request.objects.get(pk=request_id)
    try:
        mail_utils.send_request_notification_mail(request)
    except Exception:
        capture_message("Request notification mail not sent!", level="error")


@app.task()
def send_request_confirmation_mail(request_id: int) -> None:
    request = Request.objects.get(pk=request_id)
    try:
        mail_utils.send_request_confirmation_mail(request)
    except Exception:
        capture_message("Request notification mail not sent!", level="error")
