import base64
from datetime import timedelta

from rest_framework import HTTP_HEADER_ENCODING
from rest_framework.authentication import get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings

from cra.crypto import verify_pss


def is_challenge_not_expired(challenge, request_received, raise_exception=False):
    from cra.views import CHALLENGE_LIFESPAN_SEC
    is_expired = request_received - challenge.created_at > timedelta(seconds=CHALLENGE_LIFESPAN_SEC)

    if raise_exception:
        if is_expired:
            if settings.DEBUG:
                raise AuthenticationFailed(detail='Challenge expired')
            else:
                raise AuthenticationFailed()
    else:
        return is_expired


def is_challenge_response_valid(challenge, data, public_key, raise_exception=False):
    challenge_response = base64.b64decode(data['challenge_response'])
    challenge_bytes = challenge.challenge.encode('ascii')

    is_valid = verify_pss(challenge_response, challenge_bytes, public_key)

    if raise_exception:
        if not is_valid:
            if settings.DEBUG:
                raise AuthenticationFailed(detail='Challenge response is incorrect')
            else:
                raise AuthenticationFailed()
    else:
        return is_valid


def get_userpassword_from_basic_auth(request):
    auth = get_authorization_header(request).split()

    if not auth or auth[0].lower() != b'basic':
        return None

    try:
        auth_parts = base64.b64decode(auth[1]).decode(HTTP_HEADER_ENCODING).partition(':')
    except Exception:
        return None

    return auth_parts[0], auth_parts[2]
