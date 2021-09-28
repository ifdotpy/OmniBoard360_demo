import random
import secrets
import uuid

from django.contrib.auth.models import User
from django.db import models

MIN_CHALLENGE_CHAR_LENGTH = 16
MAX_CHALLENGE_CHAR_LENGTH = 64


def _random_bytes_length():
    return random.randrange(MIN_CHALLENGE_CHAR_LENGTH // 2, MAX_CHALLENGE_CHAR_LENGTH // 2)


def _gen_challenge():
    return secrets.token_hex(_random_bytes_length())


# todo: cleanup old records
class Challenge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    challenge = models.CharField(default=_gen_challenge, editable=False, max_length=MAX_CHALLENGE_CHAR_LENGTH)
